"""Filter degree systems by simultaneous conditions outside one star."""

import argparse
from functools import cache
from itertools import accumulate
from math import comb
from pathlib import Path
import json

from transport import scan


@cache
def row_states(size, profile, edges, cap_three):
    outside = edges - size
    lower, upper = [], []
    for degree in profile:
        lower.append(max(0, size + degree - (edges - 9)))
        bound = min(degree, size) - 1
        upper.append(min(1, bound) if cap_three and min(size, degree) <= 3 else bound)
    suffix = []
    tail_min = tail_max = 0
    for lo, hi in zip(lower[::-1], upper[::-1]):
        suffix.append((tail_min, tail_max))
        tail_min += lo
        tail_max += hi
    suffix.reverse()
    states = {}

    def extend(index, left, kept, incidence, intersection, crossing):
        if index == len(profile):
            largest = sorted(kept, reverse=True)
            if any(s > outside - limit for s, limit in zip(accumulate(largest), (9, 5, 3, 1))):
                return
            singles = kept.count(1)
            key = (singles, incidence, intersection)
            states[key] = max(states.get(key, -1), crossing)
            return
        tail_lo, tail_hi = suffix[index]
        lo = max(lower[index], left - tail_hi)
        hi = min(upper[index], left - tail_lo)
        if index and profile[index] == profile[index - 1]:
            hi = min(hi, profile[index - 1] - kept[-1])
        d = profile[index]
        for c in range(lo, hi + 1):
            remaining = d - c
            next_incidence = incidence + (c if remaining == 1 else 0)
            if next_incidence <= size:
                extend(index + 1, left - c, kept + (remaining,), next_incidence,
                       intersection + comb(remaining, 2), crossing + c * remaining)

    extend(0, size, (), 0, 0, 0)
    return tuple(states.items())


@cache
def star_possible(profile, other_parts, size, edges, cap_three):
    outside = edges - size
    same_side = list(profile)
    same_side.remove(size)
    if any(s > outside - limit for s, limit in zip(accumulate(same_side), (9, 5, 3, 1))):
        return False
    need_pairs = comb(outside, 2)
    need_cross = outside * size
    bounds = {(0, 0, sum(comb(x, 2) for x in same_side)): 0}
    options = [row_states(size, p, edges, cap_three) for p in other_parts]
    for rows in sorted(options, key=len):
        combined = {}
        for (ones, used, pairs), crosses in bounds.items():
            for (n_ones, n_used, n_pairs), n_cross in rows:
                if ones + n_ones > outside or used + n_used > size:
                    continue
                key = (ones + n_ones, used + n_used, min(need_pairs, pairs + n_pairs))
                value = min(need_cross, crosses + n_cross)
                combined[key] = max(combined.get(key, -1), value)
        bounds = combined
        if not bounds:
            return False
    return any(pairs >= need_pairs and value >= need_cross
               for (_, _, pairs), value in bounds.items())


def narrow(edges):
    _, _, systems = scan(edges)
    possible = []
    for system in systems:
        cap_three = edges - 2 * sum(p.count(2) for p in system) <= 1
        largest = max(p[0] for p in system)
        if all(star_possible(p, tuple(sorted(system[:i] + system[i + 1:])),
                             size, edges, cap_three)
               for i, p in enumerate(system) for size in set(p) if size == largest):
            possible.append(system)
    return possible


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edges", type=int)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    possible = narrow(arguments.edges)
    maxima = sorted({max(max(p) for p in system) for system in possible})
    print(f"joint_star_systems={len(possible)} maximum_degrees={maxima}")
    if arguments.output:
        arguments.output.write_text(json.dumps(possible, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
