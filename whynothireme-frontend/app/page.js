import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>

        {/* Hero */}
        <section style={{ textAlign: "center", padding: "90px 24px 70px", maxWidth: 860, margin: "0 auto" }}>
          <div className="fade-up" style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            fontFamily: "var(--font-dm-mono)", fontSize: "0.72rem",
            color: "var(--accent2)", background: "rgba(71,255,232,0.08)",
            border: "1px solid rgba(71,255,232,0.2)", padding: "6px 14px",
            borderRadius: 100, marginBottom: 28, letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}>
            <span className="pulsing" style={{ width: 6, height: 6, background: "var(--accent2)", borderRadius: "50%", display: "inline-block" }} />
            AI-Powered Hiring Transparency
          </div>

          <h1 className="fade-up" style={{
            fontFamily: "var(--font-syne)", fontWeight: 800,
            fontSize: "clamp(2.4rem, 6vw, 4.2rem)", lineHeight: 1.05,
            letterSpacing: "-0.03em", marginBottom: 20,
            animationDelay: "0.1s",
          }}>
            Find out <span style={{ color: "var(--accent)" }}>exactly</span> why<br />
            you didn't get hired.
          </h1>

          <p className="fade-up" style={{
            fontSize: "1.1rem", color: "var(--muted)", lineHeight: 1.75,
            maxWidth: 560, margin: "0 auto 40px", animationDelay: "0.2s",
          }}>
            Upload your resume. Paste the job description. Get a full match score,
            skill gap analysis, rejection reasons — and exactly what to fix.
          </p>

          <div className="fade-up" style={{
            display: "flex", gap: 12, justifyContent: "center",
            flexWrap: "wrap", animationDelay: "0.3s",
          }}>
            <Link href="/candidate">
              <button style={{
                fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1rem",
                background: "var(--accent)", color: "#0a0a0f",
                border: "none", borderRadius: 12, padding: "16px 32px",
                cursor: "pointer",
              }}>
                ⚡ Analyze My Resume
              </button>
            </Link>
            <Link href="/company">
              <button style={{
                fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1rem",
                background: "transparent", color: "var(--text)",
                border: "1px solid var(--border)", borderRadius: 12,
                padding: "16px 32px", cursor: "pointer",
              }}>
                ✉️ I'm a Company
              </button>
            </Link>
          </div>
        </section>

        {/* The Problem */}
        <section style={{
          maxWidth: 800, margin: "0 auto", padding: "0 24px 80px",
        }}>
          <div style={{
            background: "var(--card)", border: "1px solid var(--border)",
            borderRadius: 20, padding: "40px 48px",
          }}>
            <p style={{
              fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem",
              color: "var(--accent)", textTransform: "uppercase",
              letterSpacing: "0.1em", marginBottom: 20,
            }}>
              The Problem
            </p>
            <p style={{ fontSize: "1.05rem", color: "#c0c0d0", lineHeight: 1.85 }}>
              You spend hours tailoring your resume. You use AI to match the job description.
              You apply with full confidence. Then days pass. And finally, an email arrives —
            </p>
            <div style={{
              margin: "24px 0", padding: "20px 24px",
              background: "rgba(255,71,71,0.05)", border: "1px solid rgba(255,71,71,0.15)",
              borderRadius: 10, fontFamily: "var(--font-dm-mono)", fontSize: "0.85rem",
              color: "#c08080", lineHeight: 1.7,
            }}>
              "Thank you for your interest. <strong style={{ color: "var(--danger)" }}>Unfortunately</strong>, we have decided
              to move forward with other candidates..."
            </div>
            <p style={{ fontSize: "1.05rem", color: "#c0c0d0", lineHeight: 1.85 }}>
              No reason. No feedback. No direction. Just silence dressed in formal language.
              <strong style={{ color: "var(--text)" }}> WhyNotHireMe changes that.</strong>
            </p>
          </div>
        </section>

        {/* How it works */}
        <section style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px 80px" }}>
          <h2 style={{
            fontFamily: "var(--font-syne)", fontWeight: 800,
            fontSize: "2rem", letterSpacing: "-0.03em",
            textAlign: "center", marginBottom: 48,
          }}>
            How it works
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 20 }}>
            {[
              { num: "01", icon: "📄", title: "Upload Resume", desc: "Drop your PDF resume. Our parser extracts every detail intelligently." },
              { num: "02", icon: "🧠", title: "AI Analysis", desc: "Sentence-transformers compute semantic similarity. Skills are matched against 100+ taxonomy." },
              { num: "03", icon: "📊", title: "Get Real Feedback", desc: "Match score, skill gaps, rejection reasons, and a personalised improvement plan." },
            ].map((s) => (
              <div key={s.num} style={{
                background: "var(--card)", border: "1px solid var(--border)",
                borderRadius: 16, padding: 28,
              }}>
                <div style={{
                  fontFamily: "var(--font-dm-mono)", fontSize: "0.65rem",
                  color: "var(--accent)", letterSpacing: "0.1em", marginBottom: 16,
                }}>
                  {s.num}
                </div>
                <div style={{ fontSize: "1.8rem", marginBottom: 12 }}>{s.icon}</div>
                <h3 style={{
                  fontFamily: "var(--font-syne)", fontWeight: 700,
                  fontSize: "1rem", marginBottom: 10,
                }}>
                  {s.title}
                </h3>
                <p style={{ fontSize: "0.86rem", color: "var(--muted)", lineHeight: 1.65 }}>
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Two audiences */}
        <section style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px 100px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>

            {/* Candidate */}
            <div style={{
              background: "var(--card)", border: "1px solid var(--border)",
              borderRadius: 20, padding: 36,
            }}>
              <div style={{ fontSize: "2rem", marginBottom: 16 }}>🎯</div>
              <h3 style={{ fontFamily: "var(--font-syne)", fontWeight: 800, fontSize: "1.3rem", marginBottom: 12 }}>
                For Candidates
              </h3>
              <p style={{ fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.7, marginBottom: 24 }}>
                Know your exact match score before applying. Understand what skills are missing.
                Get a personalised roadmap to become a stronger candidate.
              </p>
              <Link href="/candidate">
                <button style={{
                  fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "0.9rem",
                  background: "var(--accent)", color: "#0a0a0f",
                  border: "none", borderRadius: 10, padding: "12px 24px", cursor: "pointer",
                }}>
                  Analyze My Resume →
                </button>
              </Link>
            </div>

            {/* Company */}
            <div style={{
              background: "var(--card)", border: "1px solid var(--border)",
              borderRadius: 20, padding: 36,
            }}>
              <div style={{ fontSize: "2rem", marginBottom: 16 }}>✉️</div>
              <h3 style={{ fontFamily: "var(--font-syne)", fontWeight: 800, fontSize: "1.3rem", marginBottom: 12 }}>
                For Companies
              </h3>
              <p style={{ fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.7, marginBottom: 24 }}>
                Turn rejection into respect. Generate personalised rejection emails with real
                feedback. One click — candidate gets honest, actionable guidance.
              </p>
              <Link href="/company">
                <button style={{
                  fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "0.9rem",
                  background: "transparent", color: "var(--accent2)",
                  border: "1px solid rgba(71,255,232,0.3)", borderRadius: 10,
                  padding: "12px 24px", cursor: "pointer",
                }}>
                  Generate Email →
                </button>
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer style={{
          textAlign: "center", padding: 28,
          borderTop: "1px solid var(--border)",
          fontFamily: "var(--font-dm-mono)", fontSize: "0.7rem",
          color: "var(--muted)",
        }}>
          Built with <span style={{ color: "var(--accent)" }}>FastAPI + sentence-transformers</span> · WhyNotHireMe v2.0
        </footer>

      </main>
    </>
  );
}