# Hermes Agent 打包指南

## 打包为 EXE (Windows)

### 方法一：使用打包脚本（推荐）

双击运行 `build_exe.bat` 即可自动完成打包。

### 方法二：手动打包

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 单文件打包（推荐）
pyinstaller --onefile --name hermes --console run.py

# 3. 使用配置文件打包
pyinstaller hermes.spec
```

### 常用打包选项

| 选项 | 说明 |
|------|------|
| `--onefile` | 打包为单个 EXE 文件 |
| `--onedir` | 打包为目录（启动更快） |
| `--console` | 显示控制台窗口（调试用） |
| `--windowed` | 隐藏控制台窗口（发布用） |
| `--icon hermes.ico` | 设置应用程序图标 |
| `--name hermes` | 输出文件名 |
| `--add-data webui.html;.` | 包含额外文件 |

### 示例：发布版本（无控制台）

```bash
pyinstaller --onefile --windowed --name hermes --icon hermes.ico run.py
```

## 输出文件

- `dist/hermes.exe` — 可执行文件
- 可单独运行，无需 Python 环境

## 注意事项

1. **文件大小**: 单文件 EXE 约 50-100 MB（包含 Python 运行时）
2. **首次启动**: 可能稍慢，因为需要解压运行时
3. **防病毒软件**: 部分杀毒软件可能误报 PyInstaller 打包的程序
4. **路径问题**: 程序运行时会在临时目录解压，确保有足够空间

## 测试打包结果

```bash
# 运行打包后的程序
dist\hermes.exe

# 指定 API 地址
dist\hermes.exe --url http://127.0.0.1:8001

# 使用 PyQt6 界面
dist\hermes.exe --qt
```

## 常见问题

### Q: 提示 "No module named 'xxx'"
A: 添加隐藏导入 `--hidden-import xxx`

### Q: 文件太大
A: 使用 `--onedir` 模式，或安装 `upx` 压缩

### Q: 中文显示乱码
A: 确保 Python 文件使用 UTF-8 编码，或设置 `PYTHONIOENCODING=utf-8`

### Q: 缺少 webui.html
A: 使用 `--add-data webui.html;.` 包含该文件
