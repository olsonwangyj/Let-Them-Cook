# Docs

Communications and integration documents. They are olsonwangyj's and live on
the fork only, not in the team repo. Formal documents are written in English
(`AGENTS.md` rule 8). Since the merge of the team main `5e3f78e` (2026-10-27)
this folder also holds Wen Ree's documents from the team repo (listed under
"Teammates' documents" below); they are his, not to be edited.

## Current

| File | What it is |
|---|---|
| [communications-handoff.md](communications-handoff.md) | The hand-off document: the project, the Communications design and its reasons, a map of every folder and file, current progress, rules and next steps. Every new agent reads this first. Updated with every code or deployment change (`AGENTS.md` rule 7). |
| [integration-journal.md](integration-journal.md) | The integration journal: the Communications side of the team's journal, by teaching week from Week 9 (12 to 18 October 2026). For each week a one-page summary, then the activities day by day, each failure with its investigation, the options considered, the change and the retest, and the decisions that affect other subsystems. A new entry with every code, deployment or integration change (`AGENTS.md` rule 9). |
| [handoff-details/](handoff-details/) | The architecture documents: six detail chapters of the hand-off (architecture, network and security; firmware; laptop relay and tools; Ultra96 service and certificates; phone client and the Week 7 receiver; tests, operations and extension points). |
| [communications-quickstart.md](communications-quickstart.md) | How to flash, pair and check the boards, deploy the Ultra96 service and run the two-board demo with `flash.py`, `tools.check_board`, `tools.deploy_service` and `demo.py`. |
| [co-protocol-v3.md](co-protocol-v3.md) | The protocol specification, version 3: the 38-byte sensor packet, the network messages and model results, the control channel, files and limits, and since 2026-10-27 the opt-in sensor version 4 of the three-flex gloves. It replaced `co-protocol-v2.md` on 2026-10-14. |
| [hand-events-for-the-game.md](hand-events-for-the-game.md) | For Jie Ling: the per-hand `HAND_EVENT` events (2026-10-28), what each field and kind means for the game, and the two CommsNative functions `CommsHandState` and `CommsNextHandEvent`. The full specification is in `co-protocol-v3.md`, "Hand events". |
| [B07-CO-protocol-explained.zh-CN.md](B07-CO-protocol-explained.zh-CN.md) | Chinese study companion with byte tables and sequence diagrams, written for protocol version 2 (32-byte packet, 8 values, `LCS1`). Its banner lists the version-3 differences. Not a formal document; `co-protocol-v3.md` governs. |
| [week7-runbook.md](week7-runbook.md) | Ultra96 deployment, TLS provisioning and bond recovery for the Week 7 deployment. Older, and about half of it is out of date; its note at the top lists what changed with version 3. |

## Teammates' documents

Wen Ree's, from the team main `5e3f78e` (2026-10-27): `HAND_COMMS_INTEGRATION.md`, `HAND_V4_TRANSPORT.md`, `HAND_FPGA_BOARD_RESULTS_20261027.md`, `HAND_RECORDING_READY.md`, `HAND_VIVADO_BUILD.md`, `INDEPENDENT_HAND_RUNTIME.md`, `AI_LAB_*.md`, `AI_INTEGRATION_JOURNAL_STARTER.md`, `FPGA_*.md`, `GESTURE_PROTOCOL_FLEX3_DRAFT.md`, `PRE_HANDOVER_TRIAGE.md`, `THREE_FLEX_NEXT_STEPS_20261025.md`, `TRIAGE_FINDINGS_20261026.md` and `ai_lab_collection.example.json`. Read them for his design; the Communications documents above govern Communications.

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
