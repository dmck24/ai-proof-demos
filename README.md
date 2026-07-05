# AI & Automation — Proof Demos

Small, runnable, **self-testing** demonstrations of the way I build AI and automation systems: *prove it works, in a test you run yourself, before you pay.*

Every script here runs on its own — no API key, no cost — because the AI calls default to a **mock mode**. Each one ships with an embedded self-test that must pass. The data is generic and fictional; the engineering is real.

— Dror M. · AI automation & integration · evidence-backed delivery

---

## The demos

### 1. `ai_report_pipeline.py` — raw input → structured, branded PDF
Turns a transcript (or any document/dataset) into a structured PDF report. The prompt lives in an **external, editable template** so you change what the AI extracts without touching code, and swapping in a real model (OpenAI or Anthropic) is a one-function change. Runs in mock mode so the whole pipeline is verifiable before spending a cent on tokens. The PDF layer also supports Hebrew RTL.
```bash
pip install reportlab
python ai_report_pipeline.py      # writes ai_report_demo_output.pdf, runs its self-test
```

### 2. `ai_risk_gate.py` — "AI proposes, deterministic code disposes"
The safe pattern for letting an LLM act in a business workflow. The model only **proposes** actions; a plain-code rule-gate it cannot override **approves or blocks** each one against your limits, and logs every decision with a reason. The demo blocks 4 of 4 out-of-policy proposals (over-limit refund, banned compliance phrases, a disallowed action, a missing required field) and approves the valid ones. Pure standard library.
```bash
python ai_risk_gate.py            # prints the decisions + audit log, runs its self-test
```

### 3. `reliability_harness.py` — honest numbers, not a flattering average
Quantifies how reliable a process really is with **bootstrap confidence intervals** instead of a single cherry-picked number: SLA breach-rate (numeric) and accuracy (binary), each with a 95% interval you can re-run on your own data. Pure standard library; the self-test validates the math against constructed data with known properties.
```bash
python reliability_harness.py     # prints the reliability report, runs its self-test
```

---

## Running everything
Python 3.9+. Only `ai_report_pipeline.py` needs a dependency (`reportlab`); the other two are pure standard library.
```bash
pip install -r requirements.txt
```

## Notes
- **Mock mode by default.** No API keys are used or needed. In `ai_report_pipeline.py`, set the provider to `openai` / `anthropic` and add a key to go live — the rest of the pipeline is identical.
- **Generic demos, fictional data.** No client data, nothing proprietary. These exist to show the method: reliable systems, proven before delivery.

## License
MIT — see `LICENSE`. Use, run, and adapt freely.
