import re
import pyttsx3
from parser import extract_tool_calls  # 原有解析器

def get_speak_text(text: str) -> str:
    """
    从AI回复中提取用于语音朗读的纯文本
    """
    # 1. 先检查是否有工具调用
    tool_calls = extract_tool_calls(text)
    
    # 2. 如果没有工具调用，全部内容都用于朗读
    if not tool_calls:
        return text
    
    # 3. 如果有工具调用，移除JSON部分
    cleaned = text
    start = text.find('[')
    if start != -1:
        # 括号匹配找到完整的工具调用JSON
        bracket_count = 0
        in_string = False
        escape_next = False
        end = len(text)
        
        for i in range(start, len(text)):
            char = text[i]
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
        
        # 移除工具调用部分
        cleaned = (text[:start] + text[end:]).strip()
        # 清理多余标点
        cleaned = re.sub(r'^[\s,，。、]+', '', cleaned)
        cleaned = re.sub(r'[\s,，。、]+$', '', cleaned)
    
    return cleaned


def speak_text(text: str, rate: int = 150, volume: float = 0.9):
    """
    语音朗读文本
    
    Args:
        text: 要朗读的文本
        rate: 语速（默认150）
        volume: 音量（默认0.9）
    """
    if not text or not text.strip():
        print("⚠️ 没有可朗读的内容")
        return
    
    try:
        # 初始化TTS引擎
        engine = pyttsx3.init()
        
        # 设置语音属性
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        
        # 获取可用语音（可选）
        voices = engine.getProperty('voices')
        if voices:
            # 选择中文语音（如果有）
            for voice in voices:
                if 'zh' in voice.languages or 'Chinese' in voice.name:
                    engine.setProperty('voice', voice.id)
                    break
        
        print(f"🔊 朗读: {text}")
        engine.say(text)
        engine.runAndWait()
        
    except Exception as e:
        print(f"❌ 语音朗读失败: {e}")


# ========== 使用示例 ==========

def process_ai_response(ai_response: str):
    """
    完整的处理流程：提取工具调用 + 语音朗读
    """
    print(f"📝 AI原始回复: {ai_response}")
    print("-" * 50)
    
    # 1. 提取工具调用（使用原函数）
    tool_calls = extract_tool_calls(ai_response)
    if tool_calls:
        print(f"🔧 工具调用: {tool_calls}")
    else:
        print("ℹ️ 无工具调用")
    
    # 2. 提取朗读文本（使用新函数）
    speak_text = get_speak_text(ai_response)
    print(f"📖 朗读文本: {speak_text}")
    
    # 3. 语音朗读
    if speak_text:
        speak_text(speak_text)
    
    return tool_calls, speak_text


# ========== 测试 ==========

if __name__ == "__main__":
    # 测试1: 有工具调用
    response1 = '好的，现在为您查询北京的天气情况。[{"name": "get_weather", "arguments": {"city": "北京"}}]'
    process_ai_response(response1)
    
    print("\n" + "="*50 + "\n")
    
    # 测试2: 无工具调用
    response2 = '今天天气晴朗，适合出门游玩。'
    process_ai_response(response2)
    
    print("\n" + "="*50 + "\n")
    
    # 测试3: 多个工具调用
    response3 = '为您查询天气和播放音乐。[{"name": "get_weather", "arguments": {"city": "上海"}}, {"name": "play_music", "arguments": {"song": "晴天"}}]'
    process_ai_response(response3)