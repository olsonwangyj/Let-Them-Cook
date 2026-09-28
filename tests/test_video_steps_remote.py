"""Run the service startup guard locally; never contact SSH or real devices."""
import os
import shlex
import shutil
import subprocess

import pytest

from test_video_steps import step


@pytest.fixture
def local_shell():
    shell = shutil.which("sh")
    if shell is None:
        pytest.skip("A local POSIX sh is required to exercise the remote script")
    probe = subprocess.run([shell, "-c", "exit 0"], capture_output=True, timeout=5)
    if probe.returncode:
        pytest.skip("The installed sh cannot execute a local POSIX script")
    return shell


def run_start_guard(shell, monkeypatch, listeners="", ss_status=0):
    module = step("08_service_start", monkeypatch)
    monkeypatch.setattr(module, "BOARD_SOURCE", "/")
    lines = module.start_script().splitlines()
    launch_lines = [index for index, line in enumerate(lines) if line.startswith("exec ")]
    assert len(launch_lines) == 1, "Refuse to run an unrecognized server-launch script"
    launch = shlex.split(lines[launch_lines[0]])
    assert launch[:5] == ["exec", "/usr/bin/python3", "-u", "-m", "ultra96.server"]
    # Replace only the external listener query and final service launch.
    lines[launch_lines[0]] = "printf 'START_REACHED\\n'"
    fake_ss = """ss() {
  case "$1" in
    -ltnH) printf '%s' "$B07_TEST_LISTENERS"; return "$B07_TEST_SS_STATUS" ;;
    -ltnp) printf '%s' "$B07_TEST_LISTENERS" ;;
    *) return 98 ;;
  esac
}
"""
    environment = dict(os.environ, B07_TEST_LISTENERS=listeners, B07_TEST_SS_STATUS=str(ss_status))
    return subprocess.run([shell, "-c", fake_ss + "\n".join(lines)], env=environment,
                          text=True, capture_output=True, timeout=5)


def test_listener_query_failure_never_starts_service(local_shell, monkeypatch):
    result = run_start_guard(local_shell, monkeypatch, ss_status=1)
    assert "START_REACHED" not in result.stdout
    assert result.returncode != 0


@pytest.mark.parametrize("address", ["127.0.0.1:8888", "[::]:9999"])
def test_either_occupied_service_port_blocks_start(local_shell, monkeypatch, address):
    listeners = "LISTEN 0 128 127.0.0.1:22 0.0.0.0:*\n" + f"LISTEN 0 128 {address} *:*\n"
    result = run_start_guard(local_shell, monkeypatch, listeners)
    assert "START_REACHED" not in result.stdout
    assert result.returncode != 0


def test_free_service_ports_reach_start(local_shell, monkeypatch):
    listeners = "LISTEN 0 128 127.0.0.1:22 0.0.0.0:*\nLISTEN 0 128 [::]:18888 [::]:*\n"
    result = run_start_guard(local_shell, monkeypatch, listeners)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "START_REACHED"


@pytest.mark.parametrize("name", ["07_service_status", "08_service_start"])
def test_remote_steps_retain_strict_host_keys_on_both_hops(monkeypatch, name):
    module = step(name, monkeypatch)
    commands = []
    monkeypatch.setattr(module, "run", lambda command: commands.append(command))
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert module.main() == 0
    command, = commands
    options = [command[index + 1] for index, value in enumerate(command[:-1]) if value == "-o"]
    assert "StrictHostKeyChecking=yes" in options
    proxy = next(option for option in options if option.startswith("ProxyCommand="))
    assert "-o StrictHostKeyChecking=yes" in proxy
    assert "StrictHostKeyChecking=no" not in " ".join(command)
    assert "-N" not in command and "-T" not in command and "-L" not in command
    assert command[-2] == "xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg"
    assert shlex.split(command[-1])[:2] == ["sh", "-c"]
