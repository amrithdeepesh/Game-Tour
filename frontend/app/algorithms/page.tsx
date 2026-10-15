"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowDownWideNarrow, Binary, Info, Search, Sparkles, Zap } from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";
import { api } from "../components/role";

type Player = { student_id: string; name: string; points: number; game: string };
type Match = { name: string; start: number; end: number };

export default function Algorithms() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [query, setQuery] = useState("");
  const [searchMethod, setSearchMethod] = useState("linear");
  const [searchResult, setSearchResult] = useState("");
  const [sortMethod, setSortMethod] = useState("merge");
  const [sorted, setSorted] = useState<Player[]>([]);
  const [schedule, setSchedule] = useState<Match[]>([]);
  const [planReady, setPlanReady] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    api("/dashboard")
      .then((data) => {
        setPlayers(data.players || []);
        setMatches(data.matches || []);
        if (data.players?.[0]) setQuery(data.players[0].name);
      })
      .catch((error: Error) => setStatus(error.message));
  }, []);

  async function searchRun(method: string) {
    setSearchMethod(method);
    try {
      const data = await api("/search", {
        method: "POST",
        body: JSON.stringify({ method, query }),
      });
      setSearchResult(
        data.player
          ? "Found " + data.player.name + " with " + data.player.points + " points (index " + data.index + ")."
          : "No participant matched that name.",
      );
    } catch (error) {
      setSearchResult(error instanceof Error ? error.message : "Search could not be completed.");
    }
  }

  async function sortRun(method: string) {
    setSortMethod(method);
    try {
      const data = await api("/sort", {
        method: "POST",
        body: JSON.stringify({ method }),
      });
      setSorted(data.players || []);
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Sorting could not be completed.");
    }
  }

  async function runGreedy() {
    try {
      const data = await api("/greedy", {
        method: "POST",
        body: JSON.stringify({ matches }),
      });
      const selected = data.selected || [];
      setSchedule(selected);
      setPlanReady(true);
      setStatus(`Suggested ${selected.length} of ${matches.length} games with no time clashes.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Scheduling could not be completed.");
    }
  }

  const visiblePlayers = sorted.length ? sorted : players;

  return (
    <>
      <PageTitle
        eyebrow="COMPETITION PLANNING"
        title="Get tournament day"
        accent="running smoothly."
        description="Find competitors, review the standings, and build a schedule with fewer time clashes."
        action="View participant leaderboard"
        href="/leaderboard"
      />

      <div className="tools-note" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--blue-soft)", borderColor: "var(--blue)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Info size={19} color="var(--blue)" />
          <span style={{ color: "var(--ink)" }}>Looking for player finder, tournament formulas, championship brackets, and interactive game flow?</span>
        </div>
        <Link href="/lab" className="button primary-button" style={{ fontSize: 12 }}>
          Open Search & Find
        </Link>
      </div>

      <div className="phase-heading">
        <div>
          <div className="eyebrow">PLAYER LOOKUP</div>
          <h2>Find a participant</h2>
        </div>
        <Tag tone="blue">Find a player</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Search player roster" aside={<Tag tone="blue">Name lookup</Tag>} />
          <p className="muted-copy">
            Find a player by name in the tournament participant list.
          </p>
          <div className="algorithm-input">
            <label className="search-field">
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Type a participant name"
              />
            </label>
            <button
              className={"button " + (searchMethod === "linear" ? "primary-button" : "secondary-button")}
              onClick={() => searchRun("linear")}
            >
              Search roster
            </button>
            <button
              className={"button " + (searchMethod === "binary" ? "primary-button" : "secondary-button")}
              onClick={() => searchRun("binary")}
            >
              <Binary size={15} /> Quick find
            </button>
          </div>
          {searchResult && <div className="result-panel" role="status">{searchResult}</div>}
          <div className="complexity-compare">
            <div><b>Search roster</b><span>Checks the participant list</span><small>Useful for any roster size</small></div>
            <div><b>Quick find</b><span>Returns a faster lookup</span><small>Useful for larger tournaments</small></div>
          </div>
        </Card>

        <Card>
          <SectionHeading title="Review the standings" aside={<Tag tone="gold">POINTS TABLE</Tag>} />
          <p className="muted-copy">
            Arrange the current participant scores to see who is leading.
          </p>
          <div className="sort-controls">
            <button
              className={"button " + (sortMethod === "selection" ? "primary-button" : "secondary-button")}
              onClick={() => sortRun("selection")}
            >
              Standard ranking
            </button>
            <button
              className={"button " + (sortMethod === "merge" ? "primary-button" : "secondary-button")}
              onClick={() => sortRun("merge")}
            >
              <ArrowDownWideNarrow size={15} /> Quick ranking
            </button>
          </div>
          <div className="sort-bars">
            {visiblePlayers.slice(0, 8).map((player) => (
              <div
                key={player.student_id}
                title={player.name + " · " + player.points}
                style={{ height: Math.max(22, player.points / 16) + "px" }}
              >
                <small>{player.points}</small>
              </div>
            ))}
          </div>
          <div className="sort-labels">
            <span>{sortMethod === "merge" ? "Quick ranking" : "Standard ranking"}</span>
            <span>{visiblePlayers.length} competitors</span>
          </div>
          <div className="sorted-list">
            {visiblePlayers.slice(0, 4).map((player, index) => (
              <span key={player.student_id}>{index + 1}. {player.name} <b>{player.points}</b></span>
            ))}
            {!visiblePlayers.length && <span>No scored participants yet.</span>}
          </div>
        </Card>
      </div>

      <div className="phase-heading second-phase">
        <div>
          <div className="eyebrow">SCHEDULE PLANNING</div>
          <h2>Avoid game-time clashes</h2>
        </div>
        <Tag tone="violet">SCHEDULE HELPER</Tag>
      </div>
      <Card className="greedy-card">
        <div className="greedy-head">
          <SectionHeading title="Suggested game-day plan" aside={<Tag tone="green">TIME-CLASH CHECK</Tag>} />
          <button className="button primary-button" onClick={runGreedy}>
            <Sparkles size={15} /> Build a game-day plan
          </button>
        </div>
        <p className="muted-copy">
          Select the largest set of scheduled games that can run without overlapping. This is a suggestion only; it does not change the published schedule.
        </p>
        <div className="greedy-grid">
          {matches.map((match) => {
            const chosen = schedule.some((item) => item.name === match.name);
            return (
              <div className={"greedy-item " + (chosen ? "is-chosen" : "")} key={match.name}>
                <span className="greedy-check">{chosen ? "✓" : "·"}</span>
                <b>{match.name}</b>
                <small>
                  {new Date(match.start * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  {" - "}
                  {new Date(match.end * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </small>
                <Tag tone={chosen ? "green" : "neutral"}>
                  {planReady ? (chosen ? "Suggested" : "Time clash") : "Ready to check"}
                </Tag>
              </div>
            );
          })}
          {!matches.length && <div className="empty-state">Add scheduled games to build a conflict-free plan.</div>}
        </div>
        <div className="algorithm-footnote">
          <Zap size={14} /> Based on the current game times in your schedule
        </div>
      </Card>
      {status && <div className="notice" role="status">{status}</div>}
    </>
  );
}
