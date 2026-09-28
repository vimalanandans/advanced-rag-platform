export function VersionHistory() {
  return <div className="drawer-stack"><p className="muted">Production versions remain immutable.</p><div className="history-item current"><b>1.0.0</b><span>Current local baseline</span><small>Fingerprint recorded on every run</small></div><div className="history-item"><b>Draft</b><span>No pending changes</span><button className="quiet-button">Create draft</button></div></div>;
}
