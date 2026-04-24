/**
 * Provider CRUD: `/api/providers`（与 `hidata.app.routers.providers` 一致）。
 */

export type ModelInfo = { id: string; name: string };

export type ProviderInfo = {
  id: string;
  name: string;
  base_url: string;
  api_key: string;
  chat_model: string;
  models: ModelInfo[];
  extra_models: ModelInfo[];
  api_key_prefix: string;
  is_local: boolean;
  freeze_url: boolean;
  require_api_key: boolean;
  is_custom: boolean;
  support_model_discovery: boolean;
  generate_kwargs: Record<string, unknown>;
};

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE as string | undefined;
  return raw?.replace(/\/$/, "") ?? "";
}

function joinApi(path: string): string {
  const base = apiBase();
  const p = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}

async function parseError(res: Response): Promise<string> {
  const t = await res.text().catch(() => "");
  if (!t) return `HTTP ${res.status}`;
  try {
    const j = JSON.parse(t) as { detail?: unknown };
    if (typeof j.detail === "string") return j.detail;
    if (Array.isArray(j.detail)) {
      return j.detail
        .map((x) => (typeof x === "object" && x && "msg" in x ? String((x as { msg: string }).msg) : String(x)))
        .join(", ");
    }
  } catch {
    // ignore
  }
  return t.slice(0, 400) || `HTTP ${res.status}`;
}

export async function listProviders(): Promise<ProviderInfo[]> {
  const res = await fetch(joinApi("/api/providers/"), {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ProviderInfo[];
}

export async function getProvider(providerId: string): Promise<ProviderInfo> {
  const res = await fetch(
    joinApi(`/api/providers/${encodeURIComponent(providerId)}`),
    { method: "GET", headers: { Accept: "application/json" } },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ProviderInfo;
}

export type CreateProviderBody = {
  id: string;
  name: string;
  base_url?: string;
  api_key?: string;
  chat_model?: "OpenAIChatModel" | "AnthropicChatModel";
  is_local?: boolean;
  require_api_key?: boolean;
  freeze_url?: boolean;
  support_model_discovery?: boolean;
  generate_kwargs?: Record<string, unknown>;
};

export async function createProvider(
  body: CreateProviderBody,
): Promise<ProviderInfo> {
  const res = await fetch(joinApi("/api/providers/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: body.id,
      name: body.name,
      base_url: body.base_url ?? "",
      api_key: body.api_key ?? "",
      chat_model: body.chat_model ?? "OpenAIChatModel",
      models: [],
      extra_models: [],
      is_local: body.is_local ?? false,
      require_api_key: body.require_api_key ?? true,
      freeze_url: body.freeze_url ?? false,
      support_model_discovery: body.support_model_discovery ?? false,
      generate_kwargs: body.generate_kwargs ?? {},
    }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ProviderInfo;
}

export type UpdateProviderConfigBody = {
  name?: string;
  base_url?: string;
  api_key?: string;
  chat_model?: "OpenAIChatModel" | "AnthropicChatModel";
  generate_kwargs?: Record<string, unknown>;
};

export async function updateProviderConfig(
  providerId: string,
  body: UpdateProviderConfigBody,
): Promise<ProviderInfo> {
  const res = await fetch(
    joinApi(`/api/providers/${encodeURIComponent(providerId)}/config`),
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ProviderInfo;
}

export async function deleteProvider(providerId: string): Promise<void> {
  const res = await fetch(
    joinApi(`/api/providers/${encodeURIComponent(providerId)}`),
    { method: "DELETE" },
  );
  if (!res.ok) throw new Error(await parseError(res));
}
