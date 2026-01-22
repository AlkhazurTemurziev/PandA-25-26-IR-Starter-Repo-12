#!/usr/bin/env python3
"""
Part 12 starter.

WHAT'S NEW IN PART 12
Added normalization and stemming to the search!
"""
from typing import List
import time

from .constants import BANNER, HELP
from .models import SearchResult, Searcher

from .file_utilities import load_config, load_sonnets, settings


def print_results(
    query: str | None,
    results: List[SearchResult],
    highlight_mode: str,
    query_time_ms: float | None = None,
) -> None:
    total_docs = len(results)
    matched = [r for r in results if r.matches > 0]

    line = f'{len(matched)} out of {total_docs} sonnets contain "{query}".'
    if query_time_ms is not None:
        line += f" Your query took {query_time_ms:.2f}ms."
    print(line)

    for idx, r in enumerate(matched, start=1):
        r.print(idx, highlight_mode, total_docs)


# ---------- CLI loop ----------

def main() -> None:
    print(BANNER)
    config = load_config()

    # Load sonnets (from cache or API)
    start = time.perf_counter()
    sonnets = load_sonnets()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"Loading sonnets took: {elapsed:.3f} [ms]")

    print(f"Loaded {len(sonnets)} sonnets.")

    # Initialize our Searcher and with it, the index
    searcher = Searcher(sonnets)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue

        # Check for commands
        if raw.startswith(":"):
            if raw == ":quit":
                print("Bye.")
                break

            if raw == ":help":
                print(HELP)
                continue

            handled = False

            for setting in settings:
                handled |= setting.handle(raw, config)

            if not handled:
                print("Unknown command. Type :help for commands.")

            continue

        # ---------- Query evaluation ----------
        words = raw.split()
        if not words:
            continue

        start = time.perf_counter()

        results = searcher.search(raw, config.search_mode)

        elapsed_ms = (time.perf_counter() - start) * 1000

        highlight_mode = config.hl_mode if config.highlight else None

        print_results(raw, results, highlight_mode, elapsed_ms)


if __name__ == "__main__":
    main()