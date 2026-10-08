"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, Boxes, Command, Moon, Sun, Trophy, Users, WandSparkles } from "lucide-react";

const nav = [
  { href: "/", label: "Overview", icon: BarChart3 },
  { href: "/tournament", label: "Tournament", icon: Trophy },
  { href: "/participants", label: "Participants", icon: Users },
  { href: "/structures", label: "Data structures", icon: Boxes },
  { href: "/algorithms", label: "Algorithms", icon: WandSparkles },
  { href: "/activity", label: "Activity", icon: Activity },
];

export default function SiteShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const saved = localStorage.getItem("arena-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(saved ? saved === "dark" : prefersDark);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("arena-theme", dark ? "dark" : "light");
  }, [dark]);
  return <div className="app-shell">
    <aside className="sidebar">
      <Link href="/" className="brand"><span className="brand-mark"><Command size={18}/></span><span>arena<span className="brand-dot">.</span></span></Link>
      <div className="workspace-switch"><span className="workspace-icon">GT</span><span><b>Game Tour DS</b><small>Workspace</small></span><span className="chevron">v</span></div>
      <div className="nav-label">WORKSPACE</div>
      <nav className="side-nav">{nav.map(({href,label,icon:Icon})=><Link href={href} key={href} className={"nav-link "+(path===href?"is-active":"")}><Icon size={17}/><span>{label}</span></Link>)}</nav>
      <div className="nav-label project-label">YOUR PROJECTS <span>+</span></div>
      <div className="project-link"><i className="project-dot purple"/> Spring Invitational</div>
      <div className="project-link"><i className="project-dot orange"/> Campus Cup</div>
      <div className="sidebar-bottom"><div className="help-card"><div className="help-icon">?</div><b>Keep exploring</b><p>See how each phase powers the tournament.</p><Link href="/structures">Open phase guide <span>→</span></Link></div><div className="profile"><span className="avatar">AD</span><span><b>Amrith Deepesh</b><small>Administrator</small></span></div></div>
    </aside>
    <section className="main-area">
      <header className="topbar"><div className="breadcrumbs"><Link href="/">Game Tour DS</Link><span>/</span><b>{nav.find(n=>n.href===path)?.label||"Overview"}</b></div><div className="topbar-actions"><span className="live-status"><i/> API ready</span><button className="theme-toggle" onClick={()=>setDark(v=>!v)} aria-label={dark?"Switch to light theme":"Switch to dark theme"} title={dark?"Switch to light theme":"Switch to dark theme"}>{dark?<Sun size={17}/>:<Moon size={17}/>}<span>{dark?"Light":"Dark"} mode</span></button><span className="avatar small-avatar">AD</span></div></header>
      <main className="page-content">{children}</main>
    </section>
  </div>;
}
