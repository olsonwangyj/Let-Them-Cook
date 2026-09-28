"""Check or establish authenticated Windows bonds for both configured FireBeetles."""
import sys
from _common import cli, run


def main():
    print("Existing authenticated bonds are reused.")
    print("First pairing: run 06_serial.py in a separate terminal for each board; keep passkeys off camera.")
    # Reuse the existing passkey flow; the first failure stops the second operation.
    for label, address in (("LEFT / device 1", "38:18:2B:19:82:AE"),
                           ("RIGHT / device 2", "38:18:2B:18:9D:6A")):
        print("\n" + label)
        run([sys.executable, "-m", "laptop.windows_pairing", "--address", address])
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
