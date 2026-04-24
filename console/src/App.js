import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button, ConfigProvider, Layout, Space, Typography, theme } from "antd";
import { useState } from "react";
import ChatPage from "./pages/Chat";
import ProvidersPage from "./pages/Providers";
export default function App() {
    const [view, setView] = useState("chat");
    return (_jsx(ConfigProvider, { theme: { algorithm: theme.defaultAlgorithm }, children: _jsxs(Layout, { style: { minHeight: "100vh" }, children: [_jsxs(Layout.Header, { style: {
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "0 20px",
                        background: "#001529",
                        gap: 16,
                    }, children: [_jsx(Typography.Text, { style: { color: "rgba(255,255,255,0.85)", fontWeight: 600 }, children: "HiData \u63A7\u5236\u53F0" }), _jsxs(Space, { children: [_jsx(Button, { type: view === "chat" ? "primary" : "default", onClick: () => setView("chat"), children: "\u804A\u5929" }), _jsx(Button, { type: view === "providers" ? "primary" : "default", onClick: () => setView("providers"), children: "\u6A21\u578B\u4F9B\u5E94\u5546" })] })] }), _jsx(Layout.Content, { children: view === "chat" ? _jsx(ChatPage, {}) : _jsx(ProvidersPage, {}) })] }) }));
}
