#!/usr/bin/env python3
"""
AI Report Pipeline - DEMO
=========================
Turns a raw text input (here: a meeting transcript) into a structured,
branded PDF report. Portfolio/demo piece by Dror M.

Design points a client cares about:
  * MOCK MODE by default - runs end-to-end with NO API key and NO cost,
    so you (or I) can verify the whole pipeline before spending a cent on tokens.
  * The prompt lives in an EXTERNAL, editable template (PROMPT_TEMPLATE below) -
    you change what the AI extracts without touching the code.
  * Swapping in a real model is one function (call_llm) - OpenAI or Anthropic;
    drop your key in the environment and set the provider.
  * Ships with an embedded self-test (_self_test) that must pass before delivery.
  * English output shown here; the PDF layer also supports Hebrew RTL.

Run it:   python ai_report_pipeline.py
          -> writes ai_report_demo_output.pdf and runs its own tests.
"""

import json
import os

PROMPT_TEMPLATE = """You are an analyst. Read the transcript and return STRICT JSON with keys:
  "summary"      : 2-3 sentence executive summary,
  "decisions"    : list of decisions made,
  "action_items" : list of objects with owner, task, due,
  "risks"        : list of risks or open questions,
  "sentiment"    : one of "positive" | "neutral" | "tense".
Transcript:
<<<
{transcript}
>>>
Return ONLY the JSON."""

SAMPLE_TRANSCRIPT = """\
Dana (PM): Thanks everyone. Goal today: lock the launch date for the mobile app.
Ron (Eng): Backend is ready. The blocker is the payment webhook - it fails on retries.
Dana: How long to fix the webhook?
Ron: Two days if I drop the analytics task.
Maya (Marketing): We already told three partners we go live on the 20th.
Dana: Okay - decision: Ron fixes the webhook first, analytics slips a week.
Ron: Agreed. I'll have the retry fix done by Thursday.
Maya: I'll prepare the partner announcement for the 20th, pending Ron's confirmation.
Dana: One risk - if the webhook fix uncovers more issues we may miss the 20th.
      Let's review Thursday EOD before we promise the partners anything public.
"""


def call_llm(prompt: str, provider: str = "mock") -> str:
    """Return the model's raw text. MOCK returns canned, schema-valid JSON so the
    pipeline is fully testable offline. Set provider to 'openai'/'anthropic' + an
    API key to go live - the rest of the pipeline is identical."""
    if provider == "mock":
        return json.dumps({
            "summary": ("The team committed to the mobile launch on the 20th, contingent on "
                        "fixing a payment-webhook retry bug first; analytics work slips one week."),
            "decisions": [
                "Prioritise the payment-webhook retry fix over analytics.",
                "Target public launch date: the 20th, to be confirmed Thursday EOD.",
            ],
            "action_items": [
                {"owner": "Ron", "task": "Fix payment-webhook retry failure", "due": "Thursday"},
                {"owner": "Maya", "task": "Prepare partner announcement (hold for confirmation)", "due": "the 20th"},
            ],
            "risks": [
                "Webhook fix may uncover further issues and jeopardise the 20th.",
                "Partners were pre-committed to the 20th before the fix is verified.",
            ],
            "sentiment": "neutral",
        })
    elif provider == "openai":
        # from openai import OpenAI
        # client = OpenAI()
        # r = client.chat.completions.create(model="gpt-4o-mini",
        #         messages=[{"role": "user", "content": prompt}])
        # return r.choices[0].message.content
        raise NotImplementedError("Set OPENAI_API_KEY and enable the live branch.")
    elif provider == "anthropic":
        # import anthropic
        # client = anthropic.Anthropic()
        # r = client.messages.create(model="claude-3-5-sonnet-latest", max_tokens=1024,
        #         messages=[{"role": "user", "content": prompt}])
        # return r.content[0].text
        raise NotImplementedError("Set ANTHROPIC_API_KEY and enable the live branch.")
    raise ValueError("unknown provider: " + provider)


def extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start:end + 1])


