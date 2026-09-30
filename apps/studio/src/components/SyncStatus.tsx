import { SyncState } from "../types";

export function SyncStatus({ state }: { state: SyncState }) {
  const label = { saved: "Saved locally", syncing: "Syncing", offline: "Offline — working locally", conflict: "Sync conflict needs review" }[state];
  return <span className={`sync-status ${state}`} aria-live="polite"><i />{label}</span>;
}
