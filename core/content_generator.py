# -*- coding: utf-8 -*-
"""
内容生成模块 - 生成小红书贴文内容
"""

import re
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .llm_client import LLMClient
from .search_client import SearchClient

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


@dataclass
class PostContent:
    """贴文内容"""
    title: str
    body: str
    tags: str
    
    def format_tags(self) -> str:
        """格式化标签为小红书格式"""
        # 确保每个标签以 # 开头
        tags = self.tags.replace("，", ",").replace("、", ",")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        formatted = []
        for tag in tag_list:
            if not tag.startswith("#"):
                tag = "#" + tag
            formatted.append(tag)
        return " ".join(formatted)
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "body": self.body,
            "tags": self.tags
        }


# Function Calling 工具定义
TOOLS = {
    "titles": {
        "description": "生成小红书爆款标题",
        "parameters": {
            "type": "object",
            "properties": {
                "标题列表": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "1个吸引人的小红书标题"
                }
            },
            "required": ["标题列表"]
        }
    },
    "xhs_creator": {
        "description": "生成完整的小红书贴文",
        "parameters": {
            "type": "object",
            "properties": {
                "标题": {
                    "type": "string",
                    "description": "贴文标题"
                },
                "正文": {
                    "type": "string", 
                    "description": "贴文正文内容"
                },
                "Tags": {
                    "type": "string",
                    "description": "3个相关话题标签，以逗号分隔，不要超过3个"
                }
            },
            "required": ["标题", "正文", "Tags"]
        }
    },
    "image_prompt": {
        "description": "生成图片描述提示词",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "用于AI生成图片的详细英文描述"
                }
            },
            "required": ["prompt"]
        }
    }
}


class ContentGenerator:
    """内容生成器"""
    
    def __init__(
        self, 
        llm_client: LLMClient, 
        category: str = "Default",
        search_client: Optional[SearchClient] = None
    ):
        self.llm = llm_client
        self.category = category
        self.search_client = search_client
        self.system_prompt = self._load_prompt(category)
    
    def _load_prompt(self, category: str) -> str:
        """加载系统提示词"""
        prompt_path = ROOT_DIR / "data" / "prompt" / "theme" / f"{category}.md"
        
        if not prompt_path.exists():
            prompt_path = ROOT_DIR / "data" / "prompt" / "theme" / "Default.md"
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def generate_title(self, theme: str) -> str:
        """
        根据主题生成标题
        
        Args:
            theme: 贴文主题
        
        Returns:
            生成的标题
        """
        self.llm.clear_history()
        
        # 生成标题时不进行搜索，仅基于主题创作
        user_message = f"主题：{theme}，请生成1个标题"
        
        result = self.llm.chat_with_function(
            user_message=user_message,
            system_prompt=self.system_prompt,
            function_name="titles",
            function_schema=TOOLS["titles"]
        )
        
        titles = result.get("标题列表", [])
        
        # 兼容字符串格式
        if isinstance(titles, str):
            try:
                titles = json.loads(titles)
            except json.JSONDecodeError:
                titles = [t.strip() for t in titles.split("\n") if t.strip()]
        
        return titles[0] if titles else ""
    
    def generate_content(self, title: str) -> PostContent:
        """
        根据标题生成完整贴文内容
        
        确定标题后，使用标题作为关键词进行联网搜索，
        然后基于搜索到的真实数据生成贴文内容。
        
        Args:
            title: 选定的标题
        
        Returns:
            PostContent 实例
        """
        # 使用标题作为关键词进行搜索
        search_context = ""
        if self.search_client:
            print(f"  🔍 正在搜索相关内容: {title}")
            search_context = self.search_client.search_for_context(title)
            if search_context:
                print(f"  ✅ 搜索完成，找到相关数据")
            else:
                print(f"  ⚠️ 未找到相关搜索结果")
        
        # 构建用户消息
        if search_context:
            user_message = f"""请根据这个标题创作完整的小红书贴文：{title}

{search_context}

【创作要求 - 非常重要！】
1. ⚠️ 必须基于上述搜索结果中的【真实数据】创作内容
2. ⚠️ 必须使用搜索结果中出现的真实店铺名称、地址、价格等信息
3. ⚠️ 不要虚构任何店铺、地址、价格或评价
4. ⚠️ 如果搜索结果中有具体的推荐菜品、服务、产品，请直接使用
5. ⚠️ 如果搜索结果信息不足，可以基于已有信息合理扩展，但核心数据必须真实
6. 只生成3个标签，不要超过3个"""
        else:
            user_message = f"请根据这个标题创作完整的小红书贴文：{title}"
        
        result = self.llm.chat_with_function(
            user_message=user_message,
            system_prompt=self.system_prompt,
            function_name="xhs_creator",
            function_schema=TOOLS["xhs_creator"]
        )
        
        return PostContent(
            title=self._clean_text(result.get("标题", title)),
            body=self._clean_text(result.get("正文", "")),
            tags=result.get("Tags", "")
        )
    
    def refine_content(self, suggestion: str) -> PostContent:
        """
        根据建议修改贴文内容
        
        Args:
            suggestion: 修改建议
        
        Returns:
            修改后的 PostContent
        """
        result = self.llm.chat_with_function(
            user_message=f"请根据以下建议修改贴文：{suggestion}",
            system_prompt=self.system_prompt,
            function_name="xhs_creator",
            function_schema=TOOLS["xhs_creator"]
        )
        
        return PostContent(
            title=self._clean_text(result.get("标题", "")),
            body=self._clean_text(result.get("正文", "")),
            tags=result.get("Tags", "")
        )
    
    def generate_image_prompt(self, title: str, body: str) -> str:
        """
        生成图片描述提示词
        
        Args:
            title: 贴文标题
            body: 贴文正文
        
        Returns:
            图片生成提示词（英文）
        """
        system_prompt = """你是一个专业的AI图片生成提示词专家。
根据用户提供的小红书贴文内容，生成一个适合AI图片生成的详细英文描述。

要求：
1. 使用英文描述
2. 描述要具体、生动，包含场景、色彩、风格等细节
3. 适合作为小红书封面图
4. 风格要时尚、吸引人
5. 避免出现文字、人脸等难以生成的元素
6. 描述长度控制在100词以内"""

        result = self.llm.chat_with_function(
            user_message=f"标题：{title}\n\n正文：{body[:500]}",
            system_prompt=system_prompt,
            function_name="image_prompt",
            function_schema=TOOLS["image_prompt"]
        )
        
        return result.get("prompt", f"A beautiful aesthetic image about {title}")
    
    def _clean_text(self, text: str) -> str:
        """清理文本中的特殊字符"""
        # 移除 markdown 格式符号
        text = re.sub(r'#{2,}', '', text)
        text = text.replace("*", "")
        return text.strip()


