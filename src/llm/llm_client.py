"""LLM客户端 - 调用大语言模型"""
import requests
from typing import Dict, Any, Optional
from .config_manager import LLMConfig, LLMConfigManager


class LLMClient:
    """LLM客户端"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            manager = LLMConfigManager()
            config = manager.get_config()
        
        self.config = config
    
    def generate(self, prompt: str, system_prompt: str = '') -> str:
        """生成文本"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.config.api_key}'
        }
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': self.config.model,
            'messages': messages,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens
        }
        
        try:
            response = requests.post(
                f'{self.config.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']
                
                # 获取content
                content = message.get('content', '') or ''
                
                return content.strip() if content else ''
            else:
                print(f'LLM API错误: {response.status_code} {response.text[:200]}')
                return ''
        except Exception as e:
            print(f'LLM调用异常: {e}')
            return ''
    
    def rewrite_article(self, original: str, comments: list, 
                       max_words: int = 2000, 
                       max_duplicate_ratio: float = 0.5) -> str:
        """改写文章"""
        comments_text = '\n'.join([f'- {c.get("content", "")[:100]}' for c in comments[:10]])
        
        system_prompt = f"""你是一个专业的内容改写助手。请根据以下要求改写文章：

1. 字数限制：不超过{max_words}字
2. 与原文重复率：不超过{int(max_duplicate_ratio * 100)}%
3. 风格：保持客观、专业
4. 结构：完整的文章，包含开头、主体、结尾

重要：直接输出改写后的文章，不要输出任何思考过程、分析步骤或解释说明。只输出最终的文章内容。"""
        
        prompt = f"""请改写以下文章：

【原文】
{original[:2000]}

【网友评论】
{comments_text}

请根据网友评论的观点，改写这篇文章，确保与原文重复率不超过{int(max_duplicate_ratio * 100)}%。"""
        
        return self.generate(prompt, system_prompt)
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        if not self.config.api_key:
            return False
        
        try:
            result = self.generate('测试', '请回复OK')
            return 'OK' in result
        except:
            return False