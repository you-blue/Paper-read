# PDF 论文摘要工具

一个桌面 GUI 工具，用于读取学术 PDF 论文，使用大语言模型生成摘要，并将摘要导出为 Markdown 文件（支持 Obsidian 知识库）。

## 功能特点

- **多模型支持** — 支持 Anthropic Claude、OpenAI GPT、DeepSeek、通义千问、Ollama（本地）以及自定义 OpenAI 兼容接口
- **PDF 智能处理** — 自动检测页面类型（文本页 vs 数学/图表页），混合渲染确保准确提取
- **Obsidian 集成** — 可配置知识库路径、YAML 前置元数据、文件名模板
- **可定制输出** — 支持语言选择、标签分类、子目录管理
- **图形界面** — 基于 customtkinter 构建，支持明暗主题切换

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动程序
python main.py
```

## 配置说明

复制配置文件模板并填入你的设置：

```bash
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入 API key 和偏好设置
```

支持的 LLM 提供商：`anthropic`、`openai`、`deepseek`、`qwen`、`ollama`、`custom`。

在图形界面的「设置」面板中也可以直接修改所有配置项。

## 项目结构

```
├── main.py                          # 程序入口
├── config.example.yaml              # 配置文件模板
├── src/
│   ├── config/settings.py           # 配置管理
│   ├── gui/
│   │   ├── app.py                   # 主窗口
│   │   ├── widgets/
│   │   │   ├── config_panel.py      # 设置面板
│   │   │   ├── pdf_selector.py      # PDF 文件选择
│   │   │   └── progress_panel.py    # 进度显示
│   ├── llm/                         # LLM 提供商
│   │   ├── base.py                  # 抽象基类
│   │   ├── anthropic_provider.py    # Claude
│   │   ├── openai_provider.py       # OpenAI 兼容接口
│   │   └── ollama_provider.py       # 本地 Ollama
│   ├── output/markdown.py           # Markdown 输出
│   ├── pdf/                         # PDF 处理
│   │   ├── detector.py              # 页面类型检测
│   │   ├── extractor.py             # 文本提取
│   │   └── renderer.py              # 页面渲染
│   └── pipeline.py                  # 工作流编排
└── utils/
    ├── helpers.py                   # 工具函数
    ├── i18n.py                      # 国际化
    └── prompts.py                   # 提示词模板
```

## 环境要求

- Python 3.10+
- Poppler（PDF 渲染用）— Windows 下可通过 `winget install oschwartz10612.Poppler` 安装

## 安全说明

`config.yaml` 文件包含 API key 等敏感信息，已被加入 `.gitignore`，不会被提交到版本控制。请使用 `config.example.yaml` 作为配置模板。
