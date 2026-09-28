"""Run the existing demo.py SSH tunnel in this terminal; keep it open during capture."""
from _common import cli


def main():
    import demo
    # Existing demo.py owns login prompts, tunnel lifetime and the exit status.
    return demo.main(["tunnel"])


if __name__ == "__main__":
    raise SystemExit(cli(__doc__, main))
