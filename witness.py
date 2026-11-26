"""Verify a rank-six witness as a JSON array of six-integer rows."""

import argparse
from functools import cache
from itertools import combinations
import json
from pathlib import Path


def validate_rows(data):
    if not isinstance(data, list) or not data:
        raise ValueError("Expected a nonempty JSON array")
    if any(not isinstance(row, list) or len(row) != 6
           or any(type(x) is not int for x in row) for row in data):
        raise ValueError("Each row must contain six integers")
    rows = [tuple(row) for row in data]
    if len(set(rows)) != len(rows):
        raise ValueError("Duplicate rows")
    for (i, a), (j, b) in combinations(enumerate(rows), 2):
        if all(x != y for x, y in zip(a, b)):
            raise ValueError(f"Rows {i + 1} and {j + 1} are disjoint")
    return rows


def cover(rows, budget=5):
    """Return coordinate-value pairs covering all rows, if one exists."""
    stars = {}
    for i, row in enumerate(rows):
        for vertex in enumerate(row):
            stars[vertex] = stars.get(vertex, 0) | (1 << i)

    @cache
    def extend(uncovered, remaining):
        if not uncovered:
            return ()
        if remaining == 0:
            return None
        candidates = [(star & uncovered).bit_count() for star in stars.values()]
        if max(candidates) * remaining < uncovered.bit_count():
            return None
        i = (uncovered & -uncovered).bit_length() - 1
        choices = list(enumerate(rows[i]))
        choices.sort(key=lambda v: (stars[v] & uncovered).bit_count(), reverse=True)
        for vertex in choices:
            tail = extend(uncovered & ~stars[vertex], remaining - 1)
            if tail is not None:
                return (vertex, *tail)
        return None

    return extend((1 << len(rows)) - 1, budget)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rows", type=Path)
    arguments = parser.parse_args()
    rows = validate_rows(json.loads(arguments.rows.read_text(encoding="utf-8")))
    found = cover(rows)
    if found is not None:
        print(f"Five-or-fewer cover: {found}")
        return 1
    print(f"Rank-six intersecting Ryser counterexample with {len(rows)} edges and cover number six")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
