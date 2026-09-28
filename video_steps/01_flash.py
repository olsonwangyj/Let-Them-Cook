"""Build and upload the protected LEFT/RIGHT firmware to two verified COM ports."""
import json
import re
import subprocess
import sys
from _common import ROOT, cli, pio, run


def detected_ports():
    # Capture only public port metadata; serial-monitor/passkey output is never saved.
    result = subprocess.run(pio() + ["device", "list", "--serial", "--json-output"],
                            cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    rows = json.loads(result.stdout)
    if not isinstance(rows, list) or not rows:
        raise ValueError("No serial ports found. Connect the boards and try again.")
    ports = []
    for row in rows:
        if not isinstance(row, dict) or not re.fullmatch(r"COM[1-9][0-9]*", str(row.get("port", "")), re.I):
            raise ValueError("Unexpected PlatformIO serial-port data.")
        ports.append(row["port"].upper())
        print(ports[-1], row.get("description", ""), row.get("hwid", ""))
    return ports


def main():
    ports = detected_ports()
    left = input("Verified LEFT / device 1 COM port: ").strip().upper()
    right = input("Verified RIGHT / device 2 COM port: ").strip().upper()
    if left == right or left not in ports or right not in ports:
        raise ValueError("Use two different COM ports from the detected list.")
    print(f"LEFT / ID 1: {left}; RIGHT / ID 2: {right}")
    run([sys.executable, "-m", "tools.generate_dummy_fixtures"])
    base = pio() + ["run", "-d", str(ROOT / "firmware" / "esp32")]
    # Both builds must succeed before either upload. A failed command stops this script.
    for profile in ("firebeetle32-left", "firebeetle32-right"):
        run(base + ["-e", profile])
    for profile, port in (("firebeetle32-left", left), ("firebeetle32-right", right)):
        run(base + ["-e", profile, "-t", "upload", "--upload-port", port])
    print("Both uploads succeeded. Pair if needed; disconnect BOTH laptop USB cables before the BLE demo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
