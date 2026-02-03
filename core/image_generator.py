# -*- coding: utf-8 -*-
"""
图片生成模块 - 统一使用 OpenAI 兼容的图片生成 API
"""

import requests
import time
import base64
from pathlib import Path
from openai import OpenAI


class ImageGenerator:
    """统一的图片生成器，使用 OpenAI 兼容接口"""
    
    def __init__(self, model: str, base_url: str, api_key: str):
        """
        初始化图片生成器
        
        Args:
            model: 模型名称
            base_url: API 地址
            api_key: API Key
        """
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def generate(self, prompt: str, save_path: str, size: str = "1024x1024") -> str:
        """
        生成图片
        
        Args:
            prompt: 图片描述
            save_path: 保存路径
            size: 图片尺寸
        
        Returns:
            图片文件路径
        """
        # 检测是否为通义万相（需要异步处理）
        if "dashscope" in self.base_url and "wanx" in self.model:
            return self._generate_qwen(prompt, save_path, size)
        
        # 标准 OpenAI 兼容接口
        return self._generate_standard(prompt, save_path, size)
    
    def _generate_standard(self, prompt: str, save_path: str, size: str) -> str:
        """标准 OpenAI 兼容接口生成"""
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
            n=1
        )
        
        image_url = response.data[0].url
        
        # 如果返回的是 base64
        if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
            return self._save_base64(response.data[0].b64_json, save_path)
        
        return self._download_image(image_url, save_path)
    
    def _generate_qwen(self, prompt: str, save_path: str, size: str) -> str:
        """通义万相异步生成"""
        submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        result_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        data = {
            "model": self.model,
            "input": {"prompt": prompt},
            "parameters": {"size": size.replace("x", "*"), "n": 1}
        }
        
        # 提交任务
        response = requests.post(submit_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        task_id = response.json()["output"]["task_id"]
        
        # 轮询获取结果
        for _ in range(60):
            time.sleep(2)
            resp = requests.get(result_url.format(task_id=task_id), headers=headers, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            status = result["output"]["task_status"]
            
            if status == "SUCCEEDED":
                image_url = result["output"]["results"][0]["url"]
                return self._download_image(image_url, save_path)
            elif status == "FAILED":
                raise Exception(f"图片生成失败: {result.get('message', '未知错误')}")
        
        raise TimeoutError("图片生成超时")
    
    def _download_image(self, url: str, save_path: str) -> str:
        """下载图片"""
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(response.content)
        
        return save_path
    
    def _save_base64(self, b64_data: str, save_path: str) -> str:
        """保存 base64 图片"""
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(b64_data))
        
        return save_path
