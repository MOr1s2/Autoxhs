# -*- coding: utf-8 -*-
"""
统一的 LLM 客户端 - 支持任何兼容 OpenAI API 格式的服务
"""

import json
from typing import Optional
from openai import OpenAI


class LLMClient:
    """统一的 LLM 客户端，使用 OpenAI 兼容接口"""
    
    def __init__(self, model: str, base_url: str, api_key: str):
        """
        初始化 LLM 客户端
        
        Args:
            model: 模型名称
            base_url: API 地址
            api_key: API Key
        """
        self.model = model
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.conversation_history = []
    
    def chat(
        self, 
        user_message: str, 
        system_prompt: Optional[str] = None,
        tools: Optional[list] = None,
        tool_choice: Optional[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> dict:
        """
        发送聊天请求
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            tools: 工具定义（Function Calling）
            tool_choice: 工具选择
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            响应字典
        """
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        messages.extend(self.conversation_history)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 构建请求参数
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 添加工具调用
        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        
        # 发送请求
        response = self.client.chat.completions.create(**kwargs)
        
        # 解析响应
        choice = response.choices[0]
        result = {
            "content": choice.message.content,
            "tool_calls": None,
            "finish_reason": choice.finish_reason
        }
        
        # 处理工具调用
        if choice.message.tool_calls:
            result["tool_calls"] = []
            for tool_call in choice.message.tool_calls:
                result["tool_calls"].append({
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
        
        # 保存到历史
        self.conversation_history.append({"role": "user", "content": user_message})
        if result["content"]:
            self.conversation_history.append({"role": "assistant", "content": result["content"]})
        elif result["tool_calls"]:
            # 工具调用时保存函数调用信息
            self.conversation_history.append({
                "role": "assistant", 
                "content": json.dumps(result["tool_calls"][0]["arguments"], ensure_ascii=False)
            })
        
        return result
    
    def chat_with_function(
        self,
        user_message: str,
        system_prompt: str,
        function_name: str,
        function_schema: dict
    ) -> dict:
        """
        使用 Function Calling 进行结构化输出
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            function_name: 函数名称
            function_schema: 函数 schema
        
        Returns:
            函数参数字典
        """
        tools = [{
            "type": "function",
            "function": {
                "name": function_name,
                **function_schema
            }
        }]
        
        tool_choice = {
            "type": "function",
            "function": {"name": function_name}
        }
        
        response = self.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            tools=tools,
            tool_choice=tool_choice
        )
        
        if response["tool_calls"]:
            return response["tool_calls"][0]["arguments"]
        
        # 如果没有工具调用，尝试从内容中解析 JSON
        if response["content"]:
            try:
                return json.loads(response["content"])
            except json.JSONDecodeError:
                pass
        
        raise ValueError("未能获取结构化输出")
    
    def clear_history(self, keep_last: int = 0):
        """清除对话历史"""
        if keep_last > 0:
            self.conversation_history = self.conversation_history[-keep_last * 2:]
        else:
            self.conversation_history = []
    
    def simple_chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """简单聊天，只返回文本内容"""
        response = self.chat(user_message, system_prompt)
        return response["content"] or ""
