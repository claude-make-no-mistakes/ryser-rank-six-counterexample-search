# Rank-six intersecting Ryser

Every finite intersecting six-partite, six-uniform hypergraph with cover number six has at least **24 edges**. The preceding public computation gave a lower bound of 22. The proof excludes 22 edges using bounds on deleting vertex stars and a congruence for repeated intersections. For 23 edges, transportation and degree constraints leave three overlap systems, each excluded by an exact integer certificate. [Paper](paper.pdf) · [Proof source](paper.tex) · [Replay record](REPLAY.txt)

The lower bound also excludes a construction based on merging whole parallel line traces and splitting the other traces in the affine plane of order five.

The rank-six conjecture remains open. The earlier SAT scout for 23 edges is preserved in the replay record. The proof of that case uses the overlap certificates.

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

## Counterexample search

```sh
python frontier.py 24 --output frontier-24.json
python sat_search.py frontier-24.json 0 --conflicts 35000 --rounds 8 --output witness.json
python witness.py witness.json
```

The SAT script requires `python-sat==1.9.dev25` with CaDiCaL 1.9.5. Its inputs are a list of degree systems and a zero-based index. It searches for distinct intersecting rows and rules out any cover of size at most five that it finds. The witness script independently checks the rows and searches for an exact cover of size at most five. One edge always gives a cover of size six. The SAT script creates a witness file only when the exact check passes.
