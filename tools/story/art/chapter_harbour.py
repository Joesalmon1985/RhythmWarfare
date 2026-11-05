"""Build target `harbour` (the Mission Count): see chapter_squadron.py."""
from . import chapter_squadron


def build(only=()) -> int:
    return chapter_squadron.build_map("harbour", only)
