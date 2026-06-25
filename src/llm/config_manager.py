"""LLM配置管理器 - 加密存储API Key"""
import json
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = 'sensenova'
    base_url: str = 'https://token.sensenova.cn/v1'
    api_key: str = ''
    model: str = 'sensenova-6.7-flash-lite'
    temperature: float = 0.7
    max_tokens: int = 2000


class LLMConfigManager:
    """LLM配置管理器"""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'llm_config.json'
        self._encryption_key = self._get_or_create_encryption_key()
    
    def _get_or_create_encryption_key(self) -> str:
        """获取或创建加密密钥"""
        key_file = self.config_dir / '.key'
        
        if key_file.exists():
            return key_file.read_text(encoding='utf-8').strip()
        
        import secrets
        key = secrets.token_hex(16)
        key_file.write_text(key, encoding='utf-8')
        
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(key_file), 2)
        except:
            pass
        
        return key
    
    def _encrypt(self, text: str) -> str:
        """加密文本"""
        if not self._encryption_key:
            return text
        
        key_bytes = self._encryption_key.encode('utf-8')
        text_bytes = text.encode('utf-8')
        
        encrypted = bytes(a ^ b for a, b in zip(text_bytes, key_bytes * (len(text_bytes) // len(key_bytes) + 1)))
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _decrypt(self, encrypted_text: str) -> str:
        """解密文本"""
        if not self._encryption_key:
            return encrypted_text
        
        try:
            key_bytes = self._encryption_key.encode('utf-8')
            encrypted_bytes = base64.b64decode(encrypted_text)
            
            decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_bytes * (len(encrypted_bytes) // len(key_bytes) + 1)))
            return decrypted.decode('utf-8')
        except:
            return encrypted_text
    
    def save_config(self, config: LLMConfig) -> None:
        """保存配置"""
        data = {
            'provider': config.provider,
            'base_url': config.base_url,
            'api_key': self._encrypt(config.api_key) if config.api_key else '',
            'model': config.model,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_config(self) -> LLMConfig:
        """加载配置"""
        if not self.config_file.exists():
            return LLMConfig()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return LLMConfig(
                provider=data.get('provider', 'sensenova'),
                base_url=data.get('base_url', 'https://token.sensenova.cn/v1'),
                api_key=self._decrypt(data.get('api_key', '')),
                model=data.get('model', 'sensenova-6.7-flash-lite'),
                temperature=data.get('temperature', 0.7),
                max_tokens=data.get('max_tokens', 2000)
            )
        except:
            return LLMConfig()
    
    def get_config(self) -> LLMConfig:
        return self.load_config()
    
    def update_config(self, **kwargs) -> LLMConfig:
        config = self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.save_config(config)
        return config
    
    def setup_from_preset(self, preset_name: str, api_key: str, 
                         model: str = None) -> LLMConfig:
        """从预设模型设置配置"""
        from .presets import get_preset
        
        preset = get_preset(preset_name)
        
        config = LLMConfig(
            provider=preset.name,
            base_url=preset.base_url,
            api_key=api_key,
            model=model or preset.model
        )
        
        self.save_config(config)
        return config