"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerCompany, loginCompany } from "@/lib/api";
import { saveAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [companyName, setCompanyName] = useState("");
  const [email,       setEmail]       = useState("");
  const [password,    setPassword]    = useState("");
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);

  async function handleRegister(e) {
    e.preventDefault();
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setLoading(true); setError(null);
    try {
      await registerCompany({ company_name: companyName, email, password });
      // Auto-login after register
      const data = await loginCompany({ email, password });
      saveAuth(data);
      router.push("/dashboard");
    } catch (err) {
      setError(err?.response?.data?.detail || "Registration failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    width: "100%", background: "rgba(255,255,255,0.03)",
    border: "1px solid var(--border)", borderRadius: 10,
    color: "var(--text)", fontSize: "0.95rem",
    padding: "13px 16px", outline: "none",
    fontFamily: "var(--font-syne)", marginTop: 6,
  };

  return (
    <main style={{
      minHeight: "100vh", display: "flex",
      alignItems: "center", justifyContent: "center",
      padding: 24, background: "var(--bg)",
    }}>
      <div style={{ width: "100%", maxWidth: 440 }}>

        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <span style={{ fontFamily: "var(--font-syne)", fontWeight: 800, fontSize: "1.5rem", letterSpacing: "-0.02em", color: "var(--text)" }}>
              WhyNot<span style={{ color: "var(--accent)" }}>HireMe</span>
            </span>
          </Link>
          <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginTop: 8 }}>
            Register your company
          </p>
        </div>

        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 16, padding: 36 }}>
          <h1 style={{ fontFamily: "var(--font-syne)", fontWeight: 800, fontSize: "1.5rem", marginBottom: 28 }}>
            Get started free
          </h1>

          <form onSubmit={handleRegister}>
            <div style={{ marginBottom: 18 }}>
              <label style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.65rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Company Name
              </label>
              <input type="text" required value={companyName} onChange={e => setCompanyName(e.target.value)} placeholder="e.g. Razorpay" style={inputStyle} />
            </div>
            <div style={{ marginBottom: 18 }}>
              <label style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.65rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Work Email
              </label>
              <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="hr@company.com" style={inputStyle} />
            </div>
            <div style={{ marginBottom: 28 }}>
              <label style={{ fontFamily: "var(--font-dm-mono)", fontSize: "0.65rem", color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                Password
              </label>
              <input type="password" required value={password} onChange={e => setPassword(e.target.value)} placeholder="Min 8 characters" style={inputStyle} />
            </div>

            {error && (
              <div style={{ background: "rgba(255,71,71,0.08)", border: "1px solid rgba(255,71,71,0.25)", borderRadius: 8, padding: "10px 14px", marginBottom: 20, fontSize: "0.82rem", color: "var(--danger)" }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} style={{
              width: "100%", padding: 15,
              background: "var(--accent)", color: "#0a0a0f",
              fontFamily: "var(--font-syne)", fontWeight: 700, fontSize: "1rem",
              border: "none", borderRadius: 10, cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            }}>
              {loading ? (
                <><span className="spinning" style={{ width: 16, height: 16, border: "2px solid rgba(0,0,0,0.3)", borderTopColor: "#0a0a0f", borderRadius: "50%", display: "inline-block" }} /> Creating account…</>
              ) : "Create Account →"}
            </button>
          </form>

          <p style={{ textAlign: "center", marginTop: 20, fontSize: "0.84rem", color: "var(--muted)" }}>
            Already registered?{" "}
            <Link href="/auth/login" style={{ color: "var(--accent)", textDecoration: "none", fontWeight: 600 }}>
              Login
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}