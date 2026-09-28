"""Small shared plumbing; each recording step still owns its own operation."""
import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # Direct script execution can import existing repo tools.
BOARD_ROOT = "/var/tmp/cg4002-week7-yanjie-20260907"
BOARD_SOURCE = BOARD_ROOT + "/source-co-v2-20260928T122047Z"


def cli(description, action):
    # Parse --help before any device, serial-port or network operation.
    argparse.ArgumentParser(description=description).parse_args()
    os.chdir(ROOT)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        return action()
    except KeyboardInterrupt:
        print("\nCancelled; no success is inferred.")
        return 130
    except subprocess.CalledProcessError as error:
        print(f"STEP FAILED: command exited with code {error.returncode}.")
        return error.returncode or 1
    except (OSError, ValueError, RuntimeError, EOFError) as error:
        print(f"STEP FAILED: {error}")
        return 2


def run(command):
    # Inherit stdin/stdout/stderr: prompts stay interactive and colors survive.
    print("\n> " + subprocess.list2cmdline([str(arg) for arg in command]), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def pio():
    installed = Path.home() / ".platformio" / "penv" / "Scripts" / "platformio.exe"
    found = str(installed) if installed.is_file() else shutil.which("platformio")
    if not found:
        raise FileNotFoundError("PlatformIO not found; expected " + str(installed))
    return [found]


def ssh_command(script):
    # Reuse the verified route and strict host checks, but remove local forwarding.
    from tools.ssh_tunnel import tunnel_command
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
