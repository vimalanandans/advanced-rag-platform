type Props = { collapsed: boolean; onToggle: () => void; active: string; onNavigate: (item: string) => void };

const items = ["Pipelines", "Corpora", "Components", "Datasets", "Experiments"];

export function NavigationSidebar({ collapsed, onToggle, active, onNavigate }: Props) {
  return <aside className={`navigation-sidebar ${collapsed ? "collapsed" : ""}`} aria-label="Workspace navigation">
    <div className="workspace-switcher"><span className="workspace-mark">RW</span>{!collapsed && <span><b>Local workspace</b><small>Engineering</small></span>}<button className="icon-button" title={collapsed ? "Expand navigation" : "Collapse navigation"} aria-label={collapsed ? "Expand navigation" : "Collapse navigation"} onClick={onToggle}>☰</button></div>
    <button className="create-button" onClick={() => onNavigate("New pipeline")} title="Create pipeline"><span>＋</span>{!collapsed && "Create"}</button>
    <nav>{items.map((item, index) => <button key={item} title={item} className={active === item ? "nav-item active" : "nav-item"} onClick={() => onNavigate(item)}><span className="nav-icon">{["⌘", "▤", "◈", "▦", "◌"][index]}</span>{!collapsed && item}</button>)}</nav>
    {!collapsed && <section className="sidebar-section"><span className="eyebrow">RECENT</span><button className="recent-item active" onClick={() => onNavigate("baseline")}>local-evidence-baseline<small>1.0.0 · local</small></button><button className="recent-item" onClick={() => onNavigate("retrieval-lab")}>retrieval-lab<small>draft · local</small></button></section>}
    <div className="sidebar-footer"><button className="nav-item" title="Data & Trust" onClick={() => onNavigate("Data & Trust")}><span className="nav-icon">♧</span>{!collapsed && "Data & Trust"}</button><button className="nav-item" title="Help and keyboard shortcuts" onClick={() => onNavigate("Help")}><span className="nav-icon">?</span>{!collapsed && "Help"}</button></div>
  </aside>;
}
