# -*- coding: utf-8 -*-
"""记忆服务 - 后台实时捕获对话并落库 + 自动加载注入上下文"""
import queue
import threading
import logging
import time
from datetime import datetime
from typing import List, Optional, Tuple

from memory_db import MemoryDB, Memory

logger = logging.getLogger(__name__)

MEMORY_CONFIG = {
    "enabled": True,
    "auto_save": True,
    "auto_load": True,
    "max_context_memories": 5,     # 每次注入上文的记忆条数
    "writer_interval": 2.0,        # 后台写入线程每几秒落库一次（实时刷新）
    "min_save_chars": 4,           # 短于该长度不入库
    "max_content_chars": 2000,     # 单条记忆截断长度
    # 加权排序权重（总和建议10）
    "weight_keyword": 5,           # 关键词匹配权重
    "weight_recency": 3,           # 最近时效权重
    "weight_importance": 2,        # 重要度权重
    "fuzzy_threshold": 2,          # 编辑距离阈值（<=2视为匹配）
}

_CATEGORY_KEYWORDS = {
    "code": ["代码", "函数", "class", "def ", "import", "print", "文件", "读取",
             "写入", "git", "commit", "脚本", ".py", ".js", ".json"],
    "task": ["完成", "做", "执行", "运行", "创建", "写", "改", "部署", "安装", "构建"],
    "preference": ["喜欢", "偏好", "习惯", "风格", "格式", "字体", "主题", "窗口"],
    "knowledge": ["学习", "了解", "概念", "原理", "知道", "解释", "是什么", "为什么"],
}

# ==================== 同义词映射 ====================
_SYNONYMS = {
    "记忆": ["回忆", "记住", "记得", "存储", "保存"],
    "源码": ["源代码", "代码", "程序", "脚本"],
    "问题": ["故障", "错误", "异常", "bug", "缺陷"],
    "修改": ["改", "变更", "更新", "编辑"],
    "文件": ["文档", "档案", "数据文件"],
    "配置": ["设置", "参数", "选项", "偏好"],
    "性能": ["速度", "效率", "吞吐", "响应"],
    "安全": ["防护", "加密", "认证", "权限"],
    "网络": ["连接", "通信", "传输", "协议"],
    "数据库": ["DB", "存储库", "SQLite", "MySQL"],
    "函数": ["方法", "过程", "子程序", "function"],
    "类": ["class", "对象", "结构体"],
    "安装": ["部署", "设置", "配置", "setup"],
    "运行": ["执行", "启动", "开始", "run"],
    "创建": ["生成", "新建", "构建", "make"],
}

# ==================== 拼音支持 ====================
try:
    from pypinyin import lazy_pinyin, pinyin, Style
    HAS_PINYIN = True
except ImportError:
    HAS_PINYIN = False
    logger.warning("⚠️ pypinyin 未安装，拼音匹配功能不可用。运行: pip install pypinyin")


def _get_pinyin(text: str) -> str:
    """获取中文文本的拼音（首字母+全拼）"""
    if not HAS_PINYIN or not text:
        return ""
    try:
        # 全拼
        full = "".join(lazy_pinyin(text))
        # 首字母
        initials = "".join([p[0][0] for p in pinyin(text, style=Style.FIRST_LETTER) if p])
        return full + initials
    except Exception:
        return ""


def _expand_query(query: str) -> List[str]:
    """扩展查询词：原始词 + 同义词 + 拼音"""
    terms = [query.lower()]
    # 同义词扩展
    for word, syns in _SYNONYMS.items():
        if word in query:
            terms.extend([s.lower() for s in syns])
        for syn in syns:
            if syn in query:
                terms.append(word.lower())
                break
    # 拼音扩展
    if HAS_PINYIN:
        pinyin_str = _get_pinyin(query)
        if pinyin_str:
            terms.append(pinyin_str)
    return list(set(terms))


def _levenshtein_distance(s1: str, s2: str) -> int:
    """编辑距离（Levenshtein）"""
    if len(s1) < len(s2):
        s1, s2 = s2, s1
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def _fuzzy_match(content: str, query_terms: List[str], threshold: int = 2) -> int:
    """模糊匹配：返回匹配到的词数量"""
    content_lower = content.lower()
    match_count = 0
    for term in query_terms:
        if term in content_lower:
            match_count += 1
            continue
        # 编辑距离模糊匹配（短词）
        if len(term) >= 2:
            for word in content_lower.split():
                if len(word) >= 2 and _levenshtein_distance(term, word) <= threshold:
                    match_count += 0.5
                    break
    return match_count


