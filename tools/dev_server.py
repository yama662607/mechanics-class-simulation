import subprocess
import sys
import time
from pathlib import Path

from utils.find_quarto import find_quarto


def run_dev_server() -> None:
    project_root = Path(__file__).parent.parent.resolve()
    quarto_bin = find_quarto()
    if quarto_bin is None:
        print(
            "Quarto was not found. Install it from https://quarto.org/docs/get-started/"
        )
        sys.exit(1)

    watcher_cmd = [
        sys.executable,
        str(project_root / "tools" / "utils" / "quarto_watcher.py"),
    ]
    quarto_cmd = [quarto_bin, "preview", "quarto", "--port", "4312", "--render", "html"]

    processes = []
    try:
        watcher_proc = subprocess.Popen(
            watcher_cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=str(project_root),
        )
        processes.append(watcher_proc)

        quarto_proc = subprocess.Popen(
            quarto_cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=str(project_root),
        )
        processes.append(quarto_proc)

        while True:
            if watcher_proc.poll() is not None:
                print("Watcher process terminated.")
                break
            if quarto_proc.poll() is not None:
                print("Quarto process terminated.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping dev server...")
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.terminate()
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    run_dev_server()
