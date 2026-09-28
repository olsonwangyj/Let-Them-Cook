"""Build both protected firmware profiles, then flash LEFT and RIGHT using one programming USB cable."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
BOARDS = (("left", "38:18:2B:19:82:AE"), ("right", "38:18:2B:18:9D:6A"))


def _pio():
    installed = Path.home() / ".platformio" / "penv" / "Scripts" / "platformio.exe"
    executable = str(installed) if installed.is_file() else shutil.which("platformio")
    if not executable:
        raise FileNotFoundError("PlatformIO not found; expected " + str(installed))
    return [executable]


def _run(command):
    # Inherit the terminal: build colors, upload progress and pairing input stay live.
    print("\n> " + subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _ports():
    # Capture only public port metadata, never serial-monitor or passkey output.
    result = subprocess.run(_pio() + ["device", "list", "--serial", "--json-output"],
                            cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    rows = json.loads(result.stdout)
    if not isinstance(rows, list):
        raise ValueError("Unexpected PlatformIO serial-port data.")
    ports = []
    for row in rows:
        if not isinstance(row, dict) or not re.fullmatch(r"COM[1-9][0-9]*", str(row.get("port", "")), re.I):
            raise ValueError("Unexpected PlatformIO COM-port data.")
        port = row["port"].upper()
        if port in ports:
            raise ValueError("PlatformIO returned a duplicate COM port.")
        ports.append(port)
        print(f"{port} | {row.get('description', '')} | {row.get('hwid', '')}")
    if not ports:
        print("No serial ports detected.")
    return ports


def _answer(prompt):
    answer = input(prompt).strip()
    if answer.lower() == "q":
        raise KeyboardInterrupt
    return answer


def _flash():
    _run([sys.executable, "-m", "tools.generate_dummy_fixtures"])
    base = _pio() + ["run", "-d", str(ROOT / "firmware" / "esp32")]
    # Finish both builds before asking the operator to connect either board.
    for label, _ in BOARDS:
        _run(base + ["-e", "firebeetle32-" + label])
    for device_id, (label, _) in enumerate(BOARDS, start=1):
        swap = "Disconnect LEFT, then connect" if device_id == 2 else "Connect"
        answer = _answer(f"\n{swap} {label.upper()} / device {device_id} only; check physical labels. "
                         "Enter to continue / q to cancel: ")
        if answer:
            raise ValueError("Press Enter after connecting the labelled board, or q to cancel.")
        # Detect afresh after each swap; one programming USB cable can reuse a COM number.
        ports = _ports()
        if not ports:
            raise ValueError("Connect the labelled board with a data cable, then rerun flash.py.")
        port = ports[0] if len(ports) == 1 else _answer("Select the attached board's COM port / q to cancel: ").upper()
        if port not in ports:
            raise ValueError("Select an actual COM port from the displayed list.")
        print(f"Uploading {label.upper()} / device {device_id} on {port}.")
        _run(base + ["-e", "firebeetle32-" + label, "-t", "upload", "--upload-port", port])
    print("Both uploads succeeded. Disconnect laptop USB and power both boards independently for the BLE demo.")


def _pair(selection):
    print("Existing authenticated bonds are reused. Power the selected board(s).")
    print("First pairing: use --pair left/right with that board's --monitor COMx in another terminal.")
    print("Keep serial passkeys private and off camera.")
    # Delegate to the existing authenticated pairing flow; stop on its first failure.
    for label, address in BOARDS:
        if selection in ("both", label):
            print("\nPairing " + label.upper())
            _run([sys.executable, "-m", "laptop.windows_pairing", "--address", address])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--ports", action="store_true", help="Only list current COM ports.")
    modes.add_argument("--pair", nargs="?", const="both", choices=("left", "right", "both"),
                       help="Check or establish authenticated bonds; default: both.")
    modes.add_argument("--monitor", metavar="COMx", help="Private 115200-baud serial monitor in this terminal.")
    args = parser.parse_args(argv)  # --help exits before any hardware operation.
    try:
        if args.ports:
            _ports()
        elif args.pair:
            _pair(args.pair)
        elif args.monitor:
            port = args.monitor.strip().upper()
            if not re.fullmatch(r"COM[1-9][0-9]*", port):
                raise ValueError("Use an actual COM port, such as COM4.")
            print("Private serial monitor: keep passkeys off camera. No log is saved; Ctrl+C exits.")
            _run(_pio() + ["device", "monitor", "--port", port, "--baud", "115200", "--no-reconnect"])
        else:
            _flash()
        return 0
    except KeyboardInterrupt:
        print("\nCancelled; remaining operations were not run.")
        return 130
    except subprocess.CalledProcessError as error:
        print(f"FAILED: command exited with code {error.returncode}; remaining operations were not run.")
        return error.returncode or 1
    except (OSError, ValueError, EOFError) as error:
        print(f"FAILED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
