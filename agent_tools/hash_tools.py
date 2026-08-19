# -*- coding: utf-8 -*-
"""
哈希校验工具集 - 支持MD5、SHA1、SHA256、CRC32等
"""

import os
import json
import hashlib
import zlib


def _hash_file(args: dict) -> str:
    try:
        path = args.get('path', '')
        algorithm = args.get('algorithm', 'md5').lower()
        if not path:
            return "❌ 请提供文件路径"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        if not os.path.isfile(path):
            return "❌ 路径不是文件"
        algorithms = {'md5': hashlib.md5, 'sha1': hashlib.sha1, 'sha256': hashlib.sha256, 'sha512': hashlib.sha512}
        if algorithm not in algorithms:
            return f"❌ 不支持的算法: {algorithm}（支持: md5, sha1, sha256, sha512）"
        hash_obj = algorithms[algorithm]()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return json.dumps({'成功': True, '文件': path, '算法': algorithm, '哈希值': hash_obj.hexdigest()}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 计算哈希失败: {e}"


def _hash_text(args: dict) -> str:
    try:
        text = args.get('text', '')
        algorithm = args.get('algorithm', 'md5').lower()
        if not text:
            return "❌ 请提供文本内容"
        algorithms = {'md5': hashlib.md5, 'sha1': hashlib.sha1, 'sha256': hashlib.sha256, 'sha512': hashlib.sha512}
        if algorithm not in algorithms:
            return f"❌ 不支持的算法: {algorithm}"
        hash_obj = algorithms[algorithm](text.encode())
        return json.dumps({'成功': True, '原文': text[:50], '算法': algorithm, '哈希值': hash_obj.hexdigest()}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 计算哈希失败: {e}"


def _verify_hash(args: dict) -> str:
    try:
        path = args.get('path', '')
        expected_hash = args.get('hash', '')
        algorithm = args.get('algorithm', 'md5').lower()
        if not path:
            return "❌ 请提供文件路径"
        if not expected_hash:
            return "❌ 请提供期望的哈希值"
        if not os.path.exists(path):
            return f"❌ 文件不存在: {path}"
        algorithms = {'md5': hashlib.md5, 'sha1': hashlib.sha1, 'sha256': hashlib.sha256, 'sha512': hashlib.sha512}
        if algorithm not in algorithms:
            return f"❌ 不支持的算法: {algorithm}"
        hash_obj = algorithms[algorithm]()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        actual_hash = hash_obj.hexdigest()
        is_valid = actual_hash.lower() == expected_hash.lower()
        return json.dumps({'成功': True, '文件': path, '算法': algorithm, '期望哈希': expected_hash, '实际哈希': actual_hash, '匹配': is_valid}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 验证失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="hash_file", description="计算文件哈希值。参数: path, algorithm(md5/sha1/sha256/sha512)", parameters={"type": "object", "properties": {"path": {"type": "string"}, "algorithm": {"type": "string"}}, "required": ["path"]}, func=_hash_file)
    tools.register(name="hash_text", description="计算字符串哈希值。参数: text, algorithm", parameters={"type": "object", "properties": {"text": {"type": "string"}, "algorithm": {"type": "string"}}, "required": ["text"]}, func=_hash_text)
    tools.register(name="verify_hash", description="验证文件哈希值。参数: path, hash, algorithm", parameters={"type": "object", "properties": {"path": {"type": "string"}, "hash": {"type": "string"}, "algorithm": {"type": "string"}}, "required": ["path", "hash"]}, func=_verify_hash)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["hash_file", "hash_text", "verify_hash"]:
        tools.TOOLS.pop(name, None)
