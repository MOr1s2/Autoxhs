# -*- coding: utf-8 -*-
"""
小红书客户端 - 处理登录和发布
"""

import json
import platform
import asyncio
from time import sleep
from typing import Optional, Tuple
from pathlib import Path

from xhs import XhsClient, DataFetchError

# Cookie 持久化文件路径
COOKIE_FILE = Path(__file__).parent.parent / "data" / ".xhs_cookie.json"


def _get_sign_function():
    """根据系统获取签名函数"""
    
    if platform.system().lower() == 'windows':
        from playwright.async_api import async_playwright
        
        async def _async_sign(uri, data=None, a1="", web_session=""):
            for _ in range(10):
                try:
                    async with async_playwright() as playwright:
                        stealth_js_path = Path(__file__).parent.parent / "stealth.min.js"
                        browser = await playwright.chromium.launch(headless=True)
                        browser_context = await browser.new_context()
                        await browser_context.add_init_script(path=str(stealth_js_path))
                        context_page = await browser_context.new_page()
                        await context_page.goto("https://www.xiaohongshu.com")
                        await browser_context.add_cookies([
                            {'name': 'a1', 'value': a1, 'domain': ".xiaohongshu.com", 'path': "/"}
                        ])
                        await context_page.reload()
                        sleep(2)
                        encrypt_params = await context_page.evaluate(
                            "([url, data]) => window._webmsxyw(url, data)", [uri, data]
                        )
                        await browser.close()
                        return {"x-s": encrypt_params["X-s"], "x-t": str(encrypt_params["X-t"])}
                except Exception as e:
                    print(f"签名失败，重试中... {e}")
            raise Exception("签名失败，请检查网络连接")
        
        def sign_wrapper(uri, data=None, a1="", web_session=""):
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_async_sign(uri, data, a1, web_session))
        
        return sign_wrapper
    
    else:
        from playwright.sync_api import sync_playwright
        
        def sign(uri, data=None, a1="", web_session=""):
            for _ in range(10):
                try:
                    with sync_playwright() as playwright:
                        stealth_js_path = Path(__file__).parent.parent / "stealth.min.js"
                        browser = playwright.chromium.launch(headless=True)
                        browser_context = browser.new_context()
                        browser_context.add_init_script(path=str(stealth_js_path))
                        context_page = browser_context.new_page()
                        context_page.goto("https://www.xiaohongshu.com")
                        browser_context.add_cookies([
                            {'name': 'a1', 'value': a1, 'domain': ".xiaohongshu.com", 'path': "/"}
                        ])
                        context_page.reload()
                        sleep(1)
                        encrypt_params = context_page.evaluate(
                            "([url, data]) => window._webmsxyw(url, data)", [uri, data]
                        )
                        browser.close()
                        return {"x-s": encrypt_params["X-s"], "x-t": str(encrypt_params["X-t"])}
                except Exception as e:
                    print(f"签名失败，重试中... {e}")
            raise Exception("签名失败，请检查网络连接")
        
        return sign


