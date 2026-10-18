"""Start the model owner's runner program for ultra96.model_bridge, replacing the one it last started.

tools/deploy_service runs this as root with sudo, once the new service listens:

    sudo -S /usr/bin/python3 -I model_runner_launch.py '<json options>'

It stops the runner recorded in the pid file (only when that process is still the
same one), starts the new runner in its own session through a login shell (so the
board's /etc/profile.d settings, such as PYNQ's environment, apply as in an
interactive `sudo -E` shell), with stdin from /dev/null and its output in a log
file, and checks that it is still running a moment later. It prints one JSON
line. Standard library only, and it imports nothing from this repository.

Options: python, script, args (list), log, pidfile, service_log, settle (seconds the
runner must survive), connect_wait (seconds to look for the bridge's "model runner
connected" in service_log).
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

CONNECTED = "model runner connected"


def _stat(pid):
    try:
        return (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
    except (FileNotFoundError, ProcessLookupError, IndexError):
        return None


def start_ticks(pid):
    fields = _stat(pid)
    return None if fields is None else fields[19]


def alive(pid, ticks):
    fields = _stat(pid)
    return fields is not None and fields[19] == ticks and fields[0] != "Z"


def stop_previous(pidfile, wait=5.0):
    """Stop the runner this launcher started last; never signal a reused PID."""
    try:
        previous = json.loads(Path(pidfile).read_text())
        pid, ticks = int(previous["pid"]), str(previous["start_ticks"])
    except (FileNotFoundError, ValueError, KeyError, TypeError):
        return "none"
    if not alive(pid, ticks):
        return "not_running"
    # The runner runs in its own session; signal the whole group so its children stop too.
    for sig, seconds in ((signal.SIGTERM, wait), (signal.SIGKILL, wait)):
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            return "sigterm" if sig == signal.SIGTERM else "sigkill"
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if not alive(pid, ticks):
                return "sigterm" if sig == signal.SIGTERM else "sigkill"
            time.sleep(0.1)
    raise RuntimeError("the previous runner did not exit after SIGKILL")


def _tail(path, lines=10):
    try:
        return Path(path).read_text(errors="replace").splitlines()[-lines:]
    except FileNotFoundError:
        return []


def _connected_since(service_log, offset):
    try:
        with open(service_log, "rb") as stream:
            stream.seek(offset)
            return CONNECTED.encode() in stream.read()
    except FileNotFoundError:
        return False


def launch(options):
    script = Path(options["script"])
    if not script.is_file():
        raise FileNotFoundError("runner script not found: " + str(script))
    if not Path(options["python"]).is_file():
        raise FileNotFoundError("runner python not found: " + options["python"])
    result = dict(script=str(script), log=options["log"])
    result["previous"] = stop_previous(options["pidfile"])
    service_log = options.get("service_log")
    offset = os.path.getsize(service_log) if service_log and os.path.exists(service_log) else 0
    argv = ["/bin/bash", "-l", "-c", 'exec "$@"', "model-runner", options["python"], str(script)]
    argv += list(options.get("args", []))
    with open(options["log"], "ab", buffering=0) as out:
        os.chmod(options["log"], 0o644)
        runner = subprocess.Popen(argv, cwd=str(script.parent), stdin=subprocess.DEVNULL,
                                  stdout=out, stderr=out, start_new_session=True)
    ticks = start_ticks(runner.pid)
    record = dict(pid=runner.pid, start_ticks=ticks, argv=argv, started=time.time())
    Path(options["pidfile"]).write_text(json.dumps(record) + "\n")
    os.chmod(options["pidfile"], 0o644)
    result.update(pid=runner.pid)
    deadline = time.monotonic() + options.get("settle", 3.0)
    while time.monotonic() < deadline:
        if runner.poll() is not None:
            result.update(status="exited", returncode=runner.returncode, log_tail=_tail(options["log"]))
            return result
        time.sleep(0.1)
    result["status"] = "running"
    result["connected"] = False
    if service_log:
        deadline = time.monotonic() + options.get("connect_wait", 10.0)
        while time.monotonic() < deadline and runner.poll() is None:
            if _connected_since(service_log, offset):
                result["connected"] = True
                break
            time.sleep(0.2)
        if runner.poll() is not None:
            result.update(status="exited", returncode=runner.returncode, log_tail=_tail(options["log"]))
    return result


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        result = launch(json.loads(argv[0]))
    except Exception as exc:
        result = dict(status="failed", error=type(exc).__name__ + ": " + str(exc))
    print(json.dumps(result), flush=True)
    return 0 if result.get("status") == "running" else 1


if __name__ == "__main__":
    sys.exit(main())
