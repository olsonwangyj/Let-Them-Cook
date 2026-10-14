# Docs

Communications and integration documents. They are olsonwangyj's and live on
the fork only, not in the team repo. Formal documents are written in English
(`AGENTS.md` rule 8).

## Current

| File | What it is |
|---|---|
| [communications-handoff.md](communications-handoff.md) | The hand-off document: the project, the Communications design and its reasons, a map of every folder and file, current progress, rules and next steps. Every new agent reads this first. Updated with every code or deployment change (`AGENTS.md` rule 7). |
| [handoff-details/](handoff-details/) | The architecture documents: six detail chapters of the hand-off (architecture, network and security; firmware; laptop relay and tools; Ultra96 service and certificates; phone client and the Week 7 receiver; tests, operations and extension points). |
| [communications-quickstart.md](communications-quickstart.md) | How to flash, pair and check the boards, deploy the Ultra96 service and run the two-board demo with `flash.py`, `tools.check_board`, `tools.deploy_service` and `demo.py`. |
| [co-protocol-v3.md](co-protocol-v3.md) | The protocol specification, version 3: the 38-byte sensor packet, the network messages and model results, the control channel, files and limits. It replaced `co-protocol-v2.md` on 2026-10-14. |
| [B07-CO-protocol-explained.zh-CN.md](B07-CO-protocol-explained.zh-CN.md) | Chinese study companion with byte tables and sequence diagrams, written for protocol version 2 (32-byte packet, 8 values, `LCS1`). Its banner lists the version-3 differences. Not a formal document; `co-protocol-v3.md` governs. |
| [week7-runbook.md](week7-runbook.md) | Ultra96 deployment, TLS provisioning and bond recovery for the Week 7 deployment. Older, and about half of it is out of date; its note at the top lists what changed with version 3. |

## Archive

[archive/](archive/README.md) holds finished-milestone records. They keep the
names that were in use at the time (`week7`, `W7`) and are not updated.

| Folder | Contents |
|---|---|
| `archive/reports/` | Week 7 technical report and testing guide (English and Chinese), and the dated progress reports. |
| `archive/test-evidence/` | Physical test results and the 28 September deployment record. |
| `archive/assessment-week7/` | Requirements, video and live-demo scripts, diagrams and the demo pack. |
| `archive/design/` | The early architecture draft, the selected design, plans and specs, and the 8 October integration note (superseded by section 7 of the hand-off document). |
| `archive/runbooks/` | Older run procedures, including the abandoned iSH phone route. |
