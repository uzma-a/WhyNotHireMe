"use client";
import { useCallback, useRef, useState } from "react";

export default function UploadZone({ file, onFile }) {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef();

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type === "application/pdf") onFile(f);
  }, [onFile]);

  const borderColor = file ? "var(--success)" : drag ? "var(--accent)" : "var(--border)";
  const bg          = file ? "rgba(71,255,184,0.04)" : drag ? "rgba(232,255,71,0.04)" : "rgba(255,255,255,0.01)";

  return (
    <div
      onClick={() => inputRef.current.click()}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${borderColor}`,
        borderRadius: 12, padding: "32px 20px",
        textAlign: "center", cursor: "pointer",
        background: bg, transition: "all 0.25s",
      }}
    >
      <input
        ref={inputRef} type="file" accept=".pdf"
        style={{ display: "none" }}
        onChange={e => { if (e.target.files[0]) onFile(e.target.files[0]); }}
      />
      <div className="floating" style={{ fontSize: "2rem", marginBottom: 10 }}>
        {file ? "✅" : "📄"}
      </div>
      {file ? (
        <>
          <p style={{ fontWeight: 700, marginBottom: 6 }}>Resume loaded</p>
          <p style={{
            fontFamily: "var(--font-dm-mono)", fontSize: "0.75rem",
            color: "var(--success)",
          }}>
            📎 {file.name}
          </p>
          <p style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: 6 }}>
            Click to replace
          </p>
        </>
      ) : (
        <>
          <p style={{ fontWeight: 700, marginBottom: 6 }}>Drop resume here</p>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
            PDF format · max 10 MB
          </p>
        </>
      )}
    </div>
  );
}