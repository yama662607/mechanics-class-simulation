import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class QuartoWatcherHandler(FileSystemEventHandler):
    """When a partial `_*.qmd` is edited, touch the parent `textbook.qmd`
    in the same directory so Quarto preview re-renders the included content.
    Works with any directory layout — no hardcoded chapter names.
    """

    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve()
        self.last_triggered = 0.0
        self.debounce_seconds = 1.0
        self.default_target = self.project_root / "quarto" / "index.qmd"

    def on_modified(self, event):
        if event.is_directory:
            return

        if not event.src_path.endswith(".qmd"):
            return

        src_path = Path(event.src_path).resolve()
        target_file = self._determine_target(src_path)

        if target_file and src_path == target_file:
            return  # avoid feedback loop on the touched file itself

        current_time = time.time()
        if current_time - self.last_triggered > self.debounce_seconds:
            if target_file:
                print(f"Detected change in {src_path.name}. Touching {target_file.name}...")
                self.touch_target(target_file)
            else:
                print(f"Detected change in {src_path.name}, but no parent qmd found.")
            self.last_triggered = current_time

    def _determine_target(self, src_path):
        """Find the nearest non-partial qmd to touch.

        Strategy:
        1. If the changed file is a partial (`_*.qmd`), look for any sibling
           non-partial `*.qmd` in the same directory and touch the first one.
        2. Otherwise fall back to `quarto/index.qmd`.
        """
        try:
            if src_path.name.startswith("_"):
                for sibling in src_path.parent.glob("*.qmd"):
                    if not sibling.name.startswith("_"):
                        return sibling.resolve()
            if self.default_target.exists():
                return self.default_target
            return None
        except Exception:
            return None

    def touch_target(self, target_file):
        # mtime のみ更新 — 「空白追加→削除」より安全 (同時編集中のレースで
        # ファイルが破損しない、Win cp932 化けも回避できる)。
        max_retries = 3
        for i in range(max_retries):
            try:
                target_file.touch()
                print(f"Successfully touched {target_file.name}.")
                return
            except Exception as e:  # noqa: BLE001 — log everything, retry
                print(f"Attempt {i + 1} failed to touch {target_file.name}: {e}")
                time.sleep(0.5)
        print(f"Failed to touch {target_file.name} after {max_retries} retries.")


def main():
    # tools/utils/quarto_watcher.py から見て 3 段上 (utils → tools → project_root)
    project_root = Path(__file__).resolve().parent.parent.parent
    watch_path = project_root / "quarto"

    print("Starting Quarto Watcher...")
    print(f"Monitoring: {watch_path}")
    print("Mapping changes in chapter dirs to chapter.qmd files.")

    event_handler = QuartoWatcherHandler(project_root)
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
