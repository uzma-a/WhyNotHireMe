"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { isLoggedIn, getCompanyName, logout } from "@/lib/auth";

export default function Navbar() {
  const router   = useRouter();
  const [loggedIn,     setLoggedIn]     = useState(false);
  const [companyName,  setCompanyName]  = useState("");

  useEffect(() => {
    setLoggedIn(isLoggedIn());
    setCompanyName(getCompanyName() || "");
  }, []);

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <nav style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "18px 40px", borderBottom: "1px solid var(--border)",
      background: "rgba(10,10,15,0.9)", backdropFilter: "blur(12px)",
      position: "sticky", top: 0, zIndex: 100,
    }}>
      {/* Logo */}
      <Link href="/" style={{ textDecoration: "none" }}>
        <span style={{
          fontFamily: "var(--font-syne)", fontWeight: 800,
          fontSize: "1.3rem", letterSpacing: "-0.02em", color: "var(--text)",
        }}>
          WhyNot<span style={{ color: "var(--accent)" }}>HireMe</span>
        </span>
      </Link>

      {/* Nav links */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <NavLink href="/candidate">For Candidates</NavLink>
        <NavLink href="/company">For Companies</NavLink>

        {loggedIn ? (
          <>
            <NavLink href="/dashboard">Dashboard</NavLink>
            <button onClick={handleLogout} style={{
              fontFamily: "var(--font-dm-mono)", fontSize: "0.72rem",
              background: "rgba(255,71,71,0.1)", color: "var(--danger)",
              border: "1px solid rgba(255,71,71,0.25)", borderRadius: "8px",
              padding: "8px 16px", cursor: "pointer", marginLeft: "8px",
            }}>
              Logout
            </button>
          </>
        ) : (
          <>
            <NavLink href="/auth/login">Login</NavLink>
            <Link href="/auth/register" style={{ textDecoration: "none" }}>
              <button style={{
                fontFamily: "var(--font-syne)", fontWeight: 700,
                fontSize: "0.82rem", background: "var(--accent)",
                color: "#0a0a0f", border: "none", borderRadius: "8px",
                padding: "8px 18px", cursor: "pointer", marginLeft: "4px",
              }}>
                Get Started
              </button>
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}

function NavLink({ href, children }) {
  return (
    <Link href={href} style={{
      fontFamily: "var(--font-dm-mono)", fontSize: "0.75rem",
      color: "var(--muted)", textDecoration: "none",
      padding: "8px 14px", borderRadius: "8px",
      transition: "color 0.2s",
    }}
      onMouseEnter={e => e.target.style.color = "var(--text)"}
      onMouseLeave={e => e.target.style.color = "var(--muted)"}
    >
      {children}
    </Link>
  );
}