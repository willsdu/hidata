from __future__ import annotations

import os
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

from .llm import chat_once, load_llm_config, make_client
from .session import ChatSession


app = typer.Typer(add_completion=False, no_args_is_help=False)
console = Console()


HELP_TEXT = """可用指令：
- /help：显示帮助
- /exit 或 /quit：退出
- /reset：清空上下文（重新开始对话）
- /clear：清屏
"""


def _clear_screen() -> None:
    os.system("clear" if os.name != "nt" else "cls")


@app.command()
def chat(
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="覆盖 OPENAI_MODEL"),
    ] = None,
    system: Annotated[
        Optional[str],
        typer.Option("--system", help="覆盖 system prompt"),
    ] = None,
) -> None:
    """
    启动可持续对话的命令行 Agent。
    """
    load_dotenv(override=False)

    cfg = load_llm_config()
    if cfg is None:
        console.print(
            "[bold red]未配置 OPENAI_API_KEY[/bold red]。请设置环境变量或创建 .env（参考 .env.example）。"
        )
        raise typer.Exit(code=2)

    if model:
        cfg = type(cfg)(api_key=cfg.api_key, base_url=cfg.base_url, model=model)

    client = make_client(cfg)

    session = ChatSession(system_prompt=system or ChatSession().system_prompt)
    session.reset()

    console.print("[bold]aishu-agent[/bold] 已启动。输入问题开始对话，输入 /help 查看指令。")

    while True:
        try:
            user_text = Prompt.ask("[bold cyan]你[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n已退出。")
            return

        if not user_text:
            continue

        cmd = user_text.lower()
        if cmd in {"/exit", "/quit"}:
            console.print("已退出。")
            return
        if cmd == "/help":
            console.print(HELP_TEXT)
            continue
        if cmd == "/reset":
            session.reset()
            console.print("已清空上下文。")
            continue
        if cmd == "/clear":
            _clear_screen()
            continue

        session.add_user(user_text)
        try:
            answer = chat_once(client=client, model=cfg.model, messages=session.messages)
        except Exception as e:
            console.print(f"[bold red]请求失败：[/bold red]{e}")
            continue

        if not answer:
            answer = "（模型未返回内容）"
        session.add_assistant(answer)
        console.print(f"[bold green]Agent[/bold green]：{answer}")


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        chat()
