"""Independently replay the 13-edge residual and 22-edge exclusion."""

from functools import cache
from itertools import accumulate, combinations, combinations_with_replacement, product
from math import comb


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def score(profile):
    return sum(comb(size, 2) for size in profile)


def profiles(total, smallest, largest, length, caps):
    for count in range(length, total // smallest + 1):
        for increasing in combinations_with_replacement(range(smallest, largest + 1), count):
            if sum(increasing) == total:
                ordered = increasing[::-1]
                if all(a <= b for a, b in zip(accumulate(ordered), caps)):
                    yield ordered


def systems(options, need, count_small, small_cap, pair=None, fifth_cap=6):
    options = sorted(options, key=lambda p: (-score(p), p))
    scores = [score(p) for p in options]
    counts = [p.count(count_small) for p in options]

    def search(start, picked, used, support_five, points, collision):
        left = 6 - len(picked)
        if not left:
            yield tuple(options[i] for i in picked)
            return
        for j in range(start, len(options)):
            possible = points + scores[j] * left
            if 2 * (possible - need) < collision:
                break
            small = used + counts[j]
            fives = support_five + (len(options[j]) == 5)
            if small > small_cap or fives > fifth_cap:
                continue
            bounds = [pair(options[i], options[j], False) for i in picked] if pair else ()
            if any(b is None for b in bounds):
                continue
            penalty = collision + sum(bounds)
            if penalty <= 2 * (possible - need):
                yield from search(j, picked + (j,), small, fives, points + scores[j], penalty)

    yield from search(0, (), 0, 0, 0, 0)


@cache
def row(size, margins, limit_three, union):
    bounds = []
    for column in margins:
        low = max(0, size + column - union)
        high = min(size, column) - 1
        if limit_three:
            high = min(high, 1) if min(size, column) <= 3 else high
        bounds.append(range(low, high + 1))
    return min((score(cells) for cells in product(*bounds) if sum(cells) == size), default=None)


@cache
def pair_lower(a, b, limit_three, union=13):
    row_minima = [row(x, b, limit_three, union) for x in a]
    col_minima = [row(y, a, limit_three, union) for y in b]
    if any(v is None for v in row_minima + col_minima):
        return None
    return max(sum(row_minima), sum(col_minima))


def main():
    residual = list(profiles(13, 1, 4, 5, (4, 8, 10, 12)))
    require(len(residual) == 35, "Wrong number of residual degree profiles")
    require(not list(systems(residual, 78, 1, 13, fifth_cap=1)), "A 13-edge system survived")
    print("13-edge residual: 35 profiles, zero systems")

    for edges in range(13, 22):
        caps = tuple(edges - minimum for minimum in (14, 9, 5, 3, 1))
        original = list(profiles(edges, 2, edges - 14, 6, caps))
        def lower(a, b, strict):
            return pair_lower(a, b, strict, edges - 9)
        require(not list(systems(original, comb(edges, 2), 2, edges // 2, lower)),
                f"A system with {edges} edges survived")
    print("13 through 21 edges: zero systems")

    original = list(profiles(22, 2, 8, 6, (8, 13, 17, 19, 21)))
    require(len(original) == 64, "Wrong number of original degree profiles")
    candidates = list(systems(original, 231, 2, 11, pair_lower))
    require(len(candidates) == 5, "Expected five systems before the degree-three cut")
    coordinates = tuple(combinations(range(6), 2))
    remaining = []
    for system in candidates:
        require(sum(p.count(2) for p in system) == 11, "A row lacks a degree-two incidence")
        redundancy = sum(map(score, system)) - 231
        lower = {ij: pair_lower(system[ij[0]], system[ij[1]], True) for ij in coordinates}
        if any(v is None for v in lower.values()) or sum(lower.values()) > 2 * redundancy:
            continue
        slack = 2 * redundancy - sum(lower.values())
        side = tuple(sum(value for ij, value in lower.items() if i in ij) for i in range(6))
        remaining.append((redundancy, slack, side))
        if slack <= 1 and redundancy % 3 == 0:
            # Any term with multiplicity two or three would use one unit of
            # slack and leave a nonzero remainder in R modulo three.
            require(any(all(candidate % 3 for candidate in range(s, s + slack + 1)) for s in side),
                    f"All side congruences pass for {system}")
        else:
            require(slack == 0 and redundancy % 3 != 0, f"Unresolved system {system}")
        print(f"22-edge residual system: R={redundancy} slack={slack} side={side} excluded")
    require(len(remaining) == 3, "Expected three systems before the congruence")
    print("22 edges excluded: 64 profiles, five systems, three after the degree-three cut")


if __name__ == "__main__":
    main()
