# Rank-six intersecting Ryser

Every finite intersecting six-partite, six-uniform hypergraph with cover number six has at least **24 edges**. The preceding public computation gave a lower bound of 22. The proof excludes 22 edges using bounds on deleting vertex stars and a congruence for repeated intersections. For 23 edges, transportation and degree constraints leave three overlap systems, each excluded by an exact integer certificate. [Paper](paper.pdf) · [Proof source](paper.tex) · [Replay record](REPLAY.txt)

At 24 edges, every vertex of a counterexample has degree at most nine. Deleting any active vertex star from a counterexample leaves a pair of edges meeting at least twice. The paper also proves two construction exclusions.

- An order-six automorphism cycling the six parts forces a five-cover when there are at most 43 edges or at most ten active vertices per part.
- Every intersecting extension of at least twelve unchanged affine-plane rows has a five-cover. The lower bound also excludes a construction based on merging whole parallel line traces and splitting the other traces.

The rank-six conjecture remains open. The SAT scouts and their finite conflict limits are recorded separately from the completed exclusions.

## Proof replay

The 22-edge replay uses Python 3.10 or later and the standard library.

```sh
python replay.py
python transport.py 22
```

The first command computes lower bounds on repeated intersections by enumerating bounded integer tuples. The second independently computes minimum transportation collision costs using integer flow. Both close the 22-edge case. The residual check also has an alternative derivation in `residual.py`. The mathematical inputs are the 13-edge minimum for cover number five and the eight-edge structure for cover number four. [Aharoni, Barát, and Wanless, Theorem 2.7](https://arxiv.org/html/1409.4833v2#S2) · [Abu-Khazneh and Pokrovskiy, Lemma 2.1](https://arxiv.org/pdf/1409.4938#page=5) · [Previous 22-edge bound](https://github.com/HRK44/ryser-conjecture-22)

The 23-edge replay uses Node and Python with NumPy and SciPy. It ran with Node 22.17.0, Python 3.12.14, NumPy 2.5.3, and SciPy 1.18.1. The independent review also replayed it with SciPy 1.14.0. SciPy proposes transportation duals, and the replay checks each relevant inequality in rational arithmetic before it uses the integer lower bound. The remaining certificates use integer arithmetic. The wrapper builds intermediate files in a temporary directory.

```sh
python edge23/replay.py
```

The degree-ten exclusion and the two construction checks replay as follows. The C++ search requires a C++20 compiler. The rotation run allows all one million words over ten labels per part, including families using fewer labels.

```sh
python edge24/residual.py
node edge24/affine-core.js 12
g++ -O3 -std=c++20 edge24/cyclic.cpp -o cyclic
./cyclic
```

## Counterexample search

```sh
python frontier.py 24 --output frontier-24.json
python sat_search.py frontier-24.json 0 --conflicts 35000 --rounds 8 --output witness.json
python witness.py witness.json
```

The SAT script requires `python-sat==1.9.dev25` with CaDiCaL 1.9.5. Its inputs are a list of degree systems and a zero-based index. It searches for distinct intersecting rows and rules out any cover of size at most five that it finds. The witness script independently checks the rows and searches for an exact cover of size at most five. One edge always gives a cover of size six. The SAT script creates a witness file only when the exact check passes.

Run `node edge24/frontier.js` for the 24-edge necessary-profile enumeration. It leaves 265,367 degree systems after using the degree cap, pair transportation, and the disjoint degree-two pairs. These systems can still be tested against geometric and incidence constraints. The optional `--stars` flag runs further residual profile filters. For the bounded SAT scout, use the ten inputs in `edge24/seed-profiles.json` with `--critical-24 --strengthened`; the replay record gives the exact limits. The critical mode adds the five-cover conditions for deleting one edge, since 24 would be the minimum possible size of a counterexample.
