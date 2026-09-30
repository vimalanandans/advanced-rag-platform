import { useState } from "react";

export function AIComposer({ onPropose }: { onPropose: () => void }) {
  const [prompt, setPrompt] = useState("");
  return <div className="ai-composer"><div className="context-chips"><span>Pipeline: baseline <button aria-label="Remove pipeline context">×</button></span><span>Approved references only <button aria-label="Remove reference context">×</button></span></div><textarea value={prompt} onChange={event => setPrompt(event.target.value)} placeholder="Ask about this pipeline…" aria-label="Ask AI about the current pipeline" /><div className="composer-footer"><small>AI sees the selected pipeline and approved references.</small><button className="primary-button" disabled={!prompt.trim()} onClick={() => { onPropose(); setPrompt(""); }}>Propose ↵</button></div></div>;
}
