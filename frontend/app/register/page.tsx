"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, UserRoundPlus } from "lucide-react";
import { api } from "../components/role";

type Faction = {
  id: number;
  name: string;
  color?: string;
  motto?: string;
};

export default function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    faction: "",
    username: "",
    password: "",
  });
  const [factions, setFactions] = useState<Faction[]>([]);
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/factions")
      .then((data) => {
        if (data.factions && data.factions.length > 0) {
          setFactions(data.factions);
        }
      })
      .catch(() => {});
  }, []);

  function set(k: string, v: string) {
    setForm((x) => ({ ...x, [k]: v }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!form.faction) {
      setError("Please select a faction from the list managed by administrator.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api("/register", { method: "POST", body: JSON.stringify(form) });
      setOk(true);
    } catch (x) {
      setError(x instanceof Error ? x.message : "Could not create the account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="auth-card">
      <Link href="/login" className="back-link">
        <ArrowLeft size={16} /> Back to sign in
      </Link>
      <span className="eyebrow">STUDENT REGISTRATION</span>
      <h1>Create your account</h1>
      <p>Register as a student to view events and submit up to five game choices.</p>
      {ok ? (
        <div className="success-box">
          <b>Your student account is ready.</b>
          <span>Sign in with your username and password to continue.</span>
          <Link href="/login" className="button primary-button">
            Go to sign in
          </Link>
        </div>
      ) : (
        <form className="stack-form" onSubmit={submit}>
          <label>
            Full name
            <input
              required
              maxLength={120}
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
            />
          </label>
          <label>
            Email
            <input
              required
              maxLength={254}
              type="email"
              value={form.email}
              onChange={(e) => set("email", e.target.value)}
            />
          </label>
          <label>
            Faction
            <select
              required
              value={form.faction}
              onChange={(e) => set("faction", e.target.value)}
            >
              <option value="">Choose your faction (managed by admin)</option>
              {factions.map((f) => (
                <option key={f.id} value={f.name}>
                  {f.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Username
            <input
              required
              minLength={3}
              maxLength={40}
              autoComplete="username"
              value={form.username}
              onChange={(e) => set("username", e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              required
              minLength={8}
              maxLength={128}
              type="password"
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => set("password", e.target.value)}
              placeholder="At least 8 characters"
            />
          </label>
          <button className="button primary-button" disabled={busy}>
            <UserRoundPlus size={16} />
            {busy ? "Creating account…" : "Create student account"}
          </button>
        </form>
      )}
      {error && <div className="form-error">{error}</div>}
      <small className="auth-note">
        Only student accounts can be created here. Admin accounts are not self-registered.
      </small>
    </section>
  );
}
