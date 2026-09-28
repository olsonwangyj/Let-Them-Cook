"""List PlatformIO serial ports so you can identify the LEFT and RIGHT boards."""
from _common import cli, pio, run


def main():
    # Port order does not identify the boards; inspect one board at a time if unsure.
    run(pio() + ["device", "list"])
    return 0


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
