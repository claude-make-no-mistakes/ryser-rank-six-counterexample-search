"""Independently replay the 14-edge residual obstruction to degree ten."""

from itertools import combinations_with_replacement
from math import comb


def profiles(minimum_length, minimum_degree):
    for length in range(minimum_length, 15):
        for entries in combinations_with_replacement(range(minimum_degree, 6), length):
            if sum(entries) == 14:
                decreasing = entries[::-1]
                if all(sum(decreasing[:i]) <= bound
                       for i, bound in enumerate((5, 9, 11, 13), 1)):
                    yield decreasing


def score(profile):
    return sum(comb(degree, 2) for degree in profile)


def check():
    own = [(score(p), p.count(5)) for p in profiles(5, 2)]
    opposite = [(score(p), p.count(5), p.count(1)) for p in profiles(6, 1)]
    maxima = {}
    initial = 0
    for system in combinations_with_replacement(opposite, 5):
        if sum(ones for _, _, ones in system) > 10:
            continue
        subtotal = sum(pairs for pairs, _, _ in system)
        subtotals = sum(fives for _, fives, _ in system)
        for own_pairs, own_fives in own:
            total = subtotal + own_pairs
            five = subtotals + own_fives
            maxima[five] = max(maxima.get(five, 0), total)
            if total >= 91:
                initial += 1
                if comb(five, 2) - five * five // 4 <= 2 * (total - 91):
                    raise ValueError("A fourteen-edge residual profile survived")
    expected = [85, 86, 88, 89, 91, 92, 93]
    if initial != 26 or [maxima[five] for five in range(7)] != expected:
        raise ValueError("Unexpected profile totals")
    print("Fourteen-edge residual maximum scores by degree-five count:", expected)
    print("26 systems reached the pair score of 91. All violate the collision bound.")


if __name__ == "__main__":
    check()
