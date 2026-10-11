"use client";

import { useEffect, useState } from "react";
import { ArrowDownWideNarrow, Binary, Search, Sparkles, Zap } from "lucide-react";
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
      setSchedule(data.selected || []);
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Scheduling could not be completed.");
    }
  }

  const visiblePlayers = sorted.length ? sorted : players;

  return (
    <>
      <PageTitle
        eyebrow="TOURNAMENT TOOLKIT"
        title="Make better"
        accent="match decisions."
        description="Find competitors, compare leaderboard sorting methods, and create a schedule with fewer venue conflicts."
        action="View participant leaderboard"
        href="/leaderboard"
      />

      <div className="phase-heading">
        <div>
          <div className="eyebrow">FIND A COMPETITOR</div>
          <h2>Search participant records</h2>
        </div>
        <Tag tone="blue">Linear · Binary</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Search the roster" aside={<Tag tone="blue">O(n) / O(log n)</Tag>} />
          <p className="muted-copy">
            Linear search scans any roster. Binary search checks a name-sorted roster and halves the remaining range.
          </p>
          <div className="algorithm-input">
            <label className="search-field">
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Participant name"
              />
            </label>
            <button
              className={"button " + (searchMethod === "linear" ? "primary-button" : "secondary-button")}
              onClick={() => searchRun("linear")}
            >
              Linear search
            </button>
            <button
              className={"button " + (searchMethod === "binary" ? "primary-button" : "secondary-button")}
              onClick={() => searchRun("binary")}
            >
              <Binary size={15} /> Binary search
            </button>
          </div>
          {searchResult && <div className="result-panel" role="status">{searchResult}</div>}
          <div className="complexity-compare">
            <div><b>Linear</b><span>Best O(1)</span><span>Worst O(n)</span><small>Any list order</small></div>
            <div><b>Binary</b><span>Best O(1)</span><span>Worst O(log n)</span><small>Needs sorted input</small></div>
          </div>
        </Card>

        <Card>
          <SectionHeading title="Rank the leaderboard" aside={<Tag tone="gold">TWO METHODS</Tag>} />
          <p className="muted-copy">
            Compare selection sort for a small roster with merge sort for larger tournaments.
          </p>
          <div className="sort-controls">
            <button
              className={"button " + (sortMethod === "selection" ? "primary-button" : "secondary-button")}
              onClick={() => sortRun("selection")}
            >
              Selection sort
            </button>
            <button
              className={"button " + (sortMethod === "merge" ? "primary-button" : "secondary-button")}
              onClick={() => sortRun("merge")}
            >
              <ArrowDownWideNarrow size={15} /> Merge sort
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
            <span>{sortMethod === "merge" ? "Merge sort · O(n log n)" : "Selection sort · O(n²)"}</span>
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
          <div className="eyebrow">AVOID FIXTURE CONFLICTS</div>
          <h2>Build a practical match schedule</h2>
        </div>
        <Tag tone="violet">GREEDY SCHEDULER</Tag>
      </div>
      <Card className="greedy-card">
        <div className="greedy-head">
          <SectionHeading title="Maximum non-overlapping fixtures" aside={<Tag tone="green">EARLIEST FINISH FIRST</Tag>} />
          <button className="button primary-button" onClick={runGreedy}>
            <Sparkles size={15} /> Solve schedule
          </button>
        </div>
        <p className="muted-copy">
          The scheduler sorts fixtures by finish time, then accepts each match that starts after the last selected match ends.
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
                  {schedule.length ? (chosen ? "Selected" : "Skipped") : "Ready"}
                </Tag>
              </div>
            );
          })}
          {!matches.length && <div className="empty-state">Add scheduled games to build a conflict-free plan.</div>}
        </div>
        <div className="algorithm-footnote">
          <Zap size={14} /> Greedy interval scheduling · O(n log n) · uses tournament fixtures
        </div>
      </Card>
      {status && <div className="notice" role="status">{status}</div>}
    </>
  );
}
