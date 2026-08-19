# -*- coding: utf-8 -*-
"""
Git 高级操作工具集（P1） - 开发流必备
封装 git 命令行：状态/日志/差异/提交/分支/合并/暂存/回退/推送。
自动向上查找 .git 仓库根目录。放于 agent_tools/ 目录，由 HotReloader 扫描注册。
"""
import json
import os
import subprocess
import sys

# agent_tools 的上一级 = hermes/
_HERMES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERMES_DIR not in sys.path:
    sys.path.insert(0, _HERMES_DIR)

_DEFAULT_TIMEOUT = 60


def _find_repo(repo_path: str = None) -> str:
    """从 repo_path（默认当前目录）向上查找含 .git 的目录"""
    start = os.path.abspath(repo_path or ".")
    cur = start
    while True:
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return ""  # 非 git 仓库


def _git(repo: str, args: list, timeout: int = _DEFAULT_TIMEOUT) -> dict:
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True,
                           timeout=timeout, cwd=repo)
        ok = r.returncode == 0
        return {
            "success": ok,
            "returncode": r.returncode,
            "stdout": (r.stdout or "").rstrip()[:6000],
            "stderr": (r.stderr or "").rstrip()[:3000],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"⏱️ git 超时（>{timeout}s）"}
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": "❌ 未安装 git 或不在 PATH"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": f"❌ git 执行失败: {e}"}


def _git_out(args: dict, git_args: list) -> str:
    repo = _find_repo(args.get("repo_path"))
    if not repo:
        return json.dumps({"success": False,
                           "error": f"未找到 git 仓库（在 {os.path.abspath(args.get('repo_path') or '.')} 及上级目录）"},
                          ensure_ascii=False, indent=2)
    r = _git(repo, git_args)
    r["repo"] = repo
    if not r["success"] and not r["stdout"]:
        r["error"] = r["stderr"] or "git 命令失败"
    return json.dumps(r, ensure_ascii=False, indent=2)


# ==================== 工具实现 ====================

def _git_status(args: dict) -> str:
    return _git_out(args, ["status", "--short", "--branch"])


def _git_log(args: dict) -> str:
    limit = min(50, int(args.get("limit", 10)))
    fmt = "%h|%ad|%an|%s"
    return _git_out(args, ["log", f"-{limit}", f"--date=format:%m-%d %H:%M",
                           f"--pretty=format:{fmt}"])


def _git_diff(args: dict) -> str:
    cmd = ["diff"]
    if args.get("staged"):
        cmd = ["diff", "--cached"]
    if args.get("path"):
        cmd.append(args["path"])
    return _git_out(args, cmd)


def _git_commit(args: dict) -> str:
    repo = _find_repo(args.get("repo_path"))
    if not repo:
        return _git_out(args, ["log"])
    message = args.get("message", "")
    if not message:
        return json.dumps({"success": False, "error": "缺少 message 参数"},
                          ensure_ascii=False, indent=2)
    if args.get("add_all", True):
        a = _git(repo, ["add", "-A"])
        if not a["success"]:
            a["repo"] = repo
            return json.dumps(a, ensure_ascii=False, indent=2)
    elif args.get("files"):
        a = _git(repo, ["add"] + args["files"])
        if not a["success"]:
            a["repo"] = repo
            return json.dumps(a, ensure_ascii=False, indent=2)
    c = _git(repo, ["commit", "-m", message])
    c["repo"] = repo
    return json.dumps(c, ensure_ascii=False, indent=2)


def _git_branch(args: dict) -> str:
    repo = _find_repo(args.get("repo_path"))
    if not repo:
        return _git_out(args, ["branch"])
    action = args.get("action", "list")
    branch = args.get("branch", "")
    if action == "list":
        return _git_out(args, ["branch", "-a"])
    if not branch:
        return json.dumps({"success": False, "error": "branch 操作需要 branch 参数"},
                          ensure_ascii=False, indent=2)
    if action == "create":
        return _git_out(args, ["branch", branch])
    if action == "switch":
        return _git_out(args, ["checkout", branch])
    if action == "create_switch":
        return _git_out(args, ["checkout", "-b", branch])
    if action == "delete":
        return _git_out(args, ["branch", "-d", branch])
    return json.dumps({"success": False,
                       "error": f"未知 action: {action}（list/create/switch/create_switch/delete）"},
                      ensure_ascii=False, indent=2)


def _git_merge(args: dict) -> str:
    branch = args.get("branch", "")
    if not branch:
        return "错误: 缺少 branch 参数"
    return _git_out(args, ["merge", branch])


def _git_stash(args: dict) -> str:
    action = args.get("action", "push")
    if action == "push":
        return _git_out(args, ["stash", "push", "-u"])
    if action == "list":
        return _git_out(args, ["stash", "list"])
    if action == "pop":
        return _git_out(args, ["stash", "pop"])
    return _git_out(args, ["stash"])


