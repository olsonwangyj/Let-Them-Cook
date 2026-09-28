"""Review one explicit capture, show matched packet examples, and record manual phone counts."""
from pathlib import Path
from _common import cli


def main():
    import demo
    from tools.video_evidence import show_packet_examples, record_phone_observation
    typed = input("Paste this capture's Saved in directory (or its report.json): ").strip().strip('"')
    if not typed:
        raise ValueError("An explicit capture path is required; no latest capture is selected.")
    folder = Path(typed).expanduser().resolve()
    if folder.name == "report.json":
        folder = folder.parent
    if not folder.is_dir():
        raise ValueError("The capture directory does not exist.")
    # Existing tools perform the statistics and exact sensor/ACK correlation.
    report_status = demo.show_report(folder)
    examples_ok = show_packet_examples(folder)
    p0 = int(input("Manually recorded starting iPhone Received count P0: "))
    p1 = int(input("Final iPhone Received count P1 after this same capture: "))
    review_status = report_status or (0 if examples_ok else 1)
    if review_status:
        print("REVIEW NOT PASSED: report or packet examples failed; this observation cannot pass.")
    # Preserve failed observations too; board ACKs never substitute for phone receipt.
    return record_phone_observation(folder, p0, p1, launcher_exit_code=review_status)


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
