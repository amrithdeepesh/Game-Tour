"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  Clock,
  MapPin,
  Trophy,
  Users,
  CheckCircle2,
  AlertCircle,
  Activity,
  ArrowRight,
  XCircle,
} from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type EnrolledGame = {
  user_id: number;
  game_id: number;
  game: string;
  category: string;
  venue: string;
  starts_at: string;
  capacity: number;
  tournament: string;
  display_name: string;
  faction: string;
};

type WaitingItem = {
  id: number;
  game_id: number;
  game_name: string;
  venue: string;
  starts_at: string;
  position: number;
  status: string;
  tournament_name: string;
};

type MatchItem = {
  id: number;
  game_name: string;
  match_name: string;
  round_number: number;
  venue: string;
  starts_at: string;
  status: string;
  score1: number;
  score2: number;
  p1_name: string;
  p2_name: string;
  p1_faction: string;
  p2_faction: string;
  winner_name: string;
};

export default function MyEventsPage() {
  const { user } = useRole();
  const [enrolled, setEnrolled] = useState<EnrolledGame[]>([]);
  const [waiting, setWaiting] = useState<WaitingItem[]>([]);
  const [myMatches, setMyMatches] = useState<MatchItem[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const [dash, waitData, matchData] = await Promise.all([
        api("/dashboard"),
        api("/waiting-list"),
        api("/matches"),
      ]);
      setEnrolled(dash.my_games || []);
      setWaiting(waitData.waiting_list || []);
      // Filter matches where current user is a participant
      const allMatches: MatchItem[] = matchData.matches || [];
      const userMatches = allMatches.filter(
        (m: any) =>
          m.p1_id === user?.id ||
          m.p2_id === user?.id ||
          (user?.name && (m.p1_name === user.name || m.p2_name === user.name))
      );
      setMyMatches(userMatches.length ? userMatches : allMatches.slice(0, 3));
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, [user]);

  async function handleWithdraw(gameId: number) {
    if (!window.confirm("Are you sure you want to withdraw from this sport? Your spot will be released to the next queued student.")) {
      return;
    }
    setError("");
    setNotice("");
    setBusy(gameId);
    try {
      const res = await api("/withdraw", {
        method: "POST",
        body: JSON.stringify({ game_id: gameId }),
      });
      if (res.promoted) {
        setNotice(`Withdrawn successfully. Student ${res.promoted.name} on the waiting list was automatically enrolled!`);
      } else {
        setNotice("Withdrawn successfully.");
      }
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleCancelWaiting(waitingId: number) {
    try {
      await api(`/waiting-list/${waitingId}`, { method: "DELETE" });
      setNotice("Removed from waiting list.");
      await load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageTitle
        eyebrow="STUDENT PORTAL"
        title="My Registered Sports"
        accent="& Match Schedule"
        description="Track your confirmed sports registrations, check your queue position on waiting lists, and monitor upcoming match times and venues."
        action="Browse More Sports"
        href="/sports"
      />

      {error && (
        <div className="conflict-alert" role="alert">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {notice && (
        <div className="notice" style={{ borderColor: "var(--green)", background: "var(--green-soft)", color: "var(--green)" }} role="status">
          <CheckCircle2 size={16} style={{ verticalAlign: "middle", marginRight: 8 }} />
          <b>{notice}</b>
        </div>
      )}

      {/* Confirmed Registrations */}
      <Card style={{ marginBottom: 24 }}>
        <SectionHeading
          title="Confirmed Event Entries"
          aside={<Tag tone="green">{enrolled.length} / 5 Enrolled</Tag>}
        />
        {enrolled.length ? (
          <div className="timeline-list">
            {enrolled.map((item) => (
              <article className="timeline-event" key={item.game_id}>
                <span className="timeline-marker">
                  <Trophy size={17} />
                </span>
                <div className="timeline-body">
                  <div className="timeline-meta">
                    <span>
                      {new Date(item.starts_at.replace(" ", "T") + "Z").toLocaleString([], {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </span>
                    <span>·</span>
                    <span>{item.tournament}</span>
                  </div>
                  <h3>{item.game}</h3>
                  <p>
                    <MapPin size={14} /> {item.venue}
                    <span style={{ margin: "0 8px" }}>·</span>
                    <Users size={14} /> Faction: <b>{item.faction}</b>
                  </p>
                </div>
                <div>
                  <button
                    className="button secondary-button"
                    style={{ color: "#e86363", borderColor: "rgba(232,99,99,0.3)" }}
                    disabled={busy === item.game_id}
                    onClick={() => handleWithdraw(item.game_id)}
                  >
                    Withdraw
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Trophy size={26} style={{ opacity: 0.5, marginBottom: 8 }} />
            <p>You have not registered for any sports events yet.</p>
            <Link href="/sports" className="button primary-button" style={{ marginTop: 12 }}>
              Explore Sports Catalogue
            </Link>
          </div>
        )}
      </Card>

      {/* Waiting Lists */}
      {waiting.length > 0 && (
        <Card style={{ marginBottom: 24 }}>
          <SectionHeading
            title="Waiting List Queue"
            aside={<Tag tone="gold">{waiting.length} Waiting</Tag>}
          />
          <div className="timeline-list">
            {waiting.map((item) => (
              <article className="timeline-event" key={item.id}>
                <span className="timeline-marker" style={{ background: "var(--gold-soft)", color: "var(--gold)" }}>
                  <Clock size={17} />
                </span>
                <div className="timeline-body">
                  <div className="timeline-meta">
                    <span>Queue Position: #{item.position}</span>
                    <span>·</span>
                    <span>Status: {item.status.toUpperCase()}</span>
                  </div>
                  <h3>{item.game_name}</h3>
                  <p>
                    <MapPin size={14} /> {item.venue} · Scheduled for{" "}
                    {new Date(item.starts_at.replace(" ", "T") + "Z").toLocaleString([], {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </p>
                </div>
                <div>
                  <button
                    className="button secondary-button"
                    onClick={() => handleCancelWaiting(item.id)}
                  >
                    <XCircle size={15} /> Leave Queue
                  </button>
                </div>
              </article>
            ))}
          </div>
        </Card>
      )}

      {/* Match Fixtures */}
      <Card>
        <SectionHeading
          title="Your Upcoming & Ongoing Matches"
          aside={
            <Link href="/live" className="text-link">
              View All Live Games <ArrowRight size={14} />
            </Link>
          }
        />
        {myMatches.length ? (
          <div className="arena-grid-2">
            {myMatches.map((m) => (
              <div
                key={m.id}
                style={{
                  padding: 16,
                  borderRadius: 12,
                  border: "1px solid var(--line)",
                  background: "var(--surface-2)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted)" }}>
                    {m.game_name} · Round {m.round_number}
                  </span>
                  <span
                    className={`live-badge ${m.status}`}
                    style={{ textTransform: "uppercase" }}
                  >
                    {m.status === "ongoing" && <i className="live-pulse" />}
                    {m.status}
                  </span>
                </div>

                <div style={{ font: "800 16px Manrope" }}>{m.match_name}</div>

                <div className="scoreboard" style={{ margin: "4px 0", padding: 12 }}>
                  <div className="scoreboard-team">
                    <b>{m.p1_name || "Team / Participant 1"}</b>
                    <small style={{ color: "var(--muted)" }}>{m.p1_faction || "TBD"}</small>
                  </div>
                  <div className="scoreboard-score">
                    {m.score1} : {m.score2}
                  </div>
                  <div className="scoreboard-team right">
                    <b>{m.p2_name || "Team / Participant 2"}</b>
                    <small style={{ color: "var(--muted)" }}>{m.p2_faction || "TBD"}</small>
                  </div>
                </div>

                <div style={{ fontSize: 12, color: "var(--muted)", display: "flex", alignItems: "center", gap: 6 }}>
                  <MapPin size={13} /> {m.venue}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <Activity size={24} style={{ opacity: 0.5, marginBottom: 6 }} />
            <p>No active match fixtures scheduled for your entered events yet.</p>
          </div>
        )}
      </Card>
    </>
  );
}
