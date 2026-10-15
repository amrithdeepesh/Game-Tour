"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  Flag,
  Mail,
  Medal,
  Shield,
  Trophy,
  User,
  CheckCircle2,
} from "lucide-react";
import { api, useRole } from "../components/role";
import { Card, PageTitle, SectionHeading, Tag } from "../components/ui";

export default function ProfilePage() {
  const { user } = useRole();
  const [leaders, setLeaders] = useState<any[]>([]);
  const [enrolled, setEnrolled] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});

  useEffect(() => {
    Promise.all([api("/leaderboard"), api("/dashboard")])
      .then(([lRes, dRes]) => {
        setLeaders(lRes.leaders || []);
        setEnrolled(dRes.my_games || []);
        setStats(dRes.stats || {});
      })
      .catch(() => {});
  }, []);

  const myRank = leaders.findIndex((x) => x.user_id === user?.id) + 1;
  const myLeaderData = leaders.find((x) => x.user_id === user?.id);

  return (
    <>
      <PageTitle
        eyebrow="STUDENT PROFILE"
        title={user?.name || "Student Profile"}
        accent="· Athletic Record"
        description="Review your verified tournament participation, assigned faction, total points scored, and individual tournament ranking."
      />

      <div className="arena-grid-3" style={{ marginBottom: 24 }}>
        <Card style={{ textAlign: "center", padding: 24 }}>
          <div
            style={{
              width: 72,
              height: 72,
              borderRadius: "50%",
              background: "linear-gradient(135deg, var(--blue), var(--violet))",
              color: "white",
              fontSize: 26,
              fontWeight: 800,
              display: "grid",
              placeItems: "center",
              margin: "0 auto 14px",
            }}
          >
            {user?.name?.slice(0, 2).toUpperCase()}
          </div>
          <h2 style={{ font: "800 22px Manrope", margin: "0 0 4px" }}>{user?.name}</h2>
          <code style={{ color: "var(--muted)", fontSize: 13 }}>@{user?.username}</code>
          <div style={{ marginTop: 12 }}>
            <Tag tone="blue">
              <Shield size={13} /> {user?.faction || "Independent"}
            </Tag>
          </div>
        </Card>

        <Card style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 12, padding: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: "var(--gold-soft)",
                color: "var(--gold)",
                display: "grid",
                placeItems: "center",
              }}
            >
              <Trophy size={22} />
            </div>
            <div>
              <small style={{ color: "var(--muted)", fontSize: 11, fontWeight: 700 }}>OVERALL RANK</small>
              <div style={{ font: "800 26px Manrope", color: "var(--ink)" }}>
                {myRank > 0 ? `#${myRank}` : "Unranked"}
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: "var(--green-soft)",
                color: "var(--green)",
                display: "grid",
                placeItems: "center",
              }}
            >
              <Medal size={22} />
            </div>
            <div>
              <small style={{ color: "var(--muted)", fontSize: 11, fontWeight: 700 }}>TOURNAMENT POINTS</small>
              <div style={{ font: "800 26px Manrope", color: "var(--ink)" }}>
                {myLeaderData?.points || 0} pts
              </div>
            </div>
          </div>
        </Card>

        <Card style={{ display: "flex", flexDirection: "column", justifyContent: "center", gap: 14, padding: 24 }}>
          <div style={{ fontSize: 13, color: "var(--muted)", display: "flex", alignItems: "center", gap: 8 }}>
            <Mail size={16} /> <span>{user?.email}</span>
          </div>
          <div style={{ fontSize: 13, color: "var(--muted)", display: "flex", alignItems: "center", gap: 8 }}>
            <Flag size={16} /> <span>Faction: <b>{user?.faction}</b></span>
          </div>
          <div style={{ fontSize: 13, color: "var(--muted)", display: "flex", alignItems: "center", gap: 8 }}>
            <CalendarDays size={16} /> <span>Active Registrations: <b>{enrolled.length} events</b></span>
          </div>
        </Card>
      </div>

      <Card>
        <SectionHeading
          title="Active Tournament Registrations"
          aside={<Tag tone="green">{enrolled.length} / 5</Tag>}
        />
        {enrolled.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>SPORT</th>
                  <th>TOURNAMENT</th>
                  <th>SCHEDULE</th>
                  <th>VENUE</th>
                </tr>
              </thead>
              <tbody>
                {enrolled.map((item) => (
                  <tr key={item.game_id}>
                    <td><b>{item.game}</b></td>
                    <td>{item.tournament}</td>
                    <td>
                      {new Date(item.starts_at.replace(" ", "T") + "Z").toLocaleString([], {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </td>
                    <td>{item.venue}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <Trophy size={24} style={{ opacity: 0.5, marginBottom: 6 }} />
            <p>You have not registered for any events yet.</p>
            <Link href="/sports" className="button primary-button" style={{ marginTop: 10 }}>
              Browse Sports
            </Link>
          </div>
        )}
      </Card>
    </>
  );
}
