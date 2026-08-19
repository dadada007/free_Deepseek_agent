# agent_tools - 热加载工具目录
# 放在此目录的 .py 文件会被自动扫描和热加载
# 每个模块需定义 register_tools() 函数，调用 tools.register() 注册工具


# 导入 fs_register 以触发工具注册
from . import fs_register

# 导入 smart_file_reader_tools 并显式注册工具
from . import smart_file_reader_tools
smart_file_reader_tools.register_tools()
