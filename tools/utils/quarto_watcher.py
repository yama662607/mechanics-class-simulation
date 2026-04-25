import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class QuartoWatcherHandler(FileSystemEventHandler):
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.last_triggered = 0.0
        self.debounce_seconds = 1.0
        self.default_target = self.project_root / "quarto" / "theory" / "textbook.qmd"

    def on_modified(self, event) -> None:
        if event.is_directory or not event.src_path.endswith(".qmd"):
            return

        src_path = Path(event.src_path).resolve()
        target_file = self._determine_target(src_path)
        if not target_file or src_path == target_file:
            return

        current_time = time.time()
        if current_time - self.last_triggered <= self.debounce_seconds:
            return

        print(f"Detected change in {src_path.name}. Touching {target_file.name}.")
        self.touch_target(target_file)
        self.last_triggered = current_time

    def _determine_target(self, src_path: Path) -> Path | None:
        if "topics" in src_path.parts and self.default_target.exists():
            return self.default_target

        index = self.project_root / "quarto" / "index.qmd"
        if index.exists():
            return index

        return None

    @staticmethod
    def touch_target(target_file: Path) -> None:
        target_file.touch()


def main() -> None:
    project_root = Path(__file__).parents[2].resolve()
    watch_path = project_root / "quarto"
    print(f"Starting Quarto watcher on {watch_path}")

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
