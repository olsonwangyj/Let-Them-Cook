"""Foreground Ultra96 status/start operations for the existing demo CLI."""
import json
from pathlib import Path
import shlex
import subprocess

from tools.ssh_tunnel import tunnel_command
from ultra96.protocol import validate_session


ROOT = Path(__file__).resolve().parents[1]
BOARD_ROOT = "/var/tmp/cg4002-week7-yanjie-20260907"
# Fallback only: the 28 September snapshot. After python -m tools.deploy_service, the
# folder it deployed (recorded locally in DEPLOYMENTS) is used instead.
BOARD_SOURCE = BOARD_ROOT + "/source-co-v2-20260928T122047Z"
DEPLOYMENTS = ROOT / ".comms-local" / "deployments"


def board_source():
    """The working folder of the service the newest local deployment record left running."""
    try:
        records = sorted(DEPLOYMENTS.glob("deployment-*.json"))
    except OSError:
        records = []
    for path in reversed(records):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            folder = record["current"]["cwd"]
        except (OSError, ValueError, KeyError, TypeError):
            continue  # unreadable, or nothing was left running
        if isinstance(folder, str) and folder.startswith(BOARD_ROOT + "/") and folder.isprintable():
            return folder
    return BOARD_SOURCE


def ssh_command(script):
    # Keep both verified SSH hops; a remote command needs no local forwarding.
    tunnel = tunnel_command("yanjie@stujump.comp.nus.edu.sg",
        "xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg", 18889, 8888, batch=False)
    command = [tunnel[0], "-tt"]
    arguments = iter(tunnel[1:-1])
    for argument in arguments:
        if argument == "-L":
            next(arguments)
        elif argument not in ("-N", "-T"):
            command.append(argument)
    return command + [tunnel[-1], "sh -c " + shlex.quote(script)]


def start_script(session_id):
    validate_session(session_id)
    # A failed listener query is an error, never evidence that the ports are free.
    return f'''set -eu
cd {shlex.quote(board_source())}
command -v ss >/dev/null
b07_listeners=$(ss -ltnH) || {{
  echo 'Could not inspect service ports. Nothing was started.' >&2
  exit 2
}}
while read -r b07_state b07_recv_q b07_send_q b07_local b07_peer; do
  case "$b07_local" in
    *:8888|*:9999)
      echo 'Service ports are already in use. Nothing was stopped or started.'
      ss -ltnp
      exit 2
      ;;
  esac
done <<EOF
$b07_listeners
EOF
exec /usr/bin/python3 -u -m ultra96.server --cert {BOARD_ROOT}/tls/server-cert.pem --key {BOARD_ROOT}/tls/server-key.pem --session-id {shlex.quote(session_id)} --ingest-port 8888 --gateway-port 9999
'''


def main(start=False, session_id="ltc-comms") -> int:
    if start:
        script = start_script(session_id)
        print("Run 'python demo.py service' first. Reuse an existing healthy service.")
        print("Confirm ESP, board and iPhone versions match this deployment: " + board_source())
        print("Session: " + session_id + " (the capture and the phone must use the same one)")
        if input("Press Enter to start only if absent, or type q to cancel: ").strip():
            return 130
    else:
        # Read-only checks: no deployment, process termination or service restart.
        script = '''set -eu
ss -ltnp
ps -u "$(id -u)" -o pid=,args=
for pid in $(pgrep -u "$(id -u)" -f '[u]ltra96.server' || true); do
  printf '\\nServer PID %s, working directory: ' "$pid"
  readlink "/proc/$pid/cwd" || true
done
'''
    # Inherited stdio keeps authentication interactive and the server in this terminal.
    return subprocess.run(ssh_command(script), cwd=ROOT).returncode
