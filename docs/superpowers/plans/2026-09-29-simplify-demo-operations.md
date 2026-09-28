# Simplify demo operations

**Goal:** Reduce recording/live operations to `flash.py` and the existing `demo.py`; remove manual phone-count entry and duplicate numbered wrappers.

**User requirements:** Film the iPhone count directly; make edit/rebuild/rerun practical for Live as well as Video; keep brief English script explanations and Chinese operating instructions; push the completed changes.

**Design:** The user has only one programming USB cable available for ESPs. `flash.py` generates fixtures and builds both protected profiles, then prompts for LEFT and RIGHT sequentially, detecting the currently attached COM each time. One detected port is selected automatically; multiple ports require explicit selection. The same COM is valid for successive boards; no cached left/right port map is needed. `--ports`, `--pair [left|right|both]`, and `--monitor COMx` are infrequent setup modes in the same entry point. `demo.py tunnel` remains the long-running tunnel; `run` is the 60-second/10-Hz video capture; `live` defaults to a 120-second keyboard-enabled capture. Both save and show report/packet examples automatically. `report` reopens saved evidence. `service [--start]` delegates existing guarded SSH maintenance to one internal module. Phone evidence is camera footage, never a script-generated receipt claim.

## Work and verification

1. Add meaningful failing tests for sequential uploads with one cable, fresh port detection, ambiguous port selection, cancellation, failure propagation and flash modes; implement `flash.py` without accessing hardware during development.
2. Test and implement live defaults, automatic evidence review without prompts, and combined service dispatch. Remove phone-observation persistence and its obsolete tests; retain matching sensor/ACK checks and strict SSH guards.
3. Delete the superseded `video_steps` wrappers and migrate relevant tests. Preserve the unrelated untracked old recording draft.
4. Update both current Markdown documents and their exact source/heading references. Add a directly readable English explanation beside every code excerpt, with Chinese guidance naming the file, relevant lines and speech to read. Keep all rubric coverage, the two-stage camera/screen-recording workflow and actual dummy edit/reflash evidence. Add a short Live operation note without treating 10 Hz as a maximum-speed demonstration.
5. Run focused regression tests, syntax checks and Markdown file/line/anchor validation. Review the final diff, commit and push. Do not flash boards, pair devices or connect to the live service while implementing.

## Constraints

- The operator identifies each physical board at the LEFT/RIGHT prompt; do not infer its label from enumeration order or COM number. Redetect the port after each swap.
- Pairing stays authenticated; no logging PINs, no bond deletion and no security downgrade.
- Preserve current-terminal processes, strict SSH host validation, and fail-closed service port checks.
- Upload success, server ACKs and observed phone counts are distinct evidence; do not synthesize phone success.
