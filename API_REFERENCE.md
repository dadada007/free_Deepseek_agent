# Hermes API 参考文档

*自动生成于 2026-08-18 10:09:57*

## 📊 统计概览

- **文件数:** 96
- **模块数:** 96
- **类数:** 29
- **函数数:** 544
- **方法数:** 225

## 📑 目录

- [agent](#agent)
- [archive_tools](#archive_tools)
- [audio_tools](#audio_tools)
- [background_tasks_tools](#background_tasks_tools)
- [barcode_tools](#barcode_tools)
- [bookmark_tools](#bookmark_tools)
- [chart_tools](#chart_tools)
- [client](#client)
- [codeformat_tools](#codeformat_tools)
- [color_tools](#color_tools)
- [convert_tools](#convert_tools)
- [csv_tools](#csv_tools)
- [currency_tools](#currency_tools)
- [dbbak_tools](#dbbak_tools)
- [debug_tools](#debug_tools)
- [diff_tools](#diff_tools)
- [dir_reader_tools](#dir_reader_tools)
- [dir_tools](#dir_tools)
- [doc_generators_tools](#doc_generators_tools)
- [email_tools](#email_tools)
- [env_tools](#env_tools)
- [execute_tools](#execute_tools)
- [file_edit_tools](#file_edit_tools)
- [file_operations_tools](#file_operations_tools)
- [file_search_tools](#file_search_tools)
- [fs_bom_utils](#fs_bom_utils)
- [fs_editor](#fs_editor)
- [fs_io_core](#fs_io_core)
- [fs_lock_utils](#fs_lock_utils)
- [fs_mutation](#fs_mutation)
- [fs_path_utils](#fs_path_utils)
- [fs_register](#fs_register)
- [fs_shell](#fs_shell)
- [func_list_tools](#func_list_tools)
- [gif_tools](#gif_tools)
- [git_tools](#git_tools)
- [gui_qt](#gui_qt)
- [hash_tools](#hash_tools)
- [health_tools](#health_tools)
- [hot_reload](#hot_reload)
- [html_tools](#html_tools)
- [http_server_tools](#http_server_tools)
- [image_tools](#image_tools)
- [ini_tools](#ini_tools)
- [log_tools](#log_tools)
- [markdown_tools](#markdown_tools)
- [media_tools](#media_tools)
- [memory](#memory)
- [memory_db](#memory_db)
- [memory_tools](#memory_tools)
- [network_tools](#network_tools)
- [notify_tools](#notify_tools)
- [parseemail_tools](#parseemail_tools)
- [parser](#parser)
- [password_tools](#password_tools)
- [permission_tools](#permission_tools)
- [pinyin_tools](#pinyin_tools)
- [plan_tools](#plan_tools)
- [planner](#planner)
- [port_tools](#port_tools)
- [progress_tools](#progress_tools)
- [qr_tools](#qr_tools)
- [rag_tools](#rag_tools)
- [random_tools](#random_tools)
- [regex_tools](#regex_tools)
- [rss_tools](#rss_tools)
- [run](#run)
- [scan_tools](#scan_tools)
- [schedule_tools](#schedule_tools)
- [search_tools](#search_tools)
- [smart_file_reader_tools](#smart_file_reader_tools)
- [sort_tools](#sort_tools)
- [stock_tools](#stock_tools)
- [summarize_tools](#summarize_tools)
- [sync_tools](#sync_tools)
- [sysdetail_tools](#sysdetail_tools)
- [system_tools](#system_tools)
- [text_tools](#text_tools)
- [time_tools](#time_tools)
- [todo_manager_tools](#todo_manager_tools)
- [tool_index](#tool_index)
- [tool_index](#tool_index)
- [tools](#tools)
- [translate_tools](#translate_tools)
- [tree_tools](#tree_tools)
- [utils](#utils)
- [validate_tools](#validate_tools)
- [video_tools](#video_tools)
- [watch_tools](#watch_tools)
- [web_tools](#web_tools)
- [wsl_advanced_tools](#wsl_advanced_tools)
- [wsl_tools](#wsl_tools)
- [xml_tools](#xml_tools)
- [yaml_tools](#yaml_tools)

---

# 模块: agent

**文件:** `agent.py`

Agent 核心循环 - 简化版

## 常量

- `MAX_TOOL_RESULT_CHARS` = `50000`

## 函数

### _inject_memories_into_prompt

```python
def _inject_memories_into_prompt(system_prompt: str, user_message: str) -> str
```

将相关记忆注入到系统提示中

**参数:**
- `system_prompt`: str **必填**
- `user_message`: str **必填**


## 类

## class Agent

Agent - 支持并行工具调用，集成记忆系统

---

### __init__

```python
def __init__(client: Client, max_rounds: int, parallel: bool, max_workers: int, on_tool_call: Callable, on_tool_result: Callable, on_thinking: Callable)
```

**参数:**
- `client`: Client **必填**
- `max_rounds`: int (默认: `100`)
- `parallel`: bool (默认: `True`)
- `max_workers`: int (默认: `4`)
- `on_tool_call`: Callable (默认: `None`)
- `on_tool_result`: Callable (默认: `None`)
- `on_thinking`: Callable (默认: `None`)

### request_stop

```python
def request_stop()
```

### reset_stop

```python
def reset_stop()
```

### should_stop

```python
def should_stop() -> bool
```

### chat

```python
def chat(user_message: str) -> str
```

**参数:**
- `user_message`: str **必填**

### _execute_one

```python
def _execute_one(tc: dict) -> dict
```

执行单个工具调用

**参数:**
- `tc`: dict **必填**

### _execute_parallel

```python
def _execute_parallel(tool_calls: List[dict]) -> List[dict]
```

并行执行多个工具调用

**参数:**
- `tool_calls`: List[dict] **必填**

### reset

```python
def reset()
```


---

# 模块: archive_tools

**文件:** `agent_tools/archive_tools.py`

压缩解压工具集 - 支持 ZIP、TAR、GZ、BZ2、XZ 等格式

## 函数

### _ensure_dir

```python
def _ensure_dir(path)
```

**参数:**
- `path` **必填**


### _get_file_size

```python
def _get_file_size(path)
```

**参数:**
- `path` **必填**


### _list_files

```python
def _list_files(dir_path)
```

**参数:**
- `dir_path` **必填**


### _zip_files

```python
def _zip_files(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _unzip_files

```python
def _unzip_files(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _tar_files

```python
def _tar_files(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _untar_files

```python
def _untar_files(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _list_archive_content

```python
def _list_archive_content(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: audio_tools

**文件:** `agent_tools/audio_tools.py`

音频处理工具集 - 获取音频信息

## 函数

### _audio_info

```python
def _audio_info(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: background_tasks_tools

**文件:** `agent_tools/background_tasks_tools.py`

后台任务管理模块

## 函数

### _run_background

```python
def _run_background(args: dict) -> str
```

后台运行命令，返回任务ID

**参数:**
- `args`: dict **必填**


### _task_output

```python
def _task_output(args: dict) -> str
```

查看后台任务输出

**参数:**
- `args`: dict **必填**


### _kill_task

```python
def _kill_task(args: dict) -> str
```

终止后台任务

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: barcode_tools

**文件:** `agent_tools/barcode_tools.py`

条形码生成工具集 - 生成条形码

## 函数

### _generate_barcode

```python
def _generate_barcode(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: bookmark_tools

**文件:** `agent_tools/bookmark_tools.py`

浏览器书签工具集 - 支持提取、整理书签

## 函数

### _extract_bookmarks

```python
def _extract_bookmarks(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: chart_tools

**文件:** `agent_tools/chart_tools.py`

数据可视化工具集 - 支持生成图表、报表、仪表盘

## 函数

### _import_matplotlib

```python
def _import_matplotlib()
```


### _ensure_dir

```python
def _ensure_dir(path)
```

**参数:**
- `path` **必填**


### _line_chart

```python
def _line_chart(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _bar_chart

```python
def _bar_chart(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _pie_chart

```python
def _pie_chart(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _scatter_plot

```python
def _scatter_plot(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: client

**文件:** `client.py`

API 客户端 - 连接 g.py DeepSeek Browser 服务

## 类

## class ChatResult

一次回复的结果

---

### __init__

```python
def __init__(content: str, tool_calls: List[dict])
```

**参数:**
- `content`: str (默认: `None`)
- `tool_calls`: List[dict] (默认: `None`)

### has_tools

```python
def has_tools() -> bool
```


## class Client

OpenAI 兼容 API 客户端

---

### __init__

```python
def __init__(base_url: str, model: str, session_id: str, api_key: str, agent_name: str)
```

**参数:**
- `base_url`: str (默认: `'http://127.0.0.1:8003'`)
- `model`: str (默认: `'deepseek-browser'`)
- `session_id`: str (默认: `None`)
- `api_key`: str (默认: `'sk-admin'`)
- `agent_name`: str (默认: `None`)

### chat_url

```python
def chat_url() -> str
```

**装饰器:** `@property`

### chat

```python
def chat(messages: List[Dict], tools: List[Dict], stream: bool, new_conversation: bool) -> ChatResult
```

发送对话请求

**参数:**
- `messages`: List[Dict] **必填**
- `tools`: List[Dict] (默认: `None`)
- `stream`: bool (默认: `False`)
- `new_conversation`: bool (默认: `False`)

### reset_conversation

```python
def reset_conversation()
```

### _chat_sync

```python
def _chat_sync(payload: dict) -> ChatResult
```

**参数:**
- `payload`: dict **必填**

### cancel_request

```python
def cancel_request()
```

### _chat_stream

```python
def _chat_stream(payload: dict) -> ChatResult
```

**参数:**
- `payload`: dict **必填**

### reset

```python
def reset() -> dict
```

### status

```python
def status() -> dict
```

### login

```python
def login() -> dict
```


---

# 模块: codeformat_tools

**文件:** `agent_tools/codeformat_tools.py`

代码格式化工具集 - 格式化Python、JSON、HTML代码

## 函数

### _format_code

```python
def _format_code(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: color_tools

**文件:** `agent_tools/color_tools.py`

颜色处理工具集 - 支持颜色格式转换、调色

## 函数

### _hex_to_rgb

```python
def _hex_to_rgb(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _rgb_to_hex

```python
def _rgb_to_hex(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: convert_tools

**文件:** `agent_tools/convert_tools.py`

单位转换工具集 - 支持长度、重量、温度转换

## 函数

### _convert_length

```python
def _convert_length(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _convert_temp

```python
def _convert_temp(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: csv_tools

**文件:** `agent_tools/csv_tools.py`

CSV处理工具集 - 支持读取、写入、转换

## 函数

### _read_csv

```python
def _read_csv(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _write_csv

```python
def _write_csv(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _csv_to_json

```python
def _csv_to_json(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: currency_tools

**文件:** `agent_tools/currency_tools.py`

货币转换工具集 - 汇率转换

## 函数

### _convert_currency

```python
def _convert_currency(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: dbbak_tools

**文件:** `agent_tools/dbbak_tools.py`

数据库备份工具集 - SQLite备份与恢复

## 函数

### _backup_db

```python
def _backup_db(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: debug_tools

**文件:** `agent_tools/debug_tools.py`

代码调试助手工具集（P0）

## 常量

- `_HERMES_DIR` = `os.path.dirname(...)`

## 函数

### _unescape_code

```python
def _unescape_code(code: str) -> str
```

**参数:**
- `code`: str **必填**


### _run_cmd

```python
def _run_cmd(cmd: list, timeout: int, cwd: str) -> dict
```

**参数:**
- `cmd`: list **必填**
- `timeout`: int **必填**
- `cwd`: str (默认: `None`)


### _debug_run_code

```python
def _debug_run_code(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _explain_error

```python
def _explain_error(error_text: str, language: str) -> list
```

**参数:**
- `error_text`: str **必填**
- `language`: str (默认: `'python'`)


### _debug_explain_error

```python
def _debug_explain_error(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _debug_analyze

```python
def _debug_analyze(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _debug_check_file

```python
def _debug_check_file(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: diff_tools

**文件:** `agent_tools/diff_tools.py`

文件差异对比工具集 - 支持文本差异对比

## 函数

### _diff_text

```python
def _diff_text(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: dir_reader_tools

**文件:** `agent_tools/dir_reader_tools.py`

友好目录阅读工具
功能：以树形结构展示目录内容，包含文件大小、修改时间、类型统计等

## 常量

- `FILE_ICONS` = `{}`

## 函数

### _format_size

```python
def _format_size(size: int) -> str
```

格式化文件大小

**参数:**
- `size`: int **必填**


### _format_time

```python
def _format_time(mtime: float) -> str
```

格式化修改时间

**参数:**
- `mtime`: float **必填**


### _get_icon

```python
def _get_icon(name: str, is_dir: bool) -> str
```

获取文件/目录图标

**参数:**
- `name`: str **必填**
- `is_dir`: bool **必填**


### _tree_walk

```python
def _tree_walk(path: str, prefix: str, max_depth: int, current_depth: int, show_hidden: bool, max_items: int) -> Tuple[List[str], Dict]
```

递归遍历目录，生成树形结构

**参数:**
- `path`: str **必填**
- `prefix`: str (默认: `''`)
- `max_depth`: int (默认: `3`)
- `current_depth`: int (默认: `0`)
- `show_hidden`: bool (默认: `False`)
- `max_items`: int (默认: `200`)


### _read_directory

```python
def _read_directory(args: dict) -> str
```

读取目录内容，以树形结构展示。
参数:
    path: 目录路径
    depth: 扫描深度（默认 3，范围 1-6）
    show_hidden: 是否显示隐藏文件（默认 False）
    max_items: 每层最多显示条目数（默认 200）

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```

注册所有工具


---

# 模块: dir_tools

**文件:** `agent_tools/dir_tools.py`

## 函数

### _list_dir

```python
def _list_dir(args)
```

**参数:**
- `args` **必填**


### _format_size

```python
def _format_size(size_bytes)
```

**参数:**
- `size_bytes` **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: doc_generators_tools

**文件:** `agent_tools/doc_generators_tools.py`

文档生成工具集 - 支持 PPT、PDF、Word、Excel 生成

## 函数

### _import_pptx

```python
def _import_pptx()
```


### _import_docx

```python
def _import_docx()
```


### _import_openpyxl

```python
def _import_openpyxl()
```


### _import_reportlab

```python
def _import_reportlab()
```


### _ensure_dir

```python
def _ensure_dir(path)
```

**参数:**
- `path` **必填**


### _get_extension

```python
def _get_extension(path)
```

**参数:**
- `path` **必填**


### _generate_ppt

```python
def _generate_ppt(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _generate_pdf

```python
def _generate_pdf(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _generate_word

```python
def _generate_word(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _generate_excel

```python
def _generate_excel(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```

卸载工具


---

# 模块: email_tools

**文件:** `agent_tools/email_tools.py`

邮件自动化工具集 - 支持发送邮件、读取邮件、批量发送、附件支持

## 常量

- `_EMAIL_CONFIG` = `{}`

## 函数

### _set_email_config

```python
def _set_email_config(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _send_email

```python
def _send_email(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _read_emails

```python
def _read_emails(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _batch_send_email

```python
def _batch_send_email(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _get_email_config

```python
def _get_email_config(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: env_tools

**文件:** `agent_tools/env_tools.py`

环境变量管理工具集 - 支持查看、设置、删除环境变量

## 函数

### _get_env

```python
def _get_env(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _set_env

```python
def _set_env(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _delete_env

```python
def _delete_env(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: execute_tools

**文件:** `agent_tools/execute_tools.py`

执行命令工具 - 统一 execute_command 接口

## 函数

### _execute_command

```python
def _execute_command(args: dict) -> str
```

执行命令并返回结果（同步）

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: file_edit_tools

**文件:** `agent_tools/file_edit_tools.py`

精准编辑模块 - 极简版（不做任何转义处理）

## 函数

### edit_file

```python
def edit_file(args: dict) -> str
```

精准编辑文件

支持模式:
- replace: 字面字符串替换 (old_string, new_string, replace_all)
- regex_replace: 正则替换 (pattern, replacement)  
- replace_lines: 行替换 (start_line, end_line, content)
- insert: 插入行 (start_line, content)
- delete: 删除行 (start_line, end_line)
- append: 追加内容 (content)

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools(tools_module)
```

注册所有工具到 tools 模块

**参数:**
- `tools_module` **必填**


---

# 模块: file_operations_tools

**文件:** `agent_tools/file_operations_tools.py`

工具注册和执行 - 使用全局 tools.TOOLS

## 常量

- `CHUNK_THRESHOLD` = `20000`
- `CHUNK_SIZE` = `20000`

## 函数

### write_file

```python
def write_file(args: dict) -> str
```

写入文件 - 直接写入，不做任何转义处理

**参数:**
- `args`: dict **必填**


### _generate_summary

```python
def _generate_summary(content: str, file_path: str) -> str
```

生成文件摘要 - 扫描全部行

**参数:**
- `content`: str **必填**
- `file_path`: str **必填**


### read_file

```python
def read_file(args: dict) -> str
```

读取文件 - 智能分块

参数:
    file_path: 文件路径
    raw: 是否返回原始完整内容（默认 False）
    chunk_index: 指定读取第几块（从1开始），不指定则返回第一块
    chunk_size: 每块大小（字符数），默认 20000

行为:
    - 文件小于阈值（20000字符）时，直接返回完整内容
    - 文件大于阈值时，自动分块，返回摘要 + 当前块内容

**参数:**
- `args`: dict **必填**


### append_file

```python
def append_file(args: dict) -> str
```

追加内容到文件

**参数:**
- `args`: dict **必填**


### delete_file

```python
def delete_file(args: dict) -> str
```

删除文件

**参数:**
- `args`: dict **必填**


### rename_file

```python
def rename_file(args: dict) -> str
```

重命名文件

**参数:**
- `args`: dict **必填**


### list_dir

```python
def list_dir(args: dict) -> str
```

列出目录

**参数:**
- `args`: dict **必填**


### get_cwd

```python
def get_cwd(args: dict) -> str
```

获取当前工作目录

**参数:**
- `args`: dict **必填**


---

# 模块: file_search_tools

**文件:** `agent_tools/file_search_tools.py`

文件搜索工具集 - 支持按名称、内容、大小搜索

## 函数

### _format_size

```python
def _format_size(size)
```

**参数:**
- `size` **必填**


### _search_by_name

```python
def _search_by_name(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _search_by_content

```python
def _search_by_content(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _search_by_size

```python
def _search_by_size(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: fs_bom_utils

**文件:** `agent_tools/fs_bom_utils.py`

fs_bom_utils.py - UTF-8 BOM 检测与处理

提供：
- UTF-8 BOM 检测
- BOM 分离与合并
- 带 BOM 的文本读写

借鉴 OpenCode 的 BOM 处理设计

## 常量

- `UTF8_BOM` = `b'\xef\xbb\xbf'`

## 函数

### has_utf8_bom

```python
def has_utf8_bom(content: bytes) -> bool
```

检查字节内容是否包含 UTF-8 BOM

示例：
    has_utf8_bom(b'ï»¿Hello') → True
    has_utf8_bom(b'Hello') → False

**参数:**
- `content`: bytes **必填**


### split_bom

```python
def split_bom(text: str) -> Tuple[bool, str]
```

分离 BOM 和文本内容

返回：
    (是否包含BOM, 去除BOM后的文本)

示例：
    split_bom('﻿Hello') → (True, 'Hello')
    split_bom('Hello') → (False, 'Hello')

**参数:**
- `text`: str **必填**


### join_bom

```python
def join_bom(text: str, include_bom: bool) -> str
```

根据需要在文本前添加 BOM

如果 include_bom 为 True，则确保文本以 BOM 开头。
如果文本已有 BOM，则保持只有一个 BOM。

示例：
    join_bom('Hello', True) → '﻿Hello'
    join_bom('﻿Hello', True) → '﻿Hello'
    join_bom('Hello', False) → 'Hello'

**参数:**
- `text`: str **必填**
- `include_bom`: bool **必填**


### detect_bom_from_file

```python
def detect_bom_from_file(file_path: str) -> bool
```

检测文件是否包含 UTF-8 BOM

示例：
    detect_bom_from_file('C:/file.txt') → True  # 如果包含 BOM

**参数:**
- `file_path`: str **必填**


### read_text_with_bom

```python
def read_text_with_bom(file_path: str, encoding: str) -> Tuple[bool, str, str]
```

读取文本文件，返回 BOM 状态和内容

返回：
    (是否包含BOM, 文本内容, 实际使用的编码)

示例：
    has_bom, content, enc = read_text_with_bom('C:/file.txt')

**参数:**
- `file_path`: str **必填**
- `encoding`: str (默认: `'utf-8'`)


### read_text_without_bom

```python
def read_text_without_bom(file_path: str, encoding: str) -> str
```

读取文本文件，自动去除 BOM

与 read_text_with_bom 的区别：只返回内容

**参数:**
- `file_path`: str **必填**
- `encoding`: str (默认: `'utf-8'`)


### write_text_with_bom

```python
def write_text_with_bom(file_path: str, content: str, preserve_bom: bool, encoding: str) -> None
```

写入文本文件，根据 preserve_bom 决定是否保留 BOM

参数：
    file_path: 文件路径
    content: 文本内容
    preserve_bom: 是否保留 BOM（写入时添加 BOM）
    encoding: 编码（默认 utf-8）

示例：
    write_text_with_bom('C:/file.txt', 'Hello', preserve_bom=True)

**参数:**
- `file_path`: str **必填**
- `content`: str **必填**
- `preserve_bom`: bool (默认: `True`)
- `encoding`: str (默认: `'utf-8'`)


### write_text_preserving_bom

```python
def write_text_preserving_bom(file_path: str, content: str, encoding: str) -> None
```

写入文本，保留原有的 BOM 状态

如果文件已存在，检测其 BOM 状态并保持一致。
如果文件不存在，不添加 BOM。

这是 write_text_with_bom 的便捷版本。

**参数:**
- `file_path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)


### remove_bom_from_string

```python
def remove_bom_from_string(text: str) -> str
```

从字符串中移除 BOM（如果有）

示例：
    remove_bom_from_string('﻿Hello') → 'Hello'

**参数:**
- `text`: str **必填**


### add_bom_to_string

```python
def add_bom_to_string(text: str) -> str
```

在字符串前添加 BOM（如果还没有）

示例：
    add_bom_to_string('Hello') → '﻿Hello'
    add_bom_to_string('﻿Hello') → '﻿Hello'

**参数:**
- `text`: str **必填**


### ensure_bom_consistent

```python
def ensure_bom_consistent(text: str, target_has_bom: bool) -> str
```

确保文本的 BOM 状态与目标一致

如果 target_has_bom 为 True，则确保有 BOM
如果 target_has_bom 为 False，则确保没有 BOM

**参数:**
- `text`: str **必填**
- `target_has_bom`: bool **必填**


---

# 模块: fs_editor

**文件:** `agent_tools/fs_editor.py`

文件编辑 - 极简版（不做任何转义处理）

## 函数

### _read_lines

```python
def _read_lines(path: str) -> List[str]
```

读取文件为行列表

**参数:**
- `path`: str **必填**


### _write_lines

```python
def _write_lines(path: str, lines: List[str]) -> None
```

将行列表写入文件

**参数:**
- `path`: str **必填**
- `lines`: List[str] **必填**


### _get_line_indent

```python
def _get_line_indent(line: str) -> str
```

获取行的缩进字符串

**参数:**
- `line`: str **必填**


### _find_line_matching

```python
def _find_line_matching(lines: List[str], pattern: str, start_from: int, match_type: str) -> int
```

在行列表中查找匹配的行

**参数:**
- `lines`: List[str] **必填**
- `pattern`: str **必填**
- `start_from`: int (默认: `0`)
- `match_type`: str (默认: `'exact'`)


### replace_string

```python
def replace_string(file_path: str, old_string: str, new_string: str, replace_all: bool) -> Dict[str, Any]
```

字符串替换

**参数:**
- `file_path`: str **必填**
- `old_string`: str **必填**
- `new_string`: str **必填**
- `replace_all`: bool (默认: `True`)


### regex_replace

```python
def regex_replace(file_path: str, pattern: str, replacement: str) -> Dict[str, Any]
```

正则替换

**参数:**
- `file_path`: str **必填**
- `pattern`: str **必填**
- `replacement`: str **必填**


### insert_lines

```python
def insert_lines(file_path: str, content: str, after: Optional[str], before: Optional[str], at_line: Optional[int], match_type: str) -> Dict[str, Any]
```

插入行

**参数:**
- `file_path`: str **必填**
- `content`: str **必填**
- `after`: Optional[str] (默认: `None`)
- `before`: Optional[str] (默认: `None`)
- `at_line`: Optional[int] (默认: `None`)
- `match_type`: str (默认: `'exact'`)


### delete_lines

```python
def delete_lines(file_path: str, start_line: Optional[int], end_line: Optional[int], pattern: Optional[str], match_type: str) -> Dict[str, Any]
```

删除行

**参数:**
- `file_path`: str **必填**
- `start_line`: Optional[int] (默认: `None`)
- `end_line`: Optional[int] (默认: `None`)
- `pattern`: Optional[str] (默认: `None`)
- `match_type`: str (默认: `'contains'`)


### edit_file

```python
def edit_file(args: dict) -> str
```

编辑文件

支持模式:
- replace: 字符串替换 (old_string, new_string, replace_all)
- regex_replace: 正则替换 (pattern, replacement)
- insert: 插入行 (content, after/before/at_line)
- delete: 删除行 (start_line/end_line/pattern)
- append: 追加内容 (content)

**参数:**
- `args`: dict **必填**


### edit_file_v2

```python
def edit_file_v2(args: dict) -> dict
```

edit_file_v2 - 兼容 fs_register.py 的接口

和 edit_file 一样，但返回 dict 而不是 str

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools(tools_module)
```

注册所有工具到 tools 模块

**参数:**
- `tools_module` **必填**


---

# 模块: fs_io_core

**文件:** `agent_tools/fs_io_core.py`

fs_io_core.py - 文件系统核心 I/O

提供：
- 文件读写（字符串/字节）
- 目录操作（创建/删除/遍历）
- 文件查询（glob/grep/find_up）
- 文件信息（stat）

借鉴 OpenCode 的 FSUtil 设计

## 函数

### read_file_safe

```python
def read_file_safe(path: str) -> Optional[str]
```

安全读取文件内容（自动处理 BOM）

**参数:**
- `path`: str **必填**


### write_file_safe

```python
def write_file_safe(path: str, content: str, preserve_bom: bool) -> bool
```

安全写入文件（自动创建目录）

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `preserve_bom`: bool (默认: `True`)


## 类

## class FSError(Exception)

文件系统操作错误


## class FSUtil

文件系统工具类
借鉴 OpenCode 的 FSUtil 设计

---

### exists

```python
def exists(path: str) -> bool
```

检查路径是否存在

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### is_file

```python
def is_file(path: str) -> bool
```

检查是否为文件

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### is_dir

```python
def is_dir(path: str) -> bool
```

检查是否为目录

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### is_symlink

```python
def is_symlink(path: str) -> bool
```

检查是否为符号链接

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### is_absolute

```python
def is_absolute(path: str) -> bool
```

检查是否为绝对路径

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### ensure_dir

```python
def ensure_dir(path: str) -> None
```

确保目录存在，自动创建父目录

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### mkdir

```python
def mkdir(path: str, mode: int) -> None
```

创建目录（父目录必须存在）

**参数:**
- `path`: str **必填**
- `mode`: int (默认: `493`)

**装饰器:** `@staticmethod`

### mkdirs

```python
def mkdirs(path: str, mode: int) -> None
```

创建目录（自动创建父目录）

**参数:**
- `path`: str **必填**
- `mode`: int (默认: `493`)

**装饰器:** `@staticmethod`

### rmdir

```python
def rmdir(path: str) -> None
```

删除空目录

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### rmtree

```python
def rmtree(path: str) -> None
```

递归删除目录

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### list_dir

```python
def list_dir(path: str) -> List[str]
```

列出目录内容（仅名称）

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### list_dir_with_info

```python
def list_dir_with_info(path: str) -> List[Dict[str, Any]]
```

列出目录内容（带详细信息）

返回每个条目的：
    - name: 名称
    - path: 完整路径
    - type: file/directory/symlink/other
    - size: 大小（字节）
    - mtime: 修改时间

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### read_file_bytes

```python
def read_file_bytes(path: str) -> bytes
```

读取文件为字节

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### read_file_string

```python
def read_file_string(path: str, encoding: str) -> str
```

读取文件为字符串，自动处理 BOM

**参数:**
- `path`: str **必填**
- `encoding`: str (默认: `'utf-8'`)

**装饰器:** `@staticmethod`

### read_file_string_safe

```python
def read_file_string_safe(path: str, encoding: str) -> Optional[str]
```

安全读取，文件不存在返回 None

**参数:**
- `path`: str **必填**
- `encoding`: str (默认: `'utf-8'`)

**装饰器:** `@staticmethod`

### read_json

```python
def read_json(path: str) -> Dict[str, Any]
```

读取 JSON 文件

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### write_file_bytes

```python
def write_file_bytes(path: str, content: bytes, mode: Optional[int]) -> None
```

写入字节文件

**参数:**
- `path`: str **必填**
- `content`: bytes **必填**
- `mode`: Optional[int] (默认: `None`)

**装饰器:** `@staticmethod`

### write_file_string

```python
def write_file_string(path: str, content: str, encoding: str, preserve_bom: bool, mode: Optional[int]) -> None
```

写入字符串文件，支持 BOM

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)
- `preserve_bom`: bool (默认: `False`)
- `mode`: Optional[int] (默认: `None`)

**装饰器:** `@staticmethod`

### write_with_dirs

```python
def write_with_dirs(path: str, content: Union[str, bytes], encoding: str, preserve_bom: bool, mode: Optional[int]) -> None
```

写入文件，自动创建父目录
借鉴 OpenCode 的 writeWithDirs

**参数:**
- `path`: str **必填**
- `content`: Union[str, bytes] **必填**
- `encoding`: str (默认: `'utf-8'`)
- `preserve_bom`: bool (默认: `False`)
- `mode`: Optional[int] (默认: `None`)

**装饰器:** `@staticmethod`

### write_text_preserving_bom

```python
def write_text_preserving_bom(path: str, content: str, encoding: str) -> None
```

写入文本，保留原有的 BOM 状态
借鉴 OpenCode 的 writeTextPreservingBom

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)

**装饰器:** `@staticmethod`

### write_if_unchanged

```python
def write_if_unchanged(path: str, content: Union[str, bytes], expected_content: Union[str, bytes], encoding: str, preserve_bom: bool) -> bool
```

条件写入：只有当当前内容与 expected_content 一致时才写入

返回：
    True 表示写入成功
    False 表示内容已变化，未写入

借鉴 OpenCode 的 writeIfUnchanged

**参数:**
- `path`: str **必填**
- `content`: Union[str, bytes] **必填**
- `expected_content`: Union[str, bytes] **必填**
- `encoding`: str (默认: `'utf-8'`)
- `preserve_bom`: bool (默认: `False`)

**装饰器:** `@staticmethod`

### remove

```python
def remove(path: str) -> bool
```

删除文件或空目录

返回：
    True 表示存在并删除
    False 表示不存在

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### remove_recursive

```python
def remove_recursive(path: str) -> bool
```

递归删除目录或文件

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### stat

```python
def stat(path: str) -> Dict[str, Any]
```

获取文件信息

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### file_size

```python
def file_size(path: str) -> int
```

获取文件大小（字节）

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### file_hash

```python
def file_hash(path: str, algorithm: str) -> str
```

计算文件哈希

**参数:**
- `path`: str **必填**
- `algorithm`: str (默认: `'sha256'`)

**装饰器:** `@staticmethod`

### glob

```python
def glob(pattern: str, root: str, recursive: bool) -> List[str]
```

通配符搜索
返回匹配文件相对于 root 的路径列表

**参数:**
- `pattern`: str **必填**
- `root`: str (默认: `'.'`)
- `recursive`: bool (默认: `True`)

**装饰器:** `@staticmethod`

### grep

```python
def grep(pattern: str, root: str, file_pattern: Optional[str], max_results: int, ignore_case: bool) -> List[Dict[str, Any]]
```

跨文件搜索内容（正则）

返回：
    [
        {'file': 'src/main.py', 'line': 10, 'content': '...'},
        ...
    ]

**参数:**
- `pattern`: str **必填**
- `root`: str **必填**
- `file_pattern`: Optional[str] (默认: `None`)
- `max_results`: int (默认: `100`)
- `ignore_case`: bool (默认: `True`)

**装饰器:** `@staticmethod`

### find_up

```python
def find_up(target: str, start: str, stop: Optional[str]) -> List[str]
```

向上查找文件

从 start 目录开始向上查找，找到所有匹配 target 的路径。

示例：
    find_up('package.json', '/project/src', '/project')

**参数:**
- `target`: str **必填**
- `start`: str **必填**
- `stop`: Optional[str] (默认: `None`)

**装饰器:** `@staticmethod`

### copy

```python
def copy(src: str, dst: str, overwrite: bool) -> None
```

复制文件或目录

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)

**装饰器:** `@staticmethod`

### move

```python
def move(src: str, dst: str, overwrite: bool) -> None
```

移动文件或目录

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)

**装饰器:** `@staticmethod`


---

# 模块: fs_lock_utils

**文件:** `agent_tools/fs_lock_utils.py`

fs_lock_utils.py - 文件锁与线程安全

提供：
- 基于线程的 KeyedMutex 锁
- 上下文管理器支持
- 跨线程文件操作安全

借鉴 OpenCode 的 KeyedMutex 设计

## 函数

### writer

```python
def writer(thread_id: int, content: str)
```

**参数:**
- `thread_id`: int **必填**
- `content`: str **必填**


## 类

## class FileLock

基于线程的文件锁（KeyedMutex 模式）

每个文件路径对应一个独立的 threading.Lock，
确保同一时刻只有一个线程操作该文件。

用法：
    with FileLock.with_lock("C:/path/to/file.txt"):
        # 安全的文件操作
        pass

注意：
    - 这是线程级锁，不是进程级锁
    - 适用于单进程内的多线程并发场景

---

### get_lock

```python
def get_lock(path: str) -> threading.Lock
```

获取指定路径的锁

如果锁不存在则创建，保证同一路径共享同一把锁。

**参数:**
- `path`: str **必填**

**装饰器:** `@classmethod`

### with_lock

```python
def with_lock(path: str)
```

上下文管理器，自动获取和释放锁

用法：
    with FileLock.with_lock("C:/file.txt"):
        # 临界区代码
        pass

**参数:**
- `path`: str **必填**

**装饰器:** `@classmethod`, `@contextmanager`

### try_lock

```python
def try_lock(path: str, timeout: Optional[float]) -> bool
```

尝试获取锁（带超时）

返回：
    True 表示成功获取锁
    False 表示超时或失败

用法：
    if FileLock.try_lock("C:/file.txt", timeout=1.0):
        try:
            # 临界区代码
            pass
        finally:
            FileLock.unlock("C:/file.txt")

**参数:**
- `path`: str **必填**
- `timeout`: Optional[float] (默认: `None`)

**装饰器:** `@classmethod`

### unlock

```python
def unlock(path: str) -> None
```

手动释放锁

注意：仅当使用 try_lock 获取锁后调用

**参数:**
- `path`: str **必填**

**装饰器:** `@classmethod`

### is_locked

```python
def is_locked(path: str) -> bool
```

检查指定路径是否被锁定

**参数:**
- `path`: str **必填**

**装饰器:** `@classmethod`

### clear_locks

```python
def clear_locks() -> None
```

清空所有锁（测试用）

**装饰器:** `@classmethod`


---

# 模块: fs_mutation

**文件:** `agent_tools/fs_mutation.py`

文件变更层 - 极简版（不做任何转义处理）

## 函数

### safe_write_file

```python
def safe_write_file(path: str, content: str, preserve_bom: bool, encoding: str) -> dict
```

安全写入文件 - 直接写入，preserve_bom 参数忽略（保持兼容）

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `preserve_bom`: bool (默认: `True`)
- `encoding`: str (默认: `'utf-8'`)


### safe_append_file

```python
def safe_append_file(path: str, content: str, encoding: str) -> dict
```

安全追加文件

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)


### safe_create_file

```python
def safe_create_file(path: str, content: str, preserve_bom: bool, encoding: str) -> dict
```

创建文件（已存在则失败）

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `preserve_bom`: bool (默认: `True`)
- `encoding`: str (默认: `'utf-8'`)


### safe_remove_file

```python
def safe_remove_file(path: str) -> dict
```

安全删除文件

**参数:**
- `path`: str **必填**


### safe_copy_file

```python
def safe_copy_file(src: str, dst: str, overwrite: bool) -> dict
```

安全复制文件

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)


### safe_move_file

```python
def safe_move_file(src: str, dst: str, overwrite: bool) -> dict
```

安全移动文件

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)


### write_file

```python
def write_file(path: str, content: str, encoding: str) -> dict
```

写入文件

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)


### append_file

```python
def append_file(path: str, content: str, encoding: str) -> dict
```

追加内容

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)


### delete_file

```python
def delete_file(path: str) -> dict
```

删除文件

**参数:**
- `path`: str **必填**


### copy_file

```python
def copy_file(src: str, dst: str, overwrite: bool) -> dict
```

复制文件

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)


### move_file

```python
def move_file(src: str, dst: str, overwrite: bool) -> dict
```

移动文件

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)


## 类

## class FileMutation

文件变更操作 - 极简版，只做原子写入，不做转义

---

### _atomic_write

```python
def _atomic_write(path: str, content: str, encoding: str) -> dict
```

原子写入：先写临时文件，再替换；失败时回退到直接写入

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)

**装饰器:** `@staticmethod`

### write

```python
def write(path: str, content: str, encoding: str) -> dict
```

写入文件 - 直接写入，不做任何转义

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)

**装饰器:** `@staticmethod`

### append

```python
def append(path: str, content: str, encoding: str) -> dict
```

追加内容到文件

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `encoding`: str (默认: `'utf-8'`)

**装饰器:** `@staticmethod`

### delete

```python
def delete(path: str) -> dict
```

删除文件

**参数:**
- `path`: str **必填**

**装饰器:** `@staticmethod`

### copy

```python
def copy(src: str, dst: str, overwrite: bool) -> dict
```

复制文件

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)

**装饰器:** `@staticmethod`

### move

```python
def move(src: str, dst: str, overwrite: bool) -> dict
```

移动文件

**参数:**
- `src`: str **必填**
- `dst`: str **必填**
- `overwrite`: bool (默认: `True`)

**装饰器:** `@staticmethod`


---

# 模块: fs_path_utils

**文件:** `agent_tools/fs_path_utils.py`

fs_path_utils.py - 路径处理与安全校验

提供：
- 路径标准化（含Windows路径兼容）
- 路径安全校验（防止越界）
- 路径查询工具

借鉴 OpenCode 的路径处理设计

## 函数

### windows_path

```python
def windows_path(p: str) -> str
```

将 Linux/cygwin/WSL 风格的路径转换为 Windows 风格

示例：
    /c:/Users → C:/Users
    /c/Users  → C:/Users
    /cygdrive/c/Users → C:/Users
    /mnt/c/Users → C:/Users

**参数:**
- `p`: str **必填**


### normalize_path

```python
def normalize_path(p: str) -> str
```

标准化路径，解析符号链接，转为绝对路径

示例：
    normalize_path("C:/temp/../file.txt") → "C:/file.txt"
    normalize_path("/c/Users") → "C:/Users"

**参数:**
- `p`: str **必填**


### to_posix_path

```python
def to_posix_path(p: str) -> str
```

将路径转为 POSIX 风格（正斜杠）

**参数:**
- `p`: str **必填**


### is_absolute_path

```python
def is_absolute_path(p: str) -> bool
```

检查是否为绝对路径

**参数:**
- `p`: str **必填**


### is_relative_path

```python
def is_relative_path(p: str) -> bool
```

检查是否为相对路径

**参数:**
- `p`: str **必填**


### contains

```python
def contains(parent: str, child: str) -> bool
```

检查 child 是否在 parent 目录内（含自身）

示例：
    contains("C:/project", "C:/project/src/main.py") → True
    contains("C:/project", "C:/other/file.txt") → False

**参数:**
- `parent`: str **必填**
- `child`: str **必填**


### resolve_safe

```python
def resolve_safe(base_dir: str, target: str) -> str
```

解析路径，确保不逃逸出 base_dir

如果越界则抛出 ValueError

示例：
    resolve_safe("C:/project", "src/main.py") → "C:/project/src/main.py"
    resolve_safe("C:/project", "../../etc/passwd") → ValueError

**参数:**
- `base_dir`: str **必填**
- `target`: str **必填**


### resolve_relative

```python
def resolve_relative(base_dir: str, target: str) -> str
```

解析相对路径，返回相对于 base_dir 的标准化路径
不进行安全检查（仅解析）

**参数:**
- `base_dir`: str **必填**
- `target`: str **必填**


### is_path_inside

```python
def is_path_inside(base_dir: str, target: str) -> tuple
```

检查目标路径是否在 base_dir 内（安全版本，不抛异常）

返回: (是否安全, 标准化后的路径, 错误信息)

**参数:**
- `base_dir`: str **必填**
- `target`: str **必填**


### get_extension

```python
def get_extension(p: str) -> str
```

获取文件扩展名（包含点）

**参数:**
- `p`: str **必填**


### get_stem

```python
def get_stem(p: str) -> str
```

获取文件名（不含扩展名）

**参数:**
- `p`: str **必填**


### get_basename

```python
def get_basename(p: str) -> str
```

获取文件名（含扩展名）

**参数:**
- `p`: str **必填**


### get_dirname

```python
def get_dirname(p: str) -> str
```

获取目录名

**参数:**
- `p`: str **必填**


### join_paths

```python
def join_paths(*paths: str) -> str
```

拼接路径并标准化

**参数:**
- `*paths`: str


### get_parents

```python
def get_parents(p: str) -> List[str]
```

获取路径的所有父目录（从近到远）

示例：
    get_parents("C:/project/src/main.py") →
    ["C:/project/src", "C:/project", "C:/"]

**参数:**
- `p`: str **必填**


### is_subpath

```python
def is_subpath(parent: str, child: str) -> bool
```

检查 child 是否是 parent 的子路径（等价于 contains）

**参数:**
- `parent`: str **必填**
- `child`: str **必填**


### get_common_parent

```python
def get_common_parent(paths: List[str]) -> Optional[str]
```

获取多个路径的共同父目录

示例：
    get_common_parent(["C:/project/src/a.py", "C:/project/src/b.py"]) → "C:/project/src"

**参数:**
- `paths`: List[str] **必填**


### get_relative_path

```python
def get_relative_path(base: str, target: str) -> str
```

获取 target 相对于 base 的相对路径

示例：
    get_relative_path("C:/project", "C:/project/src/main.py") → "src/main.py"

**参数:**
- `base`: str **必填**
- `target`: str **必填**


### match_pattern

```python
def match_pattern(name: str, pattern: str) -> bool
```

检查文件名是否匹配通配符模式

支持：* 和 ? 通配符

示例：
    match_pattern("main.py", "*.py") → True
    match_pattern("test.txt", "*.py") → False

**参数:**
- `name`: str **必填**
- `pattern`: str **必填**


### match_patterns

```python
def match_patterns(name: str, patterns: List[str]) -> bool
```

检查文件名是否匹配多个通配符模式中的任意一个

**参数:**
- `name`: str **必填**
- `patterns`: List[str] **必填**


---

# 模块: fs_register

**文件:** `agent_tools/fs_register.py`

fs_register.py - 统一注册所有文件系统工具到 Hermes

注册约 30+ 个工具到 Hermes 工具系统。
采用动态导入，确保热加载环境下闭包正常工作。

## 函数

### _get_module

```python
def _get_module(name)
```

动态导入模块，确保每次调用时重新获取

**参数:**
- `name` **必填**


### _safe_call

```python
def _safe_call(module_name, func_path, args)
```

**参数:**
- `module_name` **必填**
- `func_path` **必填**
- `args` **必填**


### _smart_read_file

```python
def _smart_read_file(args)
```

智能读取文件 - 直接使用 file_operations_tools 中的 read_file
支持分块参数：chunk_index, chunk_size, raw

**参数:**
- `args` **必填**


### register_fs_tools

```python
def register_fs_tools()
```

注册所有文件系统工具到 Hermes


---

# 模块: fs_shell

**文件:** `agent_tools/fs_shell.py`

fs_shell.py - 安全命令执行与后台任务管理

提供：
- 安全命令执行（超时、进程树管理）
- 后台任务管理（运行、查询、杀死）
- Shell 检测与选择
- 跨平台兼容（Windows/Linux/macOS）

借鉴 OpenCode 的 Shell 设计 + new2_tools.py 实现

## 常量

- `SHELL_META` = `{}`

## 函数

### get_shell_name

```python
def get_shell_name(shell_path: str) -> str
```

获取 shell 名称

**参数:**
- `shell_path`: str **必填**


### get_shell_meta

```python
def get_shell_meta(shell_path: str) -> Dict[str, bool]
```

获取 shell 元数据

**参数:**
- `shell_path`: str **必填**


### is_shell_acceptable

```python
def is_shell_acceptable(shell_path: str) -> bool
```

检查 shell 是否被拒绝

**参数:**
- `shell_path`: str **必填**


### is_login_shell

```python
def is_login_shell(shell_path: str) -> bool
```

是否为登录 shell

**参数:**
- `shell_path`: str **必填**


### is_posix_shell

```python
def is_posix_shell(shell_path: str) -> bool
```

是否为 POSIX shell

**参数:**
- `shell_path`: str **必填**


### is_powershell

```python
def is_powershell(shell_path: str) -> bool
```

是否为 PowerShell

**参数:**
- `shell_path`: str **必填**


### find_git_bash

```python
def find_git_bash() -> Optional[str]
```

查找 Git Bash 路径（Windows）


### find_shells

```python
def find_shells() -> List[str]
```

查找系统可用的 shell


### select_shell

```python
def select_shell(preferred: Optional[str], require_acceptable: bool) -> str
```

选择可用的 shell

**参数:**
- `preferred`: Optional[str] (默认: `None`)
- `require_acceptable`: bool (默认: `False`)


### get_shell_args

```python
def get_shell_args(shell_path: str, command: str, cwd: str) -> List[str]
```

获取 shell 执行参数

**参数:**
- `shell_path`: str **必填**
- `command`: str **必填**
- `cwd`: str **必填**


### _kill_tree_unix

```python
def _kill_tree_unix(pid: int, timeout_ms: int) -> bool
```

Unix 下杀死进程树

**参数:**
- `pid`: int **必填**
- `timeout_ms`: int (默认: `200`)


### _kill_tree_windows

```python
def _kill_tree_windows(pid: int) -> bool
```

Windows 下杀死进程树

**参数:**
- `pid`: int **必填**


### kill_process_tree

```python
def kill_process_tree(process: subprocess.Popen) -> bool
```

杀死整个进程树

**参数:**
- `process`: subprocess.Popen **必填**


### execute_command

```python
def execute_command(command: str, cwd: Optional[str], timeout: Optional[float], shell_path: Optional[str], env: Optional[Dict[str, str]], input_text: Optional[str], working_dir_whitelist: Optional[List[str]]) -> CommandResult
```

安全执行命令（带进程树管理和超时控制）

**参数:**
- `command`: str **必填**
- `cwd`: Optional[str] (默认: `None`)
- `timeout`: Optional[float] (默认: `None`)
- `shell_path`: Optional[str] (默认: `None`)
- `env`: Optional[Dict[str, str]] (默认: `None`)
- `input_text`: Optional[str] (默认: `None`)
- `working_dir_whitelist`: Optional[List[str]] (默认: `None`)


### execute_command_safe

```python
def execute_command_safe(command: str, cwd: Optional[str], timeout: float, max_output: int, working_dir_whitelist: Optional[List[str]]) -> Dict[str, Any]
```

安全执行命令（带输出截断，适合工具调用）

**参数:**
- `command`: str **必填**
- `cwd`: Optional[str] (默认: `None`)
- `timeout`: float (默认: `30.0`)
- `max_output`: int (默认: `1024 * 1024`)
- `working_dir_whitelist`: Optional[List[str]] (默认: `None`)


### run_background

```python
def run_background(command: str, cwd: Optional[str]) -> str
```

后台运行命令

**参数:**
- `command`: str **必填**
- `cwd`: Optional[str] (默认: `None`)


### get_background_task

```python
def get_background_task(task_id: str) -> Optional[BackgroundTask]
```

获取后台任务

**参数:**
- `task_id`: str **必填**


### kill_background_task

```python
def kill_background_task(task_id: str) -> bool
```

杀死后台任务

**参数:**
- `task_id`: str **必填**


### list_background_tasks

```python
def list_background_tasks() -> List[Dict[str, Any]]
```

列出所有后台任务


## 类

## class CommandResult

命令执行结果

---

### __init__

```python
def __init__(stdout: str, stderr: str, returncode: int, timed_out: bool, killed: bool)
```

**参数:**
- `stdout`: str **必填**
- `stderr`: str **必填**
- `returncode`: int **必填**
- `timed_out`: bool (默认: `False`)
- `killed`: bool (默认: `False`)

### success

```python
def success() -> bool
```

**装饰器:** `@property`

### to_dict

```python
def to_dict() -> Dict[str, Any]
```


## class BackgroundTask

后台任务

---

### __init__

```python
def __init__(task_id: str, process: subprocess.Popen, command: str)
```

**参数:**
- `task_id`: str **必填**
- `process`: subprocess.Popen **必填**
- `command`: str **必填**

### is_running

```python
def is_running() -> bool
```

### kill

```python
def kill() -> bool
```

### get_output

```python
def get_output(tail: Optional[int]) -> Dict[str, Any]
```

**参数:**
- `tail`: Optional[int] (默认: `None`)


---

# 模块: func_list_tools

**文件:** `agent_tools/func_list_tools.py`

列出 Python 文件中的函数/类签名

## 常量

- `SKIP_DIRS` = `{'.git', '__pycache__', '.idea', '.vscode', 'node_modules', 'venv', 'env', '.hermes_backup', 'dist', 'build'}`

## 函数

### _extract_signatures

```python
def _extract_signatures(file_path: str) -> Dict
```

提取单个文件的函数和类签名

**参数:**
- `file_path`: str **必填**


### list_functions

```python
def list_functions(args: dict) -> str
```

列出 Python 文件或项目中的函数和类签名。
参数:
    path: 文件路径或目录路径
    depth: 扫描深度（仅目录有效，默认 3）

**参数:**
- `args`: dict **必填**


### _format_result

```python
def _format_result(result: Dict) -> str
```

格式化单个文件的结果

**参数:**
- `result`: Dict **必填**


### _format_results

```python
def _format_results(results: List[Dict], base_path: str) -> str
```

格式化多个文件的结果

**参数:**
- `results`: List[Dict] **必填**
- `base_path`: str **必填**


### register_tools

```python
def register_tools() -> int
```

注册工具


---

# 模块: gif_tools

**文件:** `agent_tools/gif_tools.py`

GIF处理工具集 - 生成GIF动图

## 函数

### _create_gif

```python
def _create_gif(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: git_tools

**文件:** `agent_tools/git_tools.py`

Git 高级操作工具集（P1） - 开发流必备
封装 git 命令行：状态/日志/差异/提交/分支/合并/暂存/回退/推送。
自动向上查找 .git 仓库根目录。放于 agent_tools/ 目录，由 HotReloader 扫描注册。

## 常量

- `_HERMES_DIR` = `os.path.dirname(...)`
- `_DEFAULT_TIMEOUT` = `60`

## 函数

### _find_repo

```python
def _find_repo(repo_path: str) -> str
```

从 repo_path（默认当前目录）向上查找含 .git 的目录

**参数:**
- `repo_path`: str (默认: `None`)


### _git

```python
def _git(repo: str, args: list, timeout: int) -> dict
```

**参数:**
- `repo`: str **必填**
- `args`: list **必填**
- `timeout`: int (默认: `_DEFAULT_TIMEOUT`)


### _git_out

```python
def _git_out(args: dict, git_args: list) -> str
```

**参数:**
- `args`: dict **必填**
- `git_args`: list **必填**


### _git_status

```python
def _git_status(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_log

```python
def _git_log(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_diff

```python
def _git_diff(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_commit

```python
def _git_commit(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_branch

```python
def _git_branch(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_merge

```python
def _git_merge(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_stash

```python
def _git_stash(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_reset

```python
def _git_reset(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_push

```python
def _git_push(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_pull

```python
def _git_pull(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _git_run

```python
def _git_run(args: dict) -> str
```

通用 git 命令（高级/组合操作）

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: gui_qt

**文件:** `gui_qt.py`

GUI - PyQt6 图形界面（修复卡死问题）

用法:
    python run.py --qt              # 启动 PyQt6 界面

## 常量

- `_SETTINGS_FILE` = `os.path.join(...)`
- `_CONFIG_FILE` = `os.path.join(...)`
- `FONT_UI` = `None`
- `FONT_MONO` = `None`
- `THEMES` = `{}`
- `THEME_ORDER` = `[]`
- `_INLINE_PATTERN` = `re.compile(...)`
- `_CODE_BLOCK_RE` = `re.compile(...)`
- `_HEADER_RE` = `re.compile(...)`
- `_HR_RE` = `re.compile(...)`
- `_LIST_RE` = `re.compile(...)`
- `_STATUS_CODE_RE` = `re.compile(...)`
- `_NUMBER_RE` = `re.compile(...)`

## 函数

### _ensure_fonts

```python
def _ensure_fonts()
```

惰性初始化字体（需要 QApplication 已存在）


### _first_existing

```python
def _first_existing(available, *candidates)
```

**参数:**
- `available` **必填**
- `*candidates`


### _inline_html

```python
def _inline_html(text, c, fs)
```

**参数:**
- `text` **必填**
- `c` **必填**
- `fs` **必填**


### _parse_markdown

```python
def _parse_markdown(text)
```

**参数:**
- `text` **必填**


### main

```python
def main()
```


## 类

## class Signals(QObject)

工作线程 -> GUI 线程的信号桥

**类变量:**
- `append_msg` = `pyqtSignal(...)`
- `tool_call` = `pyqtSignal(...)`
- `tool_result` = `pyqtSignal(...)`
- `typing_start` = `pyqtSignal(...)`
- `typing_stop` = `pyqtSignal(...)`
- `set_status` = `pyqtSignal(...)`
- `send_done` = `pyqtSignal(...)`
- `login_result` = `pyqtSignal(...)`
- `inject_result` = `pyqtSignal(...)`


## class ImprovedSyntaxHighlighter(QSyntaxHighlighter)

---

### __init__

```python
def __init__(document, colors)
```

**参数:**
- `document` **必填**
- `colors` **必填**

### highlightBlock

```python
def highlightBlock(text)
```

**参数:**
- `text` **必填**


## class CodeBlock(QFrame)

---

### __init__

```python
def __init__(code, lang, colors, font_size, on_copy)
```

**参数:**
- `code` **必填**
- `lang` **必填**
- `colors` **必填**
- `font_size` **必填**
- `on_copy` **必填**


## class ToolBlock(QFrame)

---

### __init__

```python
def __init__(seq, name, args, colors, font_size)
```

**参数:**
- `seq` **必填**
- `name` **必填**
- `args` **必填**
- `colors` **必填**
- `font_size` **必填**

### _refresh_header

```python
def _refresh_header()
```

### _toggle

```python
def _toggle()
```

### append_result

```python
def append_result(result, is_error, elapsed)
```

**参数:**
- `result` **必填**
- `is_error` **必填**
- `elapsed` **必填**


## class ChatMessage(QFrame)

---

### __init__

```python
def __init__(role, text, colors, font_size, on_copy, msg_id)
```

**参数:**
- `role` **必填**
- `text` **必填**
- `colors` **必填**
- `font_size` **必填**
- `on_copy` **必填**
- `msg_id` (默认: `None`)

### _render_markdown

```python
def _render_markdown(text, v, fs, on_copy)
```

**参数:**
- `text` **必填**
- `v` **必填**
- `fs` **必填**
- `on_copy` **必填**


## class TypingIndicator(QFrame)

---

### __init__

```python
def __init__(colors, font_size)
```

**参数:**
- `colors` **必填**
- `font_size` **必填**

### _animate

```python
def _animate()
```

### stop

```python
def stop()
```


## class ConfigDialog(QDialog)

---

### __init__

```python
def __init__(parent)
```

**参数:**
- `parent` (默认: `None`)

### _load_config

```python
def _load_config()
```

### _save

```python
def _save()
```


## class GUI(QMainWindow)

---

### __init__

```python
def __init__(agent: Agent)
```

**参数:**
- `agent`: Agent **必填**

### _setup_hot_reload

```python
def _setup_hot_reload()
```

### _load_settings

```python
def _load_settings()
```

### _save_settings

```python
def _save_settings()
```

### _build_ui

```python
def _build_ui()
```

### _load_tools_once

```python
def _load_tools_once()
```

### _refresh_tools_list

```python
def _refresh_tools_list()
```

### _render_tools

```python
def _render_tools(items: List[Tuple[str, dict]])
```

**参数:**
- `items`: List[Tuple[str, dict]] **必填**

### eventFilter

```python
def eventFilter(obj, event)
```

**参数:**
- `obj` **必填**
- `event` **必填**

### _connect_signals

```python
def _connect_signals()
```

### _apply_theme

```python
def _apply_theme()
```

### _cycle_theme

```python
def _cycle_theme()
```

### _append

```python
def _append(role: str, text: str)
```

**参数:**
- `role`: str **必填**
- `text`: str **必填**

### _insert_widget

```python
def _insert_widget(widget: QWidget)
```

**参数:**
- `widget`: QWidget **必填**

### _trim_messages

```python
def _trim_messages()
```

限制消息数量，防止长时间对话导致 Widget 堆积

### _scroll_bottom

```python
def _scroll_bottom()
```

### _force_scroll_bottom

```python
def _force_scroll_bottom()
```

### _on_chat_range_changed

```python
def _on_chat_range_changed(_min, _max)
```

**参数:**
- `_min` **必填**
- `_max` **必填**

### _copy_to_clipboard

```python
def _copy_to_clipboard(text)
```

**参数:**
- `text` **必填**

### _set_status

```python
def _set_status(text: str, color: Optional[str])
```

**参数:**
- `text`: str **必填**
- `color`: Optional[str] (默认: `None`)

### _start_typing

```python
def _start_typing()
```

### _stop_typing

```python
def _stop_typing()
```

### _open_tool_block

```python
def _open_tool_block(name: str, args) -> None
```

**参数:**
- `name`: str **必填**
- `args` **必填**

### _append_tool_result

```python
def _append_tool_result(name: str, result: str) -> None
```

**参数:**
- `name`: str **必填**
- `result`: str **必填**

### _increment_operations

```python
def _increment_operations()
```

### _decrement_operations

```python
def _decrement_operations()
```

### _stop_current

```python
def _stop_current()
```

停止当前正在进行的操作

### _send

```python
def _send() -> None
```

### _on_done

```python
def _on_done()
```

### _new_chat

```python
def _new_chat()
```

### _show_config

```python
def _show_config()
```

### _reload_config

```python
def _reload_config()
```

### _login

```python
def _login()
```

### _login_result

```python
def _login_result(ok, msg)
```

**参数:**
- `ok` **必填**
- `msg` **必填**

### _inject_prompt

```python
def _inject_prompt()
```

### _load_config_from_file

```python
def _load_config_from_file()
```

### _inject_result

```python
def _inject_result(ok, msg)
```

**参数:**
- `ok` **必填**
- `msg` **必填**

### _start_auto

```python
def _start_auto()
```

### _poll_auto

```python
def _poll_auto()
```

### _stop_auto

```python
def _stop_auto()
```

### _auto_done

```python
def _auto_done()
```

### closeEvent

```python
def closeEvent(event)
```

**参数:**
- `event` **必填**

### run

```python
def run()
```


---

# 模块: hash_tools

**文件:** `agent_tools/hash_tools.py`

哈希校验工具集 - 支持MD5、SHA1、SHA256、CRC32等

## 函数

### _hash_file

```python
def _hash_file(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _hash_text

```python
def _hash_text(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _verify_hash

```python
def _verify_hash(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: health_tools

**文件:** `agent_tools/health_tools.py`

项目健康检查工具
功能：分析项目目录，检查代码质量、文件完整性、依赖状态等

## 函数

### _count_lines

```python
def _count_lines(file_path: str) -> Tuple[int, int, int]
```

统计文件行数：总行数、代码行数、注释行数

**参数:**
- `file_path`: str **必填**


### _check_requirements

```python
def _check_requirements(dir_path: str) -> Dict
```

检查 requirements.txt

**参数:**
- `dir_path`: str **必填**


### _check_gitignore

```python
def _check_gitignore(dir_path: str) -> Dict
```

检查 .gitignore

**参数:**
- `dir_path`: str **必填**


### _scan_project

```python
def _scan_project(dir_path: str, max_depth: int) -> Dict
```

扫描项目目录结构

**参数:**
- `dir_path`: str **必填**
- `max_depth`: int (默认: `3`)


### _generate_report

```python
def _generate_report(dir_path: str, options: Dict) -> str
```

生成健康报告

**参数:**
- `dir_path`: str **必填**
- `options`: Dict (默认: `None`)


### health_check

```python
def health_check(args: dict) -> str
```

执行项目健康检查。
参数:
    path: 要检查的项目目录路径
    max_depth: 扫描深度（可选，默认3）

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```

注册所有工具，供热加载器调用


---

# 模块: hot_reload

**文件:** `agent_tools/hot_reload.py`

工具热加载器 - 监听 agent_tools/ 目录，动态注册/更新工具，无需重启
适配 Hermes tools.register() 系统

## 常量

- `_SKIP_FILES` = `{'__init__.py', 'hot_reload.py', '.gitkeep'}`

## 函数

### start_hot_reload

```python
def start_hot_reload(watch_dir: str, interval: int) -> HotReloader
```

**参数:**
- `watch_dir`: str (默认: `None`)
- `interval`: int (默认: `3`)


### stop_hot_reload

```python
def stop_hot_reload()
```


### get_hot_reload_status

```python
def get_hot_reload_status() -> str
```


## 类

## class HotReloader

工具热加载器 - 轮询 agent_tools/ 目录，文件变化时自动重新加载

---

### __init__

```python
def __init__(watch_dir: str, interval: int)
```

**参数:**
- `watch_dir`: str (默认: `None`)
- `interval`: int (默认: `3`)

### start

```python
def start()
```

### stop

```python
def stop()
```

### _scan_initial

```python
def _scan_initial()
```

首次扫描，加载所有工具模块

### _watch_loop

```python
def _watch_loop()
```

### _check_files

```python
def _check_files()
```

检查文件变化，加载新模块或重载变化模块

### _reload_module

```python
def _reload_module(module_name: str, file_path: str)
```

重新加载模块并调用 register_tools()

**参数:**
- `module_name`: str **必填**
- `file_path`: str **必填**

### reload_all

```python
def reload_all()
```

手动重载所有模块

### get_status

```python
def get_status() -> str
```


---

# 模块: html_tools

**文件:** `agent_tools/html_tools.py`

HTML处理工具集 - 支持提取文本、链接、表格解析

## 函数

### _import_bs4

```python
def _import_bs4()
```


### _extract_text

```python
def _extract_text(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _extract_links

```python
def _extract_links(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _parse_table

```python
def _parse_table(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: http_server_tools

**文件:** `agent_tools/http_server_tools.py`

HTTP 文件服务器工具

启动一个简单的 HTTP 文件服务器，方便在局域网内共享文件。
基于 Python 内置的 http.server 模块。

## 函数

### find_free_port

```python
def find_free_port(start_port, max_attempts) -> int
```

查找可用的端口

**参数:**
- `start_port` (默认: `8000`)
- `max_attempts` (默认: `10`)


### get_local_ip

```python
def get_local_ip() -> str
```

获取本机局域网 IP


### start_http_server

```python
def start_http_server(args: dict) -> str
```

启动 HTTP 文件服务器

参数:
    path: 服务器根目录（默认当前目录）
    port: 端口号（默认 8000）
    bind: 绑定地址（默认 0.0.0.0，允许局域网访问）
    open_browser: 是否自动打开浏览器（默认 True）
    quiet: 是否静默模式（默认 True）

**参数:**
- `args`: dict **必填**


### stop_http_server

```python
def stop_http_server(args: dict) -> str
```

停止正在运行的 HTTP 文件服务器

**参数:**
- `args`: dict **必填**


### http_server_status

```python
def http_server_status(args: dict) -> str
```

查看 HTTP 服务器状态

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```

注册此模块中的所有工具。
热加载器会自动调用此函数。
返回注册的工具数量。


## 类

## class QuietHTTPHandler(SimpleHTTPRequestHandler)

静默版 HTTP 处理器，减少控制台输出

---

### log_message

```python
def log_message(format, *args)
```

**参数:**
- `format` **必填**
- `*args`


---

# 模块: image_tools

**文件:** `agent_tools/image_tools.py`

图片处理工具集 - 支持格式转换、裁剪、缩放、水印、拼接、滤镜

## 函数

### _import_PIL

```python
def _import_PIL()
```


### _get_supported_formats

```python
def _get_supported_formats()
```


### _is_image_file

```python
def _is_image_file(path)
```

**参数:**
- `path` **必填**


### _image_info

```python
def _image_info(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _convert_image

```python
def _convert_image(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _resize_image

```python
def _resize_image(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _crop_image

```python
def _crop_image(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: ini_tools

**文件:** `agent_tools/ini_tools.py`

INI配置文件管理工具集 - 支持读取、写入、修改配置

## 函数

### _read_ini

```python
def _read_ini(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _write_ini

```python
def _write_ini(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _set_ini_value

```python
def _set_ini_value(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: log_tools

**文件:** `agent_tools/log_tools.py`

日志工具集 - 热加载示例
放到 agent_tools/ 目录下会被自动加载

用法示例：
  write_log: {"message": "测试", "level": "INFO"}
  read_log:  {"lines": 50, "keyword": "error"}
  analyze_log: {"lines": 1000}
  clear_log: {}

## 常量

- `_LOG_FILE` = `os.path.join(...)`

## 函数

### _write_log

```python
def _write_log(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _read_log

```python
def _read_log(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _analyze_log

```python
def _analyze_log(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _clear_log

```python
def _clear_log(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册日志工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```

卸载工具（热加载重载时调用）


---

# 模块: markdown_tools

**文件:** `agent_tools/markdown_tools.py`

Markdown处理工具集 - 支持转HTML、提取标题、生成目录

## 函数

### _import_markdown

```python
def _import_markdown()
```


### _md_to_html

```python
def _md_to_html(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _extract_headers

```python
def _extract_headers(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _generate_toc

```python
def _generate_toc(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: media_tools

**文件:** `agent_tools/media_tools.py`

音频和数据库工具

## 函数

### _sql_execute

```python
def _sql_execute(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _play_sound

```python
def _play_sound(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```


---

# 模块: memory

**文件:** `memory.py`

记忆服务 - 后台实时捕获对话并落库 + 自动加载注入上下文

## 常量

- `MEMORY_CONFIG` = `{}`
- `_CATEGORY_KEYWORDS` = `{}`
- `_SYNONYMS` = `{}`
- `HAS_PINYIN` = `True`
- `HAS_PINYIN` = `False`

## 函数

### _get_pinyin

```python
def _get_pinyin(text: str) -> str
```

获取中文文本的拼音（首字母+全拼）

**参数:**
- `text`: str **必填**


### _expand_query

```python
def _expand_query(query: str) -> List[str]
```

扩展查询词：原始词 + 同义词 + 拼音

**参数:**
- `query`: str **必填**


### _levenshtein_distance

```python
def _levenshtein_distance(s1: str, s2: str) -> int
```

编辑距离（Levenshtein）

**参数:**
- `s1`: str **必填**
- `s2`: str **必填**


### _fuzzy_match

```python
def _fuzzy_match(content: str, query_terms: List[str], threshold: int) -> int
```

模糊匹配：返回匹配到的词数量

**参数:**
- `content`: str **必填**
- `query_terms`: List[str] **必填**
- `threshold`: int (默认: `2`)


### _detect_category

```python
def _detect_category(text: str) -> str
```

**参数:**
- `text`: str **必填**


### _calc_importance

```python
def _calc_importance(text: str) -> int
```

**参数:**
- `text`: str **必填**


### _smart_truncate

```python
def _smart_truncate(content: str, max_len: int) -> str
```

智能截断：在句子边界处切断，保留完整语义

**参数:**
- `content`: str **必填**
- `max_len`: int **必填**


### get_service

```python
def get_service() -> MemoryService
```


### record_turn

```python
def record_turn(role: str, content: str, source: str) -> bool
```

**参数:**
- `role`: str **必填**
- `content`: str **必填**
- `source`: str (默认: `'hermes'`)


### auto_load_memory

```python
def auto_load_memory(query: str, limit: int) -> List[Memory]
```

**参数:**
- `query`: str **必填**
- `limit`: int (默认: `None`)


### format_memories_for_context

```python
def format_memories_for_context(memories: List[Memory]) -> str
```

将记忆格式化为可注入 LLM 上下文的文本（精简分层格式）

**参数:**
- `memories`: List[Memory] **必填**


### memory_status

```python
def memory_status() -> str
```


## 类

## class MemoryService

记忆服务：后台线程实时把对话写入 SQLite；提供检索用于上下文注入。

---

### __init__

```python
def __init__(db_path: str)
```

**参数:**
- `db_path`: str (默认: `None`)

### start

```python
def start()
```

### stop

```python
def stop()
```

### _writer_loop

```python
def _writer_loop()
```

### _flush

```python
def _flush()
```

### record_turn

```python
def record_turn(role: str, content: str, source: str) -> bool
```

**参数:**
- `role`: str **必填**
- `content`: str **必填**
- `source`: str (默认: `'hermes'`)

### save

```python
def save(content: str, category: str, source: str, importance: int) -> int
```

**参数:**
- `content`: str **必填**
- `category`: str (默认: `'general'`)
- `source`: str (默认: `'user_manual'`)
- `importance`: int (默认: `5`)

### auto_load_memory

```python
def auto_load_memory(query: str, limit: int) -> List[Memory]
```

自动加载相关记忆：加权排序（关键词 + 最近 + 高重要度）

**参数:**
- `query`: str **必填**
- `limit`: int (默认: `None`)

### search

```python
def search(query: str, limit: int, category: Optional[str], min_importance: int) -> List[Memory]
```

**参数:**
- `query`: str **必填**
- `limit`: int (默认: `10`)
- `category`: Optional[str] (默认: `None`)
- `min_importance`: int (默认: `1`)

### status

```python
def status() -> str
```


---

# 模块: memory_db

**文件:** `memory_db.py`

记忆系统 - SQLite 数据库层（本地存储，零配置）

## 类

## class Memory

---

### to_dict

```python
def to_dict() -> dict
```


## class MemoryDB

SQLite 记忆存储。每次操作独立连接，线程安全；供后台写入线程使用。

---

### __init__

```python
def __init__(db_path: str)
```

**参数:**
- `db_path`: str (默认: `None`)

### _connect

```python
def _connect() -> sqlite3.Connection
```

### _init_db

```python
def _init_db()
```

### save

```python
def save(content: str, category: str, source: str, importance: int, embedding: Optional[str]) -> int
```

**参数:**
- `content`: str **必填**
- `category`: str (默认: `'general'`)
- `source`: str (默认: `''`)
- `importance`: int (默认: `1`)
- `embedding`: Optional[str] (默认: `None`)

### save_batch

```python
def save_batch(items: List[dict]) -> int
```

批量写入 [ {content, category, source, importance, embedding}, ... ]

**参数:**
- `items`: List[dict] **必填**

### _tokens

```python
def _tokens(query: str) -> List[str]
```

分词：英文/数字词（>=2 字符）+ 中文双字组

**参数:**
- `query`: str **必填**

**装饰器:** `@staticmethod`

### search

```python
def search(query: str, limit: int, category: Optional[str], min_importance: int) -> List[Memory]
```

关键词检索（多 token 匹配，按相关度 + 新鲜度排序）

**参数:**
- `query`: str **必填**
- `limit`: int (默认: `10`)
- `category`: Optional[str] (默认: `None`)
- `min_importance`: int (默认: `1`)

### search_by_time

```python
def search_by_time(days: int, limit: int) -> List[Memory]
```

**参数:**
- `days`: int (默认: `7`)
- `limit`: int (默认: `20`)

### search_by_importance

```python
def search_by_importance(min_importance: int, limit: int) -> List[Memory]
```

**参数:**
- `min_importance`: int (默认: `5`)
- `limit`: int (默认: `20`)

### recent

```python
def recent(limit: int) -> List[Memory]
```

**参数:**
- `limit`: int (默认: `20`)

### get

```python
def get(memory_id: int) -> Optional[Memory]
```

**参数:**
- `memory_id`: int **必填**

### update_importance

```python
def update_importance(memory_id: int, importance: int)
```

**参数:**
- `memory_id`: int **必填**
- `importance`: int **必填**

### link_memories

```python
def link_memories(memory_id: int, related_ids: List[int])
```

**参数:**
- `memory_id`: int **必填**
- `related_ids`: List[int] **必填**

### delete

```python
def delete(memory_id: int)
```

**参数:**
- `memory_id`: int **必填**

### delete_old

```python
def delete_old(days: int) -> int
```

**参数:**
- `days`: int (默认: `30`)

### count

```python
def count() -> int
```

### _row_to_memory

```python
def _row_to_memory(row) -> Memory
```

**参数:**
- `row` **必填**


---

# 模块: memory_tools

**文件:** `agent_tools/memory_tools.py`

记忆工具 - 手动保存 / 检索 / 总结 / 删除 / 状态（可热加载）
放于 agent_tools/ 目录，启动时由 HotReloader 自动扫描注册；修改本文件保存即热更新。

## 函数

### _memory_save

```python
def _memory_save(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _memory_search

```python
def _memory_search(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _memory_summary

```python
def _memory_summary(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _memory_forget

```python
def _memory_forget(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _memory_status

```python
def _memory_status(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: network_tools

**文件:** `agent_tools/network_tools.py`

网络请求工具集 - 支持HTTP请求、API调用、文件下载

## 函数

### _ensure_dir

```python
def _ensure_dir(path)
```

**参数:**
- `path` **必填**


### _http_request

```python
def _http_request(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _download_file

```python
def _download_file(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _batch_download

```python
def _batch_download(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: notify_tools

**文件:** `agent_tools/notify_tools.py`

桌面通知工具 - 在 Windows 右下角弹出系统通知

## 函数

### _get_notification_backend

```python
def _get_notification_backend()
```

延迟加载通知库，返回 (backend_name, notify_func)
优先使用 plyer，其次 win10toast


### _notify_plyer

```python
def _notify_plyer(notification, title: str, message: str, duration: int, icon_path: str) -> str
```

使用 plyer 发送通知

**参数:**
- `notification` **必填**
- `title`: str **必填**
- `message`: str **必填**
- `duration`: int **必填**
- `icon_path`: str (默认: `None`)


### _notify_win10toast

```python
def _notify_win10toast(ToastNotifier, title: str, message: str, duration: int, icon_path: str) -> str
```

使用 win10toast 发送通知

**参数:**
- `ToastNotifier` **必填**
- `title`: str **必填**
- `message`: str **必填**
- `duration`: int **必填**
- `icon_path`: str (默认: `None`)


### _notify_fallback

```python
def _notify_fallback(title: str, message: str) -> str
```

备用方案：控制台输出 + 系统提示音

**参数:**
- `title`: str **必填**
- `message`: str **必填**


### notify_desktop

```python
def notify_desktop(args: dict) -> str
```

发送 Windows 桌面系统通知（右下角弹窗）

**参数:**
- `args`: dict **必填**


### send_alert

```python
def send_alert(args: dict) -> str
```

发送紧急警报通知

**参数:**
- `args`: dict **必填**


### notify_quick

```python
def notify_quick(args: dict) -> str
```

快捷通知：仅需 message

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```


---

# 模块: parseemail_tools

**文件:** `agent_tools/parseemail_tools.py`

邮件解析工具集 - 解析邮件、提取附件

## 函数

### _parse_email

```python
def _parse_email(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: parser

**文件:** `parser.py`

工具调用解析器 - 只提取 name 和 arguments 原始字符串
不解析任何 JSON，只做括号匹配提取

## 函数

### extract_tool_calls

```python
def extract_tool_calls(text: str) -> list
```

从 AI 回复中提取工具调用
1. 清理中文（提取最外层 [] 内容）
2. 提取 name 原始字符串
3. 提取 arguments 原始字符串
4. 返回 name 和 arguments 原始字符串，不做任何解析

**参数:**
- `text`: str **必填**


---

# 模块: password_tools

**文件:** `agent_tools/password_tools.py`

密码生成工具集 - 支持生成强密码、密码强度检测

## 函数

### _generate_password

```python
def _generate_password(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _check_password_strength

```python
def _check_password_strength(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: permission_tools

**文件:** `agent_tools/permission_tools.py`

文件权限工具集 - 支持查看、修改文件权限

## 函数

### _get_file_permission

```python
def _get_file_permission(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: pinyin_tools

**文件:** `agent_tools/pinyin_tools.py`

拼音转换工具集 - 中文转拼音

## 函数

### _to_pinyin

```python
def _to_pinyin(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: plan_tools

**文件:** `agent_tools/plan_tools.py`

任务规划与跟踪工具集（P0） - 复杂任务的基石
规划可带依赖的任务清单，持久化到 JSON，支持状态跟踪/断点续跑。
放于 agent_tools/ 目录，由 HotReloader 自动扫描注册，改文件保存即热更新。

## 常量

- `_HERMES_DIR` = `os.path.dirname(...)`
- `_DATA_FILE` = `os.path.join(...)`
- `_VALID_STATUS` = `{'pending', 'in_progress', 'done', 'failed', 'skipped'}`

## 函数

### _get_manager

```python
def _get_manager() -> PlanManager
```


### _plan_create

```python
def _plan_create(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _plan_status

```python
def _plan_status(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _plan_mark

```python
def _plan_mark(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _plan_next

```python
def _plan_next(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _plan_reset

```python
def _plan_reset(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _plan_remove

```python
def _plan_remove(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


## 类

## class PlanManager

带依赖的任务规划，JSON 原子持久化，跨会话不丢失

---

### __init__

```python
def __init__(data_file: str)
```

**参数:**
- `data_file`: str (默认: `_DATA_FILE`)

### _load

```python
def _load()
```

### _save

```python
def _save()
```

### create

```python
def create(goal: str, tasks: list) -> dict
```

**参数:**
- `goal`: str **必填**
- `tasks`: list **必填**

### status

```python
def status() -> dict
```

### next_id_locked

```python
def next_id_locked(tasks: list) -> str | None
```

下一个可执行任务：pending 且所有依赖均 done/无依赖，按顺序

**参数:**
- `tasks`: list **必填**

### mark

```python
def mark(task_id: str, status: str, result: str) -> dict
```

**参数:**
- `task_id`: str **必填**
- `status`: str **必填**
- `result`: str (默认: `''`)

### remove

```python
def remove(task_id: str) -> dict
```

**参数:**
- `task_id`: str **必填**

### reset

```python
def reset() -> dict
```


---

# 模块: planner

**文件:** `planner.py`

任务规划器 + 顺序执行器（精简版，JSON 持久化）
================================================
- TaskPlanner: 用 LLM 把目标拆成带依赖的任务列表，写入 JSON 文件（永不丢失）
- Pipeline: 顺序执行器 —— 一个个执行任务（串行，匹配浏览器），
  支持断点续跑、连续失败自动重新拆解剩余任务

状态机: pending -> in_progress -> done | failed | skipped

## 常量

- `MAX_REPLANS` = `2`
- `REPLAN_THRESHOLD` = `2`
- `_PLAN_PROMPT` = `'你是软件项目规划专家。请把目标拆成**有序、可执行、可独立验证**的小任务，任务之间标注依赖。\n\n目标：{goal}\n\n要求：\n1. 每个任务是具体开发步骤（如创建文件、写代码、装依赖、运行测试）\n2. 有依赖关系的任务，把依赖任务 id 填进 dependencies\n3. 不超过 15 个任务，粒度适中\n4. 禁止调用任何工具，只输出 JSON\n\n输出格式（只输出以下 JSON，不要别的文字）：\n{{"tasks": [\n  {{"id": "1", "description": "...", "dependencies": []}},\n  {{"id": "2", "description": "...", "dependencies": ["1"]}}\n]}}'`

## 函数

### _ask_plan_json

```python
def _ask_plan_json(client: Client, prompt: str) -> dict
```

调 LLM 并提取 {tasks:[...]} JSON。失败抛异常。

**参数:**
- `client`: Client **必填**
- `prompt`: str **必填**


## 类

## class Task

单个任务

---

### __init__

```python
def __init__(id: str, description: str, dependencies: list)
```

**参数:**
- `id`: str **必填**
- `description`: str **必填**
- `dependencies`: list (默认: `None`)

### to_dict

```python
def to_dict() -> dict
```

### from_dict

```python
def from_dict(d: dict) -> Task
```

**参数:**
- `d`: dict **必填**

**装饰器:** `@classmethod`

### verify_completion

```python
def verify_completion() -> tuple
```

验证任务是否真正完成。返回 (通过?, 额外信息)


## class TaskPlanner

任务规划器 - JSON 持久化，单线程互斥

---

### __init__

```python
def __init__(data_file: str)
```

**参数:**
- `data_file`: str (默认: `'hermes_tasks.json'`)

### _load

```python
def _load()
```

### _save

```python
def _save()
```

原子写 JSON，保证永不丢失

### create_plan

```python
def create_plan(client: Client, goal: str) -> dict
```

用 LLM 拆解目标为任务列表

**参数:**
- `client`: Client **必填**
- `goal`: str **必填**

### replan

```python
def replan(client: Client, failure_reason: str) -> dict
```

连续失败后重新拆解剩余任务，保留已完成任务

**参数:**
- `client`: Client **必填**
- `failure_reason`: str (默认: `''`)

### get_next_task

```python
def get_next_task() -> Optional[Task]
```

取下一个依赖已满足的 pending 任务

### get_blocked_pending

```python
def get_blocked_pending() -> List[Task]
```

依赖已失败/跳过的 pending 任务（无法执行，应跳过）

### mark_task

```python
def mark_task(task_id: str, status: str, result: str)
```

**参数:**
- `task_id`: str **必填**
- `status`: str **必填**
- `result`: str (默认: `''`)

### get_progress

```python
def get_progress() -> dict
```

### resume

```python
def resume(retry_failed: bool) -> dict
```

断点续跑：in_progress -> pending；可选 failed -> pending

**参数:**
- `retry_failed`: bool (默认: `True`)

### reset

```python
def reset()
```


## class Pipeline

顺序执行器：永不阻塞 GUI，逐个执行任务，连续失败自动重新拆解

---

### __init__

```python
def __init__(client: Client, data_file: str, max_rounds: int, parallel: bool, max_workers: int, replan_threshold: int)
```

**参数:**
- `client`: Client **必填**
- `data_file`: str (默认: `'hermes_tasks.json'`)
- `max_rounds`: int (默认: `100`)
- `parallel`: bool (默认: `True`)
- `max_workers`: int (默认: `4`)
- `replan_threshold`: int (默认: `REPLAN_THRESHOLD`)

### _log

```python
def _log(msg: str, level: str)
```

**参数:**
- `msg`: str **必填**
- `level`: str (默认: `'info'`)

### _status_snapshot

```python
def _status_snapshot() -> dict
```

### get_status

```python
def get_status() -> dict
```

### plan

```python
def plan(goal: str) -> dict
```

只拆解任务（不执行），供 GUI 预览

**参数:**
- `goal`: str **必填**

### start

```python
def start(goal: Optional[str]) -> dict
```

启动流水线。goal 传入则先重新规划，否则接着现有计划跑（断点续跑）

**参数:**
- `goal`: Optional[str] (默认: `None`)

### stop

```python
def stop() -> dict
```

### wait

```python
def wait(poll_interval: float, timeout: float)
```

阻塞等待流水线结束

**参数:**
- `poll_interval`: float (默认: `1.0`)
- `timeout`: float (默认: `None`)

### _run_loop

```python
def _run_loop()
```

### _execute_task

```python
def _execute_task(agent: Agent, task: Task, goal: str) -> tuple
```

执行单个任务。返回 (成功?, 回复文本)

**参数:**
- `agent`: Agent **必填**
- `task`: Task **必填**
- `goal`: str **必填**


---

# 模块: port_tools

**文件:** `agent_tools/port_tools.py`

端口扫描工具集 - 检查端口是否开放

## 函数

### _check_port

```python
def _check_port(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: progress_tools

**文件:** `agent_tools/progress_tools.py`

进度条工具集 - 支持控制台进度条显示

## 函数

### _show_progress

```python
def _show_progress(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: qr_tools

**文件:** `agent_tools/qr_tools.py`

二维码工具集 - 支持生成二维码、识别二维码、批量生成

## 函数

### _ensure_dir

```python
def _ensure_dir(path)
```

**参数:**
- `path` **必填**


### _generate_qr

```python
def _generate_qr(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _decode_qr

```python
def _decode_qr(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _batch_generate_qr

```python
def _batch_generate_qr(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: rag_tools

**文件:** `agent_tools/rag_tools.py`

RAG 知识库工具集（P1） - 让 Agent 更聪明
把项目文件分块索引到本地 SQLite，按 token 相关度检索，注入上下文。
放于 agent_tools/ 目录，由 HotReloader 自动扫描注册，改文件保存即热更新。

## 常量

- `_HERMES_DIR` = `os.path.dirname(...)`
- `_DB_PATH` = `os.path.join(...)`
- `_DEFAULT_EXTS` = `{'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.md', '.txt', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.sh', '.bat', '.ps1', '.xml', '.csv', '.sql'}`
- `_SKIP_DIRS` = `{'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', '.hermes_backup', 'data'}`
- `_MAX_FILE_CHARS` = `200000`
- `_CHUNK_LINES` = `200`
- `_CHUNK_OVERLAP` = `40`

## 函数

### _tokens

```python
def _tokens(query: str)
```

分词：英文/数字词 + 中文双字组

**参数:**
- `query`: str **必填**


### _chunk_text

```python
def _chunk_text(text: str, lines: int, overlap: int)
```

按行分块，块间重叠

**参数:**
- `text`: str **必填**
- `lines`: int (默认: `_CHUNK_LINES`)
- `overlap`: int (默认: `_CHUNK_OVERLAP`)


### _get_index

```python
def _get_index() -> RagIndex
```


### _rag_index

```python
def _rag_index(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _rag_search

```python
def _rag_search(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _rag_status

```python
def _rag_status(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _rag_drop

```python
def _rag_drop(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _rag_clear

```python
def _rag_clear(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


## 类

## class RagIndex

本地文件 RAG 索引（SQLite 持久化）

---

### __init__

```python
def __init__(db_path: str)
```

**参数:**
- `db_path`: str (默认: `_DB_PATH`)

### _connect

```python
def _connect() -> sqlite3.Connection
```

### _init_db

```python
def _init_db()
```

### _iter_files

```python
def _iter_files(path: str)
```

**参数:**
- `path`: str **必填**

### index

```python
def index(path: str) -> dict
```

**参数:**
- `path`: str **必填**

### search

```python
def search(query: str, top_k: int) -> list
```

**参数:**
- `query`: str **必填**
- `top_k`: int (默认: `5`)

### drop

```python
def drop(path: str) -> dict
```

**参数:**
- `path`: str **必填**

### status

```python
def status() -> dict
```

### clear

```python
def clear() -> dict
```


---

# 模块: random_tools

**文件:** `agent_tools/random_tools.py`

随机数据生成工具集 - 支持随机数、随机字符串、随机日期等

## 函数

### _random_number

```python
def _random_number(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _random_string

```python
def _random_string(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _random_date

```python
def _random_date(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: regex_tools

**文件:** `agent_tools/regex_tools.py`

正则表达式工具集 - 支持匹配、替换、提取

## 函数

### _regex_match

```python
def _regex_match(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _regex_replace

```python
def _regex_replace(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: rss_tools

**文件:** `agent_tools/rss_tools.py`

RSS阅读工具集 - 解析RSS订阅源

## 函数

### _parse_rss

```python
def _parse_rss(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: run

**文件:** `run.py`

Hermes Agent - Python 图形界面版
连接 12.py DeepSeek Browser API

用法:
    python run.py              # 启动 GUI (tkinter)
    python run.py --qt         # 启动 GUI (PyQt6)
    python run.py --url http://127.0.0.1:8001
    python run.py --no-parallel   # 关闭并行动作（严格串行）

## 函数

### main

```python
def main()
```


---

# 模块: scan_tools

**文件:** `agent_tools/scan_tools.py`

代码扫描工具集

## 常量

- `SKIP_DIRS` = `{'.git', '__pycache__', '.idea', '.vscode', 'node_modules', 'venv', 'env', '.hermes_backup', 'dist', 'build'}`

## 函数

### _scan_todos_in_file

```python
def _scan_todos_in_file(file_path: str) -> List[Dict]
```

**参数:**
- `file_path`: str **必填**


### scan_todos

```python
def scan_todos(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _count_file

```python
def _count_file(file_path: str) -> Dict
```

**参数:**
- `file_path`: str **必填**


### count_code

```python
def count_code(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _extract_imports

```python
def _extract_imports(file_path: str) -> Tuple[List[str], List[str]]
```

**参数:**
- `file_path`: str **必填**


### analyze_imports

```python
def analyze_imports(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### find_unused

```python
def find_unused(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```


---

# 模块: schedule_tools

**文件:** `agent_tools/schedule_tools.py`

定时任务调度工具集 - 支持定时执行、周期性任务

## 函数

### _get_next_id

```python
def _get_next_id()
```


### _execute_task

```python
def _execute_task(task_id)
```

**参数:**
- `task_id` **必填**


### _create_task

```python
def _create_task(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _list_tasks

```python
def _list_tasks(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _run_task

```python
def _run_task(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _delete_task

```python
def _delete_task(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _toggle_task

```python
def _toggle_task(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: search_tools

**文件:** `agent_tools/search_tools.py`

搜索工具模块

## 常量

- `_IGNORE_DIRS` = `{'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next', '.nuxt', 'target', '.idea', '.vscode'}`

## 函数

### _should_ignore

```python
def _should_ignore(path: Path) -> bool
```

**参数:**
- `path`: Path **必填**


### glob

```python
def glob(args: dict) -> str
```

通配符搜索文件

**参数:**
- `args`: dict **必填**


### grep

```python
def grep(args: dict) -> str
```

跨文件内容搜索（正则）

**参数:**
- `args`: dict **必填**


### search_by_name

```python
def search_by_name(args: dict) -> str
```

按文件名搜索

**参数:**
- `args`: dict **必填**


### search_by_content

```python
def search_by_content(args: dict) -> str
```

搜索文件内容

**参数:**
- `args`: dict **必填**


### search_by_size

```python
def search_by_size(args: dict) -> str
```

按文件大小搜索

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: smart_file_reader_tools

**文件:** `agent_tools/smart_file_reader_tools.py`

智能大文件读取工具
功能：分块读取大文件，自动管理阅读进度，生成文件结构摘要

解决问题：AI 读大文件只能看到一小部分

核心策略：
1. 自动分块读取 — 大文件按行分块，每块独立返回，AI 可逐块累积理解
2. 内容缓存 — 已读文件内容存内存，后续轮次可直接引用而无需重读
3. 智能摘要 — 同时提供文件结构摘要（函数/类/变量列表），让 AI 快速定位
4. 阅读进度追踪 — 记录已读范围，避免重复读取
5. 全局视图 — 所有块读完后，汇总生成完整文件概览

## 常量

- `MAX_CHUNK_CHARS` = `200000`
- `MAX_CHUNK_LINES` = `5000`
- `MAX_CACHED_FILES` = `50`
- `MAX_CACHE_SIZE_CHARS` = `1000000`

## 函数

### read_file_by_chunks

```python
def read_file_by_chunks(args: dict) -> str
```

智能分块读取大文件

自动将大文件按行分块，每块最多指定行数或字符数。
AI 可通过 chunk_index 逐块读取，读取完所有块后获得完整理解。

参数:
    path: 文件路径
    chunk_index: 块索引（从1开始），可选值：
        - 不传或 1: 返回文件信息 + 结构摘要 + 第1块
        - N: 返回第N块
        - all: 返回所有块
        - summary_only: 只返回结构摘要
    chunk_size: 每块最大字符数，默认 200000
    chunk_lines: 每块最大行数，默认 5000

**参数:**
- `args`: dict **必填**


### get_file_summary

```python
def get_file_summary(args: dict) -> str
```

获取文件结构摘要（不返回内容）

**参数:**
- `args`: dict **必填**


### cache_file_content

```python
def cache_file_content(args: dict) -> str
```

预加载文件内容到缓存

**参数:**
- `args`: dict **必填**


### clear_file_cache

```python
def clear_file_cache(args: dict) -> str
```

清空文件缓存

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```

注册所有工具，供热加载器调用


## 类

## class FileContextCache

文件内容缓存 — 单例

---

### __new__

```python
def __new__()
```

### __init__

```python
def __init__()
```

### _make_key

```python
def _make_key(path: str) -> str
```

生成缓存 key（规范化路径 + mtime）

**参数:**
- `path`: str **必填**

### put

```python
def put(path: str, content: str, lines: List[str], summary: str)
```

缓存文件内容

**参数:**
- `path`: str **必填**
- `content`: str **必填**
- `lines`: List[str] **必填**
- `summary`: str (默认: `''`)

### get

```python
def get(path: str) -> Optional[Dict]
```

获取缓存

**参数:**
- `path`: str **必填**

### get_lines

```python
def get_lines(path: str, start: int, end: int) -> Optional[List[str]]
```

从缓存获取指定行范围

**参数:**
- `path`: str **必填**
- `start`: int **必填**
- `end`: int **必填**

### log_read

```python
def log_read(path: str, start_line: int, end_line: int)
```

记录已读范围

**参数:**
- `path`: str **必填**
- `start_line`: int **必填**
- `end_line`: int **必填**

### get_read_ranges

```python
def get_read_ranges(path: str) -> List[Tuple[int, int]]
```

获取已读范围

**参数:**
- `path`: str **必填**

### get_unread_ranges

```python
def get_unread_ranges(path: str, total_lines: int) -> List[Tuple[int, int]]
```

获取未读范围

**参数:**
- `path`: str **必填**
- `total_lines`: int **必填**

### generate_summary

```python
def generate_summary(path: str, lines: List[str]) -> str
```

生成文件结构摘要 - 扫描全部行

**参数:**
- `path`: str **必填**
- `lines`: List[str] **必填**

### _detect_language

```python
def _detect_language(ext: str) -> str
```

**参数:**
- `ext`: str **必填**

### clear

```python
def clear()
```

清空缓存


---

# 模块: sort_tools

**文件:** `agent_tools/sort_tools.py`

排序工具集 - 支持列表排序、字典排序

## 函数

### _sort_list

```python
def _sort_list(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _sort_dict

```python
def _sort_dict(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: stock_tools

**文件:** `agent_tools/stock_tools.py`

股票交易工具集 - 支持A股行情、技术分析、模拟交易

## 函数

### _import_akshare

```python
def _import_akshare()
```


### _import_pandas

```python
def _import_pandas()
```


### _import_numpy

```python
def _import_numpy()
```


### get_sim_account

```python
def get_sim_account(initial_cash)
```

**参数:**
- `initial_cash` (默认: `100000`)


### _get_stock_quote

```python
def _get_stock_quote(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _get_stock_history

```python
def _get_stock_history(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _simulate_buy

```python
def _simulate_buy(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _simulate_sell

```python
def _simulate_sell(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _view_portfolio

```python
def _view_portfolio(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```

卸载工具


## 类

## class SimulatedAccount

---

### __init__

```python
def __init__(initial_cash)
```

**参数:**
- `initial_cash` (默认: `100000`)

### buy

```python
def buy(symbol, price, shares)
```

**参数:**
- `symbol` **必填**
- `price` **必填**
- `shares` **必填**

### sell

```python
def sell(symbol, price, shares)
```

**参数:**
- `symbol` **必填**
- `price` **必填**
- `shares` (默认: `None`)

### get_portfolio

```python
def get_portfolio(current_prices)
```

**参数:**
- `current_prices` (默认: `None`)


---

# 模块: summarize_tools

**文件:** `agent_tools/summarize_tools.py`

文本摘要工具集 - 支持文本摘要、关键词提取

## 函数

### _summarize_text

```python
def _summarize_text(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: sync_tools

**文件:** `agent_tools/sync_tools.py`

文件同步工具集 - 目录同步、增量备份

## 函数

### _sync_dirs

```python
def _sync_dirs(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: sysdetail_tools

**文件:** `agent_tools/sysdetail_tools.py`

系统信息详情工具集 - 获取CPU、内存、磁盘详细信息

## 函数

### _sys_info_detail

```python
def _sys_info_detail(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: system_tools

**文件:** `agent_tools/system_tools.py`

系统监控工具集 - 支持 CPU、内存、磁盘、网络、进程监控

## 函数

### _import_psutil

```python
def _import_psutil()
```


### _format_bytes

```python
def _format_bytes(bytes_val)
```

**参数:**
- `bytes_val` **必填**


### _system_info

```python
def _system_info(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _process_list

```python
def _process_list(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _kill_process

```python
def _kill_process(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _disk_analysis

```python
def _disk_analysis(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _uptime

```python
def _uptime(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: text_tools

**文件:** `agent_tools/text_tools.py`

文本处理工具集 - 支持转换、统计、加密、格式化

## 函数

### _import_jieba

```python
def _import_jieba()
```


### _text_stats

```python
def _text_stats(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _encrypt_text

```python
def _encrypt_text(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _convert_text

```python
def _convert_text(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _extract_keywords

```python
def _extract_keywords(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _markdown_to_html

```python
def _markdown_to_html(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: time_tools

**文件:** `agent_tools/time_tools.py`

日期时间工具集 - 支持日期计算、格式转换、时区处理

## 函数

### _date_calc

```python
def _date_calc(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _date_diff

```python
def _date_diff(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _now_time

```python
def _now_time(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: todo_manager_tools

**文件:** `agent_tools/todo_manager_tools.py`

待办管理模块

## 常量

- `_TODO_FILE` = `'hermes_todos.json'`

## 函数

### _load_todos

```python
def _load_todos()
```

加载待办列表


### _save_todos

```python
def _save_todos()
```

保存待办列表


### _find_todo

```python
def _find_todo(content: str) -> int
```

查找待办项

**参数:**
- `content`: str **必填**


### _todo_add

```python
def _todo_add(args: dict) -> str
```

添加待办

**参数:**
- `args`: dict **必填**


### _todo_start

```python
def _todo_start(args: dict) -> str
```

开始执行待办

**参数:**
- `args`: dict **必填**


### _todo_complete

```python
def _todo_complete(args: dict) -> str
```

标记待办完成

**参数:**
- `args`: dict **必填**


### _todo_list_fn

```python
def _todo_list_fn(args: dict) -> str
```

查看所有待办

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: tool_index

**文件:** `tool_index.py`

工具索引 - 从 TOOLS 注册表自动生成

提供：
- 按分类列出工具
- 按关键词搜索工具
- 生成 OpenAPI 格式文档

## 常量

- `CATEGORIES` = `{}`

## 函数

### _get_tool_info

```python
def _get_tool_info(tool_name: str) -> Optional[Dict]
```

获取单个工具的完整信息

**参数:**
- `tool_name`: str **必填**


### list_categories

```python
def list_categories() -> str
```

列出所有工具分类及每个分类的工具数量


### list_tools

```python
def list_tools() -> str
```

列出所有工具（按分类分组）


### category_tools

```python
def category_tools(category: str) -> str
```

按分类查询工具

**参数:**
- `category`: str **必填**


### search_tools

```python
def search_tools(keyword: str) -> str
```

按关键词搜索工具（名称或描述中包含关键词）

**参数:**
- `keyword`: str **必填**


### export_schemas

```python
def export_schemas() -> str
```

导出所有工具的 OpenAI 格式 schema（JSON）


### tool_help

```python
def tool_help(tool_name: str) -> str
```

获取某个工具的详细帮助

**参数:**
- `tool_name`: str **必填**


### get_tool_names

```python
def get_tool_names() -> List[str]
```

获取所有已注册的工具名


### get_category_for_tool

```python
def get_category_for_tool(tool_name: str) -> Optional[str]
```

获取工具所属的分类

**参数:**
- `tool_name`: str **必填**


---

# 模块: tool_index

**文件:** `agent_tools/tool_index.py`

工具索引查询模块 - 完全自动从 tools.TOOLS 读取

无需手动维护任何列表，自动从注册表生成分类、参数等信息。

## 常量

- `CATEGORY_MAP` = `{}`

## 函数

### _get_tools_by_category

```python
def _get_tools_by_category() -> dict
```

自动从 TOOLS 生成分类 -> 工具列表的映射


### _get_tool_params

```python
def _get_tool_params(tool_name: str) -> dict
```

自动从 TOOLS 读取工具参数信息

**参数:**
- `tool_name`: str **必填**


### list_categories

```python
def list_categories(args: dict) -> str
```

列出所有工具分类及每个分类的工具数量（自动从 TOOLS 生成）

**参数:**
- `args`: dict (默认: `None`)


### list_tools

```python
def list_tools(args: dict) -> str
```

列出所有工具（按分类分组），自动从 TOOLS 读取

**参数:**
- `args`: dict (默认: `None`)


### category_tools

```python
def category_tools(args: dict) -> str
```

按分类查询工具（自动从 TOOLS 读取）

**参数:**
- `args`: dict **必填**


### _format_category_tools

```python
def _format_category_tools(category: str, tools: list) -> str
```

格式化分类工具列表

**参数:**
- `category`: str **必填**
- `tools`: list **必填**


### search_tools

```python
def search_tools(args: dict) -> str
```

按关键词搜索工具（名称或描述中包含关键词）

**参数:**
- `args`: dict **必填**


### tool_help

```python
def tool_help(args: dict) -> str
```

获取某个工具的详细帮助

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具索引查询功能到 TOOLS


---

# 模块: tools

**文件:** `tools.py`

工具注册中心 - 统一解析 arguments + JSON 转义

## 函数

### register

```python
def register(name: str, description: str, parameters: dict, func: Callable)
```

注册工具

**参数:**
- `name`: str **必填**
- `description`: str **必填**
- `parameters`: dict **必填**
- `func`: Callable **必填**


### get_schemas

```python
def get_schemas() -> list
```

获取所有工具的 OpenAI 格式 schema


### _resolve_name

```python
def _resolve_name(name: str) -> Optional[str]
```

大小写不敏感解析工具名

**参数:**
- `name`: str **必填**


### _parse_arguments

```python
def _parse_arguments(args) -> dict
```

统一解析 arguments
支持：dict、JSON 字符串、原始字符串
同时处理所有字符串参数的 JSON 转义

**参数:**
- `args` **必填**


### execute

```python
def execute(name: str, args) -> str
```

执行工具（大小写不敏感）

**参数:**
- `name`: str **必填**
- `args` **必填**


### build_system_prompt

```python
def build_system_prompt() -> str
```

从已注册工具生成系统提示词


---

# 模块: translate_tools

**文件:** `agent_tools/translate_tools.py`

翻译工具 - 读取文件内容，翻译后写入新文件

## 函数

### _translate_file

```python
def _translate_file(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```

卸载工具


---

# 模块: tree_tools

**文件:** `agent_tools/tree_tools.py`

目录树工具 - 以树形结构列出目录内容

## 函数

### _tree_list

```python
def _tree_list(args: dict) -> str
```

以树形结构列出目录内容

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: utils

**文件:** `agent_tools/utils.py`

通用工具模块 - 计算、时间等

## 函数

### calculate

```python
def calculate(args: dict) -> str
```

安全数学计算

**参数:**
- `args`: dict **必填**


### get_time

```python
def get_time(args: dict) -> str
```

获取当前时间

**参数:**
- `args`: dict **必填**


### now_time

```python
def now_time(args: dict) -> str
```

获取当前时间（多种格式）

**参数:**
- `args`: dict **必填**


### date_calc

```python
def date_calc(args: dict) -> str
```

日期加减计算

**参数:**
- `args`: dict **必填**


### date_diff

```python
def date_diff(args: dict) -> str
```

计算日期差

**参数:**
- `args`: dict **必填**


### text_stats

```python
def text_stats(args: dict) -> str
```

统计文本信息

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


---

# 模块: validate_tools

**文件:** `agent_tools/validate_tools.py`

数据验证工具集 - 验证邮箱、手机号、URL、IP等格式

## 函数

### _validate_email

```python
def _validate_email(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _validate_phone

```python
def _validate_phone(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _validate_url

```python
def _validate_url(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _validate_ip

```python
def _validate_ip(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: video_tools

**文件:** `agent_tools/video_tools.py`

视频处理工具集 - 获取视频信息

## 函数

### _video_info

```python
def _video_info(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: watch_tools

**文件:** `agent_tools/watch_tools.py`

文件监控工具集 - 监控文件/目录变化

## 函数

### _watch_directory

```python
def _watch_directory(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: web_tools

**文件:** `agent_tools/web_tools.py`

网络爬虫工具集 - 支持网页抓取、内容提取、链接分析

## 函数

### _import_requests

```python
def _import_requests()
```


### _import_bs4

```python
def _import_bs4()
```


### _extract_title

```python
def _extract_title(html)
```

**参数:**
- `html` **必填**


### _fetch_url

```python
def _fetch_url(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _extract_links

```python
def _extract_links(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _search_web

```python
def _search_web(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _web_screenshot

```python
def _web_screenshot(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```


### unregister_tools

```python
def unregister_tools()
```


---

# 模块: wsl_advanced_tools

**文件:** `agent_tools/wsl_advanced_tools.py`

WSL 高级工具集 - 进程管理、文件搜索、系统监控、服务管理、网络工具、用户管理、权限管理

## 函数

### _run_wsl

```python
def _run_wsl(command: str, cwd: str, timeout: int) -> dict
```

在 WSL 中执行命令，返回 {stdout, stderr, returncode, success}

**参数:**
- `command`: str **必填**
- `cwd`: str (默认: `None`)
- `timeout`: int (默认: `60`)


### _format_output

```python
def _format_output(result: dict, title: str) -> str
```

格式化命令输出

**参数:**
- `result`: dict **必填**
- `title`: str (默认: `''`)


### wsl_ps

```python
def wsl_ps(args: dict) -> str
```

查看或终止 WSL 中的 Linux 进程

**参数:**
- `args`: dict **必填**


### wsl_find

```python
def wsl_find(args: dict) -> str
```

在 WSL 中搜索文件

**参数:**
- `args`: dict **必填**


### wsl_top

```python
def wsl_top(args: dict) -> str
```

查看 WSL 系统资源占用

**参数:**
- `args`: dict **必填**


### wsl_service

```python
def wsl_service(args: dict) -> str
```

启动/停止/查看 systemd 服务

**参数:**
- `args`: dict **必填**


### wsl_ping

```python
def wsl_ping(args: dict) -> str
```

网络诊断 ping

**参数:**
- `args`: dict **必填**


### wsl_curl

```python
def wsl_curl(args: dict) -> str
```

HTTP 请求 curl

**参数:**
- `args`: dict **必填**


### wsl_user

```python
def wsl_user(args: dict) -> str
```

查看或创建 WSL 用户

**参数:**
- `args`: dict **必填**


### wsl_chmod

```python
def wsl_chmod(args: dict) -> str
```

修改文件权限

**参数:**
- `args`: dict **必填**


### wsl_chown

```python
def wsl_chown(args: dict) -> str
```

修改文件所有者

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```


---

# 模块: wsl_tools

**文件:** `agent_tools/wsl_tools.py`

WSL2 工具封装 - 让 Hermes 原生支持 Linux 命令

## 函数

### _wsl_path_to_win

```python
def _wsl_path_to_win(wsl_path: str) -> str
```

将 WSL 路径转换为 Windows 可访问的网络路径

**参数:**
- `wsl_path`: str **必填**


### _win_path_to_wsl

```python
def _win_path_to_wsl(win_path: str) -> str
```

将 Windows 路径转换为 WSL 路径（通过 wslpath 命令）

**参数:**
- `win_path`: str **必填**


### _run_wsl

```python
def _run_wsl(command: str, cwd: str, timeout: int) -> dict
```

在 WSL 中执行命令，返回 {stdout, stderr, returncode, success}

**参数:**
- `command`: str **必填**
- `cwd`: str (默认: `None`)
- `timeout`: int (默认: `60`)


### wsl_exec

```python
def wsl_exec(args: dict) -> str
```

在 WSL Ubuntu 中执行任意 Linux 命令

**参数:**
- `args`: dict **必填**


### wsl_read

```python
def wsl_read(args: dict) -> str
```

读取 WSL 中的文件内容

**参数:**
- `args`: dict **必填**


### wsl_write

```python
def wsl_write(args: dict) -> str
```

写入内容到 WSL 中的文件

**参数:**
- `args`: dict **必填**


### wsl_list

```python
def wsl_list(args: dict) -> str
```

列出 WSL 目录内容

**参数:**
- `args`: dict **必填**


### wsl_install

```python
def wsl_install(args: dict) -> str
```

通过 apt 在 WSL Ubuntu 中安装软件包

**参数:**
- `args`: dict **必填**


### wsl_status

```python
def wsl_status(args: dict) -> str
```

查看 WSL 运行状态和系统信息

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools() -> int
```


---

# 模块: xml_tools

**文件:** `agent_tools/xml_tools.py`

XML处理工具集 - 支持解析、生成、查询

## 函数

### _parse_xml

```python
def _parse_xml(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _create_xml

```python
def _create_xml(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```

卸载工具


---

# 模块: yaml_tools

**文件:** `agent_tools/yaml_tools.py`

YAML处理工具集 - 支持读取、写入、转换

## 函数

### _import_yaml

```python
def _import_yaml()
```


### _read_yaml

```python
def _read_yaml(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### _write_yaml

```python
def _write_yaml(args: dict) -> str
```

**参数:**
- `args`: dict **必填**


### register_tools

```python
def register_tools()
```

注册工具到 Hermes


### unregister_tools

```python
def unregister_tools()
```


---
