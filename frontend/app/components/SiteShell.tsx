"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, BookOpen, Boxes, Command, Moon, Sun, Trophy, Users, Medal } from "lucide-react";
import { RoleContext, type UserRole } from "./role";

const nav = [
  { href:"/",label:"Overview",icon:BarChart3 },
  { href:"/tournament",label:"Games & results",icon:Trophy },
  { href:"/participants",label:"Participants",icon:Users },
  { href:"/leaderboard",label:"Leaderboard",icon:Medal },
  { href:"/structures",label:"Phase 1–2",icon:Boxes },
  { href:"/algorithms",label:"Phase 3–4",icon:BookOpen },
];
export default function SiteShell({children}:{children:React.ReactNode}){
 const path=usePathname();const [dark,setDark]=useState(false);const [role,setRole]=useState<UserRole>("student");
 useEffect(()=>{const theme=localStorage.getItem("arena-theme");setDark(theme?theme==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches);const saved=localStorage.getItem("arena-role");if(saved==="admin"||saved==="student")setRole(saved)},[]);
 useEffect(()=>{document.documentElement.dataset.theme=dark?"dark":"light";localStorage.setItem("arena-theme",dark?"dark":"light")},[dark]);
 useEffect(()=>{localStorage.setItem("arena-role",role)},[role]);
 return <RoleContext.Provider value={{role,setRole}}><div className="app-shell"><aside className="sidebar">
  <Link href="/" className="brand"><span className="brand-mark"><Command size={19}/></span><span>arena<span className="brand-dot">.</span></span></Link>
  <div className="workspace-switch"><span className="workspace-icon">GT</span><span><b>Game Tour DS</b><small>Tournament workspace</small></span></div>
  <div className="nav-label">MAIN MENU</div><nav className="side-nav">{nav.map(({href,label,icon:Icon})=><Link href={href} key={href} className={"nav-link "+((href==="/" ? path==="/" : path.startsWith(href))?"is-active":"")}><Icon size={18}/><span>{label}</span></Link>)}</nav>
  <div className="sidebar-bottom"><div className="help-card"><div className="eyebrow">PROJECT PHASES</div><b>Learn while you play</b><p>Explore each data structure in the tournament workflow.</p><Link href="/structures">Open learning lab <span>→</span></Link></div><div className="profile"><span className="avatar">{role==="admin"?"AD":"ST"}</span><span><b>{role==="admin"?"Tournament admin":"Student view"}</b><small>{role==="admin"?"Manage games and results":"Join games and track scores"}</small></span></div></div>
 </aside><section className="main-area"><header className="topbar"><div className="breadcrumbs"><Link href="/">Game Tour DS</Link><span>/</span><b>{nav.find(n=>n.href==="/" ? path==="/" : path.startsWith(n.href))?.label||"Workspace"}</b></div><div className="topbar-actions"><div className="role-switch" aria-label="Choose user role"><button className={role==="student"?"selected":""} onClick={()=>setRole("student")}>Student</button><button className={role==="admin"?"selected":""} onClick={()=>setRole("admin")}>Admin</button></div><button className="theme-toggle" onClick={()=>setDark(v=>!v)} aria-label={dark?"Switch to light theme":"Switch to dark theme"}>{dark?<Sun size={17}/>:<Moon size={17}/>}<span>{dark?"Light":"Dark"}</span></button></div></header><main className="page-content">{children}</main></section></div></RoleContext.Provider>;
}
