# -*- coding: utf-8 -*-
"""
压缩解压工具集 - 支持 ZIP、TAR、GZ、BZ2、XZ 等格式
"""

import os
import json
import shutil
from datetime import datetime


def _ensure_dir(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)


def _get_file_size(path):
    size = os.path.getsize(path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _list_files(dir_path):
    files = []
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files


def _zip_files(args: dict) -> str:
    try:
        import zipfile
        source = args.get('source', '')
        output = args.get('output', 'archive.zip')
        compress_level = args.get('compress_level', 6)
        if not source:
            return "❌ 请提供源路径 (source)"
        if not os.path.exists(source):
            return f"❌ 源路径不存在: {source}"
        _ensure_dir(output)
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compress_level) as zf:
            if os.path.isfile(source):
                zf.write(source, os.path.basename(source))
                file_count = 1
            else:
                for root, _, files in os.walk(source):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(source))
                        zf.write(file_path, arcname)
                file_count = len(_list_files(source))
        return json.dumps({'success': True, '输出': output, '文件数': file_count, '压缩大小': _get_file_size(output)}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 压缩失败: {e}"


def _unzip_files(args: dict) -> str:
    try:
        import zipfile
        archive = args.get('archive', '')
        output_dir = args.get('output_dir', '')
        if not archive:
            return "❌ 请提供压缩包路径 (archive)"
        if not os.path.exists(archive):
            return f"❌ 压缩包不存在: {archive}"
        if not output_dir:
            output_dir = os.path.splitext(archive)[0] + '_extracted'
        _ensure_dir(output_dir)
        with zipfile.ZipFile(archive, 'r') as zf:
            zf.extractall(output_dir)
            file_count = len(zf.namelist())
        return json.dumps({'success': True, '输出目录': output_dir, '文件数': file_count}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 解压失败: {e}"


def _tar_files(args: dict) -> str:
    try:
        import tarfile
        source = args.get('source', '')
        output = args.get('output', 'archive.tar.gz')
        compression = args.get('compression', 'gz')
        if not source:
            return "❌ 请提供源路径 (source)"
        if not os.path.exists(source):
            return f"❌ 源路径不存在: {source}"
        _ensure_dir(output)
        mode = 'w:' + compression if compression else 'w'
        with tarfile.open(output, mode) as tf:
            if os.path.isfile(source):
                tf.add(source, os.path.basename(source))
                file_count = 1
            else:
                tf.add(source, os.path.basename(source))
                file_count = len(_list_files(source))
        return json.dumps({'success': True, '输出': output, '文件数': file_count}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 压缩失败: {e}"


def _untar_files(args: dict) -> str:
    try:
        import tarfile
        archive = args.get('archive', '')
        output_dir = args.get('output_dir', '')
        if not archive:
            return "❌ 请提供压缩包路径 (archive)"
        if not os.path.exists(archive):
            return f"❌ 压缩包不存在: {archive}"
        if not output_dir:
            output_dir = os.path.splitext(archive)[0] + '_extracted'
        _ensure_dir(output_dir)
        with tarfile.open(archive, 'r') as tf:
            tf.extractall(output_dir)
            file_count = len(tf.getmembers())
        return json.dumps({'success': True, '输出目录': output_dir, '文件数': file_count}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 解压失败: {e}"


def _list_archive_content(args: dict) -> str:
    try:
        archive = args.get('archive', '')
        if not archive:
            return "❌ 请提供压缩包路径 (archive)"
        if not os.path.exists(archive):
            return f"❌ 压缩包不存在: {archive}"
        ext = os.path.splitext(archive)[1].lower()
        result = {'压缩包': archive, '格式': ext, '大小': _get_file_size(archive)}
        if ext in ['.zip']:
            import zipfile
            with zipfile.ZipFile(archive, 'r') as zf:
                files = []
                for info in zf.infolist():
                    files.append({'名称': info.filename, '大小': _get_file_size(info.file_size)})
                result['文件列表'] = files[:100]
                result['总文件数'] = len(files)
        elif ext in ['.tar', '.gz', '.bz2', '.xz']:
            import tarfile
            with tarfile.open(archive, 'r') as tf:
                files = []
                for member in tf.getmembers():
                    files.append({'名称': member.name, '大小': _get_file_size(member.size)})
                result['文件列表'] = files[:100]
                result['总文件数'] = len(files)
        else:
            return f"❌ 不支持的压缩格式: {ext}"
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 查看失败: {e}"


def register_tools():
    """注册工具到 Hermes"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools

    tools.register(
        name="zip_files",
        description="压缩文件或目录为ZIP格式。参数: source(源路径), output(输出文件), compress_level(压缩级别)",
        parameters={"type": "object", "properties": {
            "source": {"type": "string", "description": "源文件或目录路径"},
            "output": {"type": "string", "description": "输出ZIP文件路径"},
            "compress_level": {"type": "integer", "description": "压缩级别0-9"}
        }, "required": ["source"]},
        func=_zip_files,
    )
    tools.register(
        name="unzip_files",
        description="解压ZIP文件。参数: archive(压缩包路径), output_dir(输出目录)",
        parameters={"type": "object", "properties": {
            "archive": {"type": "string", "description": "ZIP文件路径"},
            "output_dir": {"type": "string", "description": "解压输出目录"}
        }, "required": ["archive"]},
        func=_unzip_files,
    )
    tools.register(
        name="tar_files",
        description="压缩为TAR格式。参数: source(源路径), output(输出文件), compression(压缩格式gz/bz2/xz)",
        parameters={"type": "object", "properties": {
            "source": {"type": "string", "description": "源文件或目录路径"},
            "output": {"type": "string", "description": "输出TAR文件路径"},
            "compression": {"type": "string", "description": "压缩格式: gz, bz2, xz"}
        }, "required": ["source"]},
        func=_tar_files,
    )
    tools.register(
        name="untar_files",
        description="解压TAR文件。参数: archive(压缩包路径), output_dir(输出目录)",
        parameters={"type": "object", "properties": {
            "archive": {"type": "string", "description": "TAR文件路径"},
            "output_dir": {"type": "string", "description": "解压输出目录"}
        }, "required": ["archive"]},
        func=_untar_files,
    )
    tools.register(
        name="list_archive_content",
        description="查看压缩包内容。参数: archive(压缩包路径)",
        parameters={"type": "object", "properties": {
            "archive": {"type": "string", "description": "压缩包文件路径"}
        }, "required": ["archive"]},
        func=_list_archive_content,
    )
    return 5


def unregister_tools():
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import tools
    for name in ["zip_files", "unzip_files", "tar_files", "untar_files", "list_archive_content"]:
        tools.TOOLS.pop(name, None)
