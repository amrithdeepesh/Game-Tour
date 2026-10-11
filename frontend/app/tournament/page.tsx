"use client";

import { FormEvent, useEffect, useState } from "react";
import { CalendarDays, Clock3, MapPin, Medal, Pencil, Plus, Trash2, Users, X } from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type Tournament = { id: number; name: string; description: string; game_count: number };
type Game = {
  id: number; tournament_id: number; name: string; tournament: string; starts_at: string;
  venue: string; enrolled: number; capacity: number; category?: string;
};
type Participant = { id: number; name: string; faction: string; game_id: number };
type Result = { id: number; game: string; round_number: number; name: string; faction: string; score: number; placement: number };
const newTournament = { name: "", description: "" };
const newGame = { tournament_id: "", name: "", starts_at: "", venue: "", capacity: "20" };
const sqlDate = (value: string) => value ? value.replace("T", " ") + ":00" : "";
const localDate = (value: string) => value ? value.replace(" ", "T").slice(0, 16) : "";

export default function TournamentPage() {
  const { role } = useRole();
  const admin = role === "admin";
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [games, setGames] = useState<Game[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [results, setResults] = useState<Result[]>([]);
  const [tournamentForm, setTournamentForm] = useState(newTournament);
  const [gameForm, setGameForm] = useState(newGame);
  const [editingTournament, setEditingTournament] = useState<number | null>(null);
  const [editingGame, setEditingGame] = useState<number | null>(null);
  const [score, setScore] = useState({ game_id: "", winner_id: "", loser_id: "", winner_score: "0", loser_score: "0" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    const data = await api("/dashboard");
    setTournaments(data.tournaments || []);
    setGames(data.games || []);
    if (!gameForm.tournament_id && data.tournaments?.length) {
      setGameForm((form) => ({ ...form, tournament_id: String(data.tournaments[0].id) }));
    }
    if (admin) {
      const [roster, history] = await Promise.all([api("/participants"), api("/results")]);
      setParticipants(roster.participants || []);
      setResults(history.results || []);
    }
  }

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        if (active) await load();
      } catch (reason) {
        if (active) setError(reason instanceof Error ? reason.message : "Could not load tournament details.");
      }
    };
    void refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => { active = false; window.clearInterval(timer); };
  }, [role]);

  async function saveTournament(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      const body = JSON.stringify(tournamentForm);
      if (editingTournament) {
        await api(`/tournaments/${editingTournament}`, { method: "PUT", body });
        setNotice("Tournament details updated.");
      } else {
        await api("/tournaments", { method: "POST", body });
        setNotice("Tournament created.");
      }
      setTournamentForm(newTournament); setEditingTournament(null); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save this tournament.");
    }
  }

  async function removeTournament(tournament: Tournament) {
    if (!window.confirm(`Delete “${tournament.name}” and its games, sign-ups, and scores?`)) return;
    setError(""); setNotice("");
    try {
      await api(`/tournaments/${tournament.id}`, { method: "DELETE" });
      if (editingTournament === tournament.id) { setEditingTournament(null); setTournamentForm(newTournament); }
      setNotice("Tournament and its related records were deleted."); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete this tournament.");
    }
  }

  function editTournament(tournament: Tournament) {
    setTournamentForm({ name: tournament.name, description: tournament.description || "" });
    setEditingTournament(tournament.id); setNotice(""); setError("");
  }

  async function saveGame(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    const body = JSON.stringify({
      ...gameForm,
      tournament_id: Number(gameForm.tournament_id),
      capacity: Number(gameForm.capacity),
      starts_at: sqlDate(gameForm.starts_at),
      rounds: 1,
    });
    try {
      if (editingGame) {
        await api(`/games/${editingGame}`, { method: "PUT", body });
        setNotice("Scheduled game updated.");
      } else {
        await api("/games", { method: "POST", body });
        setNotice("Game added to the schedule.");
      }
      setGameForm((form) => ({ ...newGame, tournament_id: form.tournament_id }));
      setEditingGame(null); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save this game.");
    }
  }

  function editGame(game: Game) {
    setGameForm({
      tournament_id: String(game.tournament_id),
      name: game.name,
      starts_at: localDate(game.starts_at),
      venue: game.venue,
      capacity: String(game.capacity),
    });
    setEditingGame(game.id); setNotice(""); setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function removeGame(game: Game) {
    if (!window.confirm(`Delete “${game.name}” and its sign-ups and scores?`)) return;
    setError(""); setNotice("");
    try {
      await api(`/games/${game.id}`, { method: "DELETE" });
      if (editingGame === game.id) { setEditingGame(null); setGameForm(newGame); }
      setNotice("Game and its related records were deleted."); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete this game.");
    }
  }

  async function saveResult(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      await api("/results", {
        method: "POST",
        body: JSON.stringify({
          ...score, game_id: Number(score.game_id), winner_id: Number(score.winner_id),
          loser_id: Number(score.loser_id), round: 1,
          winner_score: Number(score.winner_score), loser_score: Number(score.loser_score),
        }),
      });
      setNotice("Result saved. Standings have been updated."); await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save this result.");
    }
  }

  const eligible = participants.filter((person) => String(person.game_id) === score.game_id);

  return (
    <>
      <PageTitle
        eyebrow={admin ? "ADMIN · EVENT MANAGEMENT" : "EVENT SCHEDULE"}
        title={admin ? "Manage your competition" : "Games and schedule"}
        description={admin
          ? "Create events, make changes, manage sign-ups, and post results from one place."
          : "See what is coming up, where it will happen, and how many places are left."}
      />
      {error && <div className="form-error" role="alert">{error}</div>}
      {notice && <div className="success-inline" role="status">{notice}</div>}

      {admin && (
        <>
          <div className="two-column admin-forms">
            <Card className="form-card">
              <SectionHeading title={editingTournament ? "Edit tournament" : "New tournament"} />
              <form className="stack-form" onSubmit={saveTournament}>
                <label>Tournament name<input required value={tournamentForm.name} onChange={(e) => setTournamentForm({ ...tournamentForm, name: e.target.value })} /></label>
                <label>Short description <span className="muted-copy">(optional)</span><input value={tournamentForm.description} onChange={(e) => setTournamentForm({ ...tournamentForm, description: e.target.value })} /></label>
                <div className="form-actions">
                  <button className="button primary-button"><Plus size={16} />{editingTournament ? "Save changes" : "Create tournament"}</button>
                  {editingTournament && <button type="button" className="button secondary-button" onClick={() => { setEditingTournament(null); setTournamentForm(newTournament); }}><X size={16} />Cancel</button>}
                </div>
              </form>
            </Card>

            <Card className="form-card">
              <SectionHeading title={editingGame ? "Edit scheduled game" : "Add a game"} />
              {tournaments.length ? (
                <form className="stack-form" onSubmit={saveGame}>
                  <label>Tournament<select required value={gameForm.tournament_id} onChange={(e) => setGameForm({ ...gameForm, tournament_id: e.target.value })}>{tournaments.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>
                  <label>Game name<input required value={gameForm.name} onChange={(e) => setGameForm({ ...gameForm, name: e.target.value })} /></label>
                  <div className="form-two">
                    <label>Date and time<input required type="datetime-local" value={gameForm.starts_at} onChange={(e) => setGameForm({ ...gameForm, starts_at: e.target.value })} /></label>
                    <label>Place<input required value={gameForm.venue} onChange={(e) => setGameForm({ ...gameForm, venue: e.target.value })} /></label>
                  </div>
                  <label>Maximum participants<input required type="number" min={editingGame ? games.find((item) => item.id === editingGame)?.enrolled || 1 : 1} value={gameForm.capacity} onChange={(e) => setGameForm({ ...gameForm, capacity: e.target.value })} /></label>
                  <div className="form-actions">
                    <button className="button primary-button"><Plus size={16} />{editingGame ? "Save changes" : "Add to schedule"}</button>
                    {editingGame && <button type="button" className="button secondary-button" onClick={() => { setEditingGame(null); setGameForm(newGame); }}><X size={16} />Cancel</button>}
                  </div>
                </form>
              ) : <p>Create a tournament first, then add its games.</p>}
            </Card>
          </div>

          <Card className="manage-tournaments">
            <SectionHeading title="Your tournaments" aside={<Tag>{tournaments.length} total</Tag>} />
            {!tournaments.length && <div className="empty-state">Your new tournaments will appear here.</div>}
            <div className="manage-list">
              {tournaments.map((item) => (
                <div className="manage-row" key={item.id}>
                  <span className="manage-row-icon"><CalendarDays size={18} /></span>
                  <span className="manage-row-copy"><b>{item.name}</b><small>{item.game_count} games · {item.description || "No description"}</small></span>
                  <button className="icon-button" onClick={() => editTournament(item)} aria-label={`Edit ${item.name}`}><Pencil size={16} /></button>
                  <button className="icon-button danger" onClick={() => removeTournament(item)} aria-label={`Delete ${item.name}`}><Trash2 size={16} /></button>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}

      <Card className="schedule-panel">
        <SectionHeading title={admin ? "Scheduled games" : "Upcoming games"} aside={<Tag>{games.length} events</Tag>} />
        {games.length ? (
          <div className="timeline-list">
            {games.map((game) => (
              <article className="timeline-event" key={game.id}>
                <span className="timeline-marker"><CalendarDays size={17} /></span>
                <div className="timeline-body">
                  <div className="timeline-meta">{new Date(game.starts_at.replace(" ", "T")).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })} · {game.tournament}</div>
                  <h3>{game.name}</h3>
                  <p><MapPin size={14} /> {game.venue} <span>·</span> <Users size={14} /> {game.enrolled} of {game.capacity} places filled</p>
                </div>
                {admin && <div className="admin-actions">
                  <button className="icon-button" onClick={() => editGame(game)} aria-label={`Edit ${game.name}`}><Pencil size={16} /></button>
                  <button className="icon-button danger" onClick={() => removeGame(game)} aria-label={`Delete ${game.name}`}><Trash2 size={16} /></button>
                </div>}
              </article>
            ))}
          </div>
        ) : <div className="empty-state">No games scheduled yet.</div>}
      </Card>

      {admin && <Card className="score-entry">
        <SectionHeading title="Post a result" aside={<Tag tone="gold"><Medal size={14} />Updates standings</Tag>} />
        <p className="muted-copy">Choose a game and enter the winner, runner-up, and their scores.</p>
        <form className="stack-form score-form" onSubmit={saveResult}>
          <label>Game<select required value={score.game_id} onChange={(e) => setScore({ ...score, game_id: e.target.value, winner_id: "", loser_id: "" })}><option value="">Choose a game</option>{games.map((game) => <option value={game.id} key={game.id}>{game.name} · {game.tournament}</option>)}</select></label>
          {eligible.length > 0 && <div className="form-two">
            <label>Winner<select required value={score.winner_id} onChange={(e) => setScore({ ...score, winner_id: e.target.value })}><option value="">Choose winner</option>{eligible.map((person) => <option value={person.id} key={person.id}>{person.name} · {person.faction}</option>)}</select></label>
            <label>Winner score<input required type="number" min="0" value={score.winner_score} onChange={(e) => setScore({ ...score, winner_score: e.target.value })} /></label>
            <label>Runner-up<select required value={score.loser_id} onChange={(e) => setScore({ ...score, loser_id: e.target.value })}><option value="">Choose runner-up</option>{eligible.filter((person) => String(person.id) !== score.winner_id).map((person) => <option value={person.id} key={person.id}>{person.name} · {person.faction}</option>)}</select></label>
            <label>Runner-up score<input required type="number" min="0" value={score.loser_score} onChange={(e) => setScore({ ...score, loser_score: e.target.value })} /></label>
          </div>}
          {score.game_id && !eligible.length && <div className="notice">No students have signed up for this game yet.</div>}
          <button className="button primary-button" disabled={!eligible.length}><Plus size={16} />Save result</button>
        </form>
        {results.length > 0 && <div className="recent-results"><b>Recent results</b>{results.slice(0, 5).map((result) => <div className="result-line" key={result.id}><span>{result.game}</span><span>{result.name} · {result.score} pts</span></div>)}</div>}
      </Card>}
    </>
  );
}
