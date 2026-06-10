import hashlib
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def compute_hash(filepath, algo, progress_callback=None):
    """计算文件哈希（1 MB 分块，适合 8 GB+ 镜像）。"""
    file_size = os.path.getsize(filepath)
    h = hashlib.new(algo)
    read = 0
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            read += len(chunk)
            if progress_callback:
                progress_callback(read, file_size)
    return h.hexdigest().lower()


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------

FONT_TITLE = ("", 16, "bold")
FONT_NORMAL = ("", 11)
FONT_SMALL = ("", 10)


class App:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Windows 镜像校验工具")
        self.window.geometry("620x550")
        self.window.resizable(True, True)
        self.window.minsize(560, 500)

        self.filepath = None
        self._result_queue = queue.Queue()
        self._progress_queue = queue.Queue()

        self._setup_ui()
        self._poll_queues()

    # ---- UI 构建 ----

    def _setup_ui(self):
        # ---------- 标题 ----------
        tk.Label(
            self.window, text="Windows ISO 哈希校验", font=FONT_TITLE
        ).pack(pady=(20, 10))

        # ---------- 算法选择 ----------
        algo_frame = tk.Frame(self.window)
        algo_frame.pack(pady=5)
        tk.Label(algo_frame, text="哈希算法：").pack(side=tk.LEFT)

        self.algo_var = tk.StringVar(value="sha256")
        for text, value in [("MD5", "md5"), ("SHA1", "sha1"), ("SHA256", "sha256")]:
            ttk.Radiobutton(
                algo_frame, text=text, value=value, variable=self.algo_var
            ).pack(side=tk.LEFT, padx=8)

        # ---------- 文件选择 ----------
        file_frame = tk.LabelFrame(self.window, text="镜像文件", padx=10, pady=10)
        file_frame.pack(pady=(10, 5), padx=40, fill=tk.X)

        tk.Label(
            file_frame,
            text="选择要校验的 Windows 镜像 ISO 文件",
        ).pack(pady=(0, 8))

        btn_frame = tk.Frame(file_frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="浏览...", width=12, command=self._browse).pack(
            side=tk.LEFT, padx=5
        )

        # 选中文件提示
        self.lbl_file = tk.Label(
            self.window, text="未选择文件", fg="gray", font=FONT_SMALL
        )
        self.lbl_file.pack(pady=(0, 8))

        # ---------- 期望哈希 ----------
        hash_frame = tk.Frame(self.window)
        hash_frame.pack(pady=5)
        tk.Label(hash_frame, text="期望哈希值：").pack(side=tk.LEFT)

        self.hash_entry = tk.Entry(hash_frame, width=64)
        self.hash_entry.pack(side=tk.LEFT, padx=5)

        # ---------- 进度条 ----------
        self.progress = ttk.Progressbar(self.window, mode="determinate", length=520)
        self.progress.pack(pady=(10, 0))
        self.lbl_progress = tk.Label(self.window, text="", fg="gray", font=FONT_SMALL)
        self.lbl_progress.pack()

        # ---------- 结果显示 ----------
        self.lbl_result = tk.Label(
            self.window,
            text="",
            font=FONT_NORMAL,
            fg="black",
            justify=tk.LEFT,
        )
        self.lbl_result.pack(pady=(5, 0))

        # ---------- 校验按钮 ----------
        self.btn_verify = tk.Button(
            self.window, text="开始校验", width=15, height=2, command=self._verify
        )
        self.btn_verify.pack(pady=(10, 10))

    # ---- 主线程轮询 ----

    def _poll_queues(self):
        try:
            while True:
                pct, read, total = self._progress_queue.get_nowait()
                self.progress["value"] = pct
                self.lbl_progress.config(
                    text=f"{pct}%  "
                    f"({read / (1024**2):.0f} / {total / (1024**2):.0f} MB)"
                )
        except queue.Empty:
            pass

        try:
            while True:
                result = self._result_queue.get_nowait()
                self._show_result(result)
        except queue.Empty:
            pass

        self.window.after(100, self._poll_queues)

    def _show_result(self, result):
        self.btn_verify.config(state=tk.NORMAL, text="开始校验")
        self.lbl_progress.config(text="100%")
        self.progress["value"] = 100

        error = result.get("error")
        if error:
            self.lbl_result.config(text=f"计算出错：{error}", fg="red")
            return

        algo = result["algo"]
        actual = result["actual"]
        expected = result["expected"]
        matched = result["matched"]

        if matched:
            self.lbl_result.config(
                text=(
                    f"校验通过！\n"
                    f"算法：{algo.upper()}\n"
                    f"计算值：{actual.upper()}\n"
                    f"期望值：{expected.upper()}"
                ),
                fg="green",
            )
        else:
            self.lbl_result.config(
                text=(
                    f"校验失败！\n"
                    f"算法：{algo.upper()}\n"
                    f"计算值：{actual.upper()}\n"
                    f"期望值：{expected.upper()}"
                ),
                fg="red",
            )

    # ---- 回调 ----

    def _browse(self):
        path = filedialog.askopenfilename(
            title="选择 Windows 镜像",
            filetypes=[("ISO 文件", "*.iso"), ("所有文件", "*.*")],
        )
        if path:
            self.filepath = path
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.lbl_file.config(
                text=f"{os.path.basename(path)}  ({size_mb:.0f} MB)", fg="black"
            )

    def _verify(self):
        if not self.filepath:
            self.lbl_result.config(text="请先选择镜像文件！", fg="red")
            return

        expected = self.hash_entry.get().strip().lower()
        if not expected:
            self.lbl_result.config(text="请输入期望的哈希值！", fg="red")
            return

        algo = self.algo_var.get()
        filepath = self.filepath

        self.btn_verify.config(state=tk.DISABLED, text="计算中...")
        self.progress["value"] = 0
        self.lbl_progress.config(text="0%")
        self.lbl_result.config(text="")

        def _run():
            try:
                actual = compute_hash(
                    filepath, algo,
                    progress_callback=lambda read, total: (
                        self._progress_queue.put(
                            (int(read / total * 100), read, total)
                        )
                    ),
                )
                self._result_queue.put({
                    "algo": algo,
                    "actual": actual,
                    "expected": expected,
                    "matched": actual == expected,
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._result_queue.put({"error": str(e)})

        threading.Thread(target=_run, daemon=True).start()


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = App()
    app.window.mainloop()
