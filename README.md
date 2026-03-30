# aishu-agent（命令行交互式 Agent）

运行后可持续输入问题，Agent 会持续回答（支持上下文对话）。

## 安装

建议使用当前目录里的虚拟环境（你已有 `.venv`），在项目根目录执行：

```bash
python -m pip install -U pip
python -m pip install -e .
```

## 配置（必选其一）

本项目默认使用 OpenAI SDK（也支持 OpenAI 兼容 API）。

- **OpenAI 官方**
  - `OPENAI_API_KEY`: 你的 API Key
  - `OPENAI_MODEL`: 可选，默认 `gpt-4o-mini`

- **OpenAI 兼容网关/自建**
  - `OPENAI_API_KEY`: 你的 API Key
  - `OPENAI_BASE_URL`: 例如 `https://xxx/v1`
  - `OPENAI_MODEL`: 对应模型名

你也可以在根目录创建 `.env`（参考 `.env.example`）。

## 运行

### 方式 1：安装后直接运行

```bash
aishu
```

### 方式 2：不安装，直接模块运行

```bash
python -m aishu_agent
```

## 交互指令

- `/help`：查看帮助
- `/exit` 或 `/quit`：退出
- `/reset`：清空对话上下文
- `/clear`：清屏

## 常见问题

- **提示未配置 `OPENAI_API_KEY`**
  - 设置环境变量或创建 `.env` 文件，然后重试。
