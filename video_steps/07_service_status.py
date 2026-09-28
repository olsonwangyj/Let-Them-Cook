"""Inspect Ultra96 service ports, processes and source directories over verified SSH."""
from _common import cli, run, ssh_command


def main():
    # Read-only remote checks; no deployment, process termination or service restart.
    script = '''set -eu
ss -ltnp
ps -u "$(id -u)" -o pid=,args=
for pid in $(pgrep -u "$(id -u)" -f '[u]ltra96.server' || true); do
  printf '\\nServer PID %s, working directory: ' "$pid"
  readlink "/proc/$pid/cwd" || true
done
'''
    run(ssh_command(script))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
