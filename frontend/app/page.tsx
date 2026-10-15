"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  Bell,
  Boxes,
  CalendarDays,
  Clock3,
  Flag,
  Flame,
  MapPin,
  Medal,
  Search,
  Shield,
  Trophy,
  UserCheck,
  UserRound,
  Users,
} from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "./components/ui";
import { api, useRole } from "./components/role";

type Game = {
  id: number;
  game_id?: number;
  name: string;
  tournament: string;
  starts_at: string;
  venue: string;
  enrolled: number;
  capacity: number;
  category: string;
};

export default function Dashboard() {
  const { user } = useRole();
  const isAdmin = user?.role === "admin";
  const [games, setGames] = useState<Game[]>([]);
  const [mine, setMine] = useState<Game[]>([]);
  const [liveMatches, setLiveMatches] = useState<any[]>([]);
  const [factions, setFactions] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [error, setError] = useState("");

  useEffect(() => {
    api("/dashboard")
      .then((d) => {
        setGames(d.games || []);
        setMine(d.my_games || []);
        setLiveMatches(d.live_matches || []);
        setFactions(d.factions || []);
        setAnnouncements(d.announcements || []);
        setStats(d.stats || {});
      })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="simple-dashboard">
      <PageTitle
        eyebrow={isAdmin ? "ADMINISTRATOR COMMAND CENTER" : "STUDENT ATHLETE DASHBOARD"}
        title={`Welcome, ${user?.name?.split(" ")[0] || "Athlete"}`}
        accent="· ARENA 2026"
        description={
          isAdmin
            ? "Manage tournaments, schedule sport fixtures, track live ongoing matches, and record authoritative results."
            : `Faction: ${user?.faction || "Open"} · Browse sports events, enroll, track live match scores, and review leaderboards.`
        }
        action={isAdmin ? "Event Management" : "Sports Catalogue"}
        href={isAdmin ? "/tournament" : "/sports"}
      />

      {error && (
        <div className="conflict-alert" role="alert">
          <b>Dashboard could not load: </b>
          <span>{error}</span>
        </div>
      )}

      {/* Announcements Banner */}
      {announcements.length > 0 && (
        <Card style={{ marginBottom: 18, borderLeft: "4px solid var(--blue)", background: "var(--surface-2)" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <span style={{ color: "var(--blue)", marginTop: 2 }}>
              <Bell size={18} />
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <b style={{ fontSize: 14 }}>{announcements[0].title}</b>
                <Tag tone="blue">{announcements[0].category}</Tag>
              </div>
              <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>
                {announcements[0].content}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Metrics Grid */}
      <div className="arena-grid-4" style={{ marginBottom: 20 }}>
        <Card className="dashboard-metric">
          <div className="metric-icon">
            <Trophy size={20} />
          </div>
          <div>
            <span className="metric-label">{isAdmin ? "Tournaments" : "My Events"}</span>
            <b style={{ display: "block" }}>{isAdmin ? (stats.tournaments || 0) : mine.length}</b>
            <small>{isAdmin ? "Active competitions" : "Confirmed entries"}</small>
          </div>
        </Card>

        <Card className="dashboard-metric">
          <div className="metric-icon" style={{ background: "var(--green-soft)", color: "var(--green)" }}>
            <CalendarDays size={20} />
          </div>
          <div>
            <span className="metric-label">Scheduled Sports</span>
            <b style={{ display: "block" }}>{stats.games || games.length}</b>
            <small>Across campus venues</small>
          </div>
        </Card>

        <Card className="dashboard-metric">
          <div className="metric-icon" style={{ background: "var(--gold-soft)", color: "var(--gold)" }}>
            <MapPin size={20} />
          </div>
          <div>
            <span className="metric-label">Campus Venues</span>
            <b style={{ display: "block" }}>5</b>
            <small>Sports grounds & halls</small>
          </div>
        </Card>

        <Card className="dashboard-metric">
          <div className="metric-icon" style={{ background: "rgba(138,112,211,0.15)", color: "var(--violet)" }}>
            <Shield size={20} />
          </div>
          <div>
            <span className="metric-label">Factions</span>
            <b style={{ display: "block" }}>{stats.factions || factions.length || 4}</b>
            <small>Competing houses</small>
          </div>
        </Card>
      </div>

      {/* Schedule Panel */}
      <Card className="dashboard-panel schedule-panel" style={{ marginBottom: 20 }}>
        <div className="dashboard-panel-heading">
          <div>
            <span className="eyebrow">UPCOMING SCHEDULE</span>
            <h2>{isAdmin ? "Tournament Fixture Timeline" : "Upcoming Games · Your Selections Highlighted"}</h2>
          </div>
          <Tag tone="green">{games.length} scheduled</Tag>
        </div>

        {games.length ? (
          <div className="timeline-list">
            {games.slice(0, 5).map((g) => (
              <article key={g.id} className="timeline-event">
                <span className="timeline-marker">
                  <CalendarDays size={17} />
                </span>
                <div className="timeline-body">
                  <div className="timeline-meta">
                    <span>
                      {new Date(g.starts_at.replace(" ", "T") + "Z").toLocaleString([], {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </span>
                    <span>·</span>
                    <span>{g.tournament}</span>
                  </div>
                  <h3>
                    {g.name}{" "}
                    {!isAdmin && mine.some((m) => m.game_id === g.id) && (
                      <Tag tone="green">You are entered</Tag>
                    )}
                  </h3>
                  <p>
                    <MapPin size={14} /> {g.venue}
                    <span style={{ margin: "0 8px" }}>·</span>
                    <Users size={14} /> {g.enrolled} / {g.capacity} participants
                  </p>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Clock3 size={24} style={{ opacity: 0.5, marginBottom: 8 }} />
            <p>No games scheduled yet.</p>
          </div>
        )}

        <div className="dashboard-footer-link" style={{ marginTop: 14 }}>
          <Link href={isAdmin ? "/tournament" : "/sports"}>
            {isAdmin ? "Manage tournament schedule" : "Browse all sports in catalogue"}{" "}
            <ArrowRight size={14} />
          </Link>
        </div>
      </Card>

      {/* Quick Navigation Links */}
      <div className="dashboard-quicklinks">
        <Link href="/sports">
          <Trophy size={16} /> Sports Catalogue
        </Link>
        <Link href="/schedule">
          <CalendarDays size={16} /> Timetable & Schedule
        </Link>
        <Link href="/factions">
          <Shield size={16} /> Factions
        </Link>
        <Link href="/leaderboard">
          <Medal size={16} /> Leaderboards
        </Link>
        <Link href="/lab">
          <Search size={16} /> Search & Find
        </Link>
      </div>
    </div>
  );
}
