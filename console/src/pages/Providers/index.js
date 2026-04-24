import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button, Form, Input, Layout, Modal, Select, Space, Switch, Table, Tag, Typography, message, } from "antd";
import { useCallback, useEffect, useState } from "react";
import { createProvider, deleteProvider, listProviders, updateProviderConfig, } from "../../api/providers";
const CHAT_MODELS = [
    { value: "OpenAIChatModel", label: "OpenAIChatModel" },
    { value: "AnthropicChatModel", label: "AnthropicChatModel" },
];
function maskKey(k) {
    if (!k)
        return "—";
    if (k.length <= 4)
        return "****";
    return `${k.slice(0, 2)}…${k.slice(-2)}（已配置）`;
}
export default function ProvidersPage() {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(false);
    const [edit, setEdit] = useState({ open: false, record: null });
    const [createOpen, setCreateOpen] = useState(false);
    const [editForm] = Form.useForm();
    const [createForm] = Form.useForm();
    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await listProviders();
            setRows(data);
        }
        catch (e) {
            message.error(e instanceof Error ? e.message : String(e));
        }
        finally {
            setLoading(false);
        }
    }, []);
    useEffect(() => {
        void load();
    }, [load]);
    const openEdit = (record) => {
        setEdit({ open: true, record });
        editForm.setFieldsValue({
            name: record.name,
            base_url: record.base_url,
            api_key: "",
            chat_model: record.chat_model,
            generate_json: JSON.stringify(record.generate_kwargs && Object.keys(record.generate_kwargs).length
                ? record.generate_kwargs
                : {}, null, 2),
        });
    };
    const submitEdit = async () => {
        if (!edit.open || !edit.record)
            return;
        const v = await editForm.validateFields();
        let extra = {};
        try {
            const parsed = JSON.parse(v.generate_json || "{}");
            if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
                throw new Error("generate_kwargs 须为 JSON 对象");
            }
            extra = parsed;
        }
        catch (e) {
            message.error(e instanceof Error ? e.message : "generate_kwargs 解析失败");
            return;
        }
        const id = edit.record.id;
        const body = {
            name: v.name,
            base_url: v.base_url,
            chat_model: v.chat_model,
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
        }
        catch (e) {
            message.error(e instanceof Error ? e.message : String(e));
        }
    };
    const submitCreate = async () => {
        const v = await createForm.validateFields();
        let extra = {};
        try {
            const parsed = JSON.parse(v.generate_json || "{}");
            if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
                throw new Error("generate_kwargs 须为 JSON 对象");
            }
            extra = parsed;
        }
        catch (e) {
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
                chat_model: v.chat_model,
                generate_kwargs: extra,
            });
            message.success("已创建");
            setCreateOpen(false);
            createForm.resetFields();
            await load();
        }
        catch (e) {
            message.error(e instanceof Error ? e.message : String(e));
        }
    };
    const onDelete = (record) => {
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
                }
                catch (e) {
                    message.error(e instanceof Error ? e.message : String(e));
                }
            },
        });
    };
    const columns = [
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
            render: (_, r) => (r.api_key ? maskKey(r.api_key) : "—"),
        },
        {
            title: "类型",
            key: "tags",
            width: 200,
            render: (_, r) => (_jsxs(Space, { size: [0, 4], wrap: true, children: [r.is_custom ? _jsx(Tag, { color: "blue", children: "\u81EA\u5B9A\u4E49" }) : _jsx(Tag, { children: "\u5185\u7F6E" }), r.is_local ? _jsx(Tag, { children: "\u672C\u5730" }) : null, r.freeze_url ? _jsx(Tag, { children: "\u56FA\u5B9A URL" }) : null] })),
        },
        {
            title: "操作",
            key: "actions",
            width: 200,
            fixed: "right",
            render: (_, r) => (_jsxs(Space, { children: [_jsx(Button, { type: "link", size: "small", onClick: () => openEdit(r), children: "\u7F16\u8F91" }), r.is_custom ? (_jsx(Button, { type: "link", size: "small", danger: true, onClick: () => onDelete(r), children: "\u5220\u9664" })) : null] })),
        },
    ];
    const current = edit.open ? edit.record : null;
    const freezeUrl = current?.freeze_url;
    return (_jsxs(Layout, { style: { minHeight: "calc(100vh - 64px)", padding: 16 }, children: [_jsxs(Space, { direction: "vertical", size: "middle", style: { width: "100%" }, children: [_jsxs(Space, { align: "center", style: { width: "100%", justifyContent: "space-between" }, children: [_jsx(Typography.Title, { level: 3, style: { margin: 0 }, children: "\u6A21\u578B\u4F9B\u5E94\u5546" }), _jsxs(Space, { children: [_jsx(Button, { onClick: () => void load(), loading: loading, children: "\u5237\u65B0" }), _jsx(Button, { type: "primary", onClick: () => {
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
                                        }, children: "\u65B0\u5EFA\u4F9B\u5E94\u5546" })] })] }), _jsx(Table, { rowKey: "id", loading: loading, columns: columns, dataSource: rows, scroll: { x: 1100 }, pagination: { pageSize: 12, showSizeChanger: true } })] }), _jsx(Modal, { title: "\u7F16\u8F91\u4F9B\u5E94\u5546", open: edit.open, onOk: () => void submitEdit(), onCancel: () => setEdit({ open: false, record: null }), width: 640, destroyOnClose: true, children: current && (_jsxs(Form, { form: editForm, layout: "vertical", preserve: false, children: [_jsxs(Typography.Text, { type: "secondary", style: { display: "block", marginBottom: 8 }, children: ["ID\uFF1A", current.id, "\uFF08\u53EA\u8BFB\uFF09"] }), _jsx(Form.Item, { name: "name", label: "\u663E\u793A\u540D\u79F0", rules: [{ required: true }], children: _jsx(Input, {}) }), _jsx(Form.Item, { name: "base_url", label: "Base URL", rules: [{ required: !freezeUrl, message: "请填写 Base URL" }], children: _jsx(Input, { disabled: !!freezeUrl, placeholder: freezeUrl ? "该供应商固化了地址" : "" }) }), _jsx(Form.Item, { name: "api_key", label: "API Key", extra: "\u7559\u7A7A\u5219\u4E0D\u4FEE\u6539\u5DF2\u4FDD\u5B58\u7684 Key", children: _jsx(Input.Password, { autoComplete: "new-password", placeholder: "\u4E0D\u4FEE\u6539\u8BF7\u7559\u7A7A" }) }), _jsx(Form.Item, { name: "chat_model", label: "Chat \u534F\u8BAE", rules: [{ required: true }], children: _jsx(Select, { options: [...CHAT_MODELS] }) }), _jsx(Form.Item, { name: "generate_json", label: "generate_kwargs\uFF08JSON\uFF09", rules: [{ required: true, message: "请填写 JSON" }], children: _jsx(Input.TextArea, { rows: 6, spellCheck: false }) })] })) }), _jsx(Modal, { title: "\u65B0\u5EFA\u81EA\u5B9A\u4E49\u4F9B\u5E94\u5546", open: createOpen, onOk: () => void submitCreate(), onCancel: () => setCreateOpen(false), width: 640, destroyOnClose: true, children: _jsxs(Form, { form: createForm, layout: "vertical", initialValues: {
                        is_local: false,
                        require_api_key: true,
                        chat_model: "OpenAIChatModel",
                        generate_json: "{}",
                    }, children: [_jsx(Form.Item, { name: "id", label: "ID", rules: [{ required: true, message: "填写唯一 id" }], extra: "\u82E5\u4E0E\u5DF2\u6709 id \u51B2\u7A81\uFF0C\u540E\u7AEF\u4F1A\u81EA\u52A8\u52A0\u540E\u7F00", children: _jsx(Input, { placeholder: "\u5982 my-openai" }) }), _jsx(Form.Item, { name: "name", label: "\u663E\u793A\u540D\u79F0", rules: [{ required: true }], children: _jsx(Input, {}) }), _jsx(Form.Item, { name: "is_local", label: "\u672C\u5730\u4F9B\u5E94\u5546", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { noStyle: true, shouldUpdate: (a, b) => a.is_local !== b.is_local, children: ({ getFieldValue }) => getFieldValue("is_local") ? null : (_jsx(Form.Item, { name: "base_url", label: "Base URL", rules: [{ required: true }], children: _jsx(Input, { placeholder: "https://..." }) })) }), _jsx(Form.Item, { name: "require_api_key", label: "\u9700\u8981 API Key", valuePropName: "checked", children: _jsx(Switch, {}) }), _jsx(Form.Item, { name: "api_key", label: "API Key", children: _jsx(Input.Password, { autoComplete: "new-password" }) }), _jsx(Form.Item, { name: "chat_model", label: "Chat \u534F\u8BAE", rules: [{ required: true }], children: _jsx(Select, { options: [...CHAT_MODELS] }) }), _jsx(Form.Item, { name: "generate_json", label: "generate_kwargs\uFF08JSON\uFF09", rules: [{ required: true }], children: _jsx(Input.TextArea, { rows: 5, placeholder: "{}", spellCheck: false }) })] }) })] }));
}
