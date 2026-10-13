# Agent instructions: Let Them Cook (CG4002 team B07)

This working copy belongs to **olsonwangyj**, who owns the **Communications**
subsystem and leads integration. Three teammates own the rest of the repo.
Read their code freely. Do not change it.

## Role and scope

olsonwangyj leads the integration; their own technical work is the
Communications subsystem. Each teammate stays responsible for the quality and
performance of their own component. olsonwangyj's job is to make the
components communicate correctly and to coordinate the team toward a working
integrated system.

- Frame plans, questions and tasks around interfaces and coordination: what
  crosses a boundary (formats, rates, windows, labels, transports, timing) and
  who delivers what by when.
- Do not take on a teammate's accuracy, performance, bugs or missing features.
  If you notice one, report it once as an FYI for its owner.
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

## Git layout

- `upstream` is the team repo (`B07-CG4002/Let-Them-Cook`, public).
  `origin` is olsonwangyj's fork.
- Local `main` tracks the fork. It carries files that are deliberately not in
  the team repo: `docs/`, `ios-visualizer/xcode-export/`,
  `ios-visualizer/tools/`, and these agent files. Never open a team pull
  request from local `main`. Branch from `upstream/main` instead.
- Do not push to `upstream` unless the user asks for that specific push.
