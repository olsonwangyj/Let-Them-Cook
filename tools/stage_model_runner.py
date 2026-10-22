"""Put the model owner's runner files in a folder on the Ultra96 that survives a restart.

Two runners are known (--runner):
  conv1d (default)  Wen Ree's Conv1-only runner, src.socket_worker. Its folder /tmp/cnn_conv1d
                    on the board (ai_integration/src/socket_worker.py, its weights, the bitstream
                    and its .hwh) is copied unchanged (without __pycache__), and the board empties
                    /tmp when it restarts.
  full              Wen Ree's full-CNN runner, src.socket_worker_full. The files it needs (four
                    src/ files, the weights, the overlay .bit and its .hwh) are taken from a commit
                    of this checkout (--from-git, default upstream/main: run `git fetch upstream`
                    first), uploaded and moved into place, in the repository's own layout. With
                    --source it copies a board folder in that layout instead.
The copy goes to BOARD_ROOT/model-runner/<name>; the SHA-256 of every file is checked against the
original (and, for an upload, against the commit), and the tool prints the deploy command that
starts the runner from the copy. It changes nothing else: the originals, the running service and
the running runner are untouched, and it needs no sudo. The user types the jump-host and board
passwords; nothing is saved. Run it again and it reports that the copy is already there; a copy
whose files differ is never overwritten (give another --name).

--weights picks the weights the printed command uses: a path relative to the runner folder is
copied with the runner; an absolute board path (weights staged on their own) is only printed.

    python -m tools.stage_model_runner --dry-run
    python -m tools.stage_model_runner
    python -m tools.stage_model_runner --runner full --dry-run
    python -m tools.stage_model_runner --runner full --weights fpga/hls/eightclass_weights_standard_20261021.npz --name cnn_full_std
"""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import posixpath
import shlex
import subprocess
import sys

from tools.demo_service import BOARD_ROOT
from tools.deploy_service import RECORDS, _connect, _git_bash_hint
from tools.ssh_tunnel import default_jump_user

ROOT = Path(__file__).resolve().parents[1]


class Runner:
    """Where a runner's files sit in its copy and how the deploy tool starts it."""

    def __init__(self, source, name, folder, module, weights, bitstream, code, git_ref=None):
        self.source, self.name, self.folder, self.module = source, name, folder, module
        self.weights, self.bitstream, self.code, self.git_ref = weights, bitstream, code, git_ref

    def path(self, relative):
        """A path inside the runner folder, relative to the copy."""
        return posixpath.join(self.folder, relative) if self.folder else relative

    def expected(self, weights=None):
        """Relative to the copied folder: what the deploy command reads."""
        weights = self.weights if weights is None else weights
        files = [self.path(name) for name in self.code]
        if not weights.startswith("/"):
            files.append(self.path(weights))
        return tuple(files + [self.bitstream, self.bitstream[:-len(".bit")] + ".hwh"])


RUNNERS = {
    "conv1d": Runner("/tmp/cnn_conv1d", "cnn_conv1d", "ai_integration", "src.socket_worker",
                     "fpga/hls/eightclass_weights_20261018_v2.npz", "cnn_conv1d_fixed28_v2.bit",
                     ("src/socket_worker.py",)),
    # Wen Ree's README_FULL_CNN.md lists these; it runs from a folder laid out as the repository.
    "full": Runner(None, "cnn_full_20261020", "", "src.socket_worker_full",
                   "fpga/hls/eightclass_weights_20261018_v2.npz",
                   "fpga/overlays/full_cnn/cnn_full_20261020.bit",
                   ("src/ai_common.py", "src/export_full_cnn.py", "src/full_cnn_backend.py",
                    "src/socket_worker_full.py"), git_ref="upstream/main"),
}

