"use client";

import { useEffect, useState, FormEvent } from "react";
import Link from "next/link";
import {
  Flag,
  Flame,
  Plus,
  Shield,
  Trophy,
  UserCheck,
  UserPlus,
  Users,
  Zap,
  Award,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

type Faction = {
  id: number;
  name: string;
  color: string;
  motto: string;
  badge_icon: string;
  member_count: number;
  total_points: number;
  total_entries: number;
};

type Student = {
  id: number;
  username: string;
  name: string;
  email: string;
  faction: string;
};

export default function FactionsPage() {
  const { user } = useRole();
  const isAdmin = user?.role === "admin";
  const [factions, setFactions] = useState<Faction[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedFaction, setSelectedFaction] = useState<string>("all");

  // Admin form states
  const [newFactionName, setNewFactionName] = useState("");
  const [newFactionColor, setNewFactionColor] = useState("#596fe0");
  const [newFactionMotto, setNewFactionMotto] = useState("");
  const [transferStudentId, setTransferStudentId] = useState("");
  const [transferTargetFaction, setTransferTargetFaction] = useState("");

  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const fData = await api("/factions");
      setFactions(fData.factions || []);
      if (isAdmin) {
        const sData = await api("/students");
        setStudents(sData.students || []);
      }
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, [user]);

  async function handleCreateFaction(e: FormEvent) {
    e.preventDefault();
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await api("/factions", {
        method: "POST",
        body: JSON.stringify({
          name: newFactionName,
          color: newFactionColor,
          motto: newFactionMotto,
        }),
      });
      setNotice(`Faction '${newFactionName}' created successfully!`);
      setNewFactionName("");
      setNewFactionMotto("");
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleTransferStudent(e: FormEvent) {
    e.preventDefault();
    if (!transferStudentId || !transferTargetFaction) return;
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await api("/factions/assign", {
        method: "POST",
        body: JSON.stringify({
          user_id: Number(transferStudentId),
          faction: transferTargetFaction,
        }),
      });
      setNotice("Student transferred to new faction successfully.");
      setTransferStudentId("");
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const badgeIcons: Record<string, any> = {
    zap: Zap,
    flame: Flame,
    shield: Shield,
    award: Award,
    flag: Flag,
  };

  return (
    <>
      <PageTitle
        eyebrow="CAMPUS HOUSES & HOUSES COMPETITION"
        title="College Factions"
        accent="& Standings"
        description="Every student represents an inter-college faction (Falcons, Tigers, Sharks, Eagles). Faction standings aggregate official tournament points won by member athletes without double-counting."
        action={isAdmin ? "Record Results" : "View Faction Leaderboard"}
        href={isAdmin ? "/results" : "/faction-leaderboard"}
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

      {/* Factions Cards */}
      <div className="arena-grid-4" style={{ marginBottom: 24 }}>
        {factions.map((f, i) => {
          const IconComp = badgeIcons[f.badge_icon] || Shield;
          const isUserFaction = user?.faction?.toLowerCase() === f.name.toLowerCase();

          return (
            <div
              key={f.id}
              className="faction-card"
              style={{
                borderColor: isUserFaction ? f.color : "var(--line)",
                boxShadow: isUserFaction ? `0 0 20px ${f.color}30` : "var(--shadow)",
              }}
            >
              <div className="faction-banner">
                <div
                  className="faction-icon-badge"
                  style={{ background: f.color }}
                >
                  <IconComp size={24} />
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontSize: 11, fontWeight: 800, color: "var(--muted)" }}>
                      RANK #{i + 1}
                    </span>
                    {isUserFaction && <Tag tone="green">Your Faction</Tag>}
                  </div>
                  <h3 style={{ font: "800 20px Manrope", margin: "2px 0 0", color: "var(--ink)" }}>
                    {f.name}
                  </h3>
                </div>
              </div>

              <p style={{ fontSize: 12, color: "var(--muted)", fontStyle: "italic", margin: "4px 0" }}>
                "{f.motto || "Strength in unity and fair competition."}"
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 8, padding: 10, background: "var(--surface-2)", borderRadius: 10 }}>
                <div>
                  <small style={{ color: "var(--muted)", fontSize: 10 }}>TOTAL POINTS</small>
                  <div style={{ font: "800 22px Manrope", color: f.color }}>
                    {f.total_points}
                  </div>
                </div>
                <div>
                  <small style={{ color: "var(--muted)", fontSize: 10 }}>MEMBERS</small>
                  <div style={{ font: "800 22px Manrope", color: "var(--ink)" }}>
                    {f.member_count}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Admin Controls */}
      {isAdmin && (
        <div className="arena-grid-2" style={{ marginBottom: 24 }}>
          {/* Create Faction */}
          <Card className="form-card">
            <SectionHeading title="Create New Faction" />
            <form className="stack-form" onSubmit={handleCreateFaction}>
              <label>
                Faction Name
                <input
                  required
                  placeholder="e.g. Titans, Hawks, Panthers"
                  value={newFactionName}
                  onChange={(e) => setNewFactionName(e.target.value)}
                />
              </label>
              <div className="form-two">
                <label>
                  Theme Color (Hex)
                  <input
                    type="color"
                    style={{ height: 44, padding: 2 }}
                    value={newFactionColor}
                    onChange={(e) => setNewFactionColor(e.target.value)}
                  />
                </label>
                <label>
                  Motto
                  <input
                    placeholder="e.g. Relentless Excellence"
                    value={newFactionMotto}
                    onChange={(e) => setNewFactionMotto(e.target.value)}
                  />
                </label>
              </div>
              <button className="button primary-button" disabled={busy} type="submit">
                <Plus size={16} /> Create Faction
              </button>
            </form>
          </Card>

          {/* Student Faction Assignment / Transfer */}
          <Card className="form-card">
            <SectionHeading title="Assign / Transfer Student" />
            <form className="stack-form" onSubmit={handleTransferStudent}>
              <label>
                Select Student
                <select
                  required
                  value={transferStudentId}
                  onChange={(e) => setTransferStudentId(e.target.value)}
                >
                  <option value="">Choose a registered student</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.username}) · Current: {s.faction}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Transfer to Faction
                <select
                  required
                  value={transferTargetFaction}
                  onChange={(e) => setTransferTargetFaction(e.target.value)}
                >
                  <option value="">Select target faction</option>
                  {factions.map((f) => (
                    <option key={f.id} value={f.name}>
                      {f.name}
                    </option>
                  ))}
                </select>
              </label>
              <button className="button primary-button" disabled={busy} type="submit">
                <UserCheck size={16} /> Transfer Student
              </button>
            </form>
          </Card>
        </div>
      )}

      {/* Member Roster View */}
      {isAdmin && students.length > 0 && (
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <SectionHeading title="Faction Student Rosters" aside={<Tag>{students.length} students</Tag>} />
            <select
              value={selectedFaction}
              onChange={(e) => setSelectedFaction(e.target.value)}
              style={{ maxWidth: 220 }}
            >
              <option value="all">All Factions</option>
              {factions.map((f) => (
                <option key={f.id} value={f.name}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>NAME</th>
                  <th>USERNAME</th>
                  <th>FACTION</th>
                  <th>EMAIL</th>
                </tr>
              </thead>
              <tbody>
                {students
                  .filter((s) => selectedFaction === "all" || s.faction === selectedFaction)
                  .map((s) => (
                    <tr key={s.id}>
                      <td><b>{s.name}</b></td>
                      <td><code>{s.username}</code></td>
                      <td><Tag tone="blue">{s.faction}</Tag></td>
                      <td>{s.email}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </>
  );
}
