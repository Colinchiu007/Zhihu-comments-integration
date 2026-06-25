"""LLM模型预设配置"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ModelPreset:
    """模型预设"""
    name: str
    base_url: str
    model: str
    description: str


# 预设模型列表
MODEL_PRESETS: Dict[str, ModelPreset] = {
    'sensenova': ModelPreset(
        name='SenseNova',
        base_url='https://token.sensenova.cn/v1',
        model='sensenova-6.7-flash-lite',
        description='商汤日日新大模型'
    ),
    'agnes': ModelPreset(
        name='Agnes AI',
        base_url='https://api.agnes-ai.com/v1',
        model='agnes-20-flash',
        description='Agnes AI 免费全能模型'
    ),
    'openai': ModelPreset(
        name='OpenAI',
        base_url='https://api.openai.com/v1',
        model='gpt-3.5-turbo',
        description='OpenAI GPT模型'
    ),
    'deepseek': ModelPreset(
        name='DeepSeek',
        base_url='https://api.deepseek.com/v1',
        model='deepseek-chat',
        description='DeepSeek大模型'
    ),
    'zhipu': ModelPreset(
        name='智谱AI',
        base_url='https://open.bigmodel.cn/api/paas/v4',
        model='glm-4-flash',
        description='智谱GLM模型'
    ),
    'moonshot': ModelPreset(
        name='月之暗面',
        base_url='https://api.moonshot.cn/v1',
        model='moonshot-v1-8k',
        description='Kimi大模型'
    )
}


def get_preset(name: str) -> ModelPreset:
    """获取模型预设"""
    if name not in MODEL_PRESETS:
        raise ValueError(f"未知模型: {name}，可用模型: {list(MODEL_PRESETS.keys())}")
    return MODEL_PRESETS[name]


def list_presets() -> Dict[str, str]:
    """列出所有预设模型"""
    return {name: preset.description for name, preset in MODEL_PRESETS.items()}


def create_config_from_preset(preset_name: str, api_key: str, 
                             model: str = None) -> Dict[str, Any]:
    """从预设创建配置"""
    preset = get_preset(preset_name)
    
    return {
        'provider': preset.name,
        'base_url': preset.base_url,
        'api_key': api_key,
        'model': model or preset.model
    }