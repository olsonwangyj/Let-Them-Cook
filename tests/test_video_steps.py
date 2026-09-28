"""Independent recording steps delegate existing tools and fail without fallback."""
import importlib
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
STEPS = ("00_ports", "01_flash", "02_pair", "03_tunnel", "04_capture",
         "05_report", "06_serial", "07_service_status", "08_service_start")


def step(name, monkeypatch):
    path = ROOT / "video_steps" / (name + ".py")
    assert path.is_file(), "The standalone recording step is missing: " + name
    monkeypatch.syspath_prepend(str(path.parent))
    return importlib.import_module(name)


@pytest.mark.parametrize("name", STEPS)
def test_help_works_outside_repository_without_running_the_operation(tmp_path, name):
    path = ROOT / "video_steps" / (name + ".py")
    assert path.is_file(), "The standalone recording step is missing: " + name
    result = subprocess.run([sys.executable, str(path), "--help"], cwd=tmp_path,
                            input="", capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout and "--help" in result.stdout


@pytest.mark.parametrize("left,right", [("COM4", "com4"), ("COM4", "COM8"),
                                       ("COM4", "--erase")])
def test_flash_rejects_same_or_undetected_ports_before_building(monkeypatch, left, right):
    module = step("01_flash", monkeypatch)
    monkeypatch.setattr(module, "detected_ports", lambda: ["COM4", "COM7"])
    responses = iter((left, right))
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(module, "run", lambda _: pytest.fail("Invalid ports reached a build/upload"))
    with pytest.raises(ValueError):
        module.main()


def test_flash_builds_both_protected_profiles_before_upload_and_stops_on_failure(monkeypatch):
    module = step("01_flash", monkeypatch)
    monkeypatch.setattr(module, "detected_ports", lambda: ["COM4", "COM7"])
    monkeypatch.setattr(module, "pio", lambda: ["platformio"])
    commands = []

    def run(command):
        commands.append(command)
        if "firebeetle32-right" in command and "upload" not in command:
            raise subprocess.CalledProcessError(5, command)

    responses = iter(("com4", "COM7"))
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    monkeypatch.setattr(module, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert len(commands) == 3
    assert commands[0][1:] == ["-m", "tools.generate_dummy_fixtures"]
    assert not any("upload" in command for command in commands)
    commands.clear()
    responses = iter(("com4", "COM7"))
    monkeypatch.setattr(module, "run", lambda command: commands.append(command))
    assert module.main() == 0
    uploads = [command for command in commands if "upload" in command]
    assert len(uploads) == 2
    assert uploads[0][-5:] == ["firebeetle32-left", "-t", "upload", "--upload-port", "COM4"]
    assert uploads[1][-5:] == ["firebeetle32-right", "-t", "upload", "--upload-port", "COM7"]


def test_pairing_failure_stops_before_next_board(monkeypatch):
    module = step("02_pair", monkeypatch)
    commands = []

    def fail(command):
        commands.append(command)
        raise subprocess.CalledProcessError(4, command)

    monkeypatch.setattr(module, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        module.main()
    assert len(commands) == 1
    assert commands[0][-2:] == ["--address", "38:18:2B:19:82:AE"]


@pytest.mark.parametrize("name,wanted", [("03_tunnel", ["tunnel"]),
        ("04_capture", ["run", "--duration", "60", "--rate", "10"])])
def test_tunnel_and_capture_preserve_existing_demo_exit_and_options(monkeypatch, name, wanted):
    module = step(name, monkeypatch)
    import demo
    commands = []

    def existing_demo(arguments):
        commands.append(arguments)
        return 7

    monkeypatch.setattr(demo, "main", existing_demo)
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert module.main() == 7
    assert commands == [wanted]


def test_capture_cancellation_does_not_start_existing_demo(monkeypatch):
    module = step("04_capture", monkeypatch)
    import demo
    monkeypatch.setattr(demo, "main", lambda _: pytest.fail("Cancelled capture started"))
    monkeypatch.setattr("builtins.input", lambda _: "q")
    assert module.main() != 0


@pytest.mark.parametrize("path_kind", ["directory", "report"])
def test_report_uses_only_explicit_capture_and_saves_manual_comparison(tmp_path, monkeypatch, path_kind):
    module = step("05_report", monkeypatch)
    from test_video_evidence import capture, packets, sensor, ack, observations
    folder = capture(tmp_path, "requested")
    packets(folder, [sensor(1), ack(1), sensor(2), ack(2)])
    other = capture(tmp_path, "other")
    chosen = folder if path_kind == "directory" else folder / "report.json"
    responses = iter((str(chosen), "100", "107"))
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    assert module.main() == 0
    record, = observations(folder)
    assert record["capture_directory"] == str(folder.resolve())
    assert (record["p0"], record["p1"], record["delta"], record["expected"]) == (100, 107, 7, 7)
    assert record["passed"] is True
    assert observations(other) == []


@pytest.mark.parametrize("failure", ["report", "packets"])
def test_report_or_packet_failure_cannot_print_phone_match(tmp_path, monkeypatch, capsys, failure):
    module = step("05_report", monkeypatch)
    from test_video_evidence import capture, packets, sensor, ack, observations
    folder = capture(tmp_path)
    packets(folder, [sensor(1), ack(1), sensor(2), ack(2)])
    if failure == "report":
        (folder / "exit-code.txt").write_text("7", encoding="utf-8")
    else:
        (folder / "packets.jsonl").write_text("{broken", encoding="utf-8")
    responses = iter((str(folder), "0", "7"))
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    assert module.main() != 0
    record, = observations(folder)
    assert record["passed"] is False
    output = capsys.readouterr().out
    assert "NOT PASSED" in output and "MATCH:" not in output


def test_blank_report_path_does_not_select_the_latest_capture(monkeypatch):
    module = step("05_report", monkeypatch)
    import demo
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(demo, "latest_report", lambda _: pytest.fail("Blank path selected latest"))
    with pytest.raises(ValueError, match="explicit"):
        module.main()


def test_serial_rejects_option_text_before_starting_monitor(monkeypatch):
    module = step("06_serial", monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _: "--erase")
    monkeypatch.setattr(module, "run", lambda _: pytest.fail("Invalid COM opened monitor"))
    with pytest.raises(ValueError):
        module.main()
