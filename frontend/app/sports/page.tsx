"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  Clock,
  Filter,
  MapPin,
  Trophy,
  UserCheck,
  UserPlus,
  Users,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type Game = {
  id: number;
  tournament_id: number;
  tournament: string;
  name: string;
  category: string;
  venue: string;
  starts_at: string;
  duration_minutes: number;
  capacity: number;
  enrolled: number;
  seats_left: number;
  registration_closes_at?: string | null;
};

export default function SportsCatalogue() {
  const { user } = useRole();
  const [games, setGames] = useState<Game[]>([]);
  const [myGames, setMyGames] = useState<number[]>([]);
  const [myWaiting, setMyWaiting] = useState<number[]>([]);
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const data = await api("/dashboard");
      setGames(data.games || []);
      const mine = (data.my_games || []).map((x: any) => x.game_id);
      setMyGames(mine);
      const waiting = (data.my_waiting || []).map((x: any) => x.game_id);
      setMyWaiting(waiting);
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleEnroll(gameId: number) {
    setError("");
    setNotice("");
    setBusy(gameId);
    try {
      const res = await api("/enroll-single", {
        method: "POST",
        body: JSON.stringify({ game_id: gameId }),
      });
      setNotice(`Enrolled successfully in ${res.game_name}!`);
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleJoinWaitingList(gameId: number) {
    setError("");
    setNotice("");
    setBusy(gameId);
    try {
      const res = await api("/waiting-list", {
        method: "POST",
        body: JSON.stringify({ game_id: gameId }),
      });
      setNotice(`Joined waiting list at position #${res.position}. You will be promoted automatically if a spot opens!`);
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleWithdraw(gameId: number) {
    if (!window.confirm("Are you sure you want to withdraw from this event? Your spot will be offered to the next student in line.")) {
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
        setNotice(`Withdrawn successfully. Promoted waiting list student ${res.promoted.name} to the roster!`);
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

  const categories = ["all", "Athletics", "Racquet", "Mind Sports", "Team Games", "Other"];

  const filtered = games.filter((g) => {
    const matchCat =
      category === "all" ||
      g.category?.toLowerCase() === category.toLowerCase() ||
      g.name.toLowerCase().includes(category.toLowerCase());
    const matchSearch =
      !search ||
      g.name.toLowerCase().includes(search.toLowerCase()) ||
      g.venue.toLowerCase().includes(search.toLowerCase()) ||
      g.tournament.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  return (
    <>
      <PageTitle
        eyebrow="SPORTS CATALOGUE"
        title="College Sports Events"
        accent="& Tournament Fixtures"
        description="Browse competitive inter-faction sports including Athletics, Badminton, Chess, Table Tennis, Football, and Basketball. Enroll or join the waiting list."
        action={user?.role === "admin" ? "Manage Events" : "View My Events"}
        href={user?.role === "admin" ? "/tournament" : "/my-events"}
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

      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div className="search-field" style={{ maxWidth: 300 }}>
          <input
            placeholder="Search sport, venue, tournament…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={"tag " + (category === c ? "blue" : "neutral")}
              style={{ cursor: "pointer", border: 0, padding: "6px 12px", textTransform: "capitalize" }}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="arena-grid-3">
        {filtered.map((g) => {
          const isEnrolled = myGames.includes(g.id);
          const isWaiting = myWaiting.includes(g.id);
          const isFull = g.seats_left <= 0;
          const capPercent = Math.min(100, Math.round((g.enrolled / g.capacity) * 100));

          return (
            <div className="sport-card" key={g.id}>
              <div className="sport-header">
                <div>
                  <Tag tone={isEnrolled ? "green" : isWaiting ? "gold" : "blue"}>
                    {g.category || "Tournament Sport"}
                  </Tag>
                  <h3 className="sport-title" style={{ marginTop: 8 }}>
                    {g.name}
                  </h3>
                  <small style={{ color: "var(--muted)" }}>{g.tournament}</small>
                </div>
                {isEnrolled && (
                  <Tag tone="green">
                    <UserCheck size={12} /> Enrolled
                  </Tag>
                )}
                {isWaiting && (
                  <Tag tone="gold">
                    <Clock size={12} /> Waiting List
                  </Tag>
                )}
              </div>

              <div className="sport-meta">
                <span>
                  <CalendarDays size={14} />{" "}
                  {new Date(g.starts_at.replace(" ", "T") + "Z").toLocaleString([], {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </span>
                <span>
                  <MapPin size={14} /> {g.venue}
                </span>
                <span>
                  <Clock size={14} /> {g.duration_minutes} mins
                </span>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>
                  <span>Capacity: {g.enrolled} / {g.capacity}</span>
                  <b>{isFull ? "FULL CAPACITY" : `${g.seats_left} spots left`}</b>
                </div>
                <div className="capacity-bar-bg">
                  <div
                    className={"capacity-bar-fill " + (isFull ? "warning" : "")}
                    style={{ width: `${capPercent}%` }}
                  />
                </div>
              </div>

              <div className="sport-footer">
                {user?.role === "student" && (
                  <>
                    {isEnrolled ? (
                      <button
                        className="button secondary-button"
                        style={{ color: "#e86363", borderColor: "rgba(232,99,99,0.35)" }}
                        disabled={busy === g.id}
                        onClick={() => handleWithdraw(g.id)}
                      >
                        Withdraw
                      </button>
                    ) : isWaiting ? (
                      <button
                        className="button secondary-button"
                        disabled
                        style={{ opacity: 0.8 }}
                      >
                        In Queue (Position #{myWaiting.indexOf(g.id) + 1})
                      </button>
                    ) : isFull ? (
                      <button
                        className="button secondary-button"
                        style={{ borderColor: "var(--gold)", color: "var(--gold)" }}
                        disabled={busy === g.id}
                        onClick={() => handleJoinWaitingList(g.id)}
                      >
                        <UserPlus size={15} /> Join Waiting List
                      </button>
                    ) : (
                      <button
                        className="button primary-button"
                        disabled={busy === g.id}
                        onClick={() => handleEnroll(g.id)}
                      >
                        <UserCheck size={15} /> Enroll in Sport
                      </button>
                    )}
                  </>
                )}
                {user?.role === "admin" && (
                  <Link href={`/results?game_id=${g.id}`} className="button secondary-button">
                    Enter Scores & Results
                  </Link>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {!filtered.length && (
        <Card>
          <div className="empty-state">
            <Trophy size={28} style={{ opacity: 0.5, marginBottom: 8 }} />
            <p>No sports events matched your filter. Check back soon or search another category.</p>
          </div>
        </Card>
      )}
    </>
  );
}
