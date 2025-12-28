

class ProgressTracker:
    """Simple progress tracker for terminal output."""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self._update_interval = max(1, total // 20)
        self._last_update = 0

    def update(self, increment: int = 1):
        """Update progress."""
        self.current += increment
        if self.current - self._last_update >= self._update_interval:
            self._display()
            self._last_update = self.current

    def _display(self):
        """Display progress."""
        percentage = (self.current / self.total) * 100 if self.total > 0 else 100
        print(
            f"\r{self.description}: {self.current}/{self.total} ({percentage:.1f}%)",
            end="",
            flush=True,
        )

    def complete(self):
        """Mark progress as complete."""
        self.current = self.total
        print(f"\r{self.description}: {self.current}/{self.total} (100.0%)", flush=True)


def track_progress(total: int, description: str = "Processing") -> ProgressTracker:
    """Create a progress tracker.

    Args:
        total: Total number of items to process
        description: Description of the operation

    Returns:
        ProgressTracker instance
    """
    return ProgressTracker(total, description)
