"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { getMe, getHistory } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

export default function DashboardPage() {
  const router  = useRouter();
  const [profile,  setProfile]  = useState(null);
  const [history,  setHistory]  = useState([]);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    if (!isLoggedIn()) { router.push("/auth/login"); return; }
    Promise.all([getMe(), getHistory()])
      .then(([me, hist]) => { setProfile(me); setHistory(hist.records || []); })
      .catch(() => { router.push("/auth/login"); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
      <span className="spinning" style={{ width: 32, height: 32, border: "3px solid var(--border)", borderTopColor: "var(--accent)", borderRadius: "50%", display: "inline-block" }} />
    </div>
  );

  const avgScore = history.length > 0
    ? Math.round(history.reduce((a, r) => a + (r.match_score || 0), 0) / history.length)
    : 0;

  const scoreColor = (s) => s >= 70 ? "var(--success)" : s >= 45 ? "var(--warn)" : "var(--danger)";

  return (
    <>
      <Navbar />
      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px 60px" }}>

        {/* Header */}
        <div style={{ marginBottom: 40 }}>
          <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>
            Company Dashboard
          </p>
          <h1 style={{ fontFamily: "var(--font-syne)", fontWeight: 800, fontSize: "2rem", letterSpacing: "-0.03em" }}>
            Welcome, <span style={{ color: "var(--accent)" }}>{profile?.company_name}</span>
          </h1>
        </div>

        {/* Stats cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 36 }}>
          {[
            { label: "Total Analyses", val: profile?.analyses_count || history.length, color: "var(--accent)" },
            { label: "Avg Match Score", val: avgScore + "/100", color: scoreColor(avgScore) },
            { label: "Plan", val: profile?.plan?.toUpperCase() || "FREE", color: "var(--accent2)" },
            { label: "Member Since", val: profile?.created_at ? new Date(profile.created_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" }) : "—", color: "var(--text)" },
          ].map((s, i) => (
            <div key={i} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 14, padding: "20px 22px" }}>
              <div style={{ fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1.5rem", color: s.color, marginBottom: 4 }}>{s.val}</div>
              <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.63rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* API Key */}
        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 14, padding: "20px 24px", marginBottom: 36, display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.63rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Your API Key</div>
            <code style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.82rem", color: "var(--accent2)" }}>{profile?.api_key}</code>
          </div>
          <button onClick={() => navigator.clipboard.writeText(profile?.api_key)} style={{
            fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem",
            background: "rgba(71,255,232,0.1)", color: "var(--accent2)",
            border: "1px solid rgba(71,255,232,0.25)", borderRadius: 8,
            padding: "8px 16px", cursor: "pointer",
          }}>
            Copy Key
          </button>
        </div>

        {/* History table */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 18 }}>
            <h2 style={{ fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1.1rem" }}>Analysis History</h2>
            <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
          </div>

          {history.length === 0 ? (
            <div style={{ textAlign: "center", padding: "50px 24px", color: "var(--muted)", background: "var(--card)", border: "1px solid var(--border)", borderRadius: 14 }}>
              <div style={{ fontSize: "2rem", marginBottom: 12, opacity: 0.4 }}>📋</div>
              <p style={{ fontSize: "0.88rem" }}>No analyses yet. Go to <a href="/company" style={{ color: "var(--accent)" }}>Company Tool</a> to get started.</p>
            </div>
          ) : (
            <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 14, overflow: "hidden" }}>
              {/* Table header */}
              <div style={{ display: "grid", gridTemplateColumns: "2fr 2fr 1fr 1fr 1fr", gap: 0, padding: "12px 20px", borderBottom: "1px solid var(--border)", background: "rgba(255,255,255,0.02)" }}>
                {["Candidate", "Role", "Score", "Date", "Email"].map(h => (
                  <span key={h} style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.62rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{h}</span>
                ))}
              </div>
              {/* Rows */}
              {history.map((r, i) => (
                <div key={r.id} style={{
                  display: "grid", gridTemplateColumns: "2fr 2fr 1fr 1fr 1fr",
                  gap: 0, padding: "14px 20px",
                  borderBottom: i < history.length - 1 ? "1px solid var(--border)" : "none",
                  transition: "background 0.15s",
                }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.88rem" }}>{r.candidate_name || "—"}</div>
                    <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem", color: "var(--muted)" }}>{r.candidate_email || ""}</div>
                  </div>
                  <div style={{ fontSize: "0.86rem", color: "var(--muted)", alignSelf: "center" }}>{r.role_title || "—"}</div>
                  <div style={{ fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1rem", color: scoreColor(r.match_score), alignSelf: "center" }}>
                    {r.match_score ?? "—"}
                  </div>
                  <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.72rem", color: "var(--muted)", alignSelf: "center" }}>
                    {r.created_at ? new Date(r.created_at).toLocaleDateString("en-IN") : "—"}
                  </div>
                  <div style={{ alignSelf: "center" }}>
                    <span style={{
                      fontFamily: "var(--font-dm-mono)", fontSize: "0.64rem",
                      padding: "3px 8px", borderRadius: 100,
                      background: r.email_generated ? "rgba(71,255,184,0.1)" : "rgba(255,255,255,0.05)",
                      color: r.email_generated ? "var(--success)" : "var(--muted)",
                      border: `1px solid ${r.email_generated ? "rgba(71,255,184,0.25)" : "var(--border)"}`,
                    }}>
                      {r.email_generated ? "Generated" : "Pending"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </main>
    </>
  );
}