import {
  Button,
  Form,
  Input,
  Layout,
  Modal,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useState } from "react";
import {
  createProvider,
  deleteProvider,
  listProviders,
  type ProviderInfo,
  updateProviderConfig,
} from "../../api/providers";

const CHAT_MODELS = [
  { value: "OpenAIChatModel", label: "OpenAIChatModel" },
  { value: "AnthropicChatModel", label: "AnthropicChatModel" },
] as const;

function maskKey(k: string): string {
  if (!k) return "—";
  if (k.length <= 4) return "****";
  return `${k.slice(0, 2)}…${k.slice(-2)}（已配置）`;
}

type EditState =
  | { open: true; record: ProviderInfo }
  | { open: false; record: null };

export default function ProvidersPage() {
  const [rows, setRows] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [edit, setEdit] = useState<EditState>({ open: false, record: null });
  const [createOpen, setCreateOpen] = useState(false);
  const [editForm] = Form.useForm<{
    name: string;
    base_url: string;
    api_key: string;
    chat_model: string;
    generate_json: string;
  }>();
  const [createForm] = Form.useForm<{
    id: string;
    name: string;
    base_url: string;
    api_key: string;
    is_local: boolean;
    require_api_key: boolean;
    chat_model: string;
    generate_json: string;
  }>();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listProviders();
      setRows(data);
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openEdit = (record: ProviderInfo) => {
    setEdit({ open: true, record });
    editForm.setFieldsValue({
      name: record.name,
      base_url: record.base_url,
      api_key: "",
      chat_model: record.chat_model,
      generate_json: JSON.stringify(
        record.generate_kwargs && Object.keys(record.generate_kwargs).length
          ? record.generate_kwargs
          : {},
        null,
        2,
      ),
    });
  };

  const submitEdit = async () => {
    if (!edit.open || !edit.record) return;
    const v = await editForm.validateFields();
    let extra: Record<string, unknown> = {};
    try {
      const parsed = JSON.parse(v.generate_json || "{}");
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("generate_kwargs 须为 JSON 对象");
      }
      extra = parsed as Record<string, unknown>;
    } catch (e) {
      message.error(e instanceof Error ? e.message : "generate_kwargs 解析失败");
      return;
    }
    const id = edit.record.id;
    const body: Parameters<typeof updateProviderConfig>[1] = {
      name: v.name,
      base_url: v.base_url,
      chat_model: v.chat_model as "OpenAIChatModel" | "AnthropicChatModel",
      generate_kwargs: extra,
    };
    if (v.api_key?.trim()) {
      body.api_key = v.api_key.trim();
    }
    try {
      await updateProviderConfig(id, body);
      message.success("已保存");
      setEdit({ open: false, record: null });
      await load();
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
  };

  const submitCreate = async () => {
    const v = await createForm.validateFields();
    let extra: Record<string, unknown> = {};
    try {
      const parsed = JSON.parse(v.generate_json || "{}");
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("generate_kwargs 须为 JSON 对象");
      }
      extra = parsed as Record<string, unknown>;
    } catch (e) {
      message.error(e instanceof Error ? e.message : "generate_kwargs 解析失败");
      return;
    }
    try {
      await createProvider({
        id: v.id.trim(),
        name: v.name.trim(),
        base_url: v.base_url?.trim() ?? "",
        api_key: v.api_key ?? "",
        is_local: v.is_local,
        require_api_key: v.require_api_key,
        chat_model: v.chat_model as "OpenAIChatModel" | "AnthropicChatModel",
        generate_kwargs: extra,
      });
      message.success("已创建");
      setCreateOpen(false);
      createForm.resetFields();
      await load();
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
  };

  const onDelete = (record: ProviderInfo) => {
    Modal.confirm({
      title: `删除供应商「${record.name}」？`,
      content: "仅自定义供应商可删除，此操作不可恢复。",
      okText: "删除",
      okType: "danger",
      onOk: async () => {
        try {
          await deleteProvider(record.id);
          message.success("已删除");
          await load();
        } catch (e) {
          message.error(e instanceof Error ? e.message : String(e));
        }
      },
    });
  };

  const columns: ColumnsType<ProviderInfo> = [
    { title: "ID", dataIndex: "id", width: 160, ellipsis: true },
    { title: "名称", dataIndex: "name", width: 160, ellipsis: true },
    { title: "Base URL", dataIndex: "base_url", ellipsis: true },
    {
      title: "协议",
      dataIndex: "chat_model",
      width: 150,
    },
    {
      title: "Key",
      key: "key",
      width: 140,
      render: (_: unknown, r) => (r.api_key ? maskKey(r.api_key) : "—"),
    },
    {
      title: "类型",
      key: "tags",
      width: 200,
      render: (_: unknown, r) => (
        <Space size={[0, 4]} wrap>
          {r.is_custom ? <Tag color="blue">自定义</Tag> : <Tag>内置</Tag>}
          {r.is_local ? <Tag>本地</Tag> : null}
          {r.freeze_url ? <Tag>固定 URL</Tag> : null}
        </Space>
      ),
    },
    {
      title: "操作",
      key: "actions",
      width: 200,
      fixed: "right",
      render: (_: unknown, r) => (
        <Space>
          <Button type="link" size="small" onClick={() => openEdit(r)}>
            编辑
          </Button>
          {r.is_custom ? (
            <Button type="link" size="small" danger onClick={() => onDelete(r)}>
              删除
            </Button>
          ) : null}
        </Space>
      ),
    },
  ];

  const current = edit.open ? edit.record : null;
  const freezeUrl = current?.freeze_url;

  return (
    <Layout style={{ minHeight: "calc(100vh - 64px)", padding: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Space align="center" style={{ width: "100%", justifyContent: "space-between" }}>
          <Typography.Title level={3} style={{ margin: 0 }}>
            模型供应商
          </Typography.Title>
          <Space>
            <Button onClick={() => void load()} loading={loading}>
              刷新
            </Button>
            <Button
              type="primary"
              onClick={() => {
                createForm.setFieldsValue({
                  id: "",
                  name: "",
                  base_url: "https://",
                  api_key: "",
                  is_local: false,
                  require_api_key: true,
                  chat_model: "OpenAIChatModel",
                  generate_json: "{\n  \n}",
                });
                setCreateOpen(true);
              }}
            >
              新建供应商
            </Button>
          </Space>
        </Space>

        <Table<ProviderInfo>
          rowKey="id"
          loading={loading}
          columns={columns}
          dataSource={rows}
          scroll={{ x: 1100 }}
          pagination={{ pageSize: 12, showSizeChanger: true }}
        />
      </Space>

      <Modal
        title="编辑供应商"
        open={edit.open}
        onOk={() => void submitEdit()}
        onCancel={() => setEdit({ open: false, record: null })}
        width={640}
        destroyOnClose
      >
        {current && (
          <Form form={editForm} layout="vertical" preserve={false}>
            <Typography.Text type="secondary" style={{ display: "block", marginBottom: 8 }}>
              ID：{current.id}（只读）
            </Typography.Text>
            <Form.Item name="name" label="显示名称" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item
              name="base_url"
              label="Base URL"
              rules={[{ required: !freezeUrl, message: "请填写 Base URL" }]}
            >
              <Input disabled={!!freezeUrl} placeholder={freezeUrl ? "该供应商固化了地址" : ""} />
            </Form.Item>
            <Form.Item
              name="api_key"
              label="API Key"
              extra="留空则不修改已保存的 Key"
            >
              <Input.Password autoComplete="new-password" placeholder="不修改请留空" />
            </Form.Item>
            <Form.Item name="chat_model" label="Chat 协议" rules={[{ required: true }]}>
              <Select options={[...CHAT_MODELS]} />
            </Form.Item>
            <Form.Item
              name="generate_json"
              label="generate_kwargs（JSON）"
              rules={[{ required: true, message: "请填写 JSON" }]}
            >
              <Input.TextArea rows={6} spellCheck={false} />
            </Form.Item>
          </Form>
        )}
      </Modal>

      <Modal
        title="新建自定义供应商"
        open={createOpen}
        onOk={() => void submitCreate()}
        onCancel={() => setCreateOpen(false)}
        width={640}
        destroyOnClose
      >
        <Form
          form={createForm}
          layout="vertical"
          initialValues={{
            is_local: false,
            require_api_key: true,
            chat_model: "OpenAIChatModel",
            generate_json: "{}",
          }}
        >
          <Form.Item
            name="id"
            label="ID"
            rules={[{ required: true, message: "填写唯一 id" }]}
            extra="若与已有 id 冲突，后端会自动加后缀"
          >
            <Input placeholder="如 my-openai" />
          </Form.Item>
          <Form.Item name="name" label="显示名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="is_local" label="本地供应商" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(a, b) => a.is_local !== b.is_local}
          >
            {({ getFieldValue }) =>
              getFieldValue("is_local") ? null : (
                <Form.Item name="base_url" label="Base URL" rules={[{ required: true }]}>
                  <Input placeholder="https://..." />
                </Form.Item>
              )
            }
          </Form.Item>
          <Form.Item name="require_api_key" label="需要 API Key" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item name="api_key" label="API Key">
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item name="chat_model" label="Chat 协议" rules={[{ required: true }]}>
            <Select options={[...CHAT_MODELS]} />
          </Form.Item>
          <Form.Item
            name="generate_json"
            label="generate_kwargs（JSON）"
            rules={[{ required: true }]}
          >
            <Input.TextArea rows={5} placeholder="{}" spellCheck={false} />
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
}
