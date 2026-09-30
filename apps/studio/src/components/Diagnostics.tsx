import { Run } from "../types";

export function Diagnostics({ run }: { run?: Run }) {
  return <div className="drawer-stack"><p className="muted">Safe diagnostics omit credentials and source text.</p><dl className="diagnostic-list"><dt>Trace ID</dt><dd>{run?.trace_id ?? "No run selected"}</dd><dt>Graph</dt><dd>{run?.graph_fingerprint.slice(0, 16) ?? "—"}</dd><dt>Status</dt><dd>{run?.status ?? "—"}</dd><dt>Token usage</dt><dd>{run ? `${run.token_usage.input_tokens + run.token_usage.output_tokens} total` : "—"}</dd></dl><button className="quiet-button">Export redacted diagnostics</button></div>;
}
