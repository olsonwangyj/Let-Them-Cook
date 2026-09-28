"""Reuse demo.py to capture both physical ESPs for 60 seconds at 10 Hz."""
from _common import cli


def main():
    import demo
    print("Close serial monitors; remove BOTH laptop USB cables and power each board independently.")
    print("Keep the SSH tunnel open and the Visualizer iPhone Subscribed in the foreground.")
    print("Manually record starting phone count P0 now; record P1 after this capture settles.")
    if input("Press Enter when ready, or type q to cancel: ").strip():
        print("Capture cancelled.")
        return 130
    # No new capture manager or selection state: demo.py prints the exact Saved in directory.
    return demo.main(["run", "--duration", "60", "--rate", "10"])


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
