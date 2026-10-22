import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from tools import deploy_service, stage_model_runner as stage


def make_source(root):
    files = {name: name.encode() * 3 for name in stage.EXPECTED}
    files["ai_integration/src/ai_common.py"] = b"CLASS_NAMES = []\n"
    files["ai_integration/src/__pycache__/ai_common.cpython-310.pyc"] = b"\0compiled"
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


def run_remote(source, dest, evidence, stamp="20261019T100000Z"):
    done = subprocess.run([sys.executable, "-I", "-c", stage.REMOTE_PROGRAM, str(source), str(dest),
                           stamp, json.dumps(list(stage.EXPECTED)), str(evidence)],
                          capture_output=True, text=True, timeout=60)
    record = json.loads(done.stdout.strip().splitlines()[-1])
    return done.returncode, record


def test_copies_every_file_except_pycache_and_keeps_the_original(tmp_path):
    source = make_source(tmp_path / "tmp" / "cnn_conv1d")
    dest = tmp_path / "board" / "model-runner" / "cnn_conv1d"
    code, record = run_remote(source, dest, tmp_path / "evidence")
    assert code == 0 and record["status"] == "staged"
    assert sorted(record["files"]) == sorted(list(stage.EXPECTED) + ["ai_integration/src/ai_common.py"])
    for name in record["files"]:
        assert (dest / name).read_bytes() == (source / name).read_bytes()
    assert not (dest / "ai_integration" / "src" / "__pycache__").exists()
    assert (source / "ai_integration" / "src" / "__pycache__").is_dir()
    assert not list(dest.parent.glob("*.partial-*"))
    saved = json.loads((tmp_path / "evidence" / "model-runner-stage-20261019T100000Z.json").read_text())
    assert saved["status"] == "staged" and saved["dest"] == str(dest)


def test_a_second_run_reports_the_copy_already_there(tmp_path):
    source = make_source(tmp_path / "src")
    dest = tmp_path / "copy"
    assert run_remote(source, dest, tmp_path / "e")[0] == 0
    code, record = run_remote(source, dest, tmp_path / "e", stamp="20261019T100100Z")
    assert code == 0 and record["status"] == "already_staged"


def test_a_destination_with_other_files_is_never_overwritten(tmp_path):
    source = make_source(tmp_path / "src")
    dest = tmp_path / "copy"
    assert run_remote(source, dest, tmp_path / "e")[0] == 0
    (source / stage.EXPECTED[0]).write_bytes(b"changed by the model owner")
    code, record = run_remote(source, dest, tmp_path / "e", stamp="20261019T100200Z")
    assert code == 1 and record["status"] == "failed" and "--name" in record["error"]
    assert (dest / stage.EXPECTED[0]).read_bytes() == stage.EXPECTED[0].encode() * 3


def test_a_missing_runner_file_stops_before_copying(tmp_path):
    source = make_source(tmp_path / "src")
    (source / stage.EXPECTED[3]).unlink()  # the .hwh beside the bitstream
    dest = tmp_path / "copy"
    code, record = run_remote(source, dest, tmp_path / "e")
    assert code == 1 and "missing in the source" in record["error"] and stage.EXPECTED[3] in record["error"]
    assert not dest.exists()


def test_a_missing_source_folder_says_the_board_may_have_restarted(tmp_path):
    code, record = run_remote(tmp_path / "gone", tmp_path / "copy", tmp_path / "e")
    assert code == 1 and "restarted" in record["error"]
    assert not (tmp_path / "copy").exists()


def test_the_printed_deploy_command_is_one_the_deploy_tool_accepts():
    dest = stage.destination(stage.NAME)
    assert dest == deploy_service.BOARD_ROOT + "/model-runner/cnn_conv1d"
    argv = stage.deploy_command(dest).split()[3:]
    parser_args = {}

    def capture(args):
        parser_args["options"] = deploy_service.options_from(args)
        return 0

    original = deploy_service.deploy
    deploy_service.deploy = capture
    try:
        assert deploy_service.main(argv) == 0
    finally:
        deploy_service.deploy = original
    runner = parser_args["options"]["runner"]
    assert runner["module"] == "src.socket_worker"
    assert runner["cwd"] == dest + "/ai_integration"
    assert runner["args"] == ["--weights", "fpga/hls/eightclass_weights_20261018_v2.npz",
                              "--bit", dest + "/cnn_conv1d_fixed28_v2.bit"]


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "a b", "../x"])
def test_the_copy_name_is_a_plain_folder_name(name):
    with pytest.raises(ValueError):
        stage.destination(name)


