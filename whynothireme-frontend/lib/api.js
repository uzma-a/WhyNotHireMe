import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Axios instance
const api = axios.create({ baseURL: BASE_URL });

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("wnhm_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ────────────────────────────────────────────────────────────────────

export async function registerCompany({ company_name, email, password }) {
  const res = await api.post("/auth/register", { company_name, email, password });
  return res.data;
}

export async function loginCompany({ email, password }) {
  const res = await api.post("/auth/login", { email, password });
  return res.data;
}

export async function getMe() {
  const res = await api.get("/auth/me");
  return res.data;
}

export async function getHistory(limit = 20, offset = 0) {
  const res = await api.get(`/auth/history?limit=${limit}&offset=${offset}`);
  return res.data;
}

// ── Analysis ────────────────────────────────────────────────────────────────

export async function analyzeResume({ resumeFile, jobDescription }) {
  const form = new FormData();
  form.append("resume", resumeFile);
  form.append("job_description", jobDescription);
  const res = await api.post("/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// ── Rejection Email ─────────────────────────────────────────────────────────

export async function generateRejectionEmail({
  resumeFile,
  jobDescription,
  candidateName,
  roleTitle,
  companyName,
  hiringManager,
  candidateEmail,
}) {
  const form = new FormData();
  form.append("resume", resumeFile);
  form.append("job_description", jobDescription);
  form.append("candidate_name", candidateName);
  form.append("role_title", roleTitle);
  form.append("company_name", companyName);
  form.append("hiring_manager", hiringManager || "");
  form.append("candidate_email", candidateEmail || "");
  const res = await api.post("/generate-rejection-email", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// ── Health ──────────────────────────────────────────────────────────────────

export async function checkHealth() {
  const res = await api.get("/health");
  return res.data;
}