def _detect_category(text: str) -> str:
    low = text.lower()
    for cat, kws in _CATEGORY_KEYWORDS.items():
        if any(kw in low for kw in kws):
            return cat
    return "conversation"


def _calc_importance(text: str) -> int:
    imp = 3
    if len(text) > 100:
        imp += 2
    if any(w in text for w in ("记住", "重要", "偏好", "喜欢", "密码", "账号", "地址", "邮箱")):
        imp += 3
    if any(kw in text for kw in ("def ", "class ", "import ", "函数", "算法", "配置", "密钥")):
        imp += 1
    if len(text) < 20:
        imp -= 1
    return max(1, min(10, imp))


def _smart_truncate(content: str, max_len: int) -> str:
    """智能截断：在句子边界处切断，保留完整语义"""
    if len(content) <= max_len:
        return content
    for sep in ['。', '！', '？', '. ', '! ', '? ', '\n']:
        pos = content.rfind(sep, 0, max_len)
        if pos != -1:
            return content[:pos + 1]
    for sep in [" ", "，", "、", ";", ","]:
        pos = content.rfind(sep, 0, max_len)
        if pos != -1:
            return content[:pos]
    return content[:max_len]


class MemoryService:
    """记忆服务：后台线程实时把对话写入 SQLite；提供检索用于上下文注入。"""

    def __init__(self, db_path: str = None):
        self.db = MemoryDB(db_path)
        self._queue: "queue.Queue[dict]" = queue.Queue()
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.started = False
        self._saved_count = 0

    # ---- 后台写入 ----

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._writer_loop, daemon=True,
                                        name="memory-writer")
        self._thread.start()
        self.started = True
        logger.info(f"🧠 记忆后台写入已启动: {self.db.db_path}")

    def stop(self):
        self._running = False
        if self._thread:
            self._flush()
            self._thread.join(timeout=3)
            self._thread = None

    def _writer_loop(self):
        while self._running:
            try:
                self._flush()
            except Exception as e:
                logger.warning(f"⚠️ 记忆后台写入异常: {e}")
            time.sleep(MEMORY_CONFIG["writer_interval"])

    def _flush(self):
        batch = []
        while True:
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if not batch:
            return
        with self._lock:
            try:
                n = self.db.save_batch(batch)
                self._saved_count += n
                logger.info(f"💾 记忆后台落库 {n} 条（队列剩余 {self._queue.qsize()}）")
            except Exception as e:
                logger.warning(f"⚠️ 记忆落库失败: {e}")

    # ---- 对话实时捕获 ----

    def record_turn(self, role: str, content: str, source: str = "hermes") -> bool:
        cfg = MEMORY_CONFIG
        if not cfg.get("enabled") or not cfg.get("auto_save"):
            return False
        content = (content or "").strip()
        if len(content) < cfg.get("min_save_chars", 4):
            return False
        max_len = cfg.get("max_content_chars", 2000)
        content = _smart_truncate(content, max_len)
        importance = _calc_importance(content)
        # 自动检测内容类别，而不是硬编码为 role
        category = _detect_category(content)
        self._queue.put({
            "content": content,
            "category": category,
            "source": source,
            "importance": importance,
        })
        return True

    # ---- 直接保存 / 检索 ----

    def save(self, content: str, category: str = "general",
             source: str = "user_manual", importance: int = 5) -> int:
        return self.db.save(content, category=category, source=source, importance=importance)

    def auto_load_memory(self, query: str, limit: int = None) -> List[Memory]:
        """自动加载相关记忆：加权排序（关键词 + 最近 + 高重要度）"""
        cfg = MEMORY_CONFIG
        if not cfg.get("enabled") or not cfg.get("auto_load"):
            return []
        limit = limit or cfg.get("max_context_memories", 5)
        threshold = cfg.get("fuzzy_threshold", 2)
        w_kw = cfg.get("weight_keyword", 5)
        w_rec = cfg.get("weight_recency", 3)
        w_imp = cfg.get("weight_importance", 2)

        # 扩展查询词
        expanded_terms = _expand_query(query)
        logger.debug(f"🔍 扩展查询词: {expanded_terms}")

        # 从数据库获取候选（先多取一些）
        candidate_limit = max(limit * 5, 20)
        # 使用关键词搜索获取候选
        keyword_memories = self.db.search(query, limit=candidate_limit)
        # 补充最近和高重要度记忆
        recent_memories = self.db.search_by_time(days=1, limit=5)
        important_memories = self.db.search_by_importance(min_importance=7, limit=5)

        # 合并去重
        all_memories = {}
        for m in keyword_memories + recent_memories + important_memories:
            if m.id not in all_memories:
                all_memories[m.id] = m

        if not all_memories:
            return []

        # 计算每个记忆的综合得分
        now = datetime.now().timestamp()
        scored: List[Tuple[float, Memory]] = []

        for mem in all_memories.values():
            # 1. 关键词匹配得分（使用扩展词 + 模糊匹配）
            kw_score = _fuzzy_match(mem.content, expanded_terms, threshold)
            # 归一化到 0-10
            kw_score = min(kw_score * 2, 10)

            # 2. 最近时效得分（越近越高）
            age_hours = (now - mem.timestamp) / 3600
            rec_score = max(0, 10 - age_hours * 0.5)  # 20小时后衰减到0
            rec_score = min(rec_score, 10)

            # 3. 重要度得分（直接使用 importance * 1.0）
            imp_score = min(mem.importance, 10)

            # 综合加权得分
            total = (kw_score * w_kw + rec_score * w_rec + imp_score * w_imp) / (w_kw + w_rec + w_imp)
            scored.append((total, mem))

        # 按得分降序排序
        scored.sort(key=lambda x: x[0], reverse=True)

        # 返回 top limit
        result = [mem for _, mem in scored[:limit]]
        logger.info(f"🧠 加载记忆: 从 {len(all_memories)} 条候选中选出 {len(result)} 条 (查询: {query[:30]}...)")
        return result

    def search(self, query: str, limit: int = 10,
               category: Optional[str] = None,
               min_importance: int = 1) -> List[Memory]:
        return self.db.search(query, limit=limit, category=category,
                              min_importance=min_importance)

    def status(self) -> str:
        recent = self.db.recent(5)
        lines = [
            "🧠 记忆系统状态",
            f"   数据库: {self.db.db_path}",
            f"   后台写入线程: {'运行中' if self._running else '已停止'}",
            f"   待写入队列: {self._queue.qsize()} 条",
            f"   本次运行已落库: {self._saved_count} 条",
            f"   累计记忆总数: {self.db.count()} 条",
        ]
        for m in recent:
            lines.append(f"     · [{m.to_dict()['time']}] ({m.category}) {m.content[:60]}")
        return "\n".join(lines)


