# Week 7 teacher demo materials implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development with independent documentation/visual tasks and a final integrated review. The user explicitly authorizes creating all missing materials and autonomous implementation decisions.

**Goal:** Make the existing dummy-packet system easy to demonstrate, explain and substantiate to the teacher.

**Architecture:** Reuse protected ESP BLE, the existing bounded bridge, strict TLS, and independent SSH forwards. Add an observational sender CLI and an offline trace auditor; create operator instructions, a packet walkthrough and printable teacher brief. No new wire protocol, subscriber relay, deployment service or hardware claim.

**Tech stack:** Existing Python codecs/bridge, pytest, Markdown, offline HTML/SVG and printable PDF.

**Spec:** User's request for Week 7 dummy packets proving connections; `docs/week7-selected-design-2026-09-06.md` and current evidence remain authoritative. The official written grading rubric is unavailable, so no guaranteed rubric coverage is claimed.

## Constraints and rulings

- Ultra96 external access is SSH TCP 22 only. Application listeners remain on loopback 8888/9999; Laptop/Phone own separate forwards.
- Normal demo uses actual ESP-generated dummy packets over protected BLE. Synthetic transport-only examples and recorded evidence are labelled.
- Real Phone/Unity acceptance remains unverified. Desktop subscriber must stop before the Phone connects.
- Ruling: create a printable three-page visual brief plus runnable command guide rather than require PowerPoint or online design services; this works offline at the demo.
- Ruling: add a separate observational sender, reusing Bridge, so raw/decoded packets and checked ACK IDs are visible without adding a Laptop result connection. Logging occurs after ACK validation and is labelled accordingly.
- Ruling: the offline auditor recomputes exact ID sets, validates deterministic results, and rejects missing/duplicate/mismatched records and incomplete evidence. It cannot establish remote/physical provenance from a file.
- All evidence exports contain dummy data/status only; no passwords, pairing passkeys or private keys.

## Tasks

- [x] Create `tools/week7_demo.py` with `packet`, `sender`, and `audit` commands; `tests/test_week7_demo.py` covers a literal packet vector, actual TLS sender/receiver exchange, malformed/mismatched/duplicate/incomplete logs and CLI exit status. Run failing tests before implementation, then `python -m pytest tests/test_week7_demo.py -q`.
- [x] Create `docs/week7-demo-pack/README.md` and `teacher-script.md`: exact checked commands, readiness checks, 3–5 minute talk track, evidence matrix, Phone path, troubleshooting, teardown and remaining physical acceptance.
- [x] Create `packet-walkthrough.md` and generated `packet-example.json` from `python -m tools.week7_demo packet`; hand-check bytes/frame lengths and explain the shared trace ID.
- [x] Create offline `teacher-brief.html` and PDF; render and visually inspect all pages, keeping the Phone pending label prominent.
- [x] Audit existing recorded clean/fault evidence with the new auditor; include a sanitized portable recorded sample and truthful results. Exercise sender with local TLS fixtures; do not label that test as new Ultra96/Phone evidence.
- [x] Review all claims/commands/links, run relevant tests, update README/continuation and this checklist, and commit locally on the requested branch.

## Completion evidence

203 passed / 2 Windows skips in 73.08 s; the skipped Linux signal tests have earlier separate verification. New demo suite: 22 passed, including final interruption-guard regression. Independent review findings fixed; actual local TLS verifies sender ACK display and separate result delivery. Recorded clean audits match 100 and 5,965 IDs; viewer fault retains 279 missing and a failed audit. Thirteen PowerShell blocks parse, 38 operator links resolve, and all three exported PDF pages were rendered/visually checked. No hardware claim was added by offline tooling. The supplied Phone JSONL is post-dedup/no per-result timestamps; timed device observation remains required for sustained Phone acceptance.
