"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  BarChart3,
  BookOpen,
  Boxes,
  CalendarDays,
  Command,
  Cpu,
  Flag,
  Flame,
  LogOut,
  Medal,
  Moon,
  Search,
  Shield,
  Sun,
  Trophy,
  UserCheck,
  UserRound,
  Users,
} from "lucide-react";
import { api, RoleContext, type User } from "./role";

const studentNav = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/sports", label: "Sports Catalogue", icon: Trophy },
  { href: "/my-events", label: "My Events", icon: CalendarDays },
  { href: "/factions", label: "Factions", icon: Shield },
  { href: "/leaderboard", label: "Leaderboard", icon: Medal },
  { href: "/faction-leaderboard", label: "Faction Standings", icon: Flag },
  { href: "/profile", label: "My Profile", icon: UserRound },
  { href: "/lab", label: "Search & Find", icon: Search },
];

const adminNav = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/tournament", label: "Event Management", icon: Trophy },
  { href: "/factions", label: "Faction Management", icon: Shield },
  { href: "/participants", label: "Students & Roster", icon: Users },
  { href: "/results", label: "Record Results", icon: Medal },
  { href: "/schedule", label: "Timetable & Scheduling", icon: CalendarDays },
  { href: "/leaderboard", label: "Student Standings", icon: Medal },
  { href: "/faction-leaderboard", label: "Faction Standings", icon: Flag },
  { href: "/lab", label: "Search & Find", icon: Search },
];

export default function SiteShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [dark, setDark] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const publicPage = path === "/login" || path === "/register" || path === "/logout" || path === "/signout";

  async function refresh() {
    try {
      const result = await api("/me");
      setUser(result.user || null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const saved = localStorage.getItem("arena-theme");
    setDark(saved ? saved === "dark" : true);
    void refresh();
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("arena-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    if (!loading && !publicPage && !user) router.replace("/login");
    if (!loading && publicPage && user && path !== "/logout" && path !== "/signout") router.replace("/");
  }, [loading, user, path]);

  async function logout() {
    try {
      await api("/logout", { method: "POST" });
    } catch {
      // Ignore network errors and proceed with local logout
    } finally {
      setUser(null);
      window.location.href = "/login";
    }
  }

  if (publicPage) {
    return (
      <RoleContext.Provider
        value={{ role: user?.role || "student", user, loading, refresh, logout }}
      >
        <main className="auth-page">{children}</main>
      </RoleContext.Provider>
    );
  }

  if (loading || !user) {
    return (
      <div className="auth-loading" style={{ display: "grid", placeItems: "center", minHeight: "100vh", gap: 16 }}>
        <div className="arena-logo">
          <span className="arena-badge"><Flame size={20} /></span>
          <span>ARENA</span>
        </div>
        <div>Loading college sports workspace…</div>
      </div>
    );
  }

  const nav = user.role === "admin" ? adminNav : studentNav;
  const active = nav.find((item) =>
    item.href === "/" ? path === "/" : path.startsWith(item.href)
  );

  return (
    <RoleContext.Provider
      value={{ role: user.role, user, loading, refresh, logout }}
    >
      <div className="app-shell">
        <aside className="sidebar">
          <Link href="/" className="arena-logo" style={{ textDecoration: "none", marginBottom: 12 }}>
            <span className="arena-badge"><Flame size={20} /></span>
            <div style={{ display: "flex", flexDirection: "column", lineHeight: 1 }}>
              <span style={{ fontWeight: 900, letterSpacing: "-0.5px" }}>ARENA</span>
              <span className="arena-sub">COLLEGE SPORTS</span>
            </div>
          </Link>
          <div className="nav-label" style={{ marginTop: 14 }}>WORKSPACE</div>
          <nav className="side-nav">
            {nav.map(({ href, label, icon: Icon }) => (
              <Link
                href={href}
                key={href}
                className={"nav-link " + (active?.href === href ? "is-active" : "")}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <div className="profile">
              <span className="avatar">{user.name.slice(0, 2).toUpperCase()}</span>
              <span>
                <b>{user.name}</b>
                <small>
                  {user.role === "admin"
                    ? "Administrator"
                    : `${user.faction || "Independent"} · Student`}
                </small>
              </span>
            </div>
          </div>
        </aside>
        <section className="main-area">
          <header className="topbar">
            <div className="breadcrumbs">
              <Link href="/">ARENA</Link>
              <span>/</span>
              <b>{active?.label || "Tournament Portal"}</b>
            </div>
            <div className="topbar-actions">
              <span className="role-pill">
                {user.role === "admin" ? "ADMINISTRATOR" : "STUDENT"}
              </span>
              <button
                className="theme-toggle"
                onClick={() => setDark((value) => !value)}
              >
                {dark ? <Sun size={17} /> : <Moon size={17} />}
                <span>{dark ? "Light" : "Dark"}</span>
              </button>
              <button className="theme-toggle" onClick={logout} title="Sign out">
                <LogOut size={16} />
                <span>Sign out</span>
              </button>
            </div>
          </header>
          <main className="page-content">{children}</main>
        </section>
      </div>
    </RoleContext.Provider>
  );
}