# The Conv1-only runner's values, kept under their earlier names.
_CONV1D = RUNNERS["conv1d"]
SOURCE = _CONV1D.source
NAME = _CONV1D.name
RUNNER_FOLDER = _CONV1D.folder
RUNNER_MODULE = _CONV1D.module
WEIGHTS = _CONV1D.weights
BITSTREAM = _CONV1D.bitstream
EXPECTED = _CONV1D.expected()

REMOTE_PROGRAM = r'''
import hashlib, json, os, shutil, stat, sys
from pathlib import Path

source = Path(sys.argv[1]); dest = Path(sys.argv[2]); stamp = sys.argv[3]
expected = json.loads(sys.argv[4]); evidence = Path(sys.argv[5])
# "copy" leaves the source as it is; "move" renames an uploaded folder into place and
# removes it in every other case. A dict of expected files must match exactly (size, SHA-256).
move = len(sys.argv) > 6 and sys.argv[6] == "move"
SKIP = "__pycache__"


def listing(root):
    """{relative path: (size, sha256)} of every regular file, without __pycache__."""
    files = {}
    for folder, dirs, names in os.walk(str(root)):
        dirs[:] = sorted(d for d in dirs if d != SKIP)
        for d in dirs:
            if os.path.islink(os.path.join(folder, d)):
                raise ValueError("symbolic link to a folder: " + os.path.join(folder, d))
        for name in sorted(names):
            path = os.path.join(folder, name)
            mode = os.lstat(path).st_mode
            if not stat.S_ISREG(mode):
                raise ValueError("not a regular file: " + path)
            digest = hashlib.sha256()
            with open(path, "rb") as stream:
                for block in iter(lambda: stream.read(1 << 20), b""):
                    digest.update(block)
            name = os.path.relpath(path, str(root)).replace(os.sep, "/")
            files[name] = [os.path.getsize(path), digest.hexdigest()]
    return files


def finish(status, code, **extra):
    if move and source.is_dir() and not source.is_symlink():
        shutil.rmtree(str(source), ignore_errors=True)
    record = dict(status=status, stamp=stamp, source=str(source), dest=str(dest), **extra)
    try:
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / ("model-runner-stage-" + stamp + ".json")).write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n")
    except OSError as exc:
        record["record_error"] = str(exc)
    print(json.dumps(record, sort_keys=True), flush=True)
    sys.exit(code)


try:
    if source.is_symlink() or not source.is_dir():
        finish("failed", 1, error="source folder not found (was the board restarted?): " + str(source))
    files = listing(source)
    missing = [name for name in expected if name not in files]
    if missing:
        finish("failed", 1, error="missing in the source: " + ", ".join(missing), files=files)
    if isinstance(expected, dict) and files != expected:
        wrong = sorted(n for n in set(files) | set(expected) if files.get(n) != expected.get(n))
        finish("failed", 1, error="the uploaded files differ from the originals: " + ", ".join(wrong),
               files=files)
    if dest.exists() or dest.is_symlink():
        # Already there: every file present with the same content (other files may sit beside them).
        if dest.is_dir() and not dest.is_symlink():
            present = listing(dest)
            if all(present.get(name) == entry for name, entry in files.items()):
                finish("already_staged", 0, files=files)
        finish("failed", 1, error="the destination exists with other files; it was not changed. "
                                  "Use another --name", files=files)
    dest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if move:
        os.rename(str(source), str(dest))
        if listing(dest) != files:
            finish("failed", 1, error="the moved folder does not match the upload: " + str(dest))
        finish("staged", 0, files=files)
    partial = dest.parent / (dest.name + ".partial-" + stamp)
    try:
        shutil.copytree(str(source), str(partial), symlinks=True,
                        ignore=shutil.ignore_patterns(SKIP))
        copied = listing(partial)
        if copied != files:
            raise ValueError("the copy does not match the source")
        os.rename(str(partial), str(dest))
    except BaseException:
        shutil.rmtree(str(partial), ignore_errors=True)
        raise
    finish("staged", 0, files=files)
except SystemExit:
    raise
except Exception as exc:
    finish("failed", 1, error=type(exc).__name__ + ": " + str(exc))
'''


