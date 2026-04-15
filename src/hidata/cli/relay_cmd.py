from __future__ import annotations

import json
import urllib.request
from typing import Any

import click


def _post_sse(url: str, payload: dict[str, Any], timeout: float = 60) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # SSE format: many "data: {...}\n\n" blocks. Extract message text deltas.
    answer_parts: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[len("data:") :].strip()
        if not chunk:
            continue
        try:
            obj = json.loads(chunk)
        except Exception:
            continue

        # Text adapter emits "content" objects with text deltas.
        if obj.get("object") == "content" and obj.get("type") == "text":
            delta = obj.get("text", "")
            if isinstance(delta, str) and delta:
                answer_parts.append(delta)

        # If failed, surface the error message.
        if obj.get("object") == "response" and obj.get("status") == "failed":
            err = obj.get("error") or {}
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise click.ClickException(msg or "Agent 请求失败")

    return "".join(answer_parts).strip() or raw.strip()


@click.command("relay")
@click.option("--timeout", default=60.0, show_default=True, help="请求超时时间（秒）")
@click.pass_context
def relay_cmd(ctx: click.Context, timeout: float) -> None:
    """连续读取用户输入，并通过 REST 转发给正在运行的服务处理。"""
    host = (ctx.obj or {}).get("host") or "127.0.0.1"
    port = (ctx.obj or {}).get("port") or 8088

    endpoint = f"http://{host}:{port}/api/agent/process"
    click.echo(f"relay 已启动，目标：{endpoint}")
    click.echo("输入问题回车发送。/exit 退出，/reset 清空上下文。")

    history: list[dict[str, Any]] = []

    while True:
        try:
            user_text = click.prompt("你", prompt_suffix="> ", default="", show_default=False)
            user_text = (user_text or "").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\n已退出。")
            return

        if not user_text:
            continue

        cmd = user_text.lower()
        if cmd in {"/exit", "/quit"}:
            click.echo("已退出。")
            return
        if cmd == "/reset":
            history = []
            click.echo("已清空上下文。")
            continue

        # Build AgentRequest.input history as runtime protocol "message" objects.
        history.append(
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "text", "text": user_text}],
            },
        )

        payload = {
            "input": history,
            "stream": False,
        }
        answer = _post_sse(endpoint, payload, timeout=timeout)
        click.echo(f"Agent：{answer}")
        history.append(
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": answer}],
            },
        )

