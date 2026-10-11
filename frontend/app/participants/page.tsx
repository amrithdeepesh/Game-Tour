"use client";

import { FormEvent, useEffect, useState } from "react";
import { Check, LockKeyhole, Save, Trash2, UserPlus, Users } from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type Game = { id: number; name: string; category?: string; tournament: string; starts_at: string; venue: string; enrolled: number; capacity: number };
type Student = { id: number; name: string; faction: string; username: string; email: string; game_count: number; games: string };
type Choice = { id: number; name: string; faction: string; username: string; game: string; game_id: number };

const blank = { name: "", email: "", faction: "", username: "", password: "" };

export default function Participation() {
  const { user } = useRole();
  const [games, setGames] = useState<Game[]>([]);
  const [mine, setMine] = useState<number[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [roster, setRoster] = useState<Choice[]>([]);
  const [form, setForm] = useState(blank);
  const [locked, setLocked] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    if (user?.role === "admin") {
      const [people, choices] = await Promise.all([api("/students"), api("/participants")]);
      setStudents(people.students || []);
      setRoster(choices.participants || []);
      return;
    }
    const data = await api("/dashboard");
    setGames(data.games || []);
    const selected = (data.my_games || []).map((item: { game_id: number }) => item.game_id);
    setMine(selected);
    setLocked(selected.length > 0);
  }

  useEffect(() => { load().catch((reason) => setError(reason.message)); }, [user?.role]);

  function toggle(id: number) {
    setMine((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 5 ? [...current, id] : current);
  }

  async function createStudent(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api("/participants", { method: "POST", body: JSON.stringify(form) });
      setForm(blank); setNotice("Participant account added. Share the username and starter password with the student.");
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not add participant."); }
    finally { setBusy(false); }
  }

  async function removeStudent(student: Student) {
    if (!window.confirm(`Remove ${student.name}'s account and their registrations and scores?`)) return;
    setError(""); setNotice("");
    try {
      await api(`/participants/${student.id}`, { method: "DELETE" });
      setNotice(`${student.name} was removed.`); await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not remove participant."); }
  }

  async function submitChoices(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      await api("/choices", { method: "POST", body: JSON.stringify({ game_ids: mine }) });
      setNotice("Your game choices are saved."); setLocked(true); await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save choices."); }
    finally { setBusy(false); }
  }

  if (user?.role === "admin") return <>
    <PageTitle eyebrow="PEOPLE" title="Manage participants" description="Add student accounts, see their game choices, and remove accounts when needed." />
    {error && <div className="form-error" role="alert">{error}</div>}
    {notice && <div className="success-inline" role="status">{notice}</div>}
    <div className="two-column admin-forms">
      <Card className="form-card">
        <SectionHeading title="Add a student" aside={<Tag tone="blue"><UserPlus size={14}/> New account</Tag>} />
        <form className="stack-form" onSubmit={createStudent}>
          <label>Student name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
          <label>Email address<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
          <label>Faction<input required value={form.faction} onChange={(e) => setForm({ ...form, faction: e.target.value })} /></label>
          <div className="form-two">
            <label>Username<input required minLength={3} value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></label>
            <label>Starter password<input required minLength={8} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
          </div>
          <p className="muted-copy">The student can sign in with these details and choose up to five games.</p>
          <button className="button primary-button" disabled={busy}><UserPlus size={16}/>{busy ? "Adding…" : "Add participant"}</button>
        </form>
      </Card>
      <Card>
        <SectionHeading title="Student accounts" aside={<Tag><Users size={14}/>{students.length} students</Tag>} />
        <div className="manage-list">
          {students.map((student) => <div className="manage-row" key={student.id}>
            <span className="manage-row-icon"><Users size={17}/></span>
            <span className="manage-row-copy"><b>{student.name}</b><small>{student.faction} · {student.username} · {student.game_count} games selected</small></span>
            <button className="icon-button danger" aria-label={`Remove ${student.name}`} title="Remove participant" onClick={() => removeStudent(student)}><Trash2 size={16}/></button>
          </div>)}
          {!students.length && <div className="empty-state">No student accounts yet. Add the first participant here.</div>}
        </div>
      </Card>
    </div>
    <Card>
      <SectionHeading title="Game choices" aside={<Tag>{roster.length} sign-ups</Tag>} />
      <p className="muted-copy">A live view of each student’s submitted games.</p>
      <div className="table-scroll"><table><thead><tr><th>STUDENT</th><th>FACTION</th><th>GAME</th><th>USERNAME</th></tr></thead>
        <tbody>{roster.map((item) => <tr key={item.id + "-" + item.game_id}><td><b>{item.name}</b></td><td><Tag tone="violet">{item.faction}</Tag></td><td>{item.game}</td><td>{item.username}</td></tr>)}</tbody></table></div>
      {!roster.length && <div className="empty-state">Submitted game choices will appear here.</div>}
    </Card>
  </>;

  return <>
    <PageTitle eyebrow="YOUR TOURNAMENT" title="Choose your games" description="Select up to five games. You can submit your choices once." />
    {error && <div className="form-error" role="alert">{error}</div>}
    {notice && <div className="success-inline" role="status">{notice}</div>}
    <div className="choice-summary"><span><Users size={18}/> {mine.length} of 5 games selected</span>{locked && <Tag tone="green"><LockKeyhole size={13}/> choices saved</Tag>}</div>
    <form onSubmit={submitChoices}><div className="choice-grid">
      {games.map((game) => <label key={game.id} className={"choice-card " + (mine.includes(game.id) ? "selected" : "")}>
        <input type="checkbox" checked={mine.includes(game.id)} disabled={locked || game.enrolled >= game.capacity || (!mine.includes(game.id) && mine.length >= 5)} onChange={() => toggle(game.id)} />
        <span className="choice-check">{mine.includes(game.id) && <Check size={15}/>}</span>
        <span className="choice-copy"><b>{game.name}</b><small>{game.tournament}</small><small>{new Date(game.starts_at.replace(" ", "T")).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })} · {game.venue}</small></span>
        <Tag tone={game.enrolled >= game.capacity ? "gold" : "green"}>{game.enrolled}/{game.capacity} places</Tag>
      </label>)}
    </div>
    {!games.length && <Card className="empty-state">No games have been scheduled yet.</Card>}
    {!locked && <button className="button primary-button choice-submit" disabled={busy || !mine.length}><Save size={16}/>{busy ? "Saving…" : "Submit my choices"}</button>}</form>
    {locked && <Card className="locked-note"><LockKeyhole size={18}/><span><b>Your choices are saved</b><small>Ask the tournament organizer if you need help with a selection.</small></span></Card>}
  </>;
}
