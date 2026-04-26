import subprocess
import sys
import time
from pathlib import Path

from utils.find_quarto import find_quarto


def run_dev_server():
    project_root = Path(__file__).parent.parent.resolve()

    # Quarto バイナリの検出
    quarto_bin = find_quarto()
    if quarto_bin is None:
        print(
            " Quarto が見つかりません。インストールしてください: https://quarto.org/docs/get-started/"
        )
        sys.exit(1)

    # コマンドの定義
    watcher_cmd = [
        sys.executable,
        str(project_root / "tools" / "utils" / "quarto_watcher.py"),
    ]
    quarto_cmd = [quarto_bin, "preview", "quarto", "--port", "4312", "--render", "html"]

    print(" Starting dev server (Watcher + Quarto Preview)...")

    processes = []
    try:
        # ウォッチャーの起動
        watcher_proc = subprocess.Popen(
            watcher_cmd, stdout=sys.stdout, stderr=sys.stderr, cwd=str(project_root)
        )
        processes.append(watcher_proc)

        # Quartoの起動
        quarto_proc = subprocess.Popen(
            quarto_cmd, stdout=sys.stdout, stderr=sys.stderr, cwd=str(project_root)
        )
        processes.append(quarto_proc)

        # 両方のプロセスを監視
        while True:
            if watcher_proc.poll() is not None:
                print("Watcher process terminated.")
                break
            if quarto_proc.poll() is not None:
                print("Quarto process terminated.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n Shutting down...")
    finally:
        for proc in processes:
            if proc.poll() is None:
                # WindowsとUnixでシグナルの扱いが異なる場合があるが、
                # terminate() は一般的に安全
                proc.terminate()

        # プロセスの終了を待機
        for proc in processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print(" Dev server stopped.")


if __name__ == "__main__":
    run_dev_server()
