#!/usr/bin/env python3
"""
Auditable AI workflow - "AI proposes, deterministic code disposes" - DEMO
=========================================================================
The safe pattern for letting an LLM act in a business workflow: the model only
PROPOSES actions; a deterministic RiskGate the model cannot override APPROVES or
BLOCKS each one against hard rules, and every decision is logged with a reason.

Why clients care: an LLM will occasionally propose something wrong, expensive, or
against policy. This pattern makes that harmless - the gate is plain code you can
read and test, so a bad proposal is blocked and logged, never executed.

  * Pure standard library - runs anywhere, no dependencies, no API key.
  * mock_ai_propose() stands in for the model; swap it for a real OpenAI/Anthropic
    call and nothing else changes - the gate is provider-agnostic.
  * Embedded self-test proves the gate blocks every out-of-policy action.

Run it:   python ai_risk_gate.py
"""

import json
from datetime import datetime, timezone

# ----------------------------------------------------------------------------
# POLICY  (plain, auditable rules - edit these, not the model)
# ----------------------------------------------------------------------------
POLICY = {
    "allowed_actions": {"reply", "tag", "refund", "escalate"},
    "max_refund_usd": 100.0,          # refunds above this must go to a human
    "required_fields": {
        "reply":    {"ticket_id", "text"},
        "tag":      {"ticket_id", "label"},
        "refund":   {"ticket_id", "amount_usd"},
        "escalate": {"ticket_id", "reason"},
    },
    "banned_phrases": {"guaranteed", "we promise", "risk-free"},  # compliance language
}


# ----------------------------------------------------------------------------
# THE AI STEP (mock). Deliberately includes out-of-policy proposals so the
# gate has something to catch - that is the point of the demo.
# ----------------------------------------------------------------------------
def mock_ai_propose():
    return [
        {"action": "reply",    "ticket_id": "T-101", "text": "Sorry for the delay - refunding your shipping now."},
        {"action": "refund",   "ticket_id": "T-101", "amount_usd": 12.50},
        {"action": "refund",   "ticket_id": "T-202", "amount_usd": 640.00},   # over limit -> BLOCK
        {"action": "reply",    "ticket_id": "T-303", "text": "This plan is guaranteed risk-free."},  # banned -> BLOCK
        {"action": "delete",   "ticket_id": "T-404"},                          # not allowed -> BLOCK
        {"action": "tag",      "ticket_id": "T-101", "label": "resolved"},
        {"action": "escalate", "ticket_id": "T-202"},                          # missing 'reason' -> BLOCK
    ]


# ----------------------------------------------------------------------------
# THE GATE (deterministic; the model cannot reach past it)
# ----------------------------------------------------------------------------
class RiskGate:
    def __init__(self, policy):
        self.policy = policy
        self.audit_log = []

    def evaluate(self, action: dict):
        kind = action.get("action")
        ok, reason = self._check(kind, action)
        self.audit_log.append({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "action": kind, "ticket": action.get("ticket_id"),
            "decision": "APPROVED" if ok else "BLOCKED", "reason": reason,
        })
        return ok, reason

    def _check(self, kind, action):
        if kind not in self.policy["allowed_actions"]:
            return False, f"action '{kind}' is not in the allow-list"
        missing = self.policy["required_fields"].get(kind, set()) - action.keys()
        if missing:
            return False, f"missing required field(s): {', '.join(sorted(missing))}"
        if kind == "refund" and float(action["amount_usd"]) > self.policy["max_refund_usd"]:
            return False, (f"refund ${action['amount_usd']:.2f} exceeds ${self.policy['max_refund_usd']:.2f} "
                           f"limit - needs human approval")
        if kind == "reply":
            low = action.get("text", "").lower()
            hit = [p for p in self.policy["banned_phrases"] if p in low]
            if hit:
                return False, f"reply contains banned compliance phrase(s): {', '.join(hit)}"
        return True, "within policy"

    def run(self, proposals):
        return [(a, *self.evaluate(a)) for a in proposals]


def _self_test():
    gate = RiskGate(POLICY)
    results = gate.run(mock_ai_propose())
    decisions = {r[0].get("ticket_id") + "/" + r[0].get("action"): r[1] for r in results}
    # the four deliberately-bad proposals MUST be blocked
    assert decisions["T-202/refund"] is False, "over-limit refund should be blocked"
    assert decisions["T-303/reply"] is False, "banned-phrase reply should be blocked"
    assert decisions["T-404/delete"] is False, "disallowed action should be blocked"
    assert decisions["T-202/escalate"] is False, "missing-field action should be blocked"
    # the good ones MUST pass
    assert decisions["T-101/reply"] is True and decisions["T-101/refund"] is True
    # every proposal is logged
    assert len(gate.audit_log) == len(mock_ai_propose()), "audit log must cover every proposal"
    blocked = sum(1 for e in gate.audit_log if e["decision"] == "BLOCKED")
    assert blocked == 4, f"expected 4 blocks, got {blocked}"
    print("self-test: PASS  (4/4 out-of-policy actions blocked, all decisions logged)")


if __name__ == "__main__":
    _self_test()
    gate = RiskGate(POLICY)
    print("\n--- AI proposed 7 actions; the gate decided ---")
    for action, ok, reason in gate.run(mock_ai_propose()):
        mark = "APPROVED" if ok else "BLOCKED "
        print(f"[{mark}] {action['action']:<9} {action.get('ticket_id'):<6} :: {reason}")
    print("\n--- audit log (JSON, one line per decision) ---")
    for entry in gate.audit_log:
        print(json.dumps(entry))
