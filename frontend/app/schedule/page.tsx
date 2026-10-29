"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  Clock,
  MapPin,
  Play,
  Save,
  Trophy,
  Users,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type Game = {
  id: number;
  name: string;
  venue: string;
  starts_at: string;
  duration_minutes: number;
  capacity: number;
  tournament: string;
  enrolled: number;
};

type GreedyCandidate = {
  id: number;
  name: string;
  venue: string;
  start: number;
  end: number;
  participants: string[];
  capacity: number;
  priority: number;
};

export default function SchedulingPage() {
  const { user } = useRole();
  const isAdmin = user?.role === "admin";
  const [games, setGames] = useState<Game[]>([]);
  const [activeTab, setActiveTab] = useState<"timetable" | "greedy">("timetable");

  // Greedy solver state
  const [candidates, setCandidates] = useState<GreedyCandidate[]>([
    { id: 1, name: "100m Sprint Heats", venue: "Athletics Track", start: 9.0, end: 10.5, participants: ["Aarav Nair", "Ishan Kapoor"], capacity: 20, priority: 3 },
    { id: 2, name: "Badminton Singles R1", venue: "Badminton Court", start: 9.5, end: 11.0, participants: ["Diya Menon", "Meera Rao"], capacity: 10, priority: 2 },
    { id: 3, name: "Basketball 3x3 Showcase", venue: "Basketball Court", start: 10.0, end: 11.5, participants: ["Rohan Shah", "Sana Khan"], capacity: 12, priority: 2 },
    { id: 4, name: "Relay 4x100m Final", venue: "Athletics Track", start: 10.0, end: 11.5, participants: ["Aarav Nair", "Vivaan Iyer"], capacity: 30, priority: 1 },
    { id: 5, name: "Cricket Championship Match", venue: "Cricket Ground", start: 11.0, end: 13.0, participants: ["Zoya Pillai", "Ishan Kapoor"], capacity: 22, priority: 2 },
    { id: 6, name: "Volleyball Clash", venue: "Volleyball Court", start: 11.5, end: 13.5, participants: ["Vivaan Iyer", "Diya Menon"], capacity: 25, priority: 1 },
    { id: 7, name: "Tennis Singles Finals", venue: "Tennis Court", start: 11.0, end: 12.5, participants: ["Meera Rao"], capacity: 8, priority: 3 },
    { id: 8, name: "Multi-Sport Grand Finals", venue: "Indoor Sports Complex", start: 14.0, end: 16.0, participants: ["Aarav Nair", "Rohan Shah"], capacity: 50, priority: 3 },
  ]);

  const [solverResult, setSolverResult] = useState<any>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await api("/dashboard");
      setGames(data.games || []);
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Conflict Detection in Existing Schedule
  const conflicts: string[] = [];
  for (let i = 0; i < games.length; i++) {
    for (let j = i + 1; j < games.length; j++) {
      const g1 = games[i];
      const g2 = games[j];
      if (g1.venue?.toLowerCase() === g2.venue?.toLowerCase()) {
        const s1 = new Date(g1.starts_at.replace(" ", "T") + "Z").getTime();
        const e1 = s1 + (g1.duration_minutes || 60) * 60000;
        const s2 = new Date(g2.starts_at.replace(" ", "T") + "Z").getTime();
        const e2 = s2 + (g2.duration_minutes || 60) * 60000;
        if (s1 < e2 && s2 < e1) {
          conflicts.push(`Venue Collision: '${g1.venue}' is double-booked between '${g1.name}' and '${g2.name}'!`);
        }
      }
    }
  }

  async function runGreedySolver() {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const res = await api("/ds-lab/phase4/greedy-schedule", {
        method: "POST",
        body: JSON.stringify({ candidates }),
      });
      setSolverResult(res);
      setNotice(`Greedy Algorithm allocated ${res.total_scheduled} events with 0 conflicts!`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function commitApprovedSchedule() {
    if (!solverResult?.scheduled?.length) return;
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const res = await api("/ds-lab/phase4/commit-schedule", {
        method: "POST",
        body: JSON.stringify({ approved_events: solverResult.scheduled, tournament_id: 5 }),
      });
      setNotice(`Successfully persisted ${res.count} approved fixtures into MySQL database!`);
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  // Group games by venue
  const venues = Array.from(new Set(games.map((g) => g.venue))).filter(Boolean);

  return (
    <>
      <PageTitle
        eyebrow="EVENT SCHEDULING & CONFLICT DETECTION"
        title="Tournament Timetable"
        accent="& Greedy Schedule Solver"
        description="View scheduled sports fixtures across campus venues, detect overlapping venue bookings and student schedule collisions, or execute the greedy scheduler to propose optimal collision-free schedules."
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

      {/* Conflict Warning Alerts */}
      {conflicts.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          {conflicts.map((c, idx) => (
            <div key={idx} className="conflict-alert" style={{ marginBottom: 8 }}>
              <AlertTriangle size={18} />
              <span>{c}</span>
            </div>
          ))}
        </div>
      )}

      {/* Mode Tabs */}
      <div className="ds-tabs">
        <button
          className={`ds-tab ${activeTab === "timetable" ? "active" : ""}`}
          onClick={() => setActiveTab("timetable")}
        >
          <CalendarDays size={16} /> Campus Timetable & Venue Lanes
        </button>
        <button
          className={`ds-tab ${activeTab === "greedy" ? "active" : ""}`}
          onClick={() => setActiveTab("greedy")}
        >
          <Sparkles size={16} /> Greedy Tournament Scheduler (Phase 4)
        </button>
      </div>

      {activeTab === "timetable" ? (
        <>
          <div className="arena-grid-2" style={{ marginBottom: 24 }}>
            {venues.map((venueName) => {
              const venueGames = games.filter((g) => g.venue === venueName);
              return (
                <Card key={venueName} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <SectionHeading
                    title={venueName}
                    aside={<Tag tone="blue">{venueGames.length} events</Tag>}
                  />
                  <div className="timeline-list">
                    {venueGames.map((g) => (
                      <article className="timeline-event" key={g.id}>
                        <span className="timeline-marker">
                          <CalendarDays size={16} />
                        </span>
                        <div className="timeline-body">
                          <div className="timeline-meta">
                            <span>
                              {new Date(g.starts_at.replace(" ", "T") + "Z").toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                            <span>·</span>
                            <span>{g.duration_minutes} min duration</span>
                          </div>
                          <h3>{g.name}</h3>
                          <p>
                            <Users size={13} /> {g.enrolled} / {g.capacity} participants
                          </p>
                        </div>
                      </article>
                    ))}
                  </div>
                </Card>
              );
            })}
          </div>

          {!venues.length && (
            <Card>
              <div className="empty-state">No scheduled games found in database.</div>
            </Card>
          )}
        </>
      ) : (
        /* Phase 4 Greedy Scheduler Integration */
        <div>
          <Card style={{ marginBottom: 20 }}>
            <SectionHeading
              title="Phase 4: Greedy Multi-Venue & Participant Scheduler"
              aside={<Tag tone="violet">Earliest Finish Time First (EFT)</Tag>}
            />
            <p className="muted-copy">
              The greedy algorithm prioritizes candidate requests by earliest finish time. For every candidate event,
              it strictly verifies that the venue is vacant and that none of the registered athletes have an
              overlapping match in another sport. Feasible events are accepted; colliding events are rejected with an explicit diagnostic reason.
            </p>

            <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
              <button
                className="button primary-button"
                onClick={runGreedySolver}
                disabled={busy}
              >
                <Play size={16} /> Execute Greedy Algorithm in Python
              </button>
              {isAdmin && solverResult?.scheduled?.length > 0 && (
                <button
                  className="button secondary-button"
                  style={{ borderColor: "var(--green)", color: "var(--green)" }}
                  onClick={commitApprovedSchedule}
                  disabled={busy}
                >
                  <Save size={16} /> Persist Approved Schedule to MySQL
                </button>
              )}
            </div>
          </Card>

          {/* Candidate Fixtures Table */}
          <Card style={{ marginBottom: 20 }}>
            <SectionHeading
              title="Candidate Event Requests"
              aside={<Tag>{candidates.length} candidates</Tag>}
            />
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>EVENT NAME</th>
                    <th>VENUE</th>
                    <th>TIME INTERVAL</th>
                    <th>PARTICIPANTS</th>
                    <th>PRIORITY</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((c) => (
                    <tr key={c.id}>
                      <td><b>{c.name}</b></td>
                      <td><MapPin size={12} style={{ verticalAlign: "middle" }} /> {c.venue}</td>
                      <td>{c.start}:00 – {c.end}:00</td>
                      <td>{c.participants.join(", ")}</td>
                      <td><Tag tone={c.priority === 3 ? "gold" : c.priority === 2 ? "blue" : "neutral"}>P{c.priority}</Tag></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Solver Results */}
          {solverResult && (
            <div className="arena-grid-2">
              {/* Accepted Events */}
              <Card>
                <SectionHeading
                  title="Accepted Feasible Schedule"
                  aside={<Tag tone="green">{solverResult.total_scheduled} Allocated</Tag>}
                />
                <div style={{ display: "grid", gap: 10 }}>
                  {solverResult.scheduled.map((ev: any) => (
                    <div
                      key={ev.id}
                      style={{
                        padding: 12,
                        borderRadius: 8,
                        background: "var(--green-soft)",
                        border: "1px solid var(--green)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <b>{ev.name}</b>
                        <Tag tone="green">{ev.venue}</Tag>
                      </div>
                      <div style={{ fontSize: 12, color: "var(--ink)", marginTop: 4 }}>
                        Time: {ev.start}:00 – {ev.end}:00 ({ev.duration} hrs)
                      </div>
                      <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>
                        Athletes: {ev.participants.join(", ")}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Rejected Events with Trace */}
              <Card>
                <SectionHeading
                  title="Conflict Diagnoses & Rejected Requests"
                  aside={<Tag tone="neutral">{solverResult.total_conflicts} Collisions</Tag>}
                />
                <div style={{ display: "grid", gap: 10 }}>
                  {solverResult.rejected.map((ev: any) => (
                    <div
                      key={ev.id}
                      style={{
                        padding: 12,
                        borderRadius: 8,
                        background: "rgba(232,99,99,0.08)",
                        border: "1px solid rgba(232,99,99,0.3)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <b>{ev.name}</b>
                        <Tag tone="neutral">{ev.venue}</Tag>
                      </div>
                      <div style={{ fontSize: 12, color: "#e86363", marginTop: 4, fontWeight: 600 }}>
                        {ev.reason}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Step-by-Step Decision Trace */}
              <Card style={{ gridColumn: "1 / -1" }}>
                <SectionHeading title="Algorithm Step-by-Step Decision Trace" />
                <div className="trace-box">
                  {solverResult.decision_trace.map((t: any) => (
                    <div
                      key={t.step}
                      className={`trace-item ${t.decision === "ACCEPTED" ? "match" : "reject"}`}
                    >
                      <b>Step {t.step} [{t.decision}]:</b> {t.event} ({t.venue}, {t.interval})
                      <br />
                      <span style={{ color: "var(--muted)" }}>Rationale: {t.reason}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </div>
      )}
    </>
  );
}
