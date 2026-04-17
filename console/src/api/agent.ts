/**
 * 调用 HiData 后端 Agent 接口（与 `hidata.cli.relay_cmd` 一致）。
 * POST /api/agent/process，body 为 AgentRequest；响应为 text/event-stream（即使 stream:false）。
 */

export type AgentContentBlock = { type: "text"; text: string };

export type AgentInputMessage = {
  type: "message";
  role: "user" | "assistant" | "system";
  content: AgentContentBlock[];
};

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE as string | undefined;
  return raw?.replace(/\/$/, "") ?? "";
}

export function agentProcessUrl(): string {
  const base = apiBase();
  return base ? `${base}/api/agent/process` : "/api/agent/process";
}

/**
 * 解析 runtime 返回的 SSE 文本，拼接 assistant 文本增量；若失败则抛出带服务端信息的 Error。
 */
export function parseAgentSseBody(raw: string): string {
  let answer = "";
  for (const line of raw.split(/\r?\n/)) {
    const s = line.trim();
    if (!s.startsWith("data:")) continue;
    const chunk = s.slice(5).trim();
    if (!chunk) continue;
    let obj: Record<string, unknown>;
    try {
      obj = JSON.parse(chunk) as Record<string, unknown>;
    } catch {
      continue;
    }
    if (
      obj.object === "content" &&
      obj.type === "text" &&
      typeof obj.text === "string" &&
      obj.text
    ) {
      answer += obj.text;
    }
    if (obj.object === "response" && obj.status === "failed") {
      const err = obj.error as { message?: string } | undefined;
      const msg = err?.message ?? "Agent 请求失败";
      throw new Error(msg);
    }
  }
  return answer.trim() || raw.trim();
}

export async function postAgentProcess(
  input: AgentInputMessage[],
  options?: { stream?: boolean; signal?: AbortSignal },
): Promise<string> {
  const res = await fetch(agentProcessUrl(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input,
      stream: options?.stream ?? false,
    }),
    signal: options?.signal,
  });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(
      t ? `HTTP ${res.status}: ${t.slice(0, 200)}` : `HTTP ${res.status}`,
    );
  }
  const raw = await res.text();
  return parseAgentSseBody(raw);
}

function processSseLine(
  line: string,
  onDelta: (delta: string, accumulated: string) => void,
  accumulated: { value: string },
): void {
  const s = line.trim();
  if (!s.startsWith("data:")) return;
  const chunk = s.slice(5).trim();
  if (!chunk) return;
  let obj: Record<string, unknown>;
  try {
    obj = JSON.parse(chunk) as Record<string, unknown>;
  } catch {
    return;
  }
  if (
    obj.object === "content" &&
    obj.type === "text" &&
    typeof obj.text === "string" &&
    obj.text
  ) {
    accumulated.value += obj.text;
    onDelta(obj.text, accumulated.value);
  }
  if (obj.object === "response" && obj.status === "failed") {
    const err = obj.error as { message?: string } | undefined;
    const msg = err?.message ?? "Agent 请求失败";
    throw new Error(msg);
  }
}

/**
 * 流式调用：边读 SSE 边解析，通过 onDelta 推送文本增量（与 stream:true 配合）。
 */
export async function streamAgentProcess(
  input: AgentInputMessage[],
  options: {
    onDelta: (delta: string, accumulated: string) => void;
    signal?: AbortSignal;
  },
): Promise<string> {
  const res = await fetch(agentProcessUrl(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input, stream: true }),
    signal: options.signal,
  });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(
      t ? `HTTP ${res.status}: ${t.slice(0, 200)}` : `HTTP ${res.status}`,
    );
  }
  const reader = res.body?.getReader();
  if (!reader) {
    const raw = await res.text();
    return parseAgentSseBody(raw);
  }

  const decoder = new TextDecoder();
  let buffer = "";
  const accumulated = { value: "" };

  const flushLine = (line: string) => {
    processSseLine(line, options.onDelta, accumulated);
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    for (;;) {
      const nl = buffer.indexOf("\n");
      if (nl < 0) break;
      const line = buffer.slice(0, nl);
      buffer = buffer.slice(nl + 1);
      flushLine(line);
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) {
    for (const line of buffer.split("\n")) {
      if (line.length) flushLine(line);
    }
  }

  return accumulated.value.trim();
}
