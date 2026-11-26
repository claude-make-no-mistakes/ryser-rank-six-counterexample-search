"""Check the 13-edge residual used in the maximum-degree bound."""

from itertools import combinations_with_replacement, accumulate
from math import comb


def residual_profiles():
    """Positive degree profiles of the 13-edge residual."""
    for length in range(5, 14):
        for degrees in combinations_with_replacement(range(1, 6), length):
            if sum(degrees) != 13:
                continue
            profile = degrees[::-1]
            if any(total > limit for total, limit in zip(accumulate(profile), (5, 8, 10, 12))):
                continue
            if profile[0] == 5 and profile[1] != 3:
                continue
            yield profile


def check_residual():
    profiles = sorted(residual_profiles(), key=lambda p: -sum(comb(d, 2) for d in p))
    candidates = []
    for system in combinations_with_replacement(profiles, 6):
        score = sum(comb(d, 2) for p in system for d in p)
        if score < 78 or sum(p.count(1) for p in system) > 13 or sum(len(p) == 5 for p in system) > 1:
            continue
        large = sum(p[0] == 5 for p in system)
        lower = comb(large, 2)
        upper = 5 * (score - 78) // 2
        if lower <= upper:
            raise ValueError(f"Unresolved 13-edge residual {system}")
        candidates.append((system, score, lower, upper))
    return len(profiles), candidates


if __name__ == "__main__":
    total, candidates = check_residual()
    print(f"13-edge residual profiles={total} candidates={len(candidates)}")
    for system, score, lower, upper in candidates:
        print(system, f"score={score} lower={lower} upper={upper}")
    print("13-edge residual excluded")
