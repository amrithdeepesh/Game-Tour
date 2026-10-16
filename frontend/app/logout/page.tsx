"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Command, LogOut, CheckCircle2 } from "lucide-react";
import { useRole } from "../components/role";

export default function LogoutPage() {
  const { logout } = useRole();
  const [done, setDone] = useState(false);

  useEffect(() => {
    let active = true;
    async function executeSignout() {
      try {
        await logout();
      } catch {
        // Fallback
      } finally {
        if (active) {
          setDone(true);
          setTimeout(() => {
            window.location.href = "/login";
          }, 1200);
        }
      }
    }
    void executeSignout();
    return () => {
      active = false;
    };
  }, [logout]);

  return (
    <section className="auth-card" style={{ textAlign: "center", padding: "44px 28px" }}>
      <div className="brand auth-brand" style={{ justifyContent: "center", marginBottom: 20 }}>
        <span className="brand-mark">
          <Command size={19} />
        </span>
        <span>arena<span className="brand-dot">.</span></span>
      </div>

      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: 16,
          margin: "0 auto 18px",
          background: done ? "var(--green-soft)" : "var(--blue-soft)",
          color: done ? "var(--green)" : "var(--blue)",
          display: "grid",
          placeItems: "center",
        }}
      >
        {done ? <CheckCircle2 size={28} /> : <LogOut size={26} />}
      </div>

      <span className="eyebrow">TOURNAMENT PORTAL SESSION</span>
      <h1 style={{ margin: "8px 0 6px" }}>{done ? "Signed Out" : "Signing Out…"}</h1>
      <p style={{ color: "var(--muted)", fontSize: 13, maxWidth: 320, margin: "0 auto 20px" }}>
        {done
          ? "Your session has been safely closed. Redirecting you to sign in…"
          : "Clearing your active tournament session and security credentials…"}
      </p>

      <div style={{ marginTop: 12 }}>
        <Link href="/login" className="button primary-button" style={{ fontSize: 12 }}>
          Return to Sign In
        </Link>
      </div>
    </section>
  );
}
