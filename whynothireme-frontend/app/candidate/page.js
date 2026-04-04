"use client";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import UploadZone from "@/components/UploadZone";
import ResultPanel from "@/components/ResultPanel";
import { analyzeResume } from "@/lib/api";

export default function CandidatePage() {
  const [file,    setFile]    = useState(null);
  const [jd,      setJd]      = useState("");
  const [loading, setLoading] = useState(false);
  const [result,  setResult]  = useState(null);
  const [error,   setError]   = useState(null);

  const canSubmit = file && jd.trim().length > 30 && !loading;

  async function handleAnalyze() {
    if (!canSubmit) return;
    setLoading(true); setResult(null); setError(null);
    try {
      const data = await analyzeResume({ resumeFile: file, jobDescription: jd });
      setResult(data);
      setTimeout(() => document.getElementById("results")?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Navbar />
      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px 60px" }}>

        {/* Hero */}
        <div style={{ textAlign: "center", padding: "60px 0 48px" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            fontFamily: "var(--font-dm-mono)", fontSize: "0.72rem",
            color: "var(--accent2)", background: "rgba(71,255,232,0.08)",
            border: "1px solid rgba(71,255,232,0.2)", padding: "6px 14px",
            borderRadius: 100, marginBottom: 20, letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}>
            <span className="pulsing" style={{ width: 6, height: 6, background: "var(--accent2)", borderRadius: "50%", display: "inline-block" }} />
            For Candidates
          </div>
          <h1 style={{
            fontFamily: "var(--font-syne)", fontWeight: 800,
            fontSize: "clamp(2rem, 5vw, 3.2rem)", letterSpacing: "-0.03em", marginBottom: 14,
          }}>
            Find out <span style={{ color: "var(--accent)" }}>exactly</span> why<br />you didn't get hired.
          </h1>
          <p style={{ fontSize: "1rem", color: "var(--muted)", lineHeight: 1.7, maxWidth: 480, margin: "0 auto" }}>
            Upload your resume and paste the job description. Get a full match report in seconds.
          </p>
        </div>

        {/* Input grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 20 }}>

          {/* Resume */}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 16, padding: 28 }}>
            <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 16, height: 1, background: "var(--muted)", display: "inline-block" }} />
              Step 01 — Resume
            </p>
            <UploadZone file={file} onFile={setFile} />
          </div>

          {/* JD */}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 16, padding: 28 }}>
            <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 16, height: 1, background: "var(--muted)", display: "inline-block" }} />
              Step 02 — Job Description
            </p>
            <textarea
              value={jd} onChange={e => setJd(e.target.value)}
              placeholder="Paste the full job description here…"
              style={{
                width: "100%", background: "rgba(255,255,255,0.03)",
                border: "1px solid var(--border)", borderRadius: 10,
                color: "var(--text)", fontFamily: "var(--font-dm-mono)",
                fontSize: "0.8rem", lineHeight: 1.6, padding: 14,
                resize: "vertical", minHeight: 200, outline: "none",
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
              <span style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.62rem", color: "var(--muted)" }}>
                {jd.length} / 20,000
              </span>
              {jd.length > 30 && (
                <span style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.62rem", color: "var(--success)" }}>✓ Ready</span>
              )}
            </div>
          </div>
        </div>

        {/* Analyze button */}
        <button
          onClick={handleAnalyze}
          disabled={!canSubmit}
          style={{
            width: "100%", padding: 17,
            background: loading ? "var(--bg3)" : "var(--accent)",
            color: loading ? "var(--accent)" : "#0a0a0f",
            border: loading ? "1px solid var(--accent)" : "none",
            fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1rem",
            borderRadius: 12, cursor: canSubmit ? "pointer" : "not-allowed",
            opacity: !canSubmit && !loading ? 0.5 : 1,
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
            marginBottom: 24, transition: "all 0.2s",
          }}
        >
          {loading ? (
            <>
              <span className="spinning" style={{
                width: 18, height: 18, border: "2px solid rgba(232,255,71,0.3)",
                borderTopColor: "var(--accent)", borderRadius: "50%", display: "inline-block",
              }} />
              Analyzing your profile…
            </>
          ) : !file ? "📄 Upload resume first"
            : jd.trim().length < 30 ? "📝 Add job description"
            : "⚡ Analyze My Resume"}
        </button>

        {/* Error */}
        {error && (
          <div style={{
            background: "rgba(255,71,71,0.08)", border: "1px solid rgba(255,71,71,0.3)",
            borderRadius: 12, padding: "18px 22px", marginBottom: 24,
            display: "flex", gap: 12,
          }}>
            <span>🚨</span>
            <div>
              <p style={{ color: "var(--danger)", fontWeight: 700, marginBottom: 4 }}>Analysis Failed</p>
              <p style={{ fontSize: "0.82rem", color: "#c09090" }}>{error}</p>
              <p style={{ fontSize: "0.76rem", color: "var(--muted)", marginTop: 6 }}>
                Make sure the backend is running at localhost:8000
              </p>
            </div>
          </div>
        )}

        {/* Results */}
        <div id="results" />
        {result && <ResultPanel data={result} />}

        {/* Empty state */}
        {!result && !error && !loading && (
          <div style={{ textAlign: "center", padding: "50px 24px", color: "var(--muted)" }}>
            <div style={{ fontSize: "2.5rem", marginBottom: 14, opacity: 0.4 }}>🔍</div>
            <p style={{ fontSize: "0.88rem", lineHeight: 1.6 }}>
              Upload your resume and paste a job description to get started.
            </p>
          </div>
        )}

      </main>
    </>
  );
}