"""Interactive shortcuts for filming the existing B07 communication demo.

Run Video-Demo.cmd on Windows, or python video_demo.py. Merely opening the
menu does not contact devices. Each operation reuses the project's existing
tools; physical setup and iPhone observations remain the operator's job.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import uuid
import webbrowser


ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / ".week7-local" / "video-menu" / "last-attempt.json"
ADDRESSES = (("LEFT / device 1", "38:18:2B:19:82:AE"),
             ("RIGHT / device 2", "38:18:2B:18:9D:6A"))
BOARD_ROOT = "/var/tmp/cg4002-week7-yanjie-20260907"
BOARD_SOURCE = BOARD_ROOT + "/source-co-v2-20260928T122047Z"


def run_checked(command):
    """Inherit the console: SSH/PIN input stays interactive and output keeps color."""
    print("\n> " + subprocess.list2cmdline([str(arg) for arg in command]), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def platformio_command():
    installed = Path.home() / ".platformio" / "penv" / "Scripts" / "platformio.exe"
    found = str(installed) if installed.is_file() else shutil.which("platformio")
    if not found:
        raise FileNotFoundError("PlatformIO is missing. Expected: " + str(installed))
    return [found]


def parse_ports(raw):
    ports = json.loads(raw)
    if not isinstance(ports, list) or not ports:
        raise ValueError("No serial ports found. Connect a board, then try again.")
    for item in ports:
        if not isinstance(item, dict) or not re.fullmatch(r"COM[1-9][0-9]*", str(item.get("port", "")), re.I):
            raise ValueError("Unexpected serial-port data from PlatformIO.")
        item["port"] = item["port"].upper()
    if len({item["port"] for item in ports}) != len(ports):
        raise ValueError("PlatformIO returned duplicate serial ports.")
    return ports


def serial_ports():
    result = subprocess.run(platformio_command() + ["device", "list", "--serial", "--json-output"],
                            cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    return parse_ports(result.stdout)


def validate_ports(left, right, ports):
    left, right = left.upper(), right.upper()
    available = {item["port"].upper() for item in ports}
    if left == right:
        raise ValueError("LEFT and RIGHT must use different COM ports.")
    if left not in available or right not in available:
        raise ValueError("Select two ports from the current detected list.")
    return left, right


def choose_port(ports, label):
    print("\nDetected serial ports (list order does not identify LEFT/RIGHT):")
    for number, item in enumerate(ports, 1):
        print(f"  {number}. {item['port']}  {item.get('description', '')}  {item.get('hwid', '')}")
    value = input(f"Select the verified {label} port number (q cancels): ").strip()
    if value.lower() == "q":
        raise KeyboardInterrupt
    if not value.isdecimal() or not 1 <= int(value) <= len(ports):
        raise ValueError("Choose a number from the list.")
    return ports[int(value) - 1]["port"]


def upload_boards(left, right):
    """Build both protected profiles before either upload; any failure stops here."""
    pio = platformio_command()
    run_checked([sys.executable, "-m", "tools.generate_dummy_fixtures"])
    base = pio + ["run", "-d", str(ROOT / "firmware" / "esp32")]
    for environment in ("firebeetle32-left", "firebeetle32-right"):
        run_checked(base + ["-e", environment])
    for environment, port in (("firebeetle32-left", left), ("firebeetle32-right", right)):
        run_checked(base + ["-e", environment, "-t", "upload", "--upload-port", port])
    print("\nBOTH UPLOADS SUCCEEDED. Pair if needed, close serial monitors, then remove BOTH laptop USB cables.")
    print("Power each board independently before the BLE capture.")


def write_state(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def selected_capture(state_path=STATE_PATH):
    state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    return attempt_capture(state["output_root"])


def attempt_capture(output_root):
    folders = list(Path(output_root).glob("B07-*"))
    folders = [path for path in folders if path.is_dir()]
    if not folders:
        raise FileNotFoundError("The selected attempt has no capture folder. No older success was selected.")
    if len(folders) != 1:
        raise ValueError("The selected attempt contains more than one capture; select a folder explicitly.")
    return folders[0]


def capture_attempt(p0, *, state_path=STATE_PATH, ca=None):
    """Select a unique attempt BEFORE running, including failed or cancelled runs."""
    import demo
    if type(p0) is not int or p0 < 0:
        raise ValueError("P0 must be a nonnegative whole number.")
    state_path = Path(state_path)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_root = state_path.parent / "runs" / (stamp + "-" + uuid.uuid4().hex[:8])
    output_root.mkdir(parents=True)
    state = {"output_root": str(output_root.resolve()), "p0": p0, "status": "started"}
    write_state(state_path, state)
    command = ["run", "--duration", "60", "--rate", "10", "--output-root", str(output_root)]
    if ca is not None:
        command += ["--ca", str(ca)]
    result = 130
    try:
        result = demo.main(command)
    finally:
        state["status"] = "finished"
        state["exit_code"] = result
        write_state(state_path, state)
    try:
        folder = attempt_capture(output_root)
    except FileNotFoundError:
        folder = None
    return result, folder


def count_input(label):
    while True:
        value = input(label + " (whole number, q cancels): ").strip()
        if value.lower() == "q":
            raise KeyboardInterrupt
        if re.fullmatch(r"[0-9]+", value):
            return int(value)
        print("Read the actual iPhone counter and enter a nonnegative whole number.")


def listening():
    try:
        with socket.create_connection(("127.0.0.1", 18889), timeout=0.5):
            return True
    except OSError:
        return False


def new_window(worker, *arguments):
    if os.name != "nt":
        raise RuntimeError("The extra interactive windows require Windows.")
    # These windows are explicitly requested in the menu for operator interaction.
    return subprocess.Popen([sys.executable, "-u", str(ROOT / "video_demo.py"),
                             "--worker", worker, *arguments], cwd=ROOT,
                            creationflags=subprocess.CREATE_NEW_CONSOLE)


def remote_command(start=False):
    """Reuse the independently verified SSH hops, without the local-forward flags."""
    from tools.ssh_tunnel import tunnel_command
    import shlex
    tunnel = tunnel_command("yanjie@stujump.comp.nus.edu.sg",
                            "xilinx@makerslab-fpga-35.ddns.comp.nus.edu.sg", 18889, 8888, batch=False)
    command = [tunnel[0], "-tt"]
    index = 1
    while index < len(tunnel) - 1:
        if tunnel[index] in ("-N", "-T"):
            index += 1
        elif tunnel[index] == "-L":
            index += 2
        else:
            command.append(tunnel[index])
            index += 1
    if start:
        script = f'''set -eu
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
    else:
        script = '''set -eu
ss -ltnp
ps -u "$(id -u)" -o pid=,args=
for pid in $(pgrep -u "$(id -u)" -f '[u]ltra96.server' || true); do
  printf '\\nServer PID %s, working directory: ' "$pid"
  readlink "/proc/$pid/cwd" || true
done
'''
    return command + [tunnel[-1], "sh -c " + shlex.quote(script)]


def worker_main(kind, port=None):
    try:
        if kind == "tunnel":
            import demo
            return demo.main(["tunnel"])
        if kind == "serial":
            if port is None or not re.fullmatch(r"COM[1-9][0-9]*", port, re.I):
                raise ValueError("A valid COM port is required.")
            print("PRIVATE SETUP WINDOW: do not record or save the pairing passkey.")
            run_checked(platformio_command() + ["device", "monitor", "--port", port,
                                               "--baud", "115200", "--no-reconnect"])
        else:
            run_checked(remote_command(start=kind == "service-start"))
        return 0
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Operation failed: {error}", flush=True)
        return 2
    finally:
        try:
            input("\nThis operation has ended. Press Enter to close this window.")
        except (EOFError, KeyboardInterrupt):
            pass


class VideoMenu:
    def __init__(self):
        self.monitors = []
        self.tunnel = None

    def no_monitors(self):
        self.monitors = [child for child in self.monitors if child.poll() is None]
        if self.monitors:
            raise RuntimeError("Close the serial monitor windows first, then return to this menu.")

    def upload(self):
        self.no_monitors()
        print("SETUP only: close any running BLE capture. Identify each board's COM port first.")
        print("If unsure, connect one board at a time and inspect menu 8; cancel without opening its monitor.")
        input("Connect BOTH identified boards by USB for programming. Press Enter when ready.")
        ports = serial_ports()
        left = choose_port(ports, "LEFT / device 1")
        right = choose_port(ports, "RIGHT / device 2")
        left, right = validate_ports(left, right, ports)
        print(f"\nLEFT / ID 1 -> {left}; RIGHT / ID 2 -> {right}")
        if input("Press Enter to build/upload these boards, or q to cancel: ").strip():
            return
        upload_boards(left, right)

    def pair(self):
        print("Existing authenticated bonds are reused. For a first pairing, open the serial window with menu 8 first.")
        print("If BOTH boards need first-time pairing, use menu 8 twice to open BOTH serial windows before menu 2.")
        for label, address in ADDRESSES:
            print("\nChecking " + label + " / " + address)
            run_checked([sys.executable, "-m", "laptop.windows_pairing", "--address", address])

    def open_tunnel(self):
        if self.tunnel is not None and self.tunnel.poll() is None:
            print("The tunnel window opened by this menu is still running; finish its SSH login there.")
        elif listening():
            print("Port 18889 is already in use. Reuse it only if it is your configured B07 tunnel.")
            print("A listening port alone does not prove communication; check the capture ACKs.")
        else:
            self.tunnel = new_window("tunnel")
            print("Enter SSH passwords in the new tunnel window. Keep it open during capture.")

    def capture(self):
        from tools.video_evidence import show_packet_examples, record_phone_observation
        self.no_monitors()
        if not listening():
            raise RuntimeError("No listener on port 18889. Use menu 3 and finish SSH login first.")
        print("Remove BOTH laptop USB cables; use two independent power sources.")
        print("Keep the Visualizer iPhone subscribed and in the foreground. No other phone receiver.")
        print("The script cannot detect power wiring or read the iPhone screen.")
        p0 = count_input("When physically ready, enter the iPhone starting Received count P0")
        result, folder = capture_attempt(p0)
        if folder is None:
            print("No capture folder was created. Fix the reported failure, then make a new attempt.")
            return
        print("\nExact capture folder: " + str(folder))
        if result != 0:
            print(f"CAPTURE NOT PASSED (exit {result}). Keep this attempt; do not claim success.")
        show_packet_examples(folder)
        p1 = count_input("Wait until the iPhone count settles, then enter final count P1")
        record_phone_observation(folder, p0, p1, launcher_exit_code=result)
        print("Copy the camera clips and P0/P1 screenshots into this exact folder's camera-clips subfolder.")

    def review(self):
        import demo
        from tools.video_evidence import show_packet_examples
        typed = input("Press Enter for the selected attempt, or paste a capture folder / report.json path: ").strip().strip('"')
        folder = Path(typed).expanduser().resolve() if typed else selected_capture()
        if folder.name == "report.json":
            folder = folder.parent
        print("SAVED EVIDENCE REVIEW, not a new capture: " + str(folder))
        demo.show_report(folder)
        show_packet_examples(folder)
        observations = sorted(folder.glob("phone-observation-*.json"))
        if observations:
            print("\nLatest operator-entered phone observation: " + str(observations[-1]))
            print(observations[-1].read_text(encoding="utf-8"))
        else:
            print("No saved operator-entered phone observation for this capture.")

    def visuals(self):
        webbrowser.open((ROOT / "docs" / "B07-CO-video-visuals.en.html").as_uri())

    def fixtures(self):
        path = ROOT / "common" / "dummy_fixtures.json"
        print("Edit: " + str(path))
        print("Save, then use menu 1 to regenerate/build/upload BOTH boards. After removing USB, make a NEW capture.")
        print("The presentation contains a source snapshot; show this actual JSON when explaining changes.")
        subprocess.Popen(["notepad.exe", str(path)], cwd=ROOT)

    def serial(self):
        print("SETUP only: close other serial monitors and any BLE capture. Keep passkeys off camera.")
        port = choose_port(serial_ports(), "board needing first-time pairing")
        self.monitors.append(new_window("serial", "--port", port))
        print("Wait for the serial window to open, then use menu 2. Close the serial window when done.")

    def service(self):
        print("1. Read-only Ultra96 service / port / source-directory check")
        print("2. Start the existing deployed service only if ports 8888 and 9999 are both free")
        print("Current deployment: " + BOARD_SOURCE)
        choice = input("Select 1 or 2; Enter cancels: ").strip()
        if choice in ("1", "2"):
            new_window("service-status" if choice == "1" else "service-start")
            print("Enter SSH passwords in the new window. Reuse an existing healthy server.")
            if choice == "2":
                print("Keep the new server window open while using it. Never stop a shared service just to finish filming.")

    def run(self):
        actions = {"1": self.upload, "2": self.pair, "3": self.open_tunnel,
                   "4": self.capture, "5": self.review, "6": self.visuals,
                   "7": self.fixtures, "8": self.serial, "9": self.service}
        while True:
            print("\nB07 VIDEO DEMO - choose one step")
            print("1 Upload both boards       2 Check authenticated pairing")
            print("3 Open SSH tunnel         4 Capture 60 s / 10 Hz + phone counts")
            print("5 Review saved evidence   6 Open diagrams and code")
            print("7 Edit dummy fixtures     8 Open private pairing serial window")
            print("9 Ultra96 service         0 Exit menu")
            try:
                choice = input("Step: ").strip()
                if choice == "0":
                    print("Menu closed. Close your own tunnel/serial windows when finished.")
                    return 0
                if choice not in actions:
                    print("Choose 0 to 9.")
                    continue
                actions[choice]()
            except EOFError:
                return 0
            except KeyboardInterrupt:
                print("\nOperation cancelled. No success is inferred.")
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
                print(f"\nSTEP FAILED: {error}\nResolve this issue before continuing the recording.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("tunnel", "serial", "service-status", "service-start"),
                        help=argparse.SUPPRESS)
    parser.add_argument("--port", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        return worker_main(args.worker, args.port) if args.worker else VideoMenu().run()
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Operation failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