def _git_reset(args: dict) -> str:
    commit = args.get("commit", "HEAD")
    mode = args.get("mode", "mixed")
    if mode == "hard":
        return _git_out(args, ["reset", "--hard", commit])
    if mode == "soft":
        return _git_out(args, ["reset", "--soft", commit])
    return _git_out(args, ["reset", commit])


def _git_push(args: dict) -> str:
    cmd = ["push", args.get("remote", "origin"), args.get("branch") or "HEAD"]
    return _git_out(args, cmd)


def _git_pull(args: dict) -> str:
    cmd = ["pull", args.get("remote", "origin"), args.get("branch") or ""]
    return _git_out(args, [c for c in cmd if c])


def _git_run(args: dict) -> str:
    """通用 git 命令（高级/组合操作）"""
    git_args = args.get("args", [])
    if not git_args or not isinstance(git_args, list):
        return "错误: 缺少 args 参数（git 子命令数组，如 ['log','--oneline']）"
    return _git_out(args, git_args)


# ==================== 热加载注册 ====================

def register_tools():
    import tools
    tools.register(
        name="git_status",
        description="查看 git 仓库状态（简要+分支）。参数: repo_path(可选，仓库目录)",
        parameters={"type": "object", "properties": {"repo_path": {"type": "string"}}},
        func=_git_status,
    )
    tools.register(
        name="git_log",
        description="查看最近提交记录。参数: limit(条数,默认10), repo_path",
        parameters={"type": "object", "properties": {
            "limit": {"type": "integer"}, "repo_path": {"type": "string"}}},
        func=_git_log,
    )
    tools.register(
        name="git_diff",
        description="查看未提交的改动差异。参数: staged(是否查看已暂存,默认false), path(可选限定文件), repo_path",
        parameters={"type": "object", "properties": {
            "staged": {"type": "boolean"}, "path": {"type": "string"},
            "repo_path": {"type": "string"}}},
        func=_git_diff,
    )
    tools.register(
        name="git_commit",
        description="提交所有改动。参数: message(提交信息), add_all(默认true), files(可选指定文件), repo_path",
        parameters={"type": "object", "properties": {
            "message": {"type": "string"}, "add_all": {"type": "boolean"},
            "files": {"type": "array"}, "repo_path": {"type": "string"}},
            "required": ["message"]},
        func=_git_commit,
    )
    tools.register(
        name="git_branch",
        description="分支操作。参数: action(list/create/switch/create_switch/delete), branch(分支名), repo_path",
        parameters={"type": "object", "properties": {
            "action": {"type": "string"}, "branch": {"type": "string"},
            "repo_path": {"type": "string"}}},
        func=_git_branch,
    )
    tools.register(
        name="git_merge",
        description="合并分支到当前分支。参数: branch(要合并的分支), repo_path",
        parameters={"type": "object", "properties": {
            "branch": {"type": "string"}, "repo_path": {"type": "string"}},
            "required": ["branch"]},
        func=_git_merge,
    )
    tools.register(
        name="git_stash",
        description="暂存改动。参数: action(push/list/pop), repo_path",
        parameters={"type": "object", "properties": {
            "action": {"type": "string"}, "repo_path": {"type": "string"}}},
        func=_git_stash,
    )
    tools.register(
        name="git_reset",
        description="回退提交。参数: commit(默认HEAD), mode(mixed/soft/hard,默认mixed), repo_path。注意 hard 会丢弃改动",
        parameters={"type": "object", "properties": {
            "commit": {"type": "string"}, "mode": {"type": "string"},
            "repo_path": {"type": "string"}}},
        func=_git_reset,
    )
    tools.register(
        name="git_push",
        description="推送到远程。参数: remote(默认origin), branch(分支，默认当前), repo_path",
        parameters={"type": "object", "properties": {
            "remote": {"type": "string"}, "branch": {"type": "string"},
            "repo_path": {"type": "string"}}},
        func=_git_push,
    )
    tools.register(
        name="git_pull",
        description="从远程拉取。参数: remote(默认origin), branch(可选), repo_path",
        parameters={"type": "object", "properties": {
            "remote": {"type": "string"}, "branch": {"type": "string"},
            "repo_path": {"type": "string"}}},
        func=_git_pull,
    )
    tools.register(
        name="git_run",
        description="执行任意 git 命令（高级操作）。参数: args(git 子命令数组，如 ['rebase','-i','HEAD~3']), repo_path",
        parameters={"type": "object", "properties": {
            "args": {"type": "array"}, "repo_path": {"type": "string"}},
            "required": ["args"]},
        func=_git_run,
    )
    return 11


def unregister_tools():
    import tools
    for name in ["git_status", "git_log", "git_diff", "git_commit", "git_branch",
                 "git_merge", "git_stash", "git_reset", "git_push", "git_pull",
                 "git_run"]:
        tools.TOOLS.pop(name, None)