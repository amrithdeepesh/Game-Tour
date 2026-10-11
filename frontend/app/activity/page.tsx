"use client";

import { useEffect, useState } from "react";
import { CalendarDays, MapPin, Trophy, Users } from "lucide-react";
import { api } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type Game = {
  id: number; name: string; tournament: string; starts_at: string; venue: string;
  enrolled: number; capacity: number;
};

export default function ActivityPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [students, setStudents] = useState(0);
  const [enrolled, setEnrolled] = useState(0);
  const [error, setError] = useState("");

  async function load() {
    const data = await api("/dashboard");
    setGames(data.games || []);
    setStudents(data.stats?.students || 0);
    setEnrolled(data.stats?.enrolled || 0);
  }

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try { if (active) await load(); }
      catch (reason) { if (active) setError(reason instanceof Error ? reason.message : "Could not load the schedule."); }
    };
    void refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  return <>
    <PageTitle eyebrow="TOURNAMENT OVERVIEW" title="Game day" accent="at a glance." description="See the scheduled games, their locations, and how many students have signed up." action="Manage games" href="/tournament" />
    {error && <div className="notice" role="alert">{error}</div>}
    <div className="stat-grid compact-stats">
      <Card className="stat-card"><span className="stat-icon blue"><CalendarDays size={18}/></span><span className="stat-label">Scheduled games</span><b className="stat-value">{games.length}</b><small className="stat-caption">Across all tournaments</small></Card>
      <Card className="stat-card"><span className="stat-icon green"><Users size={18}/></span><span className="stat-label">Participants</span><b className="stat-value">{students}</b><small className="stat-caption">Student accounts</small></Card>
      <Card className="stat-card"><span className="stat-icon gold"><Trophy size={18}/></span><span className="stat-label">Game sign-ups</span><b className="stat-value">{enrolled}</b><small className="stat-caption">Submitted choices</small></Card>
    </div>
    <Card>
      <SectionHeading title="Upcoming games" aside={<Tag tone="green">Refreshes automatically</Tag>} />
      {games.length ? <div className="timeline-list">
        {games.map((game) => <article className="timeline-event" key={game.id}>
          <span className="timeline-marker"><CalendarDays size={17}/></span>
          <div className="timeline-body">
            <div className="timeline-meta">{new Date(game.starts_at.replace(" ", "T")).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })} · {game.tournament}</div>
            <h3>{game.name}</h3>
            <p><MapPin size={14}/> {game.venue} <span>·</span> <Users size={14}/> {game.enrolled} of {game.capacity} places filled</p>
          </div>
        </article>)}
      </div> : <div className="empty-state">No games are scheduled yet. Games added by the organizer will appear here.</div>}
    </Card>
  </>;
}
