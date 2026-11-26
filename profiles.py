"""Necessary degree and collision constraints for six-partite counterexamples."""

import argparse
from functools import cache
import heapq
from itertools import accumulate
from math import comb
from pathlib import Path
import json

RANK = 6
# Minimum residual edge counts after deleting this many stars.
# The first two entries use the thirteen-edge check and the eight-edge structure.
RESIDUAL = (14, 9, 5, 3, 1)
CROSS_RESIDUAL = 9


def partitions(total, upper, prefix=()):
    if total == 0:
        if len(prefix) >= RANK:
            yield prefix
        return
    for part in range(min(upper, total), 1, -1):
        if total - part != 1:
            yield from partitions(total - part, part, (*prefix, part))


def side_profiles(edges):
    for profile in partitions(edges, edges - RESIDUAL[0]):
        if all(size <= edges - RESIDUAL[k] for k, size in enumerate(accumulate(profile[:5]))):
            yield profile


def row_bound(size, margins, union_cap):
    """Minimize twice the collision count for this row alone."""
    lower = [max(0, size + other - union_cap) for other in margins]
    # Each star must supply a pair meeting only at its center.
    upper = [min(size, other) - 1 for other in margins]
    if any(lo > hi for lo, hi in zip(lower, upper)):
        return None
    if sum(lower) > size or sum(upper) < size:
        return None
    score = sum(x * (x - 1) for x in lower)
    heap = [(lo, hi, i) for i, (lo, hi) in enumerate(zip(lower, upper)) if lo < hi]
    heapq.heapify(heap)
    for _ in range(size - sum(lower)):
        lo, hi, i = heapq.heappop(heap)
        score += 2 * lo
        if lo + 1 < hi:
            heapq.heappush(heap, (lo + 1, hi, i))
    return score


def pair_bound(a, b, edges):
    union_cap = edges - CROSS_RESIDUAL
    from_a = [row_bound(x, b, union_cap) for x in a]
    from_b = [row_bound(y, a, union_cap) for y in b]
    bounds = from_a + from_b
    if None in bounds:
        return None
    return max(sum(from_a), sum(from_b))


@cache
def star_bounds(size, margins, edges):
    """Independent extrema over all admissible intersections of one star."""
    lower = [max(0, size + other - (edges - CROSS_RESIDUAL)) for other in margins]
    upper = [min(size, other) - 1 for other in margins]
    suffix_min = [0] * (len(margins) + 1)
    suffix_max = suffix_min.copy()
    for k in range(len(margins) - 1, -1, -1):
        if lower[k] > upper[k]:
            return None
        suffix_min[k] = suffix_min[k + 1] + lower[k]
        suffix_max[k] = suffix_max[k + 1] + upper[k]

    occupied = edges - size
    least_collision = float("inf")
    most_crossing = -1
    most_residual = -1
    across = []

    def rec(index, remaining, collision, crossing, outside):
        nonlocal least_collision, most_crossing, most_residual
        if index == len(margins):
            degrees = sorted(across, reverse=True)
            if any(total > occupied - bound
                   for total, bound in zip(accumulate(degrees[:4]), (CROSS_RESIDUAL, 5, 3, 1))):
                return
            least_collision = min(least_collision, collision)
            most_crossing = max(most_crossing, crossing)
            most_residual = max(most_residual, outside)
            return
        largest = upper[index]
        if index and margins[index] == margins[index - 1]:
            largest = min(largest, margins[index - 1] - across[-1])
        least = max(lower[index], remaining - suffix_max[index + 1])
        largest = min(largest, remaining - suffix_min[index + 1])
        for shared in range(least, largest + 1):
            rest = margins[index] - shared
            across.append(rest)
            rec(index + 1, remaining - shared, collision + 2 * comb(shared, 2),
                crossing + shared * rest, outside + comb(rest, 2))
            across.pop()

    rec(0, size, 0, 0, 0)
    if most_crossing < 0:
        return None
    return least_collision, most_crossing, most_residual


def passes_star_bounds(system, edges):
    ready = {}
    for i, profile in enumerate(system):
        other_profiles = [p for j, p in enumerate(system) if j != i]
        for size in set(profile):
            ranges = [star_bounds(size, p, edges) for p in other_profiles]
            if None in ranges:
                return False
            remaining = edges - size
            if sum(x[1] for x in ranges) < size * remaining:
                return False
            remaining_pairs = sum(comb(x, 2) for x in profile) - comb(size, 2)
            if remaining_pairs + sum(x[2] for x in ranges) < comb(remaining, 2):
                return False
        for j, other in enumerate(other_profiles):
            ready[i, j + (j >= i)] = sum(star_bounds(size, other, edges)[0] for size in profile)
    collision = sum(max(ready[i, j], ready[j, i]) for i in range(RANK) for j in range(i + 1, RANK))
    redundancy = sum(comb(x, 2) for p in system for x in p) - comb(edges, 2)
    return collision <= 4 * redundancy


def survivors(edges):
    profiles = sorted(side_profiles(edges), key=lambda p: -sum(comb(x, 2) for x in p))
    score = [sum(comb(x, 2) for x in p) for p in profiles]
    twos = [p.count(2) for p in profiles]
    size = len(profiles)
    required = comb(edges, 2)
    pair = [[pair_bound(a, b, edges) for b in profiles] for a in profiles]
    kept = []

    def search(start, chosen, used_twos, score_sum, collision):
        remaining = RANK - len(chosen)
        if remaining == 0:
            kept.append(tuple(profiles[i] for i in chosen))
            return
        for i in range(start, size):
            best_redundancy = score_sum + remaining * score[i] - required
            if best_redundancy < 0 or collision > 4 * best_redundancy:
                break
            count = used_twos + twos[i]
            if count > edges // 2:
                continue
            added = [pair[i][j] for j in chosen]
            if None in added:
                continue
            total_collision = collision + sum(added)
            if total_collision <= 4 * best_redundancy:
                search(i, (*chosen, i), count, score_sum + score[i], total_collision)

    search(0, (), 0, 0, 0)
    return profiles, kept, [system for system in kept if passes_star_bounds(system, edges)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edges", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    profiles, first, kept = survivors(args.edges)
    print(f"edges={args.edges} side_profiles={len(profiles)} pair_systems={len(first)} star_systems={len(kept)}")
    if args.output:
        args.output.write_text(json.dumps(kept, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