def analyze(transcript: str, provider: str = "mock") -> dict:
    prompt = PROMPT_TEMPLATE.replace("{transcript}", transcript)
    data = extract_json(call_llm(prompt, provider=provider))
    for key in ("summary", "decisions", "action_items", "risks", "sentiment"):
        if key not in data:
            raise ValueError("model output missing required key: " + key)
    return data


def build_pdf(analysis: dict, out_path: str, title: str = "Meeting Report") -> str:
    """Branded PDF, house style. English/LTR here; for Hebrew set the ReportLab
    paragraph direction to RTL + an Israeli font - the same layer serves both."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit

    NAVY, ACCENT, DARK, GREY = HexColor("#0d1b2a"), HexColor("#4cc9f0"), HexColor("#1b263b"), HexColor("#9db4c0")
    SENT = {"positive": HexColor("#2e8b57"), "neutral": HexColor("#e8890c"), "tense": HexColor("#b03030")}
    W, H = A4
    c = canvas.Canvas(out_path, pagesize=A4)
    c.setFillColor(NAVY); c.rect(0, H - 30 * mm, W, 30 * mm, fill=1, stroke=0)
    c.setFillColor(ACCENT); c.rect(0, H - 30 * mm, W, 1.6 * mm, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 17); c.drawString(18 * mm, H - 15 * mm, title)
    c.setFillColor(GREY); c.setFont("Helvetica", 9.5)
    c.drawString(18 * mm, H - 22 * mm, "Auto-generated from a transcript - AI report pipeline demo - Dror M.")
    sent = analysis.get("sentiment", "neutral")
    c.setFillColor(SENT.get(sent, GREY)); c.drawRightString(W - 18 * mm, H - 22 * mm, "tone: " + sent)

    y = H - 42 * mm

    def section(label, yy):
        c.setFillColor(ACCENT); c.setFont("Helvetica-Bold", 11); c.drawString(18 * mm, yy, label)
        return yy - 6 * mm

    def wrap(txt, yy, x=22 * mm, size=9.5, lead=4.8, bullet=False):
        c.setFillColor(DARK); c.setFont("Helvetica", size)
        prefix = "-  " if bullet else ""
        for line in simpleSplit(prefix + txt, "Helvetica", size, W - x - 18 * mm):
            c.drawString(x, yy, line); yy -= lead * mm
        return yy

    y = section("Summary", y); y = wrap(analysis["summary"], y); y -= 3 * mm
    y = section("Decisions", y)
    for d in analysis["decisions"]:
        y = wrap(d, y, bullet=True)
    y -= 3 * mm
    y = section("Action items", y)
    for a in analysis["action_items"]:
        y = wrap(a.get("owner", "?") + " - " + a.get("task", "") + "  (due: " + a.get("due", "-") + ")", y, bullet=True)
    y -= 3 * mm
    y = section("Risks / open questions", y)
    for r in analysis["risks"]:
        y = wrap(r, y, bullet=True)

    c.setFillColor(HexColor("#f4f6f8")); c.rect(0, 0, W, 11 * mm, fill=1, stroke=0)
    c.setFillColor(GREY); c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(18 * mm, 4.5 * mm, "Demo output - fictional data - pipeline runs in mock mode with no API key. Dror M.")
    c.save()
    return out_path


def _self_test() -> None:
    a = analyze(SAMPLE_TRANSCRIPT, provider="mock")
    assert isinstance(a["decisions"], list) and a["decisions"], "decisions must be a non-empty list"
    assert all("task" in x for x in a["action_items"]), "each action item needs a task"
    assert a["sentiment"] in ("positive", "neutral", "tense"), "sentiment must be allowed"
    out = build_pdf(a, "/tmp/_selftest_report.pdf")
    assert os.path.getsize(out) > 1500, "PDF looks empty"
    assert extract_json('noise {"x": 1} tail')["x"] == 1
    print("self-test: PASS")


if __name__ == "__main__":
    _self_test()
    result = analyze(SAMPLE_TRANSCRIPT, provider="mock")
    print("wrote", build_pdf(result, "ai_report_demo_output.pdf"))
