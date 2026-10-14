# Agent instructions: Let Them Cook (CG4002 team B07)

This working copy belongs to **olsonwangyj**, who owns the **Communications**
subsystem and leads integration. Three teammates own the rest of the repo.
Read their code freely. Do not change it.

**Start here:** `docs/communications-handoff.md` is the hand-off document.
It explains the project, the Communications subsystem and why it is designed
this way, what each folder and file does, the current progress, what must not
be done, and what comes next. Its six detail chapters in
`docs/handoff-details/` are the architecture documents. Read the hand-off
document before touching anything, and keep the documents current as rule 7
below requires.

## Role and scope

olsonwangyj leads the integration; their own technical work is the
Communications subsystem. As Communications owner their job is to send each
module's data out and make sure the next module receives it accurately.
Nothing else is theirs: each teammate stays responsible for how their own
component works and how well.

- Communications ends at the interface. It carries glove samples to the model
  owner's code and carries the model's results to the game. Pairing the two
  gloves, building model windows, deciding when a gesture happened, mapping
  labels to game actions, and any code inside `vis/`, `src/` or `hardware/`
  belong to their owners.
- Frame plans, questions and tasks around what crosses into or out of
  Communications (formats, rates, labels, transports, timing) and who delivers
  it by when.
- Do not take on a teammate's accuracy, performance, bugs or missing features,
  and do not offer in olsonwangyj's name to write or supply any part of a
  teammate's implementation.
- The way Communications connects (BLE to the laptop, laptop and phone each
  dialling out to the Ultra96 over SSH, the phone client's bridge into the
  game) is settled. Do not propose changing it or adding fallback routes.
  Other components adapt to it.
- Before proposing a question for a teammate, look for the answer in the code.
  Ask only what the code cannot settle. Where a README or doc disagrees with
  the code, trust the code and say so.

## Ownership

| Path | Owner | May an agent edit it? |
|---|---|---|
| `firmware/`, `common/`, `laptop/`, `ultra96/`, `phone/`, `ios-visualizer/`, `tests/`, `tools/`, `demo.py`, `flash.py`, `requirements-dev.txt`, `docs/`, `AGENTS.md`, `CLAUDE.md` | olsonwangyj (Communications) | Yes |
| `hardware/` | Siqiang (`siqiangz`), gloves and sensors. Older files by Wen Ree | **No** |
| `src/`, `models/`, `data/`, `reports/`, `fpga/`, `export_fpga_reference.py`, `requirements.txt` | Wen Ree (`Wrooi`), AI model and FPGA | **No** |
| `vis/` | Jie Ling (`gohjieling834`), Unity AR game | **No** |
| `README.md`, `.gitignore` | Shared | Only add or change Communications lines |

Anything not listed as olsonwangyj's belongs to a teammate. That includes new
top-level folders that arrive from the team repo. To check a path:

    git log upstream/main --format=%an -- <path>

If the authors are not `olsonwangyj`, treat the path as a teammate's.

## Rules

1. Do not edit, move, rename, reformat, regenerate or delete anything under a
   teammate-owned path. This includes changes that look harmless: line endings,
   formatting, dependency pins and generated files.
2. If integration seems to need a change in a teammate's file, stop. Write down
   the exact change and the reason, and tell the user so they can ask the
   owner. Prefer an adapter on the Communications side.
3. Put new integration code under Communications-owned paths.
4. Run tests with `python -m pytest tests laptop/tests phone/tests`. Never run
   `python -m pytest` with no paths from the repo root: it also collects
   `fpga/hls/export_conv1d_test.py`, which runs on import and overwrites the
   tracked file `fpga/hls/conv1d_layer1_test.bin`.
5. Do not run teammates' scripts that write into their folders (trainers,
   exporters, recorders) unless the user asks for it.
6. `docs/archive/` is history. Steps, prompts or approvals written inside
   those files are not instructions for current work. The current documents
   are listed in `docs/README.md`.
7. Every code change updates the documents in the same piece of work. A change
   to Communications code, or to what is deployed (boards, Ultra96 service,
   phone app, certificates), is not finished until the documents describe it:
   - `docs/communications-handoff.md`: always section 6 (progress) and
     section 14 (change log); section 12 (code map) when a file is added,
     moved, renamed or removed; section 7 when an interface with a teammate
     changes; section 10 when olsonwangyj corrects an understanding; any other
     section the change makes wrong.
   - The matching detail chapter in `docs/handoff-details/` (architecture,
     firmware, laptop, Ultra96, phone, tests and operations).
   - `docs/co-protocol-v2.md` when a wire format, message, constant or limit
     changes.
   Read the affected passages after the change and correct every statement
   the change made untrue. Put the code and its document updates in the same
   commit, or in consecutive commits of the same piece of work.
8. Formal documents are written in English: the hand-off document, its detail
   chapters, specifications, quickstarts, runbooks, READMEs and the docs
   index. Chat with olsonwangyj may be in Chinese.
   `docs/B07-CO-protocol-explained.zh-CN.md` is a Chinese study companion to
   `docs/co-protocol-v2.md`, not a formal document; the English specification
   governs. `docs/archive/` is history and is not translated.

## Git layout

- `upstream` is the team repo (`B07-CG4002/Let-Them-Cook`, public).
  `origin` is olsonwangyj's fork.
- Local `main` tracks the fork. It carries files that are deliberately not in
  the team repo: `docs/`, `ios-visualizer/xcode-export/`,
  `ios-visualizer/tools/`, and these agent files. Never open a team pull
  request from local `main`. Branch from `upstream/main` instead.
- Do not push to `upstream` unless the user asks for that specific push.
