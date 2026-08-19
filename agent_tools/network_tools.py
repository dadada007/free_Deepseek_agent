# -*- coding: utf-8 -*-
"""
网络请求工具集 - 支持HTTP请求、API调用、文件下载
"""

import os
import json
import time


def _ensure_dir(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)


def _http_request(args: dict) -> str:
    try:
        method = args.get('method', 'GET').upper()
        url = args.get('url', '')
        headers = args.get('headers', {})
        body = args.get('data', {})
        timeout = args.get('timeout', 30)
        if not url:
            return "❌ 请提供 URL"
        try:
            import requests
        except ImportError:
            return "❌ 请安装 requests: pip install requests"
        start_time = time.time()
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            resp = requests.post(url, json=body, headers=headers, timeout=timeout)
        elif method == 'PUT':
            resp = requests.put(url, json=body, headers=headers, timeout=timeout)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return f"❌ 不支持的方法: {method}"
        elapsed = time.time() - start_time
        try:
            response_body = resp.json()
        except:
            response_body = resp.text[:1000]
        result = {'状态码': resp.status_code, '耗时': f"{elapsed:.2f}s", '响应体': response_body}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 请求失败: {e}"


def _download_file(args: dict) -> str:
    try:
        url = args.get('url', '')
        output = args.get('output', '')
        if not url:
            return "❌ 请提供 URL"
        if not output:
            return "❌ 请提供输出路径"
        try:
            import requests
        except ImportError:
            return "❌ 请安装 requests: pip install requests"
        _ensure_dir(output)
        resp = requests.get(url, stream=True, timeout=60)
        if resp.status_code != 200:
            return f"❌ 下载失败: HTTP {resp.status_code}"
        downloaded = 0
        with open(output, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        return json.dumps({'成功': True, '输出': output, '大小': f"{downloaded / 1024:.1f} KB"}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 下载失败: {e}"


def _batch_download(args: dict) -> str:
    try:
        file_list = args.get('files', [])
        if not file_list:
            return "❌ 请提供文件列表"
        results = []
        for item in file_list:
            url = item.get('url', '')
            output = item.get('output', '')
            if not url or not output:
                results.append({'url': url, 'error': '缺少URL或输出路径'})
                continue
            result = _download_file({'url': url, 'output': output})
            try:
                results.append(json.loads(result))
            except:
                results.append({'url': url, 'error': result})
        return json.dumps({'结果': results}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 批量下载失败: {e}"


def register_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    tools.register(name="http_request", description="发送HTTP请求。参数: method, url, headers, data, timeout", parameters={"type": "object", "properties": {"method": {"type": "string"}, "url": {"type": "string"}, "headers": {"type": "object"}, "data": {"type": "object"}, "timeout": {"type": "integer"}}, "required": ["url"]}, func=_http_request)
    tools.register(name="download_file", description="下载文件到本地。参数: url, output", parameters={"type": "object", "properties": {"url": {"type": "string"}, "output": {"type": "string"}}, "required": ["url", "output"]}, func=_download_file)
    tools.register(name="batch_download", description="批量下载文件。参数: files([{url, output}])", parameters={"type": "object", "properties": {"files": {"type": "array"}}, "required": ["files"]}, func=_batch_download)
    return 3


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["http_request", "download_file", "batch_download"]:
        tools.TOOLS.pop(name, None)