# 类别映射
CATEGORY_MAP = {
    "美食分享": "Food_Sharing",
    "旅行攻略": "Travel_Guides",
    "时尚穿搭": "Fashion_Outfits",
    "美妆护肤": "Beauty_&_Skincare",
    "健康生活": "Healthy_Living",
    "学习提升": "Learning_&_Growth",
    "家居生活": "Home_Life",
    "心情日记": "Mood_Diary",
    "宠物天地": "Pet_World",
    "二手交易": "Second-hand_Trade",
    "产品推荐": "Product_Recommendations"
}

CATEGORY_INFOS = [
    {"name": "美食分享", "description": "美食体验、餐厅推荐、美食制作教程"},
    {"name": "旅行攻略", "description": "旅行日记、目的地推荐、行程规划"},
    {"name": "时尚穿搭", "description": "日常穿搭、服饰搭配、时尚趋势"},
    {"name": "美妆护肤", "description": "化妆技巧、护肤品评测、美妆心得"},
    {"name": "健康生活", "description": "健康饮食、运动健身、生活习惯"},
    {"name": "学习提升", "description": "语言学习、职场技能、个人成长"},
    {"name": "家居生活", "description": "家居装饰、生活技巧、家电推荐"},
    {"name": "心情日记", "description": "情感体验、生活随笔、个人感悟"},
    {"name": "宠物天地", "description": "宠物护理、宠物趣事分享"},
    {"name": "二手交易", "description": "二手物品买卖交流"},
    {"name": "产品推荐", "description": "产品评测、优惠信息、购买建议"}
]


def auto_categorize(llm_client: LLMClient, theme: str) -> str:
    """
    自动识别主题类别
    
    Args:
        llm_client: LLM 客户端
        theme: 主题内容
    
    Returns:
        类别名称（英文）
    """
    categories = "\n".join([f"- {c['name']}: {c['description']}" for c in CATEGORY_INFOS])
    
    system_prompt = f"""你是一个分类专家。根据用户输入的主题，选择最匹配的类别。

可选类别：
{categories}

只返回类别名称（中文），不要其他内容。如果都不匹配，返回"默认"。"""
    
    response = llm_client.simple_chat(f"主题：{theme}", system_prompt)
    category_cn = response.strip().replace('"', '').replace("'", "")
    
    # 转换为英文类别名
    return CATEGORY_MAP.get(category_cn, "Default")