# ==================== 全局单例 ====================

_service: Optional[MemoryService] = None


def get_service() -> MemoryService:
    global _service
    if _service is None:
        _service = MemoryService()
        _service.start()
    return _service


def record_turn(role: str, content: str, source: str = "hermes") -> bool:
    try:
        return get_service().record_turn(role, content, source)
    except Exception:
        return False


def auto_load_memory(query: str, limit: int = None) -> List[Memory]:
    try:
        return get_service().auto_load_memory(query, limit)
    except Exception:
        return []


def format_memories_for_context(memories: List[Memory]) -> str:
    """将记忆格式化为可注入 LLM 上下文的文本（树形结构 + 编号）"""
    if not memories:
        return ""

    lines = ["【历史记忆】"]
    lines.append("├─ 共 " + str(len(memories)) + " 条相关记忆")

    # 分类 Emoji 映射
    cat_emoji = {
        "code": "💻",
        "task": "📋",
        "preference": "⭐",
        "knowledge": "🧠",
        "conversation": "💬",
        "general": "📌",
    }

    for idx, m in enumerate(memories, 1):
        t = datetime.fromtimestamp(m.timestamp).strftime("%m-%d %H:%M")
        emoji = cat_emoji.get(m.category, "📌")
        imp_star = "★" * min(m.importance // 2, 5) + "☆" * (5 - min(m.importance // 2, 5))

        # 树形结构：最后一条用 └─，其他用 ├─
        prefix = "└─" if idx == len(memories) else "├─"

        # 内容截断到 80 字
        content = m.content[:80]
        if len(m.content) > 80:
            content += "..."

        lines.append(f"{prefix} #{idx} {emoji} {content}")
        lines.append(f"│  └─ {t} | 重要度: {imp_star} | 分类: {m.category}")

    return "\n".join(lines)


def memory_status() -> str:
    try:
        return get_service().status()
    except Exception as e:
        return f"记忆系统状态获取失败: {e}"