def destination(name):
    if not name or name in (".", "..") or not all(c.isalnum() or c in "._-" for c in name):
        raise ValueError("--name must be a plain folder name (letters, digits, '.', '_', '-')")
    return BOARD_ROOT + "/model-runner/" + name


def deploy_command(dest, runner="conv1d", weights=None):
    """The PowerShell line that starts the runner from the copy (as Wen Ree starts it)."""
    runner = RUNNERS[runner]
    cwd = dest + ("/" + runner.folder if runner.folder else "")
    parts = ["python", "-m", "tools.deploy_service", "--model", "ultra96.model_bridge",
             "--runner-module", runner.module, "--runner-cwd", cwd,
             "--runner-arg=--weights", "--runner-arg", runner.weights if weights is None else weights,
             "--runner-arg=--bit", "--runner-arg", dest + "/" + runner.bitstream]
    return " ".join(parts)


def remote_command(source, dest, stamp, expected=EXPECTED, move=False):
    parts = ["/usr/bin/python3", "-I", "-c", REMOTE_PROGRAM, source, dest, stamp,
             json.dumps(expected if isinstance(expected, dict) else list(expected)),
             BOARD_ROOT + "/evidence"]
    return " ".join(shlex.quote(part) for part in parts + (["move"] if move else []))


def git_files(ref, names, root=ROOT):
    """{relative path: bytes} of each file at a commit of this checkout."""
    files = {}
    for name in names:
        done = subprocess.run(["git", "-C", str(root), "cat-file", "blob", ref + ":" + name],
                              capture_output=True)
        if done.returncode:
            raise ValueError("{} is not in {} of this checkout (run `git fetch upstream` first, or "
                             "give another --from-git)".format(name, ref))
        files[name] = done.stdout
    return files


def listing(files):
    """{relative path: [size, sha256]}, as the board program lists a folder."""
    return {name: [len(data), hashlib.sha256(data).hexdigest()] for name, data in files.items()}


def _upload(board, folder, files):
    """Write the files under a new board folder through SFTP."""
    sftp = board.open_sftp()
    try:
        made = set()
        for name in sorted(files):
            parts = (folder + "/" + name).split("/")[:-1]
            for end in range(folder.count("/") + 1, len(parts) + 1):
                path = "/".join(parts[:end])
                if path not in made:
                    try:
                        sftp.stat(path)
                    except IOError:
                        sftp.mkdir(path)
                    made.add(path)
            sftp.putfo(io.BytesIO(files[name]), folder + "/" + name, confirm=True)
    finally:
        sftp.close()


def _run(board, command):
    _, out, err = board.exec_command(command, timeout=300)
    result = out.read().decode()
    errors = err.read().decode()
    return result, errors, out.channel.recv_exit_status()


