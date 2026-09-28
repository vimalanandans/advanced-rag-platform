type Props = { open: boolean; onClose: () => void; onAction: (action: string) => void };
const actions = ["Run active pipeline", "Explain selected node", "Open Data & Trust", "Show latest trace"];

export function CommandPalette({ open, onClose, onAction }: Props) {
  if (!open) return null;
  return <div className="command-backdrop" onMouseDown={onClose}><section className="command-palette" role="dialog" aria-modal="true" aria-label="Command palette" onMouseDown={event => event.stopPropagation()}><input autoFocus placeholder="Search commands…" aria-label="Search commands" /><span className="eyebrow">CURRENT WORKSPACE</span>{actions.map(action => <button key={action} onClick={() => { onAction(action); onClose(); }}><span>{action}</span><kbd>{action.startsWith("Run") ? "R" : "↵"}</kbd></button>)}</section></div>;
}
