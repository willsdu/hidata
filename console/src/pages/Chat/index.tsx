import { Button, Card, Input, Layout, Space, Typography, message } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  streamAgentProcess,
  type AgentInputMessage,
} from "../../api/agent";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  /** 仅界面展示，不参与发给后端的 history */
  localOnly?: boolean;
};

function nowId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function toAgentInput(messages: ChatMessage[]): AgentInputMessage[] {
  return messages
    .filter((m) => !m.localOnly)
    .map((m) => ({
      type: "message" as const,
      role: m.role,
      content: [{ type: "text" as const, text: m.content }],
    }));
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: nowId(),
      role: "assistant",
      content: "你好！在下方输入问题，将通过 /api/agent/process 交给 Agent 回答。",
      localOnly: true,
    },
  ]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);

  const canSend = useMemo(
    () => !loading && draft.trim().length > 0,
    [draft, loading],
  );

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  const send = async () => {
    const text = draft.trim();
    if (!text || loading) return;
    setDraft("");

    const userMsg: ChatMessage = { id: nowId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    const historyForApi = toAgentInput([...messages, userMsg]);

    const assistantId = nowId();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "" },
    ]);

    setLoading(true);
    try {
      const final = await streamAgentProcess(historyForApi, {
        onDelta: (_delta, accumulated) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: accumulated } : m,
            ),
          );
        },
      });
      if (!final.trim()) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: "（无内容）" } : m,
          ),
        );
      }
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e);
      message.error(err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: m.content ? `${m.content}\n\n[错误] ${err}` : `请求失败：${err}` }
            : m,
        ),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: "calc(100vh - 64px)", padding: 16 }}>
      <Space direction="vertical" size={12} style={{ height: "100%" }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          聊天
        </Typography.Title>

        <Card
          bodyStyle={{
            height: "calc(100vh - 64px - 170px)",
            overflow: "auto",
          }}
          style={{ width: "min(980px, 100%)" }}
        >
          <div ref={listRef}>
            <Space direction="vertical" size={10} style={{ width: "100%" }}>
              {messages.map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    justifyContent:
                      m.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: 720,
                      padding: "10px 12px",
                      borderRadius: 12,
                      background: m.role === "user" ? "#1677ff" : "#f5f5f5",
                      color: m.role === "user" ? "#fff" : "rgba(0,0,0,0.88)",
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                    }}
                  >
                    <Typography.Text
                      style={{
                        color: m.role === "user" ? "#fff" : undefined,
                      }}
                    >
                      {m.content}
                    </Typography.Text>
                  </div>
                </div>
              ))}
            </Space>
          </div>
        </Card>

        <Space.Compact style={{ width: "min(980px, 100%)" }}>
          <Input
            value={draft}
            placeholder="输入消息…"
            disabled={loading}
            onChange={(e) => setDraft(e.target.value)}
            onPressEnter={() => {
              if (canSend) void send();
            }}
          />
          <Button
            type="primary"
            loading={loading}
            disabled={!canSend}
            onClick={() => void send()}
          >
            发送
          </Button>
        </Space.Compact>
      </Space>
    </Layout>
  );
}
