type Props = { status: "idle" | "proposed" | "accepted" | "rejected"; onAccept: () => void; onReject: () => void; onRevise: () => void };

export function AIChangeSet({ status, onAccept, onReject, onRevise }: Props) {
  if (status === "idle") return null;
  if (status === "accepted") return <div className="change-set accepted"><b>Proposal accepted</b><span>One undoable workspace change is ready.</span><button onClick={onReject}>Undo</button></div>;
  if (status === "rejected") return <div className="change-set"><b>Proposal dismissed</b><span>Your pipeline remains unchanged.</span><button onClick={onRevise}>Create another proposal</button></div>;
  return <div className="change-set proposal" aria-live="polite"><div><span className="eyebrow">AI PROPOSAL · NOT SAVED</span><b>Add a revision-policy check before evidence retrieval</b><p>Preview only: this suggestion has not changed the pipeline configuration.</p></div><div className="change-actions"><button className="quiet-button" onClick={onRevise}>Revise</button><button className="quiet-button" onClick={onReject}>Reject</button><button className="primary-button" onClick={onAccept}>Accept</button></div></div>;
}
