"""Search for a verified witness with one fixed six-side degree system."""

import argparse
from itertools import combinations
import json
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

from witness import cover, validate_rows


def run(profile, conflicts, rounds, strengthened=False):
    edge_count = sum(profile[0])
    if len(profile) != 6 or any(sum(side) != edge_count for side in profile):
        raise ValueError("The six profiles must have equal sums")
    pool = IDPool()

    def label(side, row, value):
        return pool.id(("label", side, row, value))

    with Solver(name="cadical195") as solver:
        def cardinality(variables, count, exact=True):
            encode = CardEnc.equals if exact else CardEnc.atmost
            clauses = encode(lits=variables, bound=count, vpool=pool, encoding=EncType.seqcounter)
            solver.append_formula(clauses.clauses)

        for side, degrees in enumerate(profile):
            for row in range(edge_count):
                cardinality([label(side, row, v) for v in range(len(degrees))], 1)
            for value, degree in enumerate(degrees):
                cardinality([label(side, row, value) for row in range(edge_count)], degree)
                if side and value and degrees[value - 1] == degree:
                    for row in range(edge_count):
                        solver.add_clause([-label(side, row, value)] +
                                          [label(side, u, value - 1) for u in range(row)])

        # Row permutations put the first side into fixed consecutive groups.
        # Equal-degree labels in other sides can then use first occurrence.
        start = 0
        for value, degree in enumerate(profile[0]):
            for row in range(start, start + degree):
                solver.add_clause([label(0, row, value)])
            start += degree

        for row in range(edge_count):
            small = [label(side, row, v) for side, degrees in enumerate(profile)
                     for v, degree in enumerate(degrees) if degree == 2]
            if len(small) > 1:
                cardinality(small, 1, False)

        private = [[[] for _ in range(6)] for _ in range(edge_count)]
        for i, j in combinations(range(edge_count), 2):
            both = [pool.id(("equal", i, j, side)) for side in range(6)]
            solver.add_clause(both)
            cardinality(both, 4, False)
            for side, degrees in enumerate(profile):
                same = both[side]
                for value in range(len(degrees)):
                    first, second = label(side, i, value), label(side, j, value)
                    solver.add_clause([-first, -second, same])
                    solver.add_clause([-same, -first, second])
                token = pool.id(("private", i, j, side))
                private[i][side].append(token)
                private[j][side].append(token)
                for other, equal in enumerate(both):
                    solver.add_clause([-token, equal if other == side else -equal])
        for side_list in private:
            for choices in side_list:
                solver.add_clause(choices)

        if strengthened:
            for row in range(edge_count):
                for side, choices in enumerate(private[row]):
                    small_elsewhere = [label(j, row, v) for j, degrees in enumerate(profile)
                                       if j != side for v, d in enumerate(degrees) if d == 2]
                    if small_elsewhere:
                        guard = pool.id(("two_private", row, side))
                        for small in small_elsewhere:
                            solver.add_clause([-small, guard])
                        encoding = CardEnc.atleast(lits=choices, bound=2, vpool=pool,
                                                   encoding=EncType.seqcounter)
                        for clause in encoding.clauses:
                            solver.add_clause([-guard, *clause])
            for i, j in combinations(range(6), 2):
                for v, di in enumerate(profile[i]):
                    for w, dj in enumerate(profile[j]):
                        minimum = di + dj - (edge_count - 9)
                        if minimum <= 0:
                            continue
                        joint = [pool.id(("joint", i, v, j, w, row)) for row in range(edge_count)]
                        for row, token in enumerate(joint):
                            solver.add_clause([-token, label(i, row, v)])
                            solver.add_clause([-token, label(j, row, w)])
                        encoding = CardEnc.atleast(lits=joint, bound=minimum, vpool=pool,
                                                   encoding=EncType.seqcounter)
                        solver.append_formula(encoding.clauses)

        for step in range(rounds):
            solver.conf_budget(conflicts)
            solved = solver.solve_limited()
            if solved is None:
                return "conflict limit", step, None
            if solved is False:
                return "unsatisfiable (solver report)", step, None
            model = {x for x in solver.get_model() if x > 0}
            rows = [[next(v for v in range(len(degrees)) if label(side, row, v) in model)
                     for side, degrees in enumerate(profile)] for row in range(edge_count)]
            small_cover = cover(validate_rows(rows))
            if small_cover is None:
                return "verified counterexample", step, rows
            omitted = [pool.id(("omitted", step, row)) for row in range(edge_count)]
            solver.add_clause(omitted)
            for row in range(edge_count):
                for side, value in small_cover:
                    solver.add_clause([-omitted[row], -label(side, row, value)])
        return "round limit", rounds, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profiles", type=Path)
    parser.add_argument("index", type=int)
    parser.add_argument("--conflicts", type=int, default=20_000)
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--strengthened", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    systems = json.loads(args.profiles.read_text(encoding="utf-8"))
    profile = systems[args.index]
    outcome, excluded_covers, rows = run(profile, args.conflicts, args.rounds, args.strengthened)
    print(f"profile={args.index} outcome={outcome} excluded_covers={excluded_covers}")
    if rows is not None:
        payload = json.dumps(rows, indent=2) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")


if __name__ == "__main__":
    main()
