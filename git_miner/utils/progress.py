from collections.abc import Iterable
from typing import Any

from tqdm import tqdm


def track_progress(
    iterable: Iterable[Any], description: str = "Processing", total: int | None = None
) -> Any:
    """Wrap an iterable with a progress bar.

    Args:
        iterable: Iterable to track
        description: Progress bar description
        total: Total number of items (optional)

    Returns:
        Iterable with progress bar
    """
    return tqdm(
        iterable,
        desc=description,
        total=total,
        unit="items",
        ncols=100,
    )