def stage(args):
    runner = RUNNERS[args.runner]
    weights = runner.weights if args.weights is None else args.weights
    if not weights or not weights.isprintable() or _git_bash_hint([weights]):
        raise ValueError("--weights must be a path relative to the runner folder, or an absolute "
                         "board path" + _git_bash_hint([weights]))
    expected = runner.expected(weights)
    git_ref = args.from_git or (runner.git_ref if args.source is None else None)
    if args.from_git and args.source is not None:
        raise ValueError("give --source (a board folder) or --from-git (a commit), not both")
    if git_ref is not None and runner.folder:
        raise ValueError("--from-git needs a runner laid out as the repository; the {} runner is "
                         "copied from its board folder (--source)".format(args.runner))
    source = args.source or runner.source
    if git_ref is None and not (source.startswith("/") and source.isprintable()):
        raise ValueError("--source must be an absolute path on the board" + _git_bash_hint([source]))
    dest = destination(args.name or runner.name)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    command = deploy_command(dest, args.runner, weights)
    files = None
    if git_ref is not None:
        files = git_files(git_ref, expected)
        print("Upload from {} of this checkout -> {}".format(git_ref, dest))
        for name, (size, digest) in sorted(listing(files).items()):
            print("  {:>10}  {}  {}".format(size, digest[:16], name))
    else:
        print("Copy on the board: {} -> {} (without __pycache__; the original stays)".format(source, dest))
        print("Required files: " + ", ".join(expected))
    print("Then deploy from the copy:\n  " + command)
    if args.dry_run:
        print("Dry run: nothing was connected or changed.")
        return 0
    jump, board, _ = _connect(args.jump_user, args.board_user)
    try:
        if files is None:
            result, errors, code = _run(board, remote_command(source, dest, stamp, expected))
        else:
            upload = posixpath.dirname(dest) + "/.upload-" + posixpath.basename(dest) + "-" + stamp
            try:
                _upload(board, upload, files)
            except BaseException:
                _run(board, "rm -rf -- " + shlex.quote(upload))
                raise
            result, errors, code = _run(board, remote_command(upload, dest, stamp, listing(files),
                                                              move=True))
    finally:
        board.close()
        jump.close()
    lines = [line for line in result.splitlines() if line.startswith("{")]
    if errors:
        print(errors.strip(), file=sys.stderr)
    if not lines:
        print("FAILED: no record from the board (exit {}): {}".format(code, result.strip()),
              file=sys.stderr)
        return 1
    record = json.loads(lines[-1])
    record["runner"] = args.runner
    if git_ref is not None:
        record["git_ref"] = git_ref
    RECORDS.mkdir(parents=True, exist_ok=True)
    path = RECORDS / "model-runner-stage-{}.json".format(stamp)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copied = record.get("files") or {}
    for name in sorted(copied):
        print("  {:>10}  {}  {}".format(copied[name][0], copied[name][1][:16], name))
    print("Local record: " + str(path))
    if code or record.get("status") not in ("staged", "already_staged"):
        print("FAILED: " + str(record.get("error", record.get("status"))), file=sys.stderr)
        return 1
    print(("Copied" if record["status"] == "staged" else "Already copied") +
          ": {} files in {}, each SHA-256 equal to the original.".format(len(copied), dest))
    print("Deploy from the copy (PowerShell, NUS VPN on):\n  " + command)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runner", choices=sorted(RUNNERS), default="conv1d",
                        help="which runner (default %(default)s)")
    parser.add_argument("--source", help="the runner folder on the board (default for conv1d: {}; "
                                         "the full runner uploads from --from-git instead)".format(SOURCE))
    parser.add_argument("--from-git", metavar="REF",
                        help="full runner only: upload the files from this commit of the checkout "
                             "(default upstream/main)")
    parser.add_argument("--weights", help="weights for the deploy command: relative to the runner "
                                          "folder (copied too) or an absolute board path (default: "
                                          + WEIGHTS + ")")
    parser.add_argument("--name", help="the copy's folder name under BOARD_ROOT/model-runner "
                                       "(default: cnn_conv1d or cnn_full_20261020)")
    parser.add_argument("--jump-user", default=default_jump_user(),
                        help="your NUS login for the jump host; default: LTC_JUMP_USER when set, else yanjie")
    parser.add_argument("--board-user", default="xilinx")
    parser.add_argument("--dry-run", action="store_true", help="print the plan; connect nothing")
    args = parser.parse_args(argv)
    try:
        return stage(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print("FAILED: {}".format(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # paramiko's own errors: unknown host key, wrong password, ...
        print("FAILED: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        allowed = getattr(exc, "allowed_types", None)
        if isinstance(allowed, list) and "password" not in allowed:
            print("The server does not offer password login. Off the NUS VPN, stujump accepts "
                  "only public keys: connect the NUS VPN and run this again.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
