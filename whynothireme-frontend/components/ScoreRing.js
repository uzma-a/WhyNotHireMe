"use client";
import { useEffect, useState } from "react";

export default function ScoreRing({ score }) {
  const [displayed, setDisplayed] = useState(0);
  const circumference = 565;
  const color = score >= 70 ? "#47ffb8" : score >= 45 ? "#ffb847" : "#ff4747";

  useEffect(() => {
    const t = setTimeout(() => setDisplayed(score), 150);
    return () => clearTimeout(t);
  }, [score]);

  const offset = circumference - (displayed / 100) * circumference;

  return (
    <div style={{ position: "relative", width: 160, height: 160, flexShrink: 0 }}>
      <svg viewBox="0 0 200 200" width="160" height="160"
        style={{ transform: "rotate(-90deg)" }}>
        <circle cx="100" cy="100" r="90"
          fill="none" stroke="var(--bg3)" strokeWidth="12" />
        <circle cx="100" cy="100" r="90"
          fill="none" stroke={color} strokeWidth="12"
          strokeLinecap="round" strokeDasharray="565"
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1.4s cubic-bezier(0.34,1.56,0.64,1)" }}
        />
      </svg>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
      }}>
        <span style={{
          fontFamily: "var(--font-syne)", fontWeight: 800,
          fontSize: "2.4rem", lineHeight: 1, color, letterSpacing: "-0.04em",
        }}>
          {score}
        </span>
        <span style={{
          fontFamily: "var(--font-dm-mono)", fontSize: "0.6rem",
          color: "var(--muted)", textTransform: "uppercase",
          letterSpacing: "0.08em", marginTop: 4,
        }}>
          / 100
        </span>
      </div>
    </div>
  );
}