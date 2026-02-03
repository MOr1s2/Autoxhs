# AutoXHS

> **AutoXHS** 是一款开源的小红书自动化内容创作与发布工具。支持任何兼容 OpenAI API 格式的 LLM 服务，通过终端一键执行完成登录、内容生成、图片生成和发布全流程。

## ✨ 特性

- 🤖 **多模型支持** - 支持任何兼容 OpenAI API 的服务（OpenAI、DeepSeek、智谱、通义千问、Moonshot、百川、豆包等）
- 🎨 **AI 图片生成** - 支持智谱 CogView、通义万相、硅基流动 FLUX 等图片生成服务
- 📝 **智能内容创作** - 基于 LangGPT 方法论的结构化 Prompt，自动生成爆款标题和贴文
- 🚀 **一键发布** - 终端交互式操作，支持手机号验证码登录
- 📁 **本地保存** - 自动保存生成的内容和图片

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/Gikiman/Autoxhs.git
cd Autoxhs

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

复制环境变量示例文件并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件（三个字段即可配置任意模型）：

```bash
# LLM 配置
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_api_key_here

# 图片生成配置
IMAGE_MODEL=cogview-3-plus
IMAGE_BASE_URL=https://open.bigmodel.cn/api/paas/v4
IMAGE_API_KEY=your_image_api_key_here
```

### 3. 运行

```bash
# 交互式运行
python main.py

# 直接指定主题
python main.py --theme "今日美食分享"

# 查看帮助
python main.py --help
```

## 📖 使用说明

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--theme, -t` | 贴文主题 | `--theme "探店分享"` |
| `--llm-model` | LLM 模型名称 | `--llm-model gpt-4o` |
| `--llm-base-url` | LLM API 地址 | `--llm-base-url https://api.openai.com/v1` |
| `--llm-api-key` | LLM API Key | `--llm-api-key sk-xxx` |
| `--image-model` | 图片生成模型 | `--image-model cogview-3-plus` |
| `--image-base-url` | 图片生成 API 地址 | `--image-base-url https://...` |
| `--image-api-key` | 图片生成 API Key | `--image-api-key xxx` |
| `--category, -c` | 内容类别 | `--category 美食分享` |
| `--config` | 显示配置帮助 | `--config` |

### 常用模型配置

| 服务商 | MODEL | BASE_URL |
|--------|-------|----------|
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com` |
| OpenAI | `gpt-4o` | `https://api.openai.com/v1` |
| 智谱 AI | `glm-4-plus` | `https://open.bigmodel.cn/api/paas/v4` |
| 通义千问 | `qwen-max` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Moonshot | `moonshot-v1-8k` | `https://api.moonshot.cn/v1` |
| 百川 | `Baichuan4` | `https://api.baichuan-ai.com/v1` |
| 豆包 | `doubao-pro-32k` | `https://ark.cn-beijing.volces.com/api/v3` |

### 图片生成配置

| 服务商 | MODEL | BASE_URL |
|--------|-------|----------|
| 智谱 CogView | `cogview-3-plus` | `https://open.bigmodel.cn/api/paas/v4` |
| 通义万相 | `wanx-v1` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 硅基流动 | `FLUX.1-schnell` | `https://api.siliconflow.cn/v1` |

### 内容类别

- `auto` - 自动识别（默认）
- 美食分享、旅行攻略、时尚穿搭、美妆护肤
- 健康生活、学习提升、家居生活、心情日记
- 宠物天地、二手交易、产品推荐

## 📁 项目结构

```
Autoxhs/
├── main.py              # 主程序入口
├── config/
│   └── config.py        # 应用配置
├── core/                # 核心模块
│   ├── llm_client.py    # LLM 客户端
│   ├── content_generator.py  # 内容生成
│   ├── image_generator.py    # 图片生成
│   └── xhs_client.py    # 小红书客户端
├── data/
│   ├── prompt/          # Prompt 模板
│   └── posts/           # 生成的贴文
├── .env.example         # 环境变量示例
└── requirements.txt     # 依赖列表
```

## 🔧 配置详解

### 环境变量

```bash
# LLM 配置（必填）
LLM_MODEL=deepseek-chat           # 模型名称
LLM_BASE_URL=https://api.deepseek.com  # API 地址
LLM_API_KEY=your_key              # API Key

# 图片生成配置（必填）
IMAGE_MODEL=cogview-3-plus        # 模型名称
IMAGE_BASE_URL=https://open.bigmodel.cn/api/paas/v4  # API 地址
IMAGE_API_KEY=your_key            # API Key

# 小红书配置（可选）
XHS_COOKIE=your_cookie            # Cookie（跳过登录）

# 内容配置（可选）
CATEGORY=auto                     # 内容类别
```

### Prompt 自定义

Prompt 模板位于 `data/prompt/theme/` 目录，采用 LangGPT 结构化方法论：

```markdown
# Role: 小红书爆款大师

## Profile
- Description: 描述角色定位

### 写作技巧
- 技巧列表...

## Rules
- 规则列表...

## Workflow
- 工作流程...
```

## 📝 运行示例

```
╔═══════════════════════════════════════════════════════════════╗
║     █████╗ ██╗   ██╗████████╗ ██████╗ ██╗  ██╗██╗  ██╗███████╗║
║    ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗╚██╗██╔╝██║  ██║██╔════╝║
║    ███████║██║   ██║   ██║   ██║   ██║ ╚███╔╝ ███████║███████╗║
║          🌸 小红书自动化内容创作与发布工具 🌸                 ║
╚═══════════════════════════════════════════════════════════════╝

🔧 正在初始化...
  ✅ LLM: deepseek-chat @ https://api.deepseek.com
  ✅ 图片生成: cogview-3-plus @ https://open.bigmodel.cn/api/paas/v4
  ✅ 小红书客户端就绪

📱 小红书登录
----------------------------------------
请输入手机号码: 138xxxxxxxx
✅ 验证码已发送到 138xxxxxxxx
请输入验证码: 123456
✅ 登录成功！

🎯 请输入贴文主题: 周末探店美食分享

📝 开始创作：周末探店美食分享
----------------------------------------
🔍 正在识别主题类别...
  ✅ 类别: Food_Sharing

🏷️  正在生成标题...

📋 请选择一个标题：
  [1] 🍜 周末探店｜这家隐藏小店让我惊艳了！
  [2] 😋 美食地图更新！本地人私藏的宝藏餐厅
  ...

请选择 (1-10): 1

✍️  正在生成贴文内容...

==================================================
📄 贴文预览
==================================================

【标题】🍜 周末探店｜这家隐藏小店让我惊艳了！

【正文】
周末和闺蜜约了探店...
...

【标签】#美食探店 #周末好去处 #本地美食
==================================================

对内容满意吗？ [Y/n]: y

🎨 正在生成封面图...
  ✅ 图片已保存: data/posts/2026-02-03_12-00-00/cover.png

🚀 准备发布
----------------------------------------
是否设为私密（仅自己可见）？ [Y/n]: y
确认发布？ [Y/n]: y
📤 正在发布...
✅ 发布成功！
📁 记录已保存: data/posts/2026-02-03_12-00-00/record.json

🎉 完成！
```

## ⚠️ 注意事项

1. 需要稳定的网络连接
2. 小红书登录需要手机验证码
3. 首次运行会自动安装 Playwright 浏览器
4. 发布内容默认为私密，可在发布时选择公开

## 📄 License

MIT License

## 👏 致谢

- [xhs](https://github.com/ReaJason/xhs) - 小红书 API
- [LangGPT](https://github.com/yzfly/LangGPT) - 结构化 Prompt 方法论