def test_dry_run_connects_nothing(monkeypatch, capsys):
    monkeypatch.setattr(stage, "_connect", lambda *a, **k: pytest.fail("connected"))
    assert stage.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "Dry run" in out and "/tmp/cnn_conv1d -> " in out and "--runner-cwd " in out


def test_a_windows_source_path_is_refused(capsys):
    assert stage.main(["--dry-run", "--source", "D:/Git/tmp/cnn_conv1d"]) == 2
    assert "Git Bash" in capsys.readouterr().err


FULL = stage.RUNNERS["full"]


def full_files():
    return {name: ("full " + name).encode() for name in FULL.expected()}


def run_move(upload, dest, evidence, expected, stamp="20261022T100000Z"):
    done = subprocess.run([sys.executable, "-I", "-c", stage.REMOTE_PROGRAM, str(upload), str(dest),
                           stamp, json.dumps(expected), str(evidence), "move"],
                          capture_output=True, text=True, timeout=60)
    return done.returncode, json.loads(done.stdout.strip().splitlines()[-1])


def write_upload(root, files):
    for name, data in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)
    return root


def test_the_full_runner_needs_its_code_weights_overlay_and_hwh_in_repository_layout():
    assert FULL.expected() == (
        "src/ai_common.py", "src/export_full_cnn.py", "src/full_cnn_backend.py",
        "src/socket_worker_full.py", "fpga/hls/eightclass_weights_20261018_v2.npz",
        "fpga/overlays/full_cnn/cnn_full_20261020.bit", "fpga/overlays/full_cnn/cnn_full_20261020.hwh")
    # Weights staged on their own are only named in the command, not copied.
    assert "fpga/hls/eightclass_weights_20261018_v2.npz" not in FULL.expected("/var/tmp/w/x.npz")
    # The Conv1-only runner keeps the files and names it had.
    assert stage.EXPECTED == ("ai_integration/src/socket_worker.py",
                              "ai_integration/fpga/hls/eightclass_weights_20261018_v2.npz",
                              "cnn_conv1d_fixed28_v2.bit", "cnn_conv1d_fixed28_v2.hwh")


def parsed_runner(command):
    captured = {}
    original = deploy_service.deploy
    deploy_service.deploy = lambda args: captured.update(options=deploy_service.options_from(args)) or 0
    try:
        assert deploy_service.main(command.split()[3:]) == 0
    finally:
        deploy_service.deploy = original
    return captured["options"]["runner"]


@pytest.mark.parametrize("weights", [None, deploy_service.BOARD_ROOT +
    "/model-runner/weights_standard_20261021/eightclass_weights_standard_20261021.npz"])
def test_the_full_runner_command_is_the_one_deployed_on_10_21_and_10_22(weights):
    dest = stage.destination(FULL.name)
    runner = parsed_runner(stage.deploy_command(dest, "full", weights))
    assert runner["module"] == "src.socket_worker_full" and runner["cwd"] == dest
    assert runner["args"] == ["--weights", weights or "fpga/hls/eightclass_weights_20261018_v2.npz",
                              "--bit", dest + "/fpga/overlays/full_cnn/cnn_full_20261020.bit"]
    assert "--control-address" not in stage.deploy_command(dest, "full", weights)


def test_an_upload_matching_the_commit_is_moved_into_place(tmp_path):
    files = full_files()
    upload = write_upload(tmp_path / "model-runner" / ".upload-cnn_full-1", files)
    dest = tmp_path / "model-runner" / "cnn_full_20261020"
    code, record = run_move(upload, dest, tmp_path / "e", stage.listing(files))
    assert code == 0 and record["status"] == "staged"
    assert {name: (dest / name).read_bytes() for name in files} == files
    assert not upload.exists()


def test_an_upload_that_differs_from_the_commit_is_removed_and_nothing_staged(tmp_path):
    files = full_files()
    upload = write_upload(tmp_path / ".upload", dict(files, **{"src/ai_common.py": b"damaged"}))
    dest = tmp_path / "cnn_full_20261020"
    code, record = run_move(upload, dest, tmp_path / "e", stage.listing(files))
    assert code == 1 and "src/ai_common.py" in record["error"]
    assert not dest.exists() and not upload.exists()