def _load_saved_cookie() -> Optional[str]:
    """从本地文件加载保存的 Cookie"""
    try:
        if COOKIE_FILE.exists():
            with open(COOKIE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("cookie")
    except Exception:
        pass
    return None


def _save_cookie(cookie: str):
    """保存 Cookie 到本地文件"""
    try:
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump({"cookie": cookie}, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  保存 Cookie 失败: {e}")


def _clear_saved_cookie():
    """清除保存的 Cookie"""
    try:
        if COOKIE_FILE.exists():
            COOKIE_FILE.unlink()
    except Exception:
        pass


class XHSClient:
    """小红书客户端封装"""
    
    def __init__(self, cookie: Optional[str] = None):
        self.sign_func = _get_sign_function()
        
        # Cookie 优先级: 参数传入 > 本地保存 > 无
        if not cookie:
            cookie = _load_saved_cookie()
            if cookie:
                print("  ✅ 已加载本地保存的登录信息")
        
        self.client = XhsClient(cookie=cookie, sign=self.sign_func) if cookie else XhsClient(sign=self.sign_func)
        self.logged_in = bool(cookie)
        self._cookie = cookie
    
    def login_by_phone(self, phone: str) -> bool:
        """
        手机号登录
        
        Args:
            phone: 手机号码
        
        Returns:
            是否登录成功
        """
        try:
            # 发送验证码
            self.client.send_code(phone)
            print(f"✅ 验证码已发送到 {phone}")
            
            # 获取验证码
            code = input("请输入验证码: ").strip()
            
            # 验证并登录
            check_res = self.client.check_code(phone, code)
            token = check_res["mobile_token"]
            login_res = self.client.login_code(phone, token)
            
            # 登录成功后保存 Cookie
            self._save_login_cookie()
            
            self.logged_in = True
            print("✅ 登录成功！")
            return True
            
        except DataFetchError as e:
            print(f"❌ 登录失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def _save_login_cookie(self):
        """登录成功后保存 Cookie"""
        try:
            # 从 client 获取 cookie
            cookie = self.client.cookie
            if cookie:
                _save_cookie(cookie)
                print("💾 登录信息已保存，下次可自动登录")
        except Exception as e:
            print(f"⚠️  保存登录信息失败: {e}")
    
    def logout(self):
        """退出登录并清除保存的 Cookie"""
        _clear_saved_cookie()
        self.logged_in = False
        self._cookie = None
        print("✅ 已退出登录")
    
    def verify_login(self) -> bool:
        """
        验证当前登录状态是否有效
        
        Returns:
            是否有效
        """
        if not self.logged_in:
            return False
        
        try:
            # 尝试获取用户信息来验证登录状态
            # 静默验证，不打印响应
            import logging
            logger = logging.getLogger("xhs")
            original_level = logger.level
            logger.setLevel(logging.WARNING)
            
            try:
                self.client.get_self_info()
                return True
            finally:
                logger.setLevel(original_level)
                
        except Exception:
            # 登录失效，清除保存的 Cookie
            print("⚠️  登录已过期")
            _clear_saved_cookie()
            self.logged_in = False
            return False
    
    def get_suggest_topics(self, keyword: str) -> list[dict]:
        """
        获取话题建议
        
        Args:
            keyword: 关键词
        
        Returns:
            话题列表
        """
        try:
            return self.client.get_suggest_topic(keyword)
        except Exception:
            return []
    
    def format_topics(self, tags: str, max_topics: int = 3) -> Tuple[list[dict], str]:
        """
        格式化标签为小红书话题
        
        Args:
            tags: 标签字符串
            max_topics: 最多查询的话题数量（减少 API 请求，默认 3 个）
        
        Returns:
            (话题列表, 话题后缀字符串)
        """
        import random
        
        topics = []
        tag_list = tags.replace("#", "").replace("，", ",").replace("、", ",").split(",")
        tag_list = [t.strip() for t in tag_list if t.strip()]
        
        # 只取前 max_topics 个标签查询话题，减少 API 请求
        tags_to_query = tag_list[:max_topics]
        
        for i, tag in enumerate(tags_to_query):
            # 请求间隔 1-2 秒，模拟正常用户行为
            if i > 0:
                sleep(random.uniform(1.0, 2.0))
            
            try:
                suggest_list = self.get_suggest_topics(tag)
                if suggest_list:
                    topic = suggest_list[0]
                    topics.append({
                        "id": topic["id"],
                        "name": topic["name"],
                        "type": "topic",
                        "link": topic.get("link", "")
                    })
            except Exception:
                # 单个话题查询失败不影响整体
                continue
        
        # 生成话题后缀
        suffix_parts = [f"#{t['name']}[话题]#" for t in topics]
        suffix = "\n" + " ".join(suffix_parts) if suffix_parts else ""
        
        return topics, suffix
    
    def publish_note(
        self,
        title: str,
        content: str,
        image_paths: list[str],
        tags: str = "",
        is_private: bool = True
    ) -> dict:
        """
        发布图文笔记
        
        Args:
            title: 标题
            content: 正文内容
            image_paths: 图片路径列表
            tags: 标签
            is_private: 是否私密发布
        
        Returns:
            发布结果
        """
        import datetime
        import random
        
        if not self.logged_in:
            raise RuntimeError("请先登录小红书")
        
        # 处理话题（内部已有请求间隔）
        print("  🏷️  匹配话题中...")
        topics, topics_suffix = self.format_topics(tags)
        if topics:
            print(f"  ✅ 已匹配 {len(topics)} 个话题")
        
        full_content = content + topics_suffix
        
        # 发布前等待，模拟用户编辑行为
        sleep(random.uniform(2.0, 3.0))
        
        # 发布笔记
        result = self.client.create_image_note(
            title=title,
            desc=full_content,
            files=image_paths,
            topics=topics,
            is_private=is_private,
            post_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return result


def install_playwright():
    """安装 playwright 浏览器"""
    import subprocess
    import sys
    
    try:
        if platform.system().lower() == 'windows':
            from playwright.async_api import async_playwright
            async def test():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    await browser.close()
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(test())
        else:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
    except Exception:
        print("📦 正在安装 Playwright 浏览器...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright 安装完成")
