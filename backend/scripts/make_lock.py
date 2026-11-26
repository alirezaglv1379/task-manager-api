"""Create a full dependency snapshot from the active clean virtual environment."""
from pathlib import Path
import subprocess
import sys


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    output = backend_dir / "requirements.lock"
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze", "--local"],
        check=True,
        capture_output=True,
        text=True,
    )
    output.write_text(result.stdout, encoding="utf-8")
    print(f"Wrote {output}. Generate this only inside a clean project virtual environment.")


if __name__ == "__main__":
    main()
