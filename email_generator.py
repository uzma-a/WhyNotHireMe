"""
email_generator.py — Personalised rejection email generator.

Takes the analysis result and generates a human, warm rejection email
that includes honest feedback and improvement suggestions.

This is the core differentiator of WhyNotHireMe — turning a cold
"unfortunately" email into something that actually helps the candidate.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from matcher import MatchResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Input model
# ---------------------------------------------------------------------------

@dataclass
class EmailRequest:
    candidate_name:  str               # e.g. "Uzma Aasiya"
    role_title:      str               # e.g. "Backend Engineer"
    company_name:    str               # e.g. "Razorpay"
    match_result:    MatchResult       # from matcher.compute_match()
    hiring_manager:  Optional[str] = None   # e.g. "Priya Sharma" (optional)
    candidate_email: Optional[str] = None   # for display in output


# ---------------------------------------------------------------------------
# Tone helpers
# ---------------------------------------------------------------------------

def _score_verdict(score: int) -> tuple[str, str]:
    """
    Return (tone_label, opening_line) based on match score.

    Even low-scoring candidates get a respectful, warm tone.
    The difference is in how much encouragement vs. directness we use.
    """
    if score >= 70:
        return (
            "strong",
            "Your application stood out to us, and this was genuinely a difficult decision.",
        )
    elif score >= 45:
        return (
            "moderate",
            "We could see genuine potential in your application, and we want to be honest with you about where the gap was.",
        )
    else:
        return (
            "weak",
            "We want to be transparent with you, because we believe every candidate deserves to know where they stand.",
        )


def _format_strengths(matched_skills: list[str]) -> str:
    """Format matched skills into a readable sentence."""
    if not matched_skills:
        return "your willingness to apply and the effort you put into your application"
    if len(matched_skills) == 1:
        return f"your knowledge of {matched_skills[0].title()}"
    top = matched_skills[:4]
    skill_str = ", ".join(s.title() for s in top[:-1])
    return f"your skills in {skill_str} and {top[-1].title()}"


def _format_missing(missing_skills: list[str]) -> str:
    """Format missing skills into a readable sentence."""
    if not missing_skills:
        return ""
    top = missing_skills[:4]
    if len(top) == 1:
        return top[0].title()
    return ", ".join(s.title() for s in top[:-1]) + f" and {top[-1].title()}"


def _build_improvement_bullets(
    missing_skills: list[str],
    suggestions: list[str],
) -> str:
    """
    Build a bullet-point block of improvement tips for the email body.
    Mix skill-specific tips with general suggestions.
    """
    bullets: list[str] = []

    # Skill-specific tips (max 3)
    for skill in missing_skills[:3]:
        skill_lower = skill.lower()
        if skill_lower in {"docker", "kubernetes"}:
            bullets.append(
                f"• {skill.title()} — Containerise a personal project using Docker. "
                "Start with a simple docker-compose setup and deploy it to a free cloud tier."
            )
        elif skill_lower in {"aws", "azure", "gcp"}:
            bullets.append(
                f"• {skill.upper()} — The free tier is a great place to start. "
                "Consider the AWS Cloud Practitioner certification as a structured entry point."
            )
        elif skill_lower in {"machine learning", "deep learning", "nlp"}:
            bullets.append(
                f"• {skill.title()} — Complete one project on Kaggle or build a small "
                "end-to-end ML pipeline and publish it on GitHub."
            )
        elif skill_lower in {"react", "angular", "vue", "next.js"}:
            bullets.append(
                f"• {skill.title()} — Build and deploy a full CRUD application. "
                "A live project on Vercel speaks louder than a certificate."
            )
        elif skill_lower in {"fastapi", "django", "flask"}:
            bullets.append(
                f"• {skill.title()} — Build a REST API with authentication, "
                "connect it to a database, and document it with Swagger."
            )
        else:
            bullets.append(
                f"• {skill.title()} — Spend 2–3 weeks on a focused side project "
                "that uses this technology in a real context."
            )

    # General suggestions (fill remaining spots up to 5 total)
    remaining = 5 - len(bullets)
    for suggestion in suggestions[:remaining]:
        # Avoid duplicating skill-specific ones already added
        already_covered = any(
            skill.lower() in suggestion.lower() for skill in missing_skills[:3]
        )
        if not already_covered:
            bullets.append(f"• {suggestion}")

    return "\n".join(bullets)


# ---------------------------------------------------------------------------
# Main email generator
# ---------------------------------------------------------------------------

def generate_rejection_email(req: EmailRequest) -> dict:
    """
    Generate a complete, personalised rejection email with feedback.

    Returns a dict with:
    - subject:       Email subject line
    - body:          Full plain-text email body
    - html_body:     HTML version for email clients
    - summary:       One-line summary of the feedback
    - match_score:   Numeric score for reference
    """
    score   = req.match_result.match_score
    tone, opening = _score_verdict(score)

    candidate_first = req.candidate_name.strip().split()[0] if req.candidate_name else "there"
    hiring_sign     = req.hiring_manager or f"{req.company_name} Hiring Team"

    strengths_str = _format_strengths(req.match_result.matched_skills)
    missing_str   = _format_missing(req.match_result.missing_skills)

    improvement_bullets = _build_improvement_bullets(
        req.match_result.missing_skills,
        _generate_suggestions(req.match_result),
    )

    # Score band label
    if score >= 70:
        score_label = "Strong Match"
        score_note  = "You were close — keep applying to similar roles."
    elif score >= 45:
        score_label = "Partial Match"
        score_note  = "With a few targeted improvements, you would be competitive."
    else:
        score_label = "Early Stage Match"
        score_note  = "The gap is bridgeable — most of what is missing can be learned in 2–3 months."

    # Experience gap line
    exp_line = ""
    if req.match_result.experience_gap and "no explicit" not in req.match_result.experience_gap.lower():
        exp_line = f"\n⏱  Experience: {req.match_result.experience_gap}"

    # Skill lines
    matched_line = ""
    if req.match_result.matched_skills:
        matched_line = f"✅ What we noticed: {', '.join(s.title() for s in req.match_result.matched_skills[:5])}"

    missing_line = ""
    if missing_str:
        missing_line = f"📌 Where the gap was: {missing_str}"

    # ── Plain text body ──────────────────────────────────────────────────────
    body = f"""Subject: Your application for {req.role_title} at {req.company_name}

