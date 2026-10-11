"use client";

import { useEffect, useState } from "react";
import { Medal, Trophy, Users } from "lucide-react";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";
import { api } from "../components/role";

type Game = { id: number; name: string; tournament: string };
type Leader = {
  user_id: number;
  display_name: string;
  faction: string;
  points: number | string;
  first_places: number;
  second_places: number;
  entries: number;
};

export default function Leaderboard() {
  const [games, setGames] = useState<Game[]>([]);
  const [gameId, setGameId] = useState("all");
  const [rows, setRows] = useState<Leader[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/games")
      .then((data) => setGames(data.games || []))
      .catch((reason) => setError(reason.message));
  }, []);

  useEffect(() => {
    setError("");
    const endpoint =
      gameId === "all" ? "/leaderboard" : `/game-leaderboard/${gameId}`;
    api(endpoint)
      .then((data) => setRows(data.leaders || []))
      .catch((reason) => setError(reason.message));
  }, [gameId]);

  const selectedGame = games.find((game) => String(game.id) === gameId);

  return (
    <>
      <PageTitle
        eyebrow={selectedGame ? "GAME STANDINGS" : "OVERALL TOURNAMENT"}
        title="Participant leaderboard"
        description={
          selectedGame
            ? `Top scorers for ${selectedGame.name}, with each participant’s faction and placement highlights.`
            : "Cumulative points across tournaments, with each participant’s faction and placement highlights."
        }
      />
      <Card>
        <SectionHeading
          label={selectedGame ? "GAME RANKINGS" : "ALL-TIME STANDINGS"}
          title={selectedGame ? `${selectedGame.name} top scorers` : "Top participants"}
          aside={
            <Tag>
              <Users size={14} />
              {rows.length} students
            </Tag>
          }
        />
        <label className="leaderboard-filter">
          <span>Leaderboard</span>
          <select value={gameId} onChange={(event) => setGameId(event.target.value)}>
            <option value="all">Overall tournament</option>
            {games.map((game) => (
              <option value={game.id} key={game.id}>
                {game.name} · {game.tournament}
              </option>
            ))}
          </select>
        </label>
        {error && <div className="form-error">{error}</div>}
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>PLACE</th>
                <th>PARTICIPANT</th>
                <th>FACTION</th>
                <th>{selectedGame ? "RESULTS" : "GAMES / RESULTS"}</th>
                <th>1ST</th>
                <th>2ND</th>
                <th className="right">POINTS</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.user_id} className={index < 2 ? "highlight-row" : ""}>
                  <td>
                    <span className={`rank-chip rank-${index + 1}`}>
                      {index === 0 ? (
                        <Trophy size={15} />
                      ) : index === 1 ? (
                        <Medal size={15} />
                      ) : (
                        index + 1
                      )}
                    </span>
                  </td>
                  <td><b>{row.display_name}</b></td>
                  <td><Tag tone={index === 0 ? "gold" : "violet"}>{row.faction}</Tag></td>
                  <td>{row.entries || 0}</td>
                  <td>{row.first_places || 0}</td>
                  <td>{row.second_places || 0}</td>
                  <td className="right points">{row.points || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && !error && (
          <div className="empty-state">
            {selectedGame
              ? "No participants have results for this game yet."
              : "The leaderboard will populate as tournament results are entered."}
          </div>
        )}
      </Card>
    </>
  );
}
