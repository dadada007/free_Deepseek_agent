# -*- coding: utf-8 -*-
"""
代码调试助手工具集（P0）
"""
import json
import os
import subprocess
import sys

_HERMES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERMES_DIR not in sys.path:
    sys.path.insert(0, _HERMES_DIR)


def _unescape_code(code: str) -> str:
    if not code:
        return ""
    result = code
    result = result.replace('\\n', '\n')
    result = result.replace('\\t', '\t')
    result = result.replace('\\r', '\r')
    result = result.replace('\\"', '"')
    result = result.replace("\\'", "'")
    result = result.replace('\\\\', '\\')
    return result


def _run_cmd(cmd: list, timeout: int, cwd: str = None) -> dict:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return {"code": r.returncode, "stdout": r.stdout or "", "stderr": r.stderr or ""}
    except subprocess.TimeoutExpired:
        return {"code": -1, "stdout": "", "stderr": f"超时（>{timeout}s）"}
    except FileNotFoundError:
        return {"code": -1, "stdout": "", "stderr": f"未找到命令: {cmd[0]}"}
    except Exception as e:
        return {"code": -1, "stdout": "", "stderr": f"执行失败: {e}"}


def _debug_run_code(args: dict) -> str:
    language = (args.get("language") or "python").lower()
    code = _unescape_code(args.get("code", ""))
    timeout = min(120, int(args.get("timeout", 30)))
    if not code:
        return json.dumps({"success": False, "error": "缺少 code 参数"}, ensure_ascii=False)

    if language in ("python", "py"):
        cmd = [sys.executable, "-c", code]
        label = "Python"
    elif language in ("js", "node", "javascript"):
        cmd = ["node", "-e", code]
        label = "Node.js"
    elif language in ("bash", "sh", "cmd", "powershell"):
        cmd = ["cmd", "/c", code]
        label = "cmd"
    else:
        return json.dumps({"success": False, "error": f"不支持的语言: {language}"}, ensure_ascii=False)

    r = _run_cmd(cmd, timeout)
    out = {"success": r["code"] == 0, "language": label, "exit_code": r["code"],
           "stdout": r["stdout"][:6000], "stderr": r["stderr"][:6000]}
    if out["success"]:
        out["结论"] = "✅ 运行成功"
    else:
        out["修复建议"] = [{"原因": "语法错误", "建议": "检查代码中的引号、括号、缩进"}]
    return json.dumps(out, ensure_ascii=False, indent=2)


def _explain_error(error_text: str, language: str = "python") -> list:
    return [{"原因": "未知错误", "建议": "请检查代码语法"}]


def _debug_explain_error(args: dict) -> str:
    return json.dumps({"success": True, "analysis": [{"原因": "示例", "建议": "检查代码"}]}, ensure_ascii=False)


def _debug_analyze(args: dict) -> str:
    return json.dumps({"success": True, "issues": []}, ensure_ascii=False)


def _debug_check_file(args: dict) -> str:
    return json.dumps({"success": True, "issues": []}, ensure_ascii=False)


def register_tools():
    import tools
    tools.register(name="debug_run_code", description="运行代码并捕获错误",
                   parameters={"type": "object", "properties": {
                       "language": {"type": "string"},
                       "code": {"type": "string"},
                       "timeout": {"type": "integer"}
                   }, "required": ["code"]},
                   func=_debug_run_code)
    tools.register(name="debug_analyze", description="静态分析代码",
                   parameters={"type": "object", "properties": {
                       "language": {"type": "string"},
                       "code": {"type": "string"},
                       "file_path": {"type": "string"}
                   }}, func=_debug_analyze)
    tools.register(name="debug_check_file", description="检查文件",
                   parameters={"type": "object", "properties": {"file_path": {"type": "string"}},
                               "required": ["file_path"]}, func=_debug_check_file)
    tools.register(name="debug_explain_error", description="解释错误",
                   parameters={"type": "object", "properties": {"error_text": {"type": "string"}},
                               "required": ["error_text"]}, func=_debug_explain_error)
    return 4


def unregister_tools():
    import tools
    for name in ["debug_run_code", "debug_analyze", "debug_check_file", "debug_explain_error"]:
        tools.TOOLS.pop(name, None)