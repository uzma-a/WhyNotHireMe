"use client";
import ScoreRing from "./ScoreRing";

function SkillTag({ name, type }) {
  const styles = {
    matched: { bg: "rgba(71,255,184,0.08)", color: "#47ffb8", border: "rgba(71,255,184,0.25)" },
    missing: { bg: "rgba(255,71,71,0.08)",  color: "#ff4747", border: "rgba(255,71,71,0.25)"  },
    extra:   { bg: "rgba(232,255,71,0.08)", color: "#e8ff47", border: "rgba(232,255,71,0.25)" },
  }[type];

  return (
    <span style={{
      fontFamily: "var(--font-dm-mono)", fontSize: "0.7rem",
      padding: "4px 10px", borderRadius: 6,
      background: styles.bg, color: styles.color,
      border: `1px solid ${styles.border}`,
      display: "inline-block",
    }}>
      {name}
    </span>
  );
}

function SectionHeader({ children }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      marginBottom: 14, marginTop: 24,
    }}>
      <span style={{
        fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "0.95rem",
      }}>
        {children}
      </span>
      <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
    </div>
  );
}

export default function ResultPanel({ data }) {
  const {
    match_score, matched_skills, missing_skills, extra_skills,
    experience_gap, analysis, rejection_reasons,
    improvement_suggestions, meta,
  } = data;

  const verdict = match_score >= 70 ? "strong" : match_score >= 45 ? "medium" : "weak";
  const verdictMap = {
    strong: { label: "✦ Strong Match", color: "var(--success)", bg: "rgba(71,255,184,0.12)", border: "rgba(71,255,184,0.25)" },
    medium: { label: "◈ Partial Match", color: "var(--warn)",    bg: "rgba(255,184,71,0.12)",  border: "rgba(255,184,71,0.25)"  },
    weak:   { label: "✕ Low Match",     color: "var(--danger)",  bg: "rgba(255,71,71,0.12)",   border: "rgba(255,71,71,0.25)"   },
  }[verdict];

  const stats = [
    { val: matched_skills.length,                          key: "Matched",  color: "var(--success)" },
    { val: missing_skills.length,                          key: "Missing",  color: "var(--danger)"  },
    { val: Math.round(meta.semantic_similarity * 100) + "%", key: "Semantic", color: "var(--accent)"  },
    { val: Math.round(meta.skill_coverage * 100) + "%",    key: "Coverage", color: "var(--accent2)" },
    { val: meta.total_jd_skills_detected,                  key: "JD Skills"                         },
    { val: meta.total_resume_skills_detected,              key: "Resume Skills"                     },
  ];

  return (
    <div style={{
      background: "var(--card)", border: "1px solid var(--border)",
      borderRadius: 16, padding: 28,
    }} className="fade-up">

      {/* Score + verdict */}
      <div style={{
        display: "grid", gridTemplateColumns: "auto 1fr",
        gap: 28, alignItems: "center", marginBottom: 24,
      }}>
        <ScoreRing score={match_score} />
        <div>
          <h2 style={{
            fontFamily: "var(--font-syne)", fontWeight: 800,
            fontSize: "1.5rem", letterSpacing: "-0.03em", marginBottom: 10,
          }}>
            Analysis Complete
          </h2>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            padding: "5px 12px", borderRadius: 100,
            fontFamily: "var(--font-dm-mono)", fontSize: "0.7rem",
            background: verdictMap.bg, color: verdictMap.color,
            border: `1px solid ${verdictMap.border}`, marginBottom: 12,
          }}>
            {verdictMap.label}
          </span>
          <p style={{
            fontSize: "0.86rem", color: "#b0b0c0", lineHeight: 1.75,
            borderLeft: "2px solid var(--border)", paddingLeft: 12,
          }}>
            {analysis}
          </p>
        </div>
      </div>

      {/* Stats grid */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
        gap: 10, marginBottom: 22,
      }}>
        {stats.map((s, i) => (
          <div key={i} style={{
            background: "var(--bg3)", border: "1px solid var(--border)",
            borderRadius: 10, padding: 14,
          }}>
            <div style={{
              fontFamily: "var(--font-syne)", fontWeight: 700,
              fontSize: "1.3rem", color: s.color || "var(--text)",
            }}>
              {s.val}
            </div>
            <div style={{
              fontFamily: "var(--font-dm-mono)", fontSize: "0.61rem",
              color: "var(--muted)", textTransform: "uppercase",
              letterSpacing: "0.08em", marginTop: 2,
            }}>
              {s.key}
            </div>
          </div>
        ))}
      </div>

      {/* Coverage bar */}
      <div style={{ marginBottom: 22 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.63rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
            Skill Coverage
          </span>
          <span style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.63rem", color: "var(--accent)" }}>
            {Math.round(meta.skill_coverage * 100)}%
          </span>
        </div>
        <div style={{ height: 4, background: "var(--bg3)", borderRadius: 100, overflow: "hidden" }}>
          <div style={{
            height: "100%", borderRadius: 100,
            width: `${meta.skill_coverage * 100}%`,
            background: "linear-gradient(90deg, var(--accent2), var(--accent))",
            transition: "width 1.2s cubic-bezier(0.34,1.56,0.64,1)",
          }} />
        </div>
      </div>

      {/* Skills */}
      <SectionHeader>Skills</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
        <div>
          <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.64rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 10 }}>
            ● Matched ({matched_skills.length})
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {matched_skills.length > 0
              ? matched_skills.map(s => <SkillTag key={s} name={s} type="matched" />)
              : <span style={{ fontSize: "0.76rem", color: "var(--muted)" }}>None found</span>}
          </div>
        </div>
        <div>
          <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.64rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 10 }}>
            ● Missing ({missing_skills.length})
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {missing_skills.length > 0
              ? missing_skills.map(s => <SkillTag key={s} name={s} type="missing" />)
              : <span style={{ fontSize: "0.76rem", color: "var(--muted)" }}>None 🎉</span>}
          </div>
        </div>
      </div>

      {extra_skills.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.64rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 10 }}>
            ● Extra Skills (not in JD)
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {extra_skills.map(s => <SkillTag key={s} name={s} type="extra" />)}
          </div>
        </div>
      )}

      {/* Experience gap */}
      <SectionHeader>Experience</SectionHeader>
      <div style={{
        background: "rgba(255,184,71,0.05)", border: "1px solid rgba(255,184,71,0.2)",
        borderRadius: 10, padding: "14px 16px", marginBottom: 4,
        display: "flex", gap: 12,
      }}>
        <span>⏱</span>
        <div>
          <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.61rem", color: "var(--warn)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>
            Gap Analysis
          </div>
          <div style={{ fontSize: "0.84rem", color: "#c0b880", lineHeight: 1.5 }}>
            {experience_gap}
          </div>
        </div>
      </div>

      {/* Rejection reasons */}
      <SectionHeader>Why Rejected</SectionHeader>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 4 }}>
        {rejection_reasons.map((r, i) => (
          <div key={i} style={{
            display: "flex", gap: 12, alignItems: "flex-start",
            background: "rgba(255,71,71,0.04)", border: "1px solid rgba(255,71,71,0.15)",
            borderRadius: 10, padding: "12px 14px",
          }}>
            <span>⚠</span>
            <span style={{ fontSize: "0.82rem", color: "#c0b0b0", lineHeight: 1.6 }}>{r}</span>
          </div>
        ))}
      </div>

      {/* Suggestions */}
      <SectionHeader>How to Improve</SectionHeader>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {improvement_suggestions.map((s, i) => (
          <div key={i} style={{
            display: "flex", gap: 12, alignItems: "flex-start",
            background: "rgba(71,255,232,0.04)", border: "1px solid rgba(71,255,232,0.15)",
            borderRadius: 10, padding: "12px 14px",
            transition: "all 0.2s",
          }}>
            <span style={{
              fontFamily: "var(--font-dm-mono)", fontSize: "0.64rem",
              color: "var(--accent2)", background: "rgba(71,255,232,0.12)",
              borderRadius: 4, padding: "2px 6px", flexShrink: 0, marginTop: 2,
            }}>
              #{String(i + 1).padStart(2, "0")}
            </span>
            <span style={{ fontSize: "0.82rem", color: "#b0c0c0", lineHeight: 1.6 }}>{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}