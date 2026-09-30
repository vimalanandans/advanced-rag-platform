import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { Component, DrawerMode, DrawerTab, LocalSettings, Run, SyncState } from "../types";
import { useLocalState } from "../lib/useLocalState";
import { CommandPalette } from "./CommandPalette";
import { ContextDrawer } from "./ContextDrawer";
import { NavigationSidebar } from "./NavigationSidebar";
import { PrimaryCanvas } from "./PrimaryCanvas";
import { SyncStatus } from "./SyncStatus";

const API = import.meta.env.VITE_API_URL ?? "/api";
const defaults: LocalSettings = { tenant: "local", user: "local-admin", token: "local-development-token" };

export function AppShell() {
  const [components, setComponents] = useState<Component[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [question, setQuestion] = useLocalState("studio.question", "When should a RAG system abstain?");
  const [answer, setAnswer] = useLocalState("studio.answer", "Run the local baseline to inspect approved evidence, context, and trace events.");
  const [settings, setSettings] = useLocalState<LocalSettings>("studio.local-settings", defaults);
  const [collapsed, setCollapsed] = useLocalState("studio.sidebar-collapsed", false);
  const [drawerOpen, setDrawerOpen] = useLocalState("studio.drawer-open", true);
  const [drawerMode, setDrawerMode] = useLocalState<DrawerMode>("studio.drawer-mode", "docked");
  const [drawerWidth, setDrawerWidth] = useLocalState("studio.drawer-width", 380);
  const [drawerTab, setDrawerTab] = useLocalState<DrawerTab>("studio.drawer-tab", "inspector");
  const [active, setActive] = useState("Pipelines");
  const [selectedNode, setSelectedNode] = useState("dense");
  const [syncState, setSyncState] = useState<SyncState>("saved");
  const [proposal, setProposal] = useState<"idle" | "proposed" | "accepted" | "rejected">("idle");
  const [running, setRunning] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);

  const headers = useMemo(() => ({ "Content-Type": "application/json", "X-Tenant-Id": settings.tenant, "X-User-Id": settings.user, "X-Local-Admin-Token": settings.token }), [settings]);
  const refresh = async () => {
    try {
      const [catalog, history] = await Promise.all([fetch(`${API}/components`), fetch(`${API}/runs`, { headers })]);
      if (!catalog.ok || !history.ok) throw new Error("Local API unavailable");
      setComponents(await catalog.json()); setRuns(await history.json()); setSyncState("saved");
    } catch { setSyncState("offline"); }
  };
  useEffect(() => { refresh(); }, [headers]);
  useEffect(() => { const listener = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setPaletteOpen(true); } }; window.addEventListener("keydown", listener); return () => window.removeEventListener("keydown", listener); }, []);
  const run = async () => {
    setRunning(true); setSyncState("syncing");
    try {
      const response = await fetch(`${API}/runs`, { method: "POST", headers, body: JSON.stringify({ question }) });
      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      setAnswer(`${result.answer}\n\nCitations: ${result.citations.map((item: { id: string }) => item.id).join(", ") || "none"}`);
      setDrawerTab("activity"); setDrawerOpen(true); await refresh();
    } catch { setAnswer("The local runtime could not be reached. Your question remains saved locally; open Data & Trust to check the local connection."); setSyncState("offline"); }
    finally { setRunning(false); }
  };
  const command = (action: string) => { if (action.startsWith("Run")) run(); else if (action.includes("Explain")) { setDrawerTab("assistant"); setDrawerOpen(true); setProposal("proposed"); } else if (action.includes("Trust")) { setDrawerTab("settings"); setDrawerOpen(true); } else { setDrawerTab("diagnostics"); setDrawerOpen(true); } };
  const latest = runs[0];
  return <main className={`app-shell ${collapsed ? "sidebar-collapsed" : ""} ${drawerOpen && drawerMode === "docked" ? "drawer-docked" : ""}`} style={{ "--drawer-width": `${drawerWidth}px` } as CSSProperties}>
    <header className="topbar"><button className="icon-button mobile-nav" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle navigation">☰</button><div className="topbar-title"><span className="workspace-dot" />RAG Engineering Workbench <small>Local workspace</small></div><div className="topbar-actions"><SyncStatus state={syncState} /><button className="command-trigger" onClick={() => setPaletteOpen(true)}>⌘ <span>Search commands</span><kbd>⌘K</kbd></button><button className="quiet-button" onClick={() => { setDrawerTab("assistant"); setDrawerOpen(true); }}>Ask AI</button><button className="primary-button" onClick={run} disabled={running}>{running ? "Running…" : "Run"}</button></div></header>
    <NavigationSidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} active={active} onNavigate={(item) => { setActive(item); if (item === "Data & Trust") { setDrawerTab("settings"); setDrawerOpen(true); } }} />
    <PrimaryCanvas components={components} run={latest} question={question} answer={answer} running={running} selectedNode={selectedNode} proposal={proposal} onQuestion={setQuestion} onRun={run} onSelectNode={(node) => { setSelectedNode(node); setDrawerTab("inspector"); setDrawerOpen(true); }} onProposal={setProposal} />
    <ContextDrawer open={drawerOpen} mode={drawerMode} width={drawerWidth} tab={drawerTab} run={latest} selectedNode={selectedNode} settings={settings} onClose={() => setDrawerOpen(false)} onMode={setDrawerMode} onTab={setDrawerTab} onResize={setDrawerWidth} onSettings={setSettings} onPropose={() => { setProposal("proposed"); setDrawerTab("assistant"); }} />
    <footer className="command-surface"><button className="command-entry" onClick={() => setPaletteOpen(true)}>⌘ Command</button><span>Current context: <b>baseline</b> · <b>{selectedNode}</b> · approved references only</span><button className="drawer-toggle" onClick={() => setDrawerOpen(!drawerOpen)}>{drawerOpen ? "Hide context" : "Show context"}</button></footer>
    <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} onAction={command} />
  </main>;
}
