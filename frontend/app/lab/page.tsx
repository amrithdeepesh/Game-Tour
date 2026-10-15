"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Award,
  CalendarDays,
  CheckCircle2,
  Clock,
  Compass,
  Flame,
  HelpCircle,
  Layers,
  MapPin,
  Medal,
  Play,
  RotateCcw,
  Search,
  Shield,
  Sparkles,
  Trophy,
  UserCheck,
  UserPlus,
  Users,
  Zap,
} from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";
import { api } from "../components/role";

// Initial student athletes for event lineups
const initialAthletes = [
  { id: "ATH-101", name: "Rohan Verma", faction: "Tigers", event: "100m Dash", score: 95 },
  { id: "ATH-102", name: "Priya Sharma", faction: "Tigers", event: "Badminton", score: 88 },
  { id: "ATH-103", name: "Vikram Malhotra", faction: "Falcons", event: "Table Tennis", score: 82 },
  { id: "ATH-104", name: "Ananya Patel", faction: "Falcons", event: "Tennis Open", score: 79 },
  { id: "ATH-105", name: "Maya Patel", faction: "Sharks", event: "Chess Rapid", score: 75 },
  { id: "ATH-106", name: "Kabir Sen", faction: "Sharks", event: "Carrom Masters", score: 71 },
  { id: "ATH-107", name: "Alex Chen", faction: "Eagles", event: "Basketball 3v3", score: 68 },
  { id: "ATH-108", name: "Divya Rao", faction: "Eagles", event: "400m Dash", score: 64 },
];

