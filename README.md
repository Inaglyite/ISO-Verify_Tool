# Windows ISO 校验工具

一个基于 Python + Tkinter 的桌面工具，用于校验 Windows 镜像文件的完整性。

## 截图


## 功能

- **SHA512 / SHA256 / SHA1 / MD5** — 四种哈希算法可选

- **拖放 + 浏览** — 支持拖放 ISO 到窗口，也可点按钮浏览选择

- **进度条** — 大文件分块读取，实时显示百分比和 MB 进度

- **多线程** — 后台计算哈希，UI 不卡死

- **大小写不敏感** — 哈希比对时自动忽略大小写

## 运行

### 从源码运行

```
pip install tkinterdnd2  
python windows-ISO-verify.py
```

### 打包为可执行文件

```
pip install pyinstaller  
pyinstaller --onefile --name win-iso-verify windows-ISO-verify.py  
\# 输出在 dist/ 目录下
```

> **注意**：PyInstaller 只能在当前操作系统上打当前系统的包。 要在 Windows 上生成 `.exe`，需要在 Windows 机器上执行上述命令。

## 依赖

| 包 | 用途 |
| - | - |
| `tkinter` | GUI 界面（Python 自带） |
| `tkinterdnd2` | 拖放文件支持 |


## 使用方法

1. 选择哈希算法（默认 SHA256）

2. 拖放 ISO 文件到窗口，或点击"浏览"选择

3. 填入微软官方公布的期望哈希值

4. 点击"开始校验"

5. 绿色 = 通过，红色 = 失败并显示计算值和期望值对比

## 许可证

GNU General Public License v3.0

