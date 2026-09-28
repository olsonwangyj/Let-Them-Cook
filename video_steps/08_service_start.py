"""Start the matching deployed Ultra96 service only when both application ports are free."""
import shlex
from _common import BOARD_ROOT, BOARD_SOURCE, cli, run, ssh_command


def start_script():
    # A failed listener query is an error, never evidence that the ports are free.
    return f'''set -eu
cd {shlex.quote(BOARD_SOURCE)}
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
exec /usr/bin/python3 -u -m ultra96.server --cert {BOARD_ROOT}/tls/server-cert.pem --key {BOARD_ROOT}/tls/server-key.pem --session-id week7-demo --ingest-port 8888 --gateway-port 9999
'''


def main():
    print("Use 07_service_status.py first. Reuse an existing healthy service; do not start another.")
    print("Confirm ESP, board and iPhone versions match this deployment: " + BOARD_SOURCE)
    if input("Press Enter to start only if absent, or type q to cancel: ").strip():
        return 130
    # SSH and the server stay in this terminal; no background process is created.
    run(ssh_command(start_script()))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
