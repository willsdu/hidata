import { Button, ConfigProvider, Layout, Space, Typography, theme } from "antd";
import { useState } from "react";
import ChatPage from "./pages/Chat";
import ProvidersPage from "./pages/Providers";

type View = "chat" | "providers";

export default function App() {
  const [view, setView] = useState<View>("chat");

  return (
    <ConfigProvider theme={{ algorithm: theme.defaultAlgorithm }}>
      <Layout style={{ minHeight: "100vh" }}>
        <Layout.Header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 20px",
            background: "#001529",
            gap: 16,
          }}
        >
          <Typography.Text style={{ color: "rgba(255,255,255,0.85)", fontWeight: 600 }}>
            HiData 控制台
          </Typography.Text>
          <Space>
            <Button
              type={view === "chat" ? "primary" : "default"}
              onClick={() => setView("chat")}
            >
              聊天
            </Button>
            <Button
              type={view === "providers" ? "primary" : "default"}
              onClick={() => setView("providers")}
            >
              模型供应商
            </Button>
          </Space>
        </Layout.Header>
        <Layout.Content>
          {view === "chat" ? <ChatPage /> : <ProvidersPage />}
        </Layout.Content>
      </Layout>
    </ConfigProvider>
  );
}

