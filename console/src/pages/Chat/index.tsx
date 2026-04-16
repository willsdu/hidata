import { Button, Card, Input, Layout, Space, Typography } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

function nowId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: nowId(),
      role: "assistant",
      content: "你好！这里是 console 的初始聊天页。",
    },
  ]);
  const [draft, setDraft] = useState("");
  const listRef = useRef<HTMLDivElement | null>(null);

  const canSend = useMemo(() => draft.trim().length > 0, [draft]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages.length]);

  const send = () => {
    const text = draft.trim();
    if (!text) return;
    setDraft("");

    const userMsg: ChatMessage = { id: nowId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    window.setTimeout(() => {
      const assistantMsg: ChatMessage = {
        id: nowId(),
        role: "assistant",
        content: `收到：${text}`,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }, 300);
  };

  return (
    <Layout style={{ height: "100vh", padding: 16 }}>
      <Space direction="vertical" size={12} style={{ height: "100%" }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          聊天
        </Typography.Title>

        <Card
          bodyStyle={{ height: "calc(100vh - 170px)", overflow: "auto" }}
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
            onChange={(e) => setDraft(e.target.value)}
            onPressEnter={() => {
              if (canSend) send();
            }}
          />
          <Button type="primary" disabled={!canSend} onClick={send}>
            发送
          </Button>
        </Space.Compact>
      </Space>
    </Layout>
  );
}

