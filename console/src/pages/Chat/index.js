import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button, Card, Input, Layout, Space, Typography, message } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import { streamAgentProcess, } from "../../api/agent";
function nowId() {
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function toAgentInput(messages) {
    return messages
        .filter((m) => !m.localOnly)
        .map((m) => ({
        type: "message",
        role: m.role,
        content: [{ type: "text", text: m.content }],
    }));
}
export default function ChatPage() {
    const [messages, setMessages] = useState([
        {
            id: nowId(),
            role: "assistant",
            content: "你好！在下方输入问题，将通过 /api/agent/process 交给 Agent 回答。",
            localOnly: true,
        },
    ]);
    const [draft, setDraft] = useState("");
    const [loading, setLoading] = useState(false);
    const listRef = useRef(null);
    const canSend = useMemo(() => !loading && draft.trim().length > 0, [draft, loading]);
    useEffect(() => {
        listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
    }, [messages]);
    const send = async () => {
        const text = draft.trim();
        if (!text || loading)
            return;
        setDraft("");
        const userMsg = { id: nowId(), role: "user", content: text };
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
                    setMessages((prev) => prev.map((m) => m.id === assistantId ? { ...m, content: accumulated } : m));
                },
            });
            if (!final.trim()) {
                setMessages((prev) => prev.map((m) => m.id === assistantId ? { ...m, content: "（无内容）" } : m));
            }
        }
        catch (e) {
            const err = e instanceof Error ? e.message : String(e);
            message.error(err);
            setMessages((prev) => prev.map((m) => m.id === assistantId
                ? { ...m, content: m.content ? `${m.content}\n\n[错误] ${err}` : `请求失败：${err}` }
                : m));
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx(Layout, { style: { height: "100vh", padding: 16 }, children: _jsxs(Space, { direction: "vertical", size: 12, style: { height: "100%" }, children: [_jsx(Typography.Title, { level: 3, style: { margin: 0 }, children: "\u804A\u5929" }), _jsx(Card, { bodyStyle: { height: "calc(100vh - 170px)", overflow: "auto" }, style: { width: "min(980px, 100%)" }, children: _jsx("div", { ref: listRef, children: _jsx(Space, { direction: "vertical", size: 10, style: { width: "100%" }, children: messages.map((m) => (_jsx("div", { style: {
                                    display: "flex",
                                    justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                                }, children: _jsx("div", { style: {
                                        maxWidth: 720,
                                        padding: "10px 12px",
                                        borderRadius: 12,
                                        background: m.role === "user" ? "#1677ff" : "#f5f5f5",
                                        color: m.role === "user" ? "#fff" : "rgba(0,0,0,0.88)",
                                        whiteSpace: "pre-wrap",
                                        wordBreak: "break-word",
                                    }, children: _jsx(Typography.Text, { style: {
                                            color: m.role === "user" ? "#fff" : undefined,
                                        }, children: m.content }) }) }, m.id))) }) }) }), _jsxs(Space.Compact, { style: { width: "min(980px, 100%)" }, children: [_jsx(Input, { value: draft, placeholder: "\u8F93\u5165\u6D88\u606F\u2026", disabled: loading, onChange: (e) => setDraft(e.target.value), onPressEnter: () => {
                                if (canSend)
                                    void send();
                            } }), _jsx(Button, { type: "primary", loading: loading, disabled: !canSend, onClick: () => void send(), children: "\u53D1\u9001" })] })] }) }));
}
