# -*- coding: utf-8 -*-
"""
搜索客户端 - 使用 Tavily API 进行联网搜索
"""

import requests
from typing import Optional


class SearchClient:
    """Tavily 搜索客户端"""
    
    def __init__(self, api_key: str):
        """
        初始化搜索客户端
        
        Args:
            api_key: Tavily API Key
        """
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
    
    def search(
        self, 
        query: str, 
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = True
    ) -> dict:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            search_depth: 搜索深度 (basic/advanced)
            include_answer: 是否包含 AI 摘要
        
        Returns:
            搜索结果字典
        """
        url = f"{self.base_url}/search"
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": include_answer
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def search_for_context(self, theme: str) -> str:
        """
        根据主题搜索并返回格式化的上下文信息
        
        Args:
            theme: 搜索主题
        
        Returns:
            格式化的搜索结果文本
        """
        try:
            # 构建多个搜索查询，获取更真实具体的数据
            queries = [
                f"{theme} 真实评价 具体地址",
                f"{theme} 推荐 2024 2025",
            ]
            
            all_results = []
            seen_urls = set()
            
            for query in queries:
                try:
                    result = self.search(query, max_results=3, search_depth="advanced")
                    if result.get("results"):
                        for item in result["results"]:
                            url = item.get("url", "")
                            if url not in seen_urls:
                                seen_urls.add(url)
                                all_results.append(item)
                except Exception:
                    continue
            
            if not all_results:
                return ""
            
            # 格式化搜索结果，强调真实来源
            context_parts = [
                "⚠️ 重要：以下是联网搜索到的【真实数据】，请务必基于这些真实信息创作内容：",
                ""
            ]
            
            for i, item in enumerate(all_results[:6], 1):
                title = item.get("title", "")
                content = item.get("content", "")[:300]
                url = item.get("url", "")
                source = url.split("/")[2] if url and "/" in url else "未知来源"
                
                context_parts.append(f"【来源{i}】{source}")
                context_parts.append(f"标题: {title}")
                context_parts.append(f"内容: {content}")
                context_parts.append(f"链接: {url}")
                context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"  ⚠️ 搜索失败: {e}")
            return ""


def create_search_client(api_key: Optional[str]) -> Optional[SearchClient]:
    """
    创建搜索客户端
    
    Args:
        api_key: Tavily API Key
    
    Returns:
        SearchClient 实例，如果 API Key 无效则返回 None
    """
    if not api_key:
        return None
    return SearchClient(api_key)
