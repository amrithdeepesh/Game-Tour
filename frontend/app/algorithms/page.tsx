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
        description="Find a player, arrange scores, or check a schedule for overlapping games."
        action="View participant leaderboard"
        href="/leaderboard"
      />

      <div className="phase-heading">
        <div>
          <div className="eyebrow">FIND A COMPETITOR</div>
          <h2>Search participant records</h2>
        </div>
        <Tag tone="blue">Find a player</Tag>
      </div>
      <div className="two-column">
        <Card>
          <SectionHeading title="Search the roster" aside={<Tag tone="blue">Quick lookup</Tag>} />
          <p className="muted-copy">
            Search by name. The quick option works best for a large player list.
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
              Search all names
            </button>
            <button
              className={"button " + (searchMethod === "binary" ? "primary-button" : "secondary-button")}
              onClick={() => searchRun("binary")}
            >
              <Binary size={15} /> Quick name search
            </button>
          </div>
          {searchResult && <div className="result-panel" role="status">{searchResult}</div>}
          <div className="complexity-compare">
            <div><b>Search all names</b><span>Checks each player</span><small>Works in any order</small></div>
            <div><b>Quick name search</b><span>Narrows down the list</span><small>Best for many players</small></div>
          </div>
        </Card>

        <Card>
          <SectionHeading title="Arrange scores" aside={<Tag tone="gold">ORDER THE LIST</Tag>} />
          <p className="muted-copy">
            Sort participants by points to see who is leading.
          </p>
          <div className="sort-controls">
            <button
              className={"button " + (sortMethod === "selection" ? "primary-button" : "secondary-button")}
              onClick={() => sortRun("selection")}
            >
              Simple ordering
            </button>
            <button
              className={"button " + (sortMethod === "merge" ? "primary-button" : "secondary-button")}
              onClick={() => sortRun("merge")}
            >
              <ArrowDownWideNarrow size={15} /> Fast ordering
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
            <span>{sortMethod === "merge" ? "Fast ordering" : "Simple ordering"}</span>
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
          <div className="eyebrow">PLAN GAME TIMES</div>
          <h2>Find a schedule with fewer overlaps</h2>
        </div>
        <Tag tone="violet">SCHEDULE HELPER</Tag>
      </div>
      <Card className="greedy-card">
        <div className="greedy-head">
          <SectionHeading title="Games that fit one after another" aside={<Tag tone="green">FEWER OVERLAPS</Tag>} />
          <button className="button primary-button" onClick={runGreedy}>
            <Sparkles size={15} /> Suggest a schedule
          </button>
        </div>
        <p className="muted-copy">
          This suggestion arranges your scheduled games so fewer of them overlap.
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
          <Zap size={14} /> Suggestions are based on your scheduled games
        </div>
      </Card>
      {status && <div className="notice" role="status">{status}</div>}
    </>
  );
}