def test_an_existing_copy_with_the_same_files_and_more_counts_as_staged(tmp_path):
    files = full_files()
    dest = write_upload(tmp_path / "cnn_full_20261020", dict(files, **{"extra.npz": b"other weights"}))
    upload = write_upload(tmp_path / ".upload", files)
    code, record = run_move(upload, dest, tmp_path / "e", stage.listing(files))
    assert code == 0 and record["status"] == "already_staged"
    assert not upload.exists() and (dest / "extra.npz").exists()
    changed = write_upload(tmp_path / ".upload2", dict(files, **{"src/ai_common.py": b"new"}))
    code, record = run_move(changed, dest, tmp_path / "e", stage.listing(
        dict(files, **{"src/ai_common.py": b"new"})))
    assert code == 1 and "--name" in record["error"]
    assert (dest / "src/ai_common.py").read_bytes() == files["src/ai_common.py"]
    assert not changed.exists()


def test_git_files_reads_each_file_of_a_commit_and_names_a_missing_one(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    git("init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_bytes(b"\x00binary\r\n")
    git("add", "src/a.py")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "a")
    assert stage.git_files("HEAD", ["src/a.py"], root=tmp_path) == {"src/a.py": b"\x00binary\r\n"}
    with pytest.raises(ValueError, match="git fetch upstream"):
        stage.git_files("HEAD", ["src/missing.py"], root=tmp_path)


def test_full_dry_run_reads_the_commit_and_connects_nothing(monkeypatch, capsys):
    monkeypatch.setattr(stage, "_connect", lambda *a, **k: pytest.fail("connected"))
    seen = []
    monkeypatch.setattr(stage, "git_files", lambda ref, names: seen.append(ref) or
                        {name: b"x" for name in names})
    assert stage.main(["--runner", "full", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert seen == ["upstream/main"]
    assert "Upload from upstream/main" in out and "--runner-module src.socket_worker_full" in out
    assert "Dry run" in out


def test_from_git_is_refused_for_the_conv1d_folder_layout(capsys):
    assert stage.main(["--dry-run", "--from-git", "HEAD"]) == 2
    assert "--source" in capsys.readouterr().err


def test_the_jump_user_defaults_to_ltc_jump_user(monkeypatch):
    seen = []
    monkeypatch.setenv("LTC_JUMP_USER", "e0123456")
    monkeypatch.setattr(stage, "stage", lambda args: seen.append(args.jump_user) or 0)
    assert stage.main([]) == 0 and seen == ["e0123456"]


class FakeBoard:
    """SFTP writes and commands run on this machine, under the test's BOARD_ROOT."""

    def __init__(self):
        self.closed = False
        board = self

        class Sftp:
            def stat(self, path):
                if not Path(path).exists():
                    raise IOError(path)

            def mkdir(self, path):
                Path(path).mkdir()

            def putfo(self, stream, path, confirm=True):
                Path(path).write_bytes(stream.read())

            def close(self):
                pass
        self.sftp = Sftp

    def open_sftp(self):
        return self.sftp()

    def exec_command(self, command, timeout=None):
        argv = shlex.split(command)
        if argv[0] == "/usr/bin/python3":
            argv[0] = sys.executable
        done = subprocess.run(argv, capture_output=True, timeout=60)

        class Out(io.BytesIO):
            class channel:
                @staticmethod
                def recv_exit_status():
                    return done.returncode
        return None, Out(done.stdout), io.BytesIO(done.stderr)

    def close(self):
        self.closed = True


@pytest.mark.skipif(os.name == "nt", reason="runs the board program with POSIX paths")
def test_full_staging_uploads_checks_and_reports_end_to_end(tmp_path, monkeypatch, capsys):
    board_root = tmp_path / "board"
    (board_root / "model-runner").mkdir(parents=True)
    monkeypatch.setattr(stage, "BOARD_ROOT", str(board_root))
    monkeypatch.setattr(stage, "RECORDS", tmp_path / "records")
    files = full_files()
    monkeypatch.setattr(stage, "git_files", lambda ref, names: {n: files[n] for n in names})
    users = []
    monkeypatch.setattr(stage, "_connect", lambda jump, board: users.append((jump, board)) or
                        (FakeBoard(), FakeBoard(), None))
    assert stage.main(["--runner", "full", "--jump-user", "e0123456"]) == 0
    dest = board_root / "model-runner" / "cnn_full_20261020"
    assert {name: (dest / name).read_bytes() for name in files} == files
    assert sorted(p.name for p in (board_root / "model-runner").iterdir()) == ["cnn_full_20261020"]
    assert users == [("e0123456", "xilinx")]
    record = json.loads(next((tmp_path / "records").glob("model-runner-stage-*.json")).read_text())
    assert record["status"] == "staged" and record["runner"] == "full"
    assert record["git_ref"] == "upstream/main"
    assert "Copied: 7 files" in capsys.readouterr().out
    assert stage.main(["--runner", "full"]) == 0
    assert "Already copied" in capsys.readouterr().out
