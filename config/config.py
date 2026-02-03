# -*- coding: utf-8 -*-
"""
配置管理 - 支持环境变量和配置文件
"""

import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent / "data"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    """应用配置"""
    # LLM 配置
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: Optional[str] = None
    
    # 图片生成配置
    image_model: str = "cogview-3-plus"
    image_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    image_api_key: Optional[str] = None
    
    # 搜索配置
    search_api_key: Optional[str] = None
    search_enabled: bool = True
    
    # 小红书配置
    xhs_cookie: Optional[str] = None
    
    # 内容配置
    category: str = "auto"  # auto 表示自动选择


def load_config() -> AppConfig:
    """加载配置"""
    config = AppConfig()
    
    # 从环境变量加载 LLM 配置
    config.llm_model = os.getenv("LLM_MODEL", config.llm_model)
    config.llm_base_url = os.getenv("LLM_BASE_URL", config.llm_base_url)
    config.llm_api_key = os.getenv("LLM_API_KEY", config.llm_api_key)
    
    # 从环境变量加载图片生成配置
    config.image_model = os.getenv("IMAGE_MODEL", config.image_model)
    config.image_base_url = os.getenv("IMAGE_BASE_URL", config.image_base_url)
    config.image_api_key = os.getenv("IMAGE_API_KEY", config.image_api_key)
    
    # 搜索配置
    config.search_api_key = os.getenv("SEARCH_API_KEY", config.search_api_key)
    config.search_enabled = os.getenv("SEARCH_ENABLED", "true").lower() == "true"
    
    # 其他配置
    config.xhs_cookie = os.getenv("XHS_COOKIE", config.xhs_cookie)
    config.category = os.getenv("CATEGORY", config.category)
    
    # 从配置文件加载（覆盖环境变量）
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            file_config = json.load(f)
            for key, value in file_config.items():
                if hasattr(config, key) and value is not None:
                    setattr(config, key, value)
    
    return config


def save_config(config: AppConfig):
    """保存配置到文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 不保存敏感信息到文件
    config_dict = asdict(config)
    sensitive_keys = ["llm_api_key", "image_api_key", "search_api_key", "xhs_cookie"]
    for key in sensitive_keys:
        config_dict.pop(key, None)
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)


def print_config_help():
    """打印配置帮助信息"""
    print("\n" + "=" * 60)
    print("📋 AutoXHS 配置说明")
    print("=" * 60)
    
    print("\n🔧 环境变量配置（在 .env 文件中设置）：")
    print("-" * 40)
    print("  LLM 配置:")
    print("    LLM_MODEL     - 模型名称")
    print("    LLM_BASE_URL  - API 地址")
    print("    LLM_API_KEY   - API Key")
    print()
    print("  图片生成配置:")
    print("    IMAGE_MODEL    - 模型名称")
    print("    IMAGE_BASE_URL - API 地址")
    print("    IMAGE_API_KEY  - API Key")
    print()
    print("  联网搜索配置:")
    print("    SEARCH_API_KEY  - Tavily API Key（可选，用于联网搜索）")
    print("    SEARCH_ENABLED  - 是否启用搜索（默认 true）")
    print()
    print("  其他配置:")
    print("    XHS_COOKIE    - 小红书 Cookie（可选，跳过登录）")
    print("    CATEGORY      - 内容类别（默认 auto）")
    
    print("\n🤖 常用 LLM 配置示例：")
    print("-" * 40)
    print("  DeepSeek:    MODEL=deepseek-chat      BASE_URL=https://api.deepseek.com")
    print("  OpenAI:      MODEL=gpt-4o             BASE_URL=https://api.openai.com/v1")
    print("  智谱:        MODEL=glm-4-plus         BASE_URL=https://open.bigmodel.cn/api/paas/v4")
    print("  通义千问:    MODEL=qwen-max           BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1")
    print("  Moonshot:    MODEL=moonshot-v1-8k     BASE_URL=https://api.moonshot.cn/v1")
    print("  百川:        MODEL=Baichuan4          BASE_URL=https://api.baichuan-ai.com/v1")
    print("  豆包:        MODEL=doubao-pro-32k     BASE_URL=https://ark.cn-beijing.volces.com/api/v3")
    
    print("\n🖼️ 常用图片生成配置示例：")
    print("-" * 40)
    print("  智谱 CogView:  MODEL=cogview-3-plus   BASE_URL=https://open.bigmodel.cn/api/paas/v4")
    print("  通义万相:      MODEL=wanx-v1          BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1")
    print("  硅基流动:      MODEL=FLUX.1-schnell   BASE_URL=https://api.siliconflow.cn/v1")
    
    print("\n" + "=" * 60)
