"use client";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import UploadZone from "@/components/UploadZone";
import { generateRejectionEmail } from "@/lib/api";
import axios from "axios";
import { getToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CompanyPage() {
  const [file,        setFile]        = useState(null);
  const [jd,          setJd]          = useState("");
  const [cname,       setCname]       = useState("");
  const [role,        setRole]        = useState("");
  const [company,     setCompany]     = useState("");
  const [hm,          setHm]          = useState("");
  const [cemail,      setCemail]      = useState("");
  const [loading,     setLoading]     = useState(false);
  const [sending,     setSending]     = useState(false);
  const [result,      setResult]      = useState(null);
  const [error,       setError]       = useState(null);
  const [copied,      setCopied]      = useState("");
  const [sendStatus,  setSendStatus]  = useState(null); // {success, message}

  const canSubmit = file && jd.trim().length > 30 && cname.trim() && role.trim() && company.trim() && !loading;
  const canSend   = result && cemail.includes("@") && !sending;

  async function handleGenerate() {
    if (!canSubmit) return;
    setLoading(true); setResult(null); setError(null); setSendStatus(null);
    try {
      const data = await generateRejectionEmail({
        resumeFile: file, jobDescription: jd,
        candidateName: cname, roleTitle: role,
        companyName: company, hiringManager: hm, candidateEmail: cemail,
      });
      setResult(data);
      setTimeout(() => document.getElementById("email-out")?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSendEmail() {
    if (!canSend) return;
    setSending(true); setSendStatus(null);
    try {
      const form = new FormData();
      form.append("resume",          file);
      form.append("job_description", jd);
      form.append("candidate_name",  cname);
      form.append("candidate_email", cemail);
      form.append("role_title",      role);
      form.append("company_name",    company);
      form.append("hiring_manager",  hm || "");

      const token = getToken();
      const res = await axios.post(`${API_BASE}/send-rejection-email`, form, {
        headers: {
          "Content-Type": "multipart/form-data",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      setSendStatus({ success: true, message: `Email sent to ${cemail} successfully!` });
    } catch (e) {
      const msg = e?.response?.data?.detail || e.message || "Failed to send email.";
      setSendStatus({ success: false, message: msg });
    } finally {
      setSending(false);
    }
  }

  function copy(text, key) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(""), 2000);
    });
  }

  const score = result?.analysis?.match_score;
  const scoreColor = score >= 70 ? "var(--success)" : score >= 45 ? "var(--warn)" : "var(--danger)";

  const inputStyle = {
    width: "100%", background: "rgba(255,255,255,0.03)",
    border: "1px solid var(--border)", borderRadius: 10,
    color: "var(--text)", fontSize: "0.9rem",
    padding: "11px 14px", outline: "none",
    fontFamily: "var(--font-syne)",
  };
  const labelStyle = {
    fontFamily: "var(--font-dm-mono)", fontSize: "0.65rem",
    textTransform: "uppercase", letterSpacing: "0.08em",
    color: "var(--muted)", marginBottom: 6, display: "block",
  };

  return (
    <>
      <Navbar />
      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px 60px" }}>

        {/* Hero */}
        <div style={{ textAlign: "center", padding: "60px 0 48px" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            fontFamily: "var(--font-dm-mono)", fontSize: "0.72rem",
            color: "var(--accent)", background: "rgba(232,255,71,0.08)",
            border: "1px solid rgba(232,255,71,0.2)", padding: "6px 14px",
            borderRadius: 100, marginBottom: 20, letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}>
            For Companies
          </div>
          <h1 style={{
            fontFamily: "var(--font-syne)", fontWeight: 800,
            fontSize: "clamp(2rem, 5vw, 3.2rem)", letterSpacing: "-0.03em", marginBottom: 14,
          }}>
            Turn rejection into <span style={{ color: "var(--accent)" }}>respect.</span>
          </h1>
          <p style={{ fontSize: "1rem", color: "var(--muted)", lineHeight: 1.7, maxWidth: 500, margin: "0 auto" }}>
            Generate a warm, honest rejection email with real feedback — ready to send in one click.
          </p>
        </div>

        {/* Input grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 20 }}>

          {/* Left — resume + candidate */}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 16, padding: 28 }}>
            <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16 }}>
              Step 01 — Resume & Candidate
            </p>
            <UploadZone file={file} onFile={setFile} />
            <div style={{ marginTop: 20 }}>
              <div style={{ marginBottom: 14 }}>
                <label style={labelStyle}>Candidate Full Name *</label>
                <input type="text" placeholder="e.g. Uzma Aasiya" value={cname} onChange={e => setCname(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Candidate Email (optional)</label>
                <input type="email" placeholder="candidate@email.com" value={cemail} onChange={e => setCemail(e.target.value)} style={inputStyle} />
              </div>
            </div>
          </div>

          {/* Right — role + JD */}
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 16, padding: 28 }}>
            <p style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16 }}>
              Step 02 — Role & Company
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
              <div>
                <label style={labelStyle}>Role Title *</label>
                <input type="text" placeholder="Backend Engineer" value={role} onChange={e => setRole(e.target.value)} style={inputStyle} />
              </div>
              <div>
                <label style={labelStyle}>Company Name *</label>
                <input type="text" placeholder="Razorpay" value={company} onChange={e => setCompany(e.target.value)} style={inputStyle} />
              </div>
            </div>
            <div style={{ marginBottom: 14 }}>
              <label style={labelStyle}>Hiring Manager (optional)</label>
              <input type="text" placeholder="Priya Sharma" value={hm} onChange={e => setHm(e.target.value)} style={inputStyle} />
            </div>
            <label style={labelStyle}>Job Description *</label>
            <textarea
              value={jd} onChange={e => setJd(e.target.value)}
              placeholder="Paste the full job description here…"
              style={{
                width: "100%", background: "rgba(255,255,255,0.03)",
                border: "1px solid var(--border)", borderRadius: 10,
                color: "var(--text)", fontFamily: "var(--font-dm-mono)",
                fontSize: "0.8rem", lineHeight: 1.6, padding: 14,
                resize: "vertical", minHeight: 150, outline: "none",
              }}
            />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 5 }}>
              <span style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.62rem", color: "var(--muted)" }}>{jd.length} / 20,000</span>
            </div>
          </div>
        </div>

        {/* Generate button */}
        <button onClick={handleGenerate} disabled={!canSubmit} style={{
          width: "100%", padding: 17,
          background: loading ? "var(--bg3)" : "var(--accent)",
          color: loading ? "var(--accent)" : "#0a0a0f",
          border: loading ? "1px solid var(--accent)" : "none",
          fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1rem",
          borderRadius: 12, cursor: canSubmit ? "pointer" : "not-allowed",
          opacity: !canSubmit && !loading ? 0.5 : 1,
          display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
          marginBottom: 24, transition: "all 0.2s",
        }}>
          {loading ? (
            <><span className="spinning" style={{ width: 18, height: 18, border: "2px solid rgba(232,255,71,0.3)", borderTopColor: "var(--accent)", borderRadius: "50%", display: "inline-block" }} /> Generating rejection email…</>
          ) : !file ? "📄 Upload resume first"
            : !cname.trim() ? "👤 Enter candidate name"
            : !role.trim() ? "💼 Enter role title"
            : !company.trim() ? "🏢 Enter company name"
            : jd.trim().length < 30 ? "📝 Add job description"
            : "✉️ Generate Rejection Email"}
        </button>

        {/* Error */}
        {error && (
          <div style={{ background: "rgba(255,71,71,0.08)", border: "1px solid rgba(255,71,71,0.3)", borderRadius: 12, padding: "18px 22px", marginBottom: 24, display: "flex", gap: 12 }}>
            <span>🚨</span>
            <div>
              <p style={{ color: "var(--danger)", fontWeight: 700, marginBottom: 4 }}>Generation Failed</p>
              <p style={{ fontSize: "0.82rem", color: "#c09090" }}>{error}</p>
            </div>
          </div>
        )}

        <div id="email-out" />

        {/* Result */}
        {result && (
          <>
            {/* Score summary */}
            <div style={{
              display: "flex", alignItems: "center", gap: 20,
              padding: "18px 22px", background: "var(--card)",
              border: "1px solid var(--border)", borderRadius: 12,
              marginBottom: 16, flexWrap: "wrap",
            }} className="fade-in">
              <div>
                <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.62rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 2 }}>Match Score</div>
                <div style={{ fontFamily: "var(--font-syne)", fontWeight: 800, fontSize: "1.7rem", color: scoreColor, lineHeight: 1 }}>
                  {score}<span style={{ fontSize: "0.85rem", color: "var(--muted)", fontWeight: 400 }}>/100</span>
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 180 }}>
                <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.62rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>Skill Coverage</div>
                <div style={{ height: 4, background: "var(--bg3)", borderRadius: 100, overflow: "hidden" }}>
                  <div style={{ height: "100%", borderRadius: 100, width: `${result.analysis.meta.skill_coverage * 100}%`, background: "linear-gradient(90deg, var(--accent2), var(--accent))", transition: "width 1.2s ease" }} />
                </div>
              </div>
              <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.72rem", color: "var(--muted)" }}>
                ✅ {result.analysis.matched_skills.length} matched &nbsp;|&nbsp; ❌ {result.analysis.missing_skills.length} missing
              </div>
            </div>

            {/* Email output */}
            <div style={{ background: "var(--bg3)", border: "1px solid var(--border)", borderRadius: 12, overflow: "hidden" }} className="fade-up">
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "14px 20px", borderBottom: "1px solid var(--border)",
                background: "rgba(255,255,255,0.02)", flexWrap: "wrap", gap: 10,
              }}>
                <div>
                  <div style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.64rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 3 }}>
                    ✉️ Ready to send
                  </div>
                  <div style={{ fontSize: "0.88rem", fontWeight: 600 }}>{result.email.subject}</div>
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button onClick={() => copy(result.email.body, "plain")} style={{
                    fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem",
                    background: "rgba(232,255,71,0.1)", color: "var(--accent)",
                    border: "1px solid rgba(232,255,71,0.25)", borderRadius: 6,
                    padding: "6px 14px", cursor: "pointer",
                  }}>
                    {copied === "plain" ? "✓ Copied!" : "Copy Text"}
                  </button>
                  <button onClick={() => copy(result.email.html_body, "html")} style={{
                    fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem",
                    background: "rgba(71,255,232,0.1)", color: "var(--accent2)",
                    border: "1px solid rgba(71,255,232,0.25)", borderRadius: 6,
                    padding: "6px 14px", cursor: "pointer",
                  }}>
                    {copied === "html" ? "✓ Copied!" : "Copy HTML"}
                  </button>

                  {/* SEND DIRECTLY TO CANDIDATE */}
                  <button
                    onClick={handleSendEmail}
                    disabled={!canSend}
                    style={{
                      fontFamily: "var(--font-dm-mono)", fontSize: "0.68rem",
                      background: canSend ? "var(--accent)" : "rgba(255,255,255,0.05)",
                      color: canSend ? "#0a0a0f" : "var(--muted)",
                      border: "none", borderRadius: 6,
                      padding: "6px 18px",
                      cursor: canSend ? "pointer" : "not-allowed",
                      fontWeight: 700,
                      display: "flex", alignItems: "center", gap: 6,
                    }}
                  >
                    {sending
                      ? <><span className="spinning" style={{ width: 12, height: 12, border: "2px solid rgba(0,0,0,0.2)", borderTopColor: "#0a0a0f", borderRadius: "50%", display: "inline-block" }}/> Sending…</>
                      : !cemail.includes("@") ? "⚠ Add email to send"
                      : "📨 Send to Candidate"}
                  </button>
                </div>
              </div>

              {/* Send status message */}
              {sendStatus && (
                <div style={{
                  padding: "12px 20px",
                  background: sendStatus.success ? "rgba(71,255,184,0.08)" : "rgba(255,71,71,0.08)",
                  borderBottom: `1px solid ${sendStatus.success ? "rgba(71,255,184,0.2)" : "rgba(255,71,71,0.2)"}`,
                  display: "flex", alignItems: "center", gap: 10,
                  fontFamily: "var(--font-dm-mono)", fontSize: "0.76rem",
                  color: sendStatus.success ? "var(--success)" : "var(--danger)",
                }}>
                  {sendStatus.success ? "✅" : "❌"} {sendStatus.message}
                </div>
              )}
              <pre style={{
                fontFamily: "var(--font-dm-mono)", fontSize: "0.76rem",
                lineHeight: 1.85, color: "#c0c0d0", padding: 24,
                whiteSpace: "pre-wrap", maxHeight: 560, overflowY: "auto",
              }}>
                {result.email.body}
              </pre>
            </div>
          </>
        )}

        {!result && !error && !loading && (
          <div style={{ textAlign: "center", padding: "50px 24px", color: "var(--muted)" }}>
            <div style={{ fontSize: "2.5rem", marginBottom: 14, opacity: 0.4 }}>✉️</div>
            <p style={{ fontSize: "0.88rem", lineHeight: 1.6 }}>Fill in the details above to generate a personalised rejection email.</p>
          </div>
        )}

      </main>
    </>
  );
}