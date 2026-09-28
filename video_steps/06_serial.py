"""Open one private 115200-baud pairing serial monitor in the current terminal."""
import re
from _common import cli, pio, run


def main():
    port = input("Verified board COM port (for example COM4): ").strip().upper()
    if not re.fullmatch(r"COM[1-9][0-9]*", port):
        raise ValueError("Enter an actual COM port, such as COM4.")
    print("PRIVATE SETUP: do not record or save pairing passkeys. Close this monitor before BLE capture.")
    # Inherited console streams keep the passkey local; no output file is created.
    run(pio() + ["device", "monitor", "--port", port, "--baud", "115200", "--no-reconnect"])
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