Dear {candidate_first},

Thank you for taking the time to apply for the {req.role_title} position at {req.company_name}.

{opening}

After a careful review of your application, we have decided to move forward with other candidates at this time. We know this is not the news you were hoping for, and we genuinely appreciate the effort you invested.

We believe every candidate deserves more than a generic rejection. So here is an honest, transparent look at where things stood:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  YOUR PROFILE SNAPSHOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Match Score:  {score}/100  ({score_label})
  {score_note}
{exp_line}

  {matched_line}
  {missing_line}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  WHAT YOU CAN DO NEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We have put together some specific steps that would make you a stronger candidate for roles like this one:

{improvement_bullets}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

We genuinely hope this feedback is useful. The gap between where you are and where you want to be is smaller than it might feel right now. Most of what is missing can be built with focused effort over the next few months.

We wish you every success in your journey, {candidate_first}. Please do not hesitate to apply again in the future as you grow your skills.

Warm regards,
{hiring_sign}
{req.company_name}

---
This feedback was generated to help you grow.
Powered by WhyNotHireMe — making hiring more human, one email at a time.
"""

    # ── HTML body ────────────────────────────────────────────────────────────
    improvement_html = "\n".join(
        f"<li style='margin-bottom:10px;color:#334155;'>{line.lstrip('• ')}</li>"
        for line in improvement_bullets.splitlines()
        if line.strip()
    )

    score_color = "#16a34a" if score >= 70 else "#d97706" if score >= 45 else "#dc2626"

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Application Update — {req.company_name}</title>
</head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#0f172a;padding:32px 40px;">
            <p style="margin:0;color:#94a3b8;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Application Update</p>
            <h1 style="margin:8px 0 0;color:#f8fafc;font-size:24px;font-weight:700;">{req.company_name}</h1>
            <p style="margin:4px 0 0;color:#64748b;font-size:14px;">{req.role_title}</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">

            <p style="color:#334155;font-size:16px;margin:0 0 8px;">Dear {candidate_first},</p>
            <p style="color:#64748b;font-size:14px;line-height:1.7;margin:0 0 24px;">
              Thank you for applying for the <strong>{req.role_title}</strong> position at {req.company_name}.
              {opening}
            </p>
            <p style="color:#64748b;font-size:14px;line-height:1.7;margin:0 0 32px;">
              After careful review, we have decided to move forward with other candidates at this time.
              We know this is not the news you were hoping for — and we want to give you more than just a standard rejection.
            </p>

            <!-- Score card -->
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:32px;">
              <tr>
                <td style="padding:24px;">
                  <p style="margin:0 0 16px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#94a3b8;font-weight:600;">Your Profile Snapshot</p>

                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding-bottom:16px;">
                        <span style="font-size:13px;color:#64748b;">Match Score</span><br/>
                        <span style="font-size:32px;font-weight:800;color:{score_color};">{score}</span>
                        <span style="font-size:16px;color:#94a3b8;">/100</span>
                        <span style="display:inline-block;margin-left:12px;background:{score_color}18;color:{score_color};font-size:11px;padding:3px 10px;border-radius:100px;font-weight:600;">{score_label}</span>
                      </td>
                    </tr>
                    {"<tr><td style='padding-bottom:12px;'><span style='font-size:13px;color:#16a34a;font-weight:600;'>✅ Strengths noticed:</span><br/><span style='font-size:13px;color:#475569;'>" + ", ".join(s.title() for s in req.match_result.matched_skills[:5]) + "</span></td></tr>" if req.match_result.matched_skills else ""}
                    {"<tr><td style='padding-bottom:12px;'><span style='font-size:13px;color:#dc2626;font-weight:600;'>📌 Where the gap was:</span><br/><span style='font-size:13px;color:#475569;'>" + missing_str + "</span></td></tr>" if missing_str else ""}
                    {"<tr><td><span style='font-size:13px;color:#d97706;font-weight:600;'>⏱ Experience:</span><br/><span style='font-size:13px;color:#475569;'>" + req.match_result.experience_gap + "</span></td></tr>" if req.match_result.experience_gap and "no explicit" not in req.match_result.experience_gap.lower() else ""}
                  </table>
                </td>
              </tr>
            </table>

            <!-- Improvements -->
            <p style="font-size:16px;font-weight:700;color:#0f172a;margin:0 0 16px;">What you can do next 💡</p>
            <p style="font-size:13px;color:#64748b;margin:0 0 16px;line-height:1.6;">
              Here are specific steps that would make you a much stronger candidate for roles like this one:
            </p>
            <ul style="padding-left:0;margin:0 0 32px;list-style:none;">
              {improvement_html}
            </ul>

            <!-- Closing -->
            <div style="border-top:1px solid #e2e8f0;padding-top:24px;">
              <p style="color:#64748b;font-size:14px;line-height:1.7;margin:0 0 16px;">
                We genuinely hope this is useful, {candidate_first}. The gap between where you are and where you want to be is smaller than it might feel right now.
              </p>
              <p style="color:#64748b;font-size:14px;line-height:1.7;margin:0;">
                Warm regards,<br/>
                <strong style="color:#0f172a;">{hiring_sign}</strong><br/>
                <span style="color:#94a3b8;">{req.company_name}</span>
              </p>
            </div>

          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f1f5f9;padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:11px;color:#94a3b8;">
              Feedback powered by <strong>WhyNotHireMe</strong> — making hiring more human, one email at a time.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    summary = (
        f"{candidate_first} scored {score}/100 for {req.role_title}. "
        f"Top gap: {missing_str or 'general profile alignment'}."
    )

    return {
        "subject":     f"Your application for {req.role_title} at {req.company_name}",
        "body":        body.strip(),
        "html_body":   html_body.strip(),
        "summary":     summary,
        "match_score": score,
        "tone":        tone,
        "to":          req.candidate_email or "",
    }


# ---------------------------------------------------------------------------
# Internal suggestion builder (mirrors analyzer.py but email-friendly)
# ---------------------------------------------------------------------------

def _generate_suggestions(result: MatchResult) -> list[str]:
    suggestions = []
    if result.match_score < 50:
        suggestions.append(
            "Tailor your resume to mirror the exact language of each job description."
        )
    if result.semantic_similarity < 0.4:
        suggestions.append(
            "Rewrite your professional summary to focus on the specific domain this role requires."
        )
    if len(result.extra_skills) > len(result.matched_skills):
        suggestions.append(
            "Create a role-specific resume that highlights the most relevant skills rather than listing everything."
        )
    suggestions.append(
        "Add a Projects section with 2–3 deployed projects that demonstrate practical skills."
    )
    return suggestions