"""The recording menu must preserve device selection and exact capture evidence."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


def menu_module():
    # Keep a missing implementation an explicit failing requirement during TDD.
    import importlib.util
    assert importlib.util.find_spec("video_demo"), "The video menu has not been implemented"
    import video_demo
    return video_demo


def test_ports_require_two_distinct_actual_serial_devices():
    menu = menu_module()
    ports = menu.parse_ports('[{"port":"COM4","description":"USB","hwid":"a"},'
                             '{"port":"COM7","description":"USB","hwid":"b"}]')
    assert menu.validate_ports("com4", "COM7", ports) == ("COM4", "COM7")
    for left, right in [("COM4", "com4"), ("COM4", "COM8"), ("COM4", "--erase")]:
        with pytest.raises(ValueError):
            menu.validate_ports(left, right, ports)
    for raw in ["[]", "{}", "not json", '[{"port":"--erase"}]']:
        with pytest.raises(ValueError):
            menu.parse_ports(raw)


def test_upload_uses_distinct_protected_profiles_and_stops_on_failure(monkeypatch):
    menu = menu_module()
    commands = []
    monkeypatch.setattr(menu, "platformio_command", lambda: ["platformio"])

    def run(command):
        commands.append(command)
        if "firebeetle32-right" in command and "upload" not in command:
            raise subprocess.CalledProcessError(5, command)

    monkeypatch.setattr(menu, "run_checked", run)
    with pytest.raises(subprocess.CalledProcessError):
        menu.upload_boards("COM4", "COM7")
    assert len(commands) == 3  # fixture generation, then the two builds
    assert not any("upload" in command for command in commands)
    commands.clear()
    monkeypatch.setattr(menu, "run_checked", lambda command: commands.append(command))
    menu.upload_boards("COM4", "COM7")
    uploads = [command for command in commands if "upload" in command]
    assert len(uploads) == 2
    assert uploads[0][-5:] == ["firebeetle32-left", "-t", "upload", "--upload-port", "COM4"]
    assert uploads[1][-5:] == ["firebeetle32-right", "-t", "upload", "--upload-port", "COM7"]


def test_failed_new_capture_never_reopens_previous_success(tmp_path, monkeypatch):
    menu = menu_module()
    from test_demo_launcher import physical_report, install_child

    ca = tmp_path / "ca.pem"
    ca.write_text("LOCAL TEST ONLY", encoding="utf-8")
    state = tmp_path / "menu" / "last-attempt.json"
    install_child(monkeypatch, physical_report())
    result, first = menu.capture_attempt(12, state_path=state, ca=ca)
    assert result == 0 and first.is_dir()
    assert menu.selected_capture(state) == first
    # A preflight failure produces no new B07 folder. Its attempt still replaces
    # the selection so that the old successful result cannot be misrepresented.
    result, failed = menu.capture_attempt(50, state_path=state, ca=tmp_path / "missing.pem")
    assert result != 0 and failed is None
    with pytest.raises(FileNotFoundError):
        menu.selected_capture(state)
    record = json.loads(state.read_text(encoding="utf-8"))
    assert record["p0"] == 50
    assert not (Path(record["output_root"]) / first.name).exists()
    assert (first / "report.json").is_file()


def test_capture_failure_keeps_its_own_report_and_exit_status(tmp_path, monkeypatch):
    menu = menu_module()
    from test_demo_launcher import physical_report, install_child
    ca = tmp_path / "ca.pem"
    ca.write_text("LOCAL TEST ONLY", encoding="utf-8")
    state = tmp_path / "menu" / "last-attempt.json"
    install_child(monkeypatch, physical_report(), exit_code=7)
    result, folder = menu.capture_attempt(0, state_path=state, ca=ca)
    assert result == 7
    assert menu.selected_capture(state) == folder
    assert (folder / "exit-code.txt").read_text().strip() == "7"


def test_report_selection_rejects_ambiguous_attempts(tmp_path):
    menu = menu_module()
    root = tmp_path / "attempt"
    (root / "B07-one").mkdir(parents=True)
    (root / "B07-two").mkdir()
    state = tmp_path / "last-attempt.json"
    state.write_text(json.dumps({"output_root": str(root), "p0": 0}))
    with pytest.raises(ValueError, match="more than one"):
        menu.selected_capture(state)


def test_opening_and_quitting_menu_never_starts_hardware():
    menu_module()
    result = subprocess.run([sys.executable, "video_demo.py"], input="0\n",
                            text=True, capture_output=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0
    assert "1" in result.stdout and "Upload" in result.stdout
    assert "9" in result.stdout and "Ultra96" in result.stdout


def test_worker_failure_is_visible_before_close_prompt():
    menu_module()
    result = subprocess.run([sys.executable, "video_demo.py", "--worker", "serial", "--port", "invalid"],
                            input="\n", text=True, capture_output=True, encoding="utf-8", timeout=10)
    assert result.returncode != 0
    assert "Operation failed:" in result.stdout
    assert result.stdout.index("Operation failed:") < result.stdout.index("Press Enter to close")


def test_capture_returns_its_own_folder_if_another_menu_changes_selection(tmp_path, monkeypatch):
    menu = menu_module()
    from test_demo_launcher import physical_report, install_child
    ca = tmp_path / "ca.pem"
    ca.write_text("LOCAL TEST ONLY", encoding="utf-8")
    state = tmp_path / "menu" / "last-attempt.json"
    other = tmp_path / "another-menu"
    (other / "B07-other").mkdir(parents=True)
    original_write = menu.write_state

    def competing_selection(path, data):
        original_write(path, data)
        if data["status"] == "finished":
            original_write(path, {"output_root": str(other), "p0": 999})

    monkeypatch.setattr(menu, "write_state", competing_selection)
    install_child(monkeypatch, physical_report())
    result, folder = menu.capture_attempt(12, state_path=state, ca=ca)
    assert result == 0
    assert folder.parent != other
    assert (folder / "report.json").is_file()