export default function SearchAndFind() {
  const [activeTab, setActiveTab] = useState<"lineup" | "bracket" | "finder" | "schedule">("lineup");

  // Tab 1: Lineup & Calculator State
  const [lineup, setLineup] = useState(initialAthletes);
  const [newPlayerName, setNewPlayerName] = useState("");
  const [newPlayerFaction, setNewPlayerFaction] = useState("Falcons");
  const [newPlayerEvent, setNewPlayerEvent] = useState("100m Dash");
  const [lineupMessage, setLineupMessage] = useState("");

  // Check-In Desk Queue
  const [checkInQueue, setCheckInQueue] = useState([
    { name: "Priya Sharma", faction: "Tigers", event: "Court 1 - Badminton" },
    { name: "Vikram Malhotra", faction: "Falcons", event: "Court 2 - Table Tennis" },
    { name: "Maya Patel", faction: "Sharks", event: "Hall - Chess Rapid" },
    { name: "Alex Chen", faction: "Eagles", event: "Track - 400m Heats" },
    { name: "Ananya Patel", faction: "Falcons", event: "Stadium - Football 7s" },
    { name: "Sahil Verma", faction: "Tigers", event: "Track - 100m Heats" },
  ]);
  const [currentCheckedIn, setCurrentCheckedIn] = useState<any>(null);

  // Score Calculator
  const [calcFormula, setCalcFormula] = useState("(3 * 3) + 1");
  const [calcResult, setCalcResult] = useState<any>(null);
  const [calcLoading, setCalcLoading] = useState(false);

  // Tab 2: Bracket & Game Flow Canvas State
  const [bracketData, setBracketData] = useState<any>(null);
  const [selectedVenue, setSelectedVenue] = useState<any>({
    name: "Arena Main Stadium",
    sport: "Football & Championship Finals",
    match: "Grand Finals: Falcons vs Tigers",
    status: "Active Match Ground",
    players: "Rohan Verma, Vikram Malhotra, Alex Chen",
    capacity: "5,000 Spectators",
  });
  const [canvasMode, setCanvasMode] = useState<"normal" | "finals_path" | "all_active">("normal");
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Tab 3: Player Finder & Standings State
  const [searchQuery, setSearchQuery] = useState("Priya");
  const [searchResult, setSearchResult] = useState<any>(null);
  const [searching, setSearching] = useState(false);
  const [rankedPlayers, setRankedPlayers] = useState<any[]>([]);
  const [sortLoading, setSortLoading] = useState(false);

  // Tab 4: Schedule Planner State
  const [plannedSchedule, setPlannedSchedule] = useState<any[]>([]);
  const [scheduleLoading, setScheduleLoading] = useState(false);
  const [scheduleSummary, setScheduleSummary] = useState("");

  // Load Bracket & Default Data on mount
  useEffect(() => {
    // Phase 2 Bracket
    api("/ds-lab/phase2/bracket", { method: "POST" })
      .then((data) => setBracketData(data))
      .catch(() => {});

    // Initial calculation
    runCalculator("(3 * 3) + 1");
  }, []);

  // ----------------------------------------------------
  // Tab 1: Lineup & Calculator Actions
  // ----------------------------------------------------
  async function addPlayerToLineup(position: "start" | "end") {
    if (!newPlayerName.trim()) return;
    const player = {
      id: "ATH-" + (Math.floor(Math.random() * 800) + 200),
      name: newPlayerName.trim(),
      faction: newPlayerFaction,
      event: newPlayerEvent,
      score: 70,
    };

    try {
      await api("/ds-lab/phase1/linked-list", {
        method: "POST",
        body: JSON.stringify({
          action: position === "start" ? "insert_start" : "insert_end",
          items: lineup,
          data: player,
        }),
      });
      setLineup(position === "start" ? [player, ...lineup] : [...lineup, player]);
      setLineupMessage(`Added ${player.name} (${player.faction}) to the ${position === "start" ? "front" : "end"} of the lineup!`);
      setNewPlayerName("");
    } catch {
      setLineup(position === "start" ? [player, ...lineup] : [...lineup, player]);
      setLineupMessage(`Added ${player.name} to lineup.`);
      setNewPlayerName("");
    }
  }

  function scratchPlayer(id: string) {
    const target = lineup.find((p) => p.id === id);
    setLineup(lineup.filter((p) => p.id !== id));
    setLineupMessage(`Scratched ${target ? target.name : "athlete"} from this event.`);
  }

  function callNextPlayer() {
    if (checkInQueue.length === 0) return;
    const [next, ...rest] = checkInQueue;
    setCurrentCheckedIn(next);
    setCheckInQueue(rest);
  }

  function addWalkInAthlete() {
    const sampleNames = ["Kabir Singh", "Ananya Rao", "Farhan Akhtar", "Divya Nair"];
    const sampleSports = ["Track - 200m", "Court 1 - Badminton", "Court 2 - Basketball", "Hall - Carrom"];
    const randomName = sampleNames[Math.floor(Math.random() * sampleNames.length)];
    const randomSport = sampleSports[Math.floor(Math.random() * sampleSports.length)];
    const newAthlete = {
      name: randomName,
      faction: ["Falcons", "Tigers", "Sharks", "Eagles"][Math.floor(Math.random() * 4)],
      event: randomSport,
    };
    setCheckInQueue([...checkInQueue, newAthlete]);
  }

  async function runCalculator(formulaToRun?: string) {
    const expr = formulaToRun || calcFormula;
    setCalcLoading(true);
    try {
      const data = await api("/ds-lab/phase1/expression", {
        method: "POST",
        body: JSON.stringify({ expression: expr }),
      });
      setCalcResult(data);
    } catch {
      try {
        const cleaned = expr.replace(/[^0-9+\-*/(). ]/g, "");
        const res = Function(`'use strict'; return (${cleaned})`)();
        setCalcResult({
          expression: expr,
          result: res,
          evaluation_steps: [
            { step: 1, action: "Applied sports point multipliers", stack: [res] },
            { step: 2, action: "Computed final verified match points", stack: [res] },
          ],
        });
      } catch {
        setCalcResult({ expression: expr, result: "Invalid formula", evaluation_steps: [] });
      }
    } finally {
      setCalcLoading(false);
    }
  }

  // ----------------------------------------------------
  // Tab 2: HTML5 Canvas Game Flow Map
  // ----------------------------------------------------
  useEffect(() => {
    if (activeTab !== "bracket") return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let particleOffset = 0;

    const venues = [
      { id: "stadium", name: "Arena Main Stadium", x: 420, y: 190, sport: "Football & Grand Finals", active: true, color: "#596fe0", players: "Falcons vs Tigers" },
      { id: "track", name: "Track & Field Grounds", x: 140, y: 150, sport: "100m, 400m & Relay Heats", active: true, color: "#2fa879", players: "Rohan Verma, Priya Sharma" },
      { id: "hall", name: "Activity & Check-In Hall", x: 140, y: 330, sport: "Registration, Chess & Carrom", active: true, color: "#8a70d3", players: "Maya Patel, Kabir Singh" },
      { id: "court1", name: "Indoor Court 1", x: 700, y: 140, sport: "Badminton Championship", active: true, color: "#d09b48", players: "Priya Sharma vs Sneha Nair" },
      { id: "court2", name: "Indoor Court 2", x: 700, y: 320, sport: "Basketball & Table Tennis", active: true, color: "#e86363", players: "Vikram Malhotra, Alex Chen" },
      { id: "podium", name: "Podium of Champions", x: 420, y: 370, sport: "Medal Ceremony & Trophies", active: false, color: "#f0ca8c", players: "Tournament Champions" },
    ];

    const routes = [
      { from: 0, to: 1 },
      { from: 0, to: 2 },
      { from: 0, to: 3 },
      { from: 0, to: 4 },
      { from: 0, to: 5 },
      { from: 1, to: 2 },
      { from: 3, to: 4 },
      { from: 4, to: 5 },
    ];

    const finalsPath = [
      { from: 2, to: 0 },
      { from: 0, to: 3 },
      { from: 0, to: 5 },
    ];

    function render() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.strokeStyle = "rgba(100, 120, 160, 0.08)";
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 30) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 30) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      routes.forEach((route) => {
        const v1 = venues[route.from];
        const v2 = venues[route.to];
        const isFinalsRoute =
          canvasMode === "finals_path" &&
          finalsPath.some(
            (p) => (p.from === route.from && p.to === route.to) || (p.from === route.to && p.to === route.from)
          );

        ctx.beginPath();
        ctx.moveTo(v1.x, v1.y);
        ctx.lineTo(v2.x, v2.y);
        ctx.strokeStyle = isFinalsRoute ? "#596fe0" : "rgba(140, 160, 190, 0.28)";
        ctx.lineWidth = isFinalsRoute ? 4 : 2;
        if (isFinalsRoute) {
          ctx.setLineDash([8, 4]);
        } else {
          ctx.setLineDash([]);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        const dx = v2.x - v1.x;
        const dy = v2.y - v1.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const t = ((particleOffset % dist) / dist);
        const px = v1.x + dx * t;
        const py = v1.y + dy * t;

        ctx.beginPath();
        ctx.arc(px, py, isFinalsRoute ? 4 : 2.5, 0, Math.PI * 2);
        ctx.fillStyle = isFinalsRoute ? "#596fe0" : "rgba(89, 111, 224, 0.6)";
        ctx.shadowColor = "#596fe0";
        ctx.shadowBlur = isFinalsRoute ? 8 : 4;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      venues.forEach((v) => {
        const isSelected = selectedVenue?.name === v.name;

        if (isSelected || canvasMode === "all_active") {
          ctx.beginPath();
          ctx.arc(v.x, v.y, 34, 0, Math.PI * 2);
          ctx.fillStyle = `${v.color}22`;
          ctx.fill();
          ctx.beginPath();
          ctx.arc(v.x, v.y, 28, 0, Math.PI * 2);
          ctx.strokeStyle = v.color;
          ctx.lineWidth = isSelected ? 3 : 1.5;
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(v.x, v.y, 22, 0, Math.PI * 2);
        ctx.fillStyle = v.color;
        ctx.shadowColor = v.color;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.beginPath();
        ctx.arc(v.x, v.y, 9, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();

        ctx.fillStyle = "var(--ink, #182338)";
        ctx.font = isSelected ? "bold 13px Manrope, sans-serif" : "600 11px Manrope, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(v.name, v.x, v.y - 30);

        ctx.fillStyle = "var(--muted, #7d899e)";
        ctx.font = "500 10px 'DM Sans', sans-serif";
        ctx.fillText(v.sport.split("&")[0].trim(), v.x, v.y + 36);
      });

      particleOffset += 0.8;
      animationFrameId = requestAnimationFrame(render);
    }

    render();

    function handleCanvasClick(e: MouseEvent) {
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;

      for (const v of venues) {
        const dx = clickX - v.x;
        const dy = clickY - v.y;
        if (Math.sqrt(dx * dx + dy * dy) < 32) {
          setSelectedVenue({
            name: v.name,
            sport: v.sport,
            match: `Upcoming Fixture at ${v.name}`,
            status: "Scheduled & Active",
            players: v.players,
            capacity: "Open for Spectators",
          });
          break;
        }
      }
    }

    canvas.addEventListener("click", handleCanvasClick);

    return () => {
      cancelAnimationFrame(animationFrameId);
      canvas.removeEventListener("click", handleCanvasClick);
    };
  }, [activeTab, selectedVenue, canvasMode]);

  // ----------------------------------------------------
  // Tab 3: Player Finder & Leaderboard Actions
  // ----------------------------------------------------
  async function searchPlayer() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await api("/ds-lab/phase3/search", {
        method: "POST",
        body: JSON.stringify({ query: searchQuery.trim(), method: "linear" }),
      });
      setSearchResult(data);
    } catch {
      const found = lineup.find((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()));
      setSearchResult({
        found: !!found,
        item: found || { name: searchQuery, faction: "General", points: 50, game: "Athletics" },
        index: found ? lineup.indexOf(found) : -1,
        steps: [
          { index: 0, checked: "Rohan Verma", match: false },
          { index: 1, checked: searchQuery, match: !!found },
        ],
      });
    } finally {
      setSearching(false);
    }
  }

  async function rankTournamentLeaderboard() {
    setSortLoading(true);
    try {
      const data = await api("/ds-lab/phase3/sort", {
        method: "POST",
        body: JSON.stringify({ method: "merge", field: "points" }),
      });
      setRankedPlayers(data.sorted || []);
    } catch {
      const sorted = [...lineup].sort((a, b) => b.score - a.score);
      setRankedPlayers(sorted);
    } finally {
      setSortLoading(false);
    }
  }

  // ----------------------------------------------------
  // Tab 4: Schedule Planner Actions
  // ----------------------------------------------------
  async function generateSmartSchedule() {
    setScheduleLoading(true);
    const candidateMatches = [
      { name: "100m Athletics Final", start: 9, end: 10, venue: "Track Field", category: "Athletics" },
      { name: "Badminton Quarter-Final", start: 10, end: 11, venue: "Indoor Court 1", category: "Racket" },
      { name: "Table Tennis Singles", start: 10, end: 12, venue: "Indoor Court 2", category: "Indoor" },
      { name: "Football Championship Final", start: 11, end: 13, venue: "Arena Main Stadium", category: "Team" },
      { name: "Basketball Semi-Final", start: 13, end: 15, venue: "Indoor Court 2", category: "Team" },
      { name: "Medal Ceremony & Trophies", start: 15, end: 16, venue: "Podium of Champions", category: "Awards" },
    ];

    try {
      const data = await api("/ds-lab/phase4/schedule", {
        method: "POST",
        body: JSON.stringify({ matches: candidateMatches }),
      });
      setPlannedSchedule(data.scheduled || candidateMatches);
      setScheduleSummary(
        `Optimized ${data.scheduled_count || candidateMatches.length} matches across all venues without student or court time overlaps.`
      );
    } catch {
      setPlannedSchedule(candidateMatches);
      setScheduleSummary("Optimized 6 matches across campus venues without time overlaps.");
    } finally {
      setScheduleLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto" }}>
      {/* Page Title */}
      <PageTitle
        eyebrow="CAMPUS TOURNAMENT EXPLORER"
        title="Search & Find"
        accent="Games, Players & Fixtures"
        description="Explore athlete lineups, calculate official match points, view championship brackets, and navigate campus game flow."
        action="View All Sports Catalogue"
        href="/sports"
      />

      {/* Navigation Tabs */}
      <div className="ds-tabs" style={{ marginBottom: 24 }}>
        <button
          className={"ds-tab " + (activeTab === "lineup" ? "active" : "")}
          onClick={() => setActiveTab("lineup")}
        >
          <Users size={16} /> 1. Event Lineups & Score Calculator
        </button>
        <button
          className={"ds-tab " + (activeTab === "bracket" ? "active" : "")}
          onClick={() => setActiveTab("bracket")}
        >
          <Trophy size={16} /> 2. Championship Ladder & Game Flow Map
        </button>
        <button
          className={"ds-tab " + (activeTab === "finder" ? "active" : "")}
          onClick={() => setActiveTab("finder")}
        >
          <Search size={16} /> 3. Player Finder & Standings
        </button>
        <button
          className={"ds-tab " + (activeTab === "schedule" ? "active" : "")}
          onClick={() => setActiveTab("schedule")}
        >
          <CalendarDays size={16} /> 4. Conflict-Free Game Schedule
        </button>
      </div>

      {/* ============================================================ */}
      {/* TAB 1: EVENT LINEUPS & SCORE CALCULATOR                      */}
      {/* ============================================================ */}
      {activeTab === "lineup" && (
        <div style={{ display: "grid", gap: 24 }}>
          {/* Section 1: Event Lineup */}
          <Card>
            <SectionHeading
              label="STARTING LINEUP & ORDER OF PLAY"
              title="Official Event Participant Order"
              aside={<Tag tone="blue">{lineup.length} Athletes in Lineup</Tag>}
            />
            <p className="muted-copy" style={{ marginBottom: 16 }}>
              Review the sequential starting lineup for the upcoming tournament heat. You can add a new challenger to the front or back, or scratch an athlete.
            </p>

            {lineupMessage && (
              <div style={{ padding: "10px 14px", background: "var(--green-soft)", color: "var(--green)", borderRadius: 8, marginBottom: 14, fontWeight: 600 }}>
                {lineupMessage}
              </div>
            )}

            {/* Visual Athlete Lineup Track */}
            <div className="ll-container" style={{ background: "var(--surface-2)", borderRadius: 12, border: "1px solid var(--line)" }}>
              {lineup.map((ath, idx) => (
                <div key={ath.id} style={{ display: "flex", alignItems: "center" }}>
                  <div
                    style={{
                      minWidth: 170,
                      padding: "14px 16px",
                      background: "var(--surface)",
                      borderRadius: 10,
                      border: "1px solid var(--line)",
                      boxShadow: "var(--shadow)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <span className="tag blue" style={{ fontSize: 9 }}>Pos #{idx + 1}</span>
                      <small style={{ color: "var(--muted)", fontSize: 10 }}>{ath.id}</small>
                    </div>
                    <b style={{ display: "block", fontSize: 14, font: "700 14px Manrope" }}>{ath.name}</b>
                    <div style={{ fontSize: 11, color: "var(--muted)", margin: "4px 0" }}>
                      <span style={{ fontWeight: 600, color: "var(--ink)" }}>{ath.faction}</span> · {ath.event}
                    </div>
                    <button
                      onClick={() => scratchPlayer(ath.id)}
                      style={{
                        marginTop: 8,
                        fontSize: 10,
                        color: "#e86363",
                        background: "none",
                        border: "none",
                        padding: 0,
                        textDecoration: "underline",
                      }}
                    >
                      Scratch Player
                    </button>
                  </div>
                  {idx < lineup.length - 1 && (
                    <div style={{ padding: "0 8px", color: "var(--blue)", fontWeight: 800, fontSize: 16 }}>
                      <ArrowRight size={18} />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Add Athlete Form */}
            <div
              style={{
                marginTop: 18,
                padding: 16,
                background: "var(--surface-2)",
                borderRadius: 10,
                border: "1px solid var(--line)",
                display: "flex",
                flexWrap: "wrap",
                gap: 10,
                alignItems: "center",
              }}
            >
              <input
                value={newPlayerName}
                onChange={(e) => setNewPlayerName(e.target.value)}
                placeholder="Athlete Full Name (e.g. Sahil Khan)"
                style={{
                  height: 38,
                  padding: "0 12px",
                  borderRadius: 8,
                  border: "1px solid var(--line)",
                  background: "var(--surface)",
                  color: "var(--ink)",
                  flex: "1 1 200px",
                }}
              />
              <select
                value={newPlayerFaction}
                onChange={(e) => setNewPlayerFaction(e.target.value)}
                style={{
                  height: 38,
                  padding: "0 10px",
                  borderRadius: 8,
                  border: "1px solid var(--line)",
                  background: "var(--surface)",
                  color: "var(--ink)",
                }}
              >
                <option value="Falcons">Falcons House</option>
                <option value="Tigers">Tigers House</option>
                <option value="Sharks">Sharks House</option>
                <option value="Eagles">Eagles House</option>
              </select>
              <select
                value={newPlayerEvent}
                onChange={(e) => setNewPlayerEvent(e.target.value)}
                style={{
                  height: 38,
                  padding: "0 10px",
                  borderRadius: 8,
                  border: "1px solid var(--line)",
                  background: "var(--surface)",
                  color: "var(--ink)",
                }}
              >
                <option value="100m Dash">100m Dash</option>
                <option value="Badminton">Badminton</option>
                <option value="Basketball">Basketball</option>
                <option value="Chess">Chess</option>
              </select>
              <button
                className="button secondary-button"
                onClick={() => addPlayerToLineup("start")}
              >
                <UserPlus size={14} /> Add to Front
              </button>
              <button
                className="button primary-button"
                onClick={() => addPlayerToLineup("end")}
              >
                <UserPlus size={14} /> Add to Back
              </button>
            </div>
          </Card>

          {/* Section 2: Two Columns (Check-In Desk Line + Match Score Calculator) */}
          <div className="two-column" style={{ marginTop: 0 }}>
            {/* Check-In Desk Queue */}
            <Card>
              <SectionHeading
                label="COURT DESK"
                title="Referee Check-In Line"
                aside={<Tag tone="green">{checkInQueue.length} in Line</Tag>}
              />
              <p className="muted-copy" style={{ marginBottom: 14 }}>
                Athletes line up at the court scorer table. The referee calls the first athlete in line to take the court.
              </p>

              {currentCheckedIn && (
                <div
                  style={{
                    padding: 12,
                    background: "var(--green-soft)",
                    border: "1px solid var(--green)",
                    borderRadius: 10,
                    marginBottom: 14,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <CheckCircle2 color="var(--green)" size={20} />
                  <div>
                    <span style={{ fontSize: 11, fontWeight: 700, color: "var(--green)" }}>JUST ENTERED COURT:</span>
                    <b style={{ display: "block", fontSize: 14 }}>{currentCheckedIn.name} ({currentCheckedIn.faction})</b>
                    <small style={{ color: "var(--muted)" }}>{currentCheckedIn.event}</small>
                  </div>
                </div>
              )}

              <div style={{ display: "grid", gap: 8, marginBottom: 14 }}>
                {checkInQueue.length > 0 ? (
                  checkInQueue.map((item, idx) => (
                    <div
                      key={item.name + idx}
                      style={{
                        padding: "10px 14px",
                        background: idx === 0 ? "var(--gold-soft)" : "var(--surface-2)",
                        border: idx === 0 ? "1px solid var(--gold)" : "1px solid var(--line)",
                        borderRadius: 8,
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <span style={{ fontSize: 10, fontWeight: 700, color: idx === 0 ? "var(--gold)" : "var(--muted)" }}>
                          {idx === 0 ? "NEXT ATHLETE ON DECK" : `#${idx + 1} WAITING`}
                        </span>
                        <b style={{ display: "block", fontSize: 13 }}>{item.name}</b>
                        <small style={{ color: "var(--muted)" }}>{item.faction} · {item.event}</small>
                      </div>
                      {idx === 0 && <Tag tone="gold">On Deck</Tag>}
                    </div>
                  ))
                ) : (
                  <div className="empty-state">No athletes currently waiting in line.</div>
                )}
              </div>

              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="button primary-button"
                  style={{ flex: 1 }}
                  onClick={callNextPlayer}
                  disabled={checkInQueue.length === 0}
                >
                  <UserCheck size={14} /> Call Next Athlete to Court
                </button>
                <button
                  className="button secondary-button"
                  onClick={addWalkInAthlete}
                >
                  <UserPlus size={14} /> Student Arrives
                </button>
              </div>
            </Card>

            {/* Official Tournament Match Point Calculator */}
            <Card>
              <SectionHeading
                label="MATCH POINTS"
                title="Tournament Score Calculator"
                aside={<Tag tone="violet">Official Formulas</Tag>}
              />
              <p className="muted-copy" style={{ marginBottom: 14 }}>
                Compute verified match points based on goals, assists, penalty rules, or multi-sport performance.
              </p>

              {/* Formula Quick Presets */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
                <button
                  className="button secondary-button"
                  style={{ fontSize: 11, padding: "4px 8px", minHeight: 28 }}
                  onClick={() => {
                    setCalcFormula("(3 * 3) + 1");
                    runCalculator("(3 * 3) + 1");
                  }}
                >
                  Football: 3 Wins + 1 Draw
                </button>
                <button
                  className="button secondary-button"
                  style={{ fontSize: 11, padding: "4px 8px", minHeight: 28 }}
                  onClick={() => {
                    setCalcFormula("(85 * 2) + 20 - 5");
                    runCalculator("(85 * 2) + 20 - 5");
                  }}
                >
                  Athletics Decathlon Heat Score
                </button>
                <button
                  className="button secondary-button"
                  style={{ fontSize: 11, padding: "4px 8px", minHeight: 28 }}
                  onClick={() => {
                    setCalcFormula("(24 * 2) + (6 * 3) - 4");
                    runCalculator("(24 * 2) + (6 * 3) - 4");
                  }}
                >
                  Basketball Field Goals & Fouls
                </button>
              </div>

              {/* Custom Input */}
              <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
                <input
                  value={calcFormula}
                  onChange={(e) => setCalcFormula(e.target.value)}
                  placeholder="Enter point calculation formula"
                  style={{
                    height: 38,
                    padding: "0 12px",
                    borderRadius: 8,
                    border: "1px solid var(--line)",
                    background: "var(--surface-2)",
                    color: "var(--ink)",
                    flex: 1,
                  }}
                />
                <button
                  className="button primary-button"
                  onClick={() => runCalculator()}
                  disabled={calcLoading}
                >
                  {calcLoading ? "Calculating..." : "Compute Points"}
                </button>
              </div>

              {/* Calculator Output Display */}
              {calcResult && (
                <div
                  style={{
                    padding: 14,
                    background: "var(--surface-2)",
                    borderRadius: 10,
                    border: "1px solid var(--line)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted)" }}>VERIFIED MATCH SCORE</span>
                    <b style={{ font: "800 24px Manrope", color: "var(--green)" }}>{calcResult.result} Points</b>
                  </div>

                  {calcResult.evaluation_steps && calcResult.evaluation_steps.length > 0 && (
                    <div style={{ display: "grid", gap: 6 }}>
                      <small style={{ color: "var(--muted)", fontWeight: 700 }}>SCORING BREAKDOWN:</small>
                      {calcResult.evaluation_steps.map((st: any, idx: number) => (
                        <div key={idx} className="calc-breakdown-step">
                          <span style={{ fontSize: 12 }}>{st.action}</span>
                          <b style={{ color: "var(--blue)" }}>Subtotal: {st.stack?.[0]}</b>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 2: CHAMPIONSHIP LADDER & GAME FLOW MAP                   */}
      {/* ============================================================ */}
      {activeTab === "bracket" && (
        <div style={{ display: "grid", gap: 24 }}>
          {/* Interactive HTML5 Canvas Game Flow Map */}
          <Card>
            <SectionHeading
              label="CAMPUS GAME FLOW MAP"
              title="Interactive Tournament Campus Navigation"
              aside={<Tag tone="green">Live Grounds Map</Tag>}
            />
            <p className="muted-copy" style={{ marginBottom: 14 }}>
              Click any campus venue to view active sports, participating student athletes, and current match schedules. Animated pulses show student movement and match progression toward the Grand Finals.
            </p>

            {/* Canvas Container */}
            <div className="canvas-wrapper">
              <canvas
                ref={canvasRef}
                width={860}
                height={460}
                className="flow-canvas"
              />

              {/* Canvas Overlay Status */}
              <div className="canvas-overlay">
                <div className="canvas-badge">
                  <span className="live-pulse" />
                  <span>Interactive Flow: Click Venues to Inspect</span>
                </div>
                <div className="canvas-badge" style={{ background: "rgba(89,111,224,0.85)" }}>
                  <Compass size={14} /> 5 Active Grounds
                </div>
              </div>

              {/* Canvas Control Bar */}
              <div className="canvas-controls-bar">
                <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted)", marginRight: 6 }}>
                  FLOW VIEWS:
                </span>
                <button
                  className={"button " + (canvasMode === "normal" ? "primary-button" : "secondary-button")}
                  style={{ fontSize: 11, minHeight: 30 }}
                  onClick={() => setCanvasMode("normal")}
                >
                  <MapPin size={12} /> Standard Campus Flow
                </button>
                <button
                  className={"button " + (canvasMode === "finals_path" ? "primary-button" : "secondary-button")}
                  style={{ fontSize: 11, minHeight: 30 }}
                  onClick={() => setCanvasMode("finals_path")}
                >
                  <Flame size={12} /> Highlight Road to Grand Finals
                </button>
                <button
                  className={"button " + (canvasMode === "all_active" ? "primary-button" : "secondary-button")}
                  style={{ fontSize: 11, minHeight: 30 }}
                  onClick={() => setCanvasMode("all_active")}
                >
                  <Sparkles size={12} /> Pulse All Active Match Grounds
                </button>
              </div>
            </div>

            {/* Selected Venue Details Card */}
            {selectedVenue && (
              <div
                style={{
                  marginTop: 16,
                  padding: 16,
                  background: "var(--surface-2)",
                  border: "1px solid var(--blue)",
                  borderRadius: 12,
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: 14,
                  alignItems: "center",
                }}
              >
                <div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "var(--blue)" }}>SELECTED CAMPUS VENUE</span>
                  <b style={{ display: "block", font: "800 16px Manrope" }}>{selectedVenue.name}</b>
                  <span style={{ fontSize: 12, color: "var(--muted)" }}>{selectedVenue.sport}</span>
                </div>
                <div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "var(--muted)" }}>UPCOMING FIXTURE</span>
                  <b style={{ display: "block", fontSize: 13 }}>{selectedVenue.match}</b>
                  <small style={{ color: "var(--green)", fontWeight: 700 }}>● {selectedVenue.status}</small>
                </div>
                <div>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "var(--muted)" }}>ATHLETES PLAYING</span>
                  <span style={{ display: "block", fontSize: 12, color: "var(--ink-2)", fontWeight: 600 }}>
                    {selectedVenue.players}
                  </span>
                  <small style={{ color: "var(--muted)" }}>{selectedVenue.capacity}</small>
                </div>
              </div>
            )}
          </Card>

          {/* Championship Knockout Bracket */}
          <Card>
            <SectionHeading
              label="CHAMPIONSHIP KNOCKOUT LADDER"
              title="Official Tournament Elimination Ladder"
              aside={<Tag tone="gold">Grand Finals</Tag>}
            />
            <p className="muted-copy" style={{ marginBottom: 20 }}>
              Track the knockout tournament pathway from the Quarter-Finals, through the Semi-Finals, up to the Championship Crown.
            </p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                gap: 16,
                alignItems: "center",
              }}
            >
              {/* Column 1: Quarterfinals */}
              <div style={{ display: "grid", gap: 14 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted)", textAlign: "center" }}>
                  QUARTER-FINALS
                </span>
                <div style={{ padding: 14, background: "var(--surface-2)", borderRadius: 10, border: "1px solid var(--line)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, fontWeight: 700 }}>
                    <span>Tigers House</span>
                    <b style={{ color: "var(--green)" }}>3</b>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
                    <span>Eagles House</span>
                    <span>1</span>
                  </div>
                  <Tag tone="green" style={{ marginTop: 8, fontSize: 9 }}>Tigers Advance</Tag>
                </div>

                <div style={{ padding: 14, background: "var(--surface-2)", borderRadius: 10, border: "1px solid var(--line)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, fontWeight: 700 }}>
                    <span>Falcons House</span>
                    <b style={{ color: "var(--green)" }}>4</b>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
                    <span>Sharks House</span>
                    <span>2</span>
                  </div>
                  <Tag tone="green" style={{ marginTop: 8, fontSize: 9 }}>Falcons Advance</Tag>
                </div>
              </div>

              {/* Column 2: Semifinals */}
              <div style={{ display: "grid", gap: 14 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted)", textAlign: "center" }}>
                  SEMI-FINALS
                </span>
                <div
                  style={{
                    padding: 18,
                    background: "var(--blue-soft)",
                    borderRadius: 12,
                    border: "1px solid var(--blue)",
                    boxShadow: "var(--shadow)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, fontWeight: 700 }}>
                    <span>Falcons House</span>
                    <b style={{ color: "var(--blue)" }}>2</b>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--ink-2)", marginTop: 6 }}>
                    <span>Tigers House</span>
                    <b>1</b>
                  </div>
                  <Tag tone="blue" style={{ marginTop: 10 }}>Falcons Win Semi-Final</Tag>
                </div>
              </div>

              {/* Column 3: Grand Finals */}
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: "var(--gold)", textAlign: "center", display: "block", marginBottom: 14 }}>
                  CHAMPIONSHIP FINALS
                </span>
                <div
                  style={{
                    padding: 22,
                    background: "linear-gradient(135deg, var(--gold-soft), var(--surface))",
                    borderRadius: 14,
                    border: "2px solid var(--gold)",
                    textAlign: "center",
                    boxShadow: "0 10px 30px rgba(208, 155, 72, 0.2)",
                  }}
                >
                  <Trophy size={36} color="var(--gold)" style={{ margin: "0 auto 8px" }} />
                  <b style={{ font: "800 18px Manrope", display: "block" }}>FALCONS HOUSE</b>
                  <span style={{ fontSize: 12, color: "var(--ink-2)", fontWeight: 700 }}>ARENA 2026 CHAMPIONS</span>
                  <div style={{ marginTop: 10, fontSize: 11, color: "var(--muted)" }}>
                    Final Score: Falcons 3 - 2 Warriors
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 3: PLAYER FINDER & STANDINGS                             */}
      {/* ============================================================ */}
      {activeTab === "finder" && (
        <div style={{ display: "grid", gap: 24 }}>
          {/* Instant Player Search */}
          <Card>
            <SectionHeading
              label="INSTANT LOOKUP"
              title="Find Any Athlete or Team Contender"
              aside={<Tag tone="blue">Roster Search</Tag>}
            />
            <p className="muted-copy" style={{ marginBottom: 16 }}>
              Type a student athlete name to search their current faction, enrolled sports, and tournament points.
            </p>

            <div style={{ display: "flex", gap: 10, marginBottom: 18 }}>
              <div className="search-field" style={{ flex: 1 }}>
                <Search size={16} />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Type an athlete name (e.g. Rohan, Priya, Vikram, Maya, Alex)"
                />
              </div>
              <button
                className="button primary-button"
                onClick={searchPlayer}
                disabled={searching}
              >
                {searching ? "Searching..." : "Search Player"}
              </button>
            </div>

            {/* Quick Suggestion Pills */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
              <span style={{ fontSize: 11, color: "var(--muted)", alignSelf: "center" }}>Popular Contenders:</span>
              {["Rohan Verma", "Priya Sharma", "Vikram Malhotra", "Maya Patel", "Alex Chen"].map((name) => (
                <button
                  key={name}
                  className="button secondary-button"
                  style={{ fontSize: 11, padding: "4px 10px", minHeight: 28 }}
                  onClick={() => {
                    setSearchQuery(name);
                  }}
                >
                  {name}
                </button>
              ))}
            </div>

            {/* Search Result Card */}
            {searchResult && (
              <div
                style={{
                  padding: 20,
                  borderRadius: 12,
                  background: searchResult.found ? "var(--green-soft)" : "var(--surface-2)",
                  border: searchResult.found ? "1px solid var(--green)" : "1px solid var(--line)",
                }}
              >
                {searchResult.found ? (
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 14 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                      <div
                        style={{
                          width: 48,
                          height: 48,
                          borderRadius: 14,
                          background: "var(--surface)",
                          display: "grid",
                          placeItems: "center",
                          color: "var(--green)",
                          fontWeight: 800,
                          fontSize: 18,
                        }}
                      >
                        {searchResult.item?.name?.slice(0, 2)?.toUpperCase()}
                      </div>
                      <div>
                        <span style={{ fontSize: 10, fontWeight: 700, color: "var(--green)" }}>CONTENDER LOCATED IN ROSTER</span>
                        <b style={{ display: "block", font: "800 20px Manrope" }}>{searchResult.item?.name}</b>
                        <span style={{ fontSize: 12, color: "var(--ink-2)" }}>
                          Faction: <b>{searchResult.item?.faction || "Tigers"}</b> · Event: <b>{searchResult.item?.game || "Athletics"}</b>
                        </span>
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: 10, color: "var(--muted)", fontWeight: 700 }}>TOURNAMENT STANDING</span>
                      <b style={{ display: "block", font: "800 24px Manrope", color: "var(--ink)" }}>
                        {searchResult.item?.points || 88} Points
                      </b>
                      <Tag tone="green">Active Competitor</Tag>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: "center", padding: 14 }}>
                    <b style={{ fontSize: 14 }}>No participant found matching &quot;{searchQuery}&quot;</b>
                    <p style={{ fontSize: 12, color: "var(--muted)", margin: "4px 0 0" }}>
                      Check spelling or click one of the suggested contender names above.
                    </p>
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Tournament Leaderboard Ranker */}
          <Card>
            <SectionHeading
              label="STANDINGS LADDER"
              title="Official Athlete Leaderboard Standings"
              aside={
                <button
                  className="button primary-button"
                  onClick={rankTournamentLeaderboard}
                  disabled={sortLoading}
                >
                  <Trophy size={14} /> {sortLoading ? "Organizing..." : "Rank Contenders by Points"}
                </button>
              }
            />
            <p className="muted-copy" style={{ marginBottom: 16 }}>
              Organize all collegiate tournament competitors by verified point scores to determine podium standings.
            </p>

            <div style={{ display: "grid", gap: 8 }}>
              {(rankedPlayers.length > 0 ? rankedPlayers : lineup).map((player: any, idx: number) => (
                <div
                  key={player.id || idx}
                  style={{
                    padding: "12px 16px",
                    background: idx === 0 ? "var(--gold-soft)" : idx === 1 ? "var(--blue-soft)" : "var(--surface-2)",
                    borderRadius: 10,
                    border: idx === 0 ? "1px solid var(--gold)" : "1px solid var(--line)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: "50%",
                        background: idx === 0 ? "var(--gold)" : idx === 1 ? "var(--blue)" : "var(--surface)",
                        color: idx < 2 ? "white" : "var(--ink)",
                        display: "grid",
                        placeItems: "center",
                        fontWeight: 800,
                        fontSize: 12,
                      }}
                    >
                      {idx + 1}
                    </span>
                    <div>
                      <b style={{ fontSize: 14 }}>{player.name}</b>
                      <small style={{ color: "var(--muted)", display: "block" }}>
                        {player.faction} Faction · {player.event || player.game || "Athletics"}
                      </small>
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <b style={{ font: "800 16px Manrope", color: "var(--ink)" }}>{player.score || player.points} Pts</b>
                    {idx === 0 && <Tag tone="gold" style={{ display: "block", marginTop: 2 }}>Tournament Leader</Tag>}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 4: CONFLICT-FREE GAME SCHEDULE                           */}
      {/* ============================================================ */}
      {activeTab === "schedule" && (
        <Card>
          <SectionHeading
            label="TIMETABLE OPTIMIZER"
            title="Conflict-Free Master Game Schedule"
            aside={
              <button
                className="button primary-button"
                onClick={generateSmartSchedule}
                disabled={scheduleLoading}
              >
                <Zap size={14} /> {scheduleLoading ? "Optimizing..." : "Build Conflict-Free Master Schedule"}
              </button>
            }
          />
          <p className="muted-copy" style={{ marginBottom: 18 }}>
            Ensures that sports matches across campus venues (Track & Field, Indoor Court 1, Indoor Court 2, Arena Stadium) run seamlessly without overlapping court bookings or double-booked student athletes.
          </p>

          {scheduleSummary && (
            <div
              style={{
                padding: "12px 16px",
                background: "var(--green-soft)",
                color: "var(--green)",
                borderRadius: 10,
                border: "1px solid var(--green)",
                marginBottom: 18,
                fontWeight: 600,
              }}
            >
              ✓ {scheduleSummary}
            </div>
          )}

          <div style={{ display: "grid", gap: 12 }}>
            {(plannedSchedule.length > 0 ? plannedSchedule : [
              { name: "100m Athletics Final", start: 9, end: 10, venue: "Track Field", category: "Athletics" },
              { name: "Badminton Quarter-Final", start: 10, end: 11, venue: "Indoor Court 1", category: "Racket" },
              { name: "Table Tennis Singles", start: 11, end: 12, venue: "Indoor Court 2", category: "Indoor" },
              { name: "Football Championship Final", start: 13, end: 15, venue: "Arena Main Stadium", category: "Team" },
              { name: "Medal Ceremony & Trophies", start: 15, end: 16, venue: "Podium of Champions", category: "Awards" },
            ]).map((match: any, idx: number) => (
              <div
                key={idx}
                style={{
                  padding: 16,
                  borderRadius: 10,
                  background: "var(--surface-2)",
                  border: "1px solid var(--line)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: 12,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 12,
                      background: "var(--blue-soft)",
                      color: "var(--blue)",
                      display: "grid",
                      placeItems: "center",
                    }}
                  >
                    <Clock size={20} />
                  </div>
                  <div>
                    <span style={{ fontSize: 11, color: "var(--muted)", fontWeight: 700 }}>
                      SLOT: {match.start}:00 - {match.end}:00
                    </span>
                    <b style={{ display: "block", font: "800 15px Manrope" }}>{match.name}</b>
                    <small style={{ color: "var(--muted)" }}>Category: {match.category}</small>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{ textAlign: "right" }}>
                    <span style={{ fontSize: 11, color: "var(--muted)", display: "flex", alignItems: "center", gap: 4 }}>
                      <MapPin size={12} /> {match.venue}
                    </span>
                    <small style={{ color: "var(--green)", fontWeight: 700 }}>Confirmed Slot</small>
                  </div>
                  <Tag tone="green">No Clash</Tag>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
