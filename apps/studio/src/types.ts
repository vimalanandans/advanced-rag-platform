export type Component = { id: string; version: string; category: string; description: string };
export type Run = {
  run_id: string;
  trace_id: string;
  pipeline_id: string;
  pipeline_version: string;
  graph_fingerprint: string;
  status: "completed" | "failed";
  token_usage: { context_tokens: number; input_tokens: number; output_tokens: number; retrieval_reasoning_tokens?: number };
  node_executions: { node_id: string; status: string; duration_ms: number; iteration?: number }[];
};

export type DrawerTab = "assistant" | "inspector" | "activity" | "versions" | "diagnostics" | "settings";
export type DrawerMode = "docked" | "overlay";
export type SyncState = "saved" | "syncing" | "offline" | "conflict";

export type LocalSettings = { tenant: string; user: string; token: string };
