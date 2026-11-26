"use strict";

// For k>=14 a retained core cannot be met by fewer than four old labels,
// and for k>=10 it cannot be met by fewer than three.
// Record every retained point set, marking which directions an added row
// could introduce a new label in. A new label in each direction is necessary.
const k = Number(process.argv[2] || 12);
if (!Number.isInteger(k) || k < 10 || k > 19) throw new Error("select k=10..19");
const maxNew = k >= 14 ? 2 : 3;
const width = 25;
const full = (1 << width) - 1;
const directionMask = 63;
const possible = new Uint8Array(1 << width);
const line = Array.from({length: 6}, () => Array(5).fill(0));
for (let p = 0; p < width; p++) {
    const x = p % 5;
    const y = Math.floor(p / 5);
    for (let g = 0; g < 6; g++) {
        const offset = g === 5 ? x : (y - g * x + 20) % 5;
        line[g][offset] |= 1 << p;
    }
}

function bits(mask) {
    const result = [];
    while (mask) {
        const bit = mask & -mask;
        result.push(bit);
        mask ^= bit;
    }
    return result;
}

const tupleAreas = {"3": {}, "4": {}, "5": {}};
for (let omitted = 1; omitted < 63; omitted++) {
    const missing = bits(omitted).length;
    if (missing > maxNew) continue;
    const directions = bits(directionMask ^ omitted).map(x => 31 - Math.clz32(x));
    const candidates = new Set();
    function rainbow(j, union) {
        if (j === directions.length) {
            const size = bits(union).length;
            if (size < k) return;
            const areas = tupleAreas[directions.length];
            areas[size] = (areas[size] || 0) + 1;
            candidates.add(union);
            return;
        }
        for (const block of line[directions[j]]) rainbow(j + 1, union | block);
    }
    rainbow(0, 0);
    for (const union of candidates) {
        const points = bits(union);
        function core(first, drop, remaining) {
            if (drop === 0) {
                possible[remaining] |= omitted;
                return;
            }
            for (let i = first; i + drop <= points.length; i++) {
                core(i + 1, drop - 1, remaining ^ points[i]);
            }
        }
        core(0, points.length - k, union);
    }
}

const directionCounts = Array(7).fill(0);
const exampleDeletions = [];
for (let p = 0; p < possible.length; p++) {
    if (!possible[p]) continue;
    const count = bits(possible[p]).length;
    directionCounts[count]++;
    if (count === 6 && exampleDeletions.length < 3) {
        exampleDeletions.push(bits(p ^ full).map(x => 31 - Math.clz32(x)));
    }
}
console.log(JSON.stringify({k, tupleAreas, directionCounts, exampleDeletions}));

if (directionCounts[6] === 0) process.exit(0);
const maps = [];
for (let a = 0; a < 5; a++) for (let b = 0; b < 5; b++) {
    for (let c = 0; c < 5; c++) for (let d = 0; d < 5; d++) {
        if ((a * d - b * c) % 5 === 0) continue;
        for (let e = 0; e < 5; e++) for (let f = 0; f < 5; f++) {
            maps.push(Array.from({length: 25}, (_, p) => {
                const x = p % 5;
                const y = Math.floor(p / 5);
                const toX = (a * x + b * y + e) % 5;
                const toY = (c * x + d * y + f) % 5;
                return 1 << (toX + 5 * toY);
            }));
        }
    }
}
const coreOrbits = [];
for (let p = 0; p < possible.length; p++) {
    if (possible[p] !== 63) continue;
    const indices = bits(p).map(x => 31 - Math.clz32(x));
    let orbitSize = 0;
    for (const map of maps) {
        const image = indices.reduce((mask, i) => mask | map[i], 0);
        if (possible[image] === 63) {
            orbitSize++;
            possible[image] = 0;
        }
    }
    const oneNew = Array(6).fill(0);
    const twoNew = Array(6).fill(0);
    for (let omitted = 1; omitted < 63; omitted++) {
        const missing = bits(omitted).length;
        if (missing > maxNew) continue;
        const directions = bits(directionMask ^ omitted).map(x => 31 - Math.clz32(x));
        const introduced = bits(omitted).map(x => 31 - Math.clz32(x));
        function count(j, union) {
            if (j === directions.length) {
                if ((p & union) === p) {
                    const counts = missing === 1 ? oneNew : twoNew;
                    for (const i of introduced) counts[i]++;
                }
                return;
            }
            for (const block of line[directions[j]]) count(j + 1, union | block);
        }
        count(0, 0);
    }
    const degreeOneForced = oneNew.some((n, i) => n < 2 && twoNew[i] === 0);
    const deleted = bits(p ^ full).map(x => 31 - Math.clz32(x));
    const record = {orbitSize, deleted, oneNew, twoNew, degreeOneForced};
    if (!degreeOneForced) Object.assign(record, extensionCover(p, oneNew, twoNew));
    coreOrbits.push(record);
}

function extensionCover(core, oneNew, twoNew) {
    const types = [];
    const choices = [];
    function walk(g, union, missing, old) {
        if (g === 6) {
            if ((core & union) === core) types.push({values: choices.slice(), missing, old});
            return;
        }
        for (let label = 0; label < 6; label++) {
            choices[g] = label;
            walk(g + 1, union | (label < 5 ? line[g][label] : 0),
                 missing | (label === 5 ? 1 << g : 0),
                 old | (label < 5 ? 1 << (5 * g + label) : 0));
        }
    }
    walk(0, 0, 0, 0);
    const mandatory = types.filter(t => oneNew.some((count, g) =>
        count === 2 && twoNew[g] === 0 && t.missing === (1 << g)));
    const mayRemain = types.filter(t => mandatory.every(mt =>
        mt.values.some((symbol, g) => symbol === t.values[g])));
    // Use only old labels, so an agreement with this cover cannot be
    // broken by replacing a wildcard with distinct new labels.
    function cover(chosen, left) {
        const uncovered = mayRemain.find(t => !(t.old & chosen));
        if (uncovered === undefined) return chosen;
        if (left === 0) return null;
        for (const b of bits(uncovered.old)) {
            const candidate = cover(chosen | b, left - 1);
            if (candidate !== null) return candidate;
        }
        return null;
    }
    let found = null;
    for (let budget = 1; budget <= 5 && found === null; budget++) {
        found = cover(0, budget);
    }
    const oldCover = found === null ? null : bits(found).map(b => {
        const index = 31 - Math.clz32(b);
        return [Math.floor(index / 5), index % 5];
    });
    const continuation = found === null ? exploreExtensions(core, mayRemain, mandatory) : {};
    return {allowed: types.length, mandatory: mandatory.length,
        remaining: mayRemain.length, oldCover, ...continuation};
}

function exploreExtensions(core, types, mandatory) {
    const required = types.filter(t => {
        if (mandatory.includes(t)) return true;
        if (t.missing !== 0) return false;
        return Boolean(t.values.reduce((b, v, g) => b & line[g][v], core));
    });
    if (required.length < k || !mandatory.every(t => types.includes(t))) {
        return {nodes: 1, branchExcluded: true, maxSelected: required.length};
    }
    const optional = types.filter(t => !required.includes(t));
    const index = b => 31 - Math.clz32(b);
    const coversCore = t => t.values.reduce((b, v, g) => b | (v < 5 ? line[g][v] : 0), 0);
    if (required.some(t => (coversCore(t) & core) !== core)) throw new Error("invalid required row");
    function oldCover(tuples, weights) {
        const ranked = tuples.map(t => {
            const max = Math.max(...bits(t.old).map(b => weights[index(b)]));
            return [max, t.old];
        }).sort((a, b) => a[0] - b[0]);
        const failed = new Set();
        function search(chosen, left) {
            const entry = ranked.find(t => !(t[1] & chosen));
            if (!entry) return chosen;
            if (left === 0 || failed.has(chosen)) return null;
            const candidates = bits(entry[1]).sort((a, b) => weights[index(b)] - weights[index(a)]);
            for (const c of candidates) {
                const found = search(chosen | c, left - 1);
                if (found !== null) return found;
            }
            failed.add(chosen);
            return null;
        }
        return search(0, 5);
    }
    let nodes = 0;
    let maxSelected = 0;
    function branch(chosen, future) {
        nodes++;
        maxSelected = Math.max(maxSelected, chosen.length);
        const potential = [...chosen, ...future];
        const single = Array(6).fill(0);
        const multi = Array(6).fill(0);
        const weights = Array(30).fill(0);
        const degreeUpperTest = Array(30).fill(0);
        for (const t of potential) {
            const missing = bits(t.missing);
            for (const b of missing) {
                (missing.length === 1 ? single : multi)[index(b)]++;
            }
            for (const b of bits(t.old)) {
                const i = index(b);
                weights[i]++;
                // An old-only type can occur at most once. Overestimate the
                // contribution of a type with new labels when testing degree 2.
                degreeUpperTest[i] += t.missing ? 2 : 1;
            }
        }
        if (single.some((count, i) => count < 2 && multi[i] === 0)) return null;
        if (chosen.some(t => bits(t.old).some(b => degreeUpperTest[index(b)] < 2))) return null;
        if (oldCover(potential, weights) !== null) return null;
        const cover = oldCover(chosen, weights);
        if (cover === null) return chosen.map(t => t.values);
        const breakers = future.filter(t => !(t.old & cover));
        const others = future.filter(t => t.old & cover);
        for (let i = 0; i < breakers.length; i++) {
            const next = breakers[i];
            const compatible = breakers.slice(i + 1).concat(others).filter(t =>
                next.values.some((v, g) => t.values[g] === v));
            const found = branch([...chosen, next], compatible);
            if (found !== null) return found;
        }
        return null;
    }
    const optimisticExtension = branch(required, optional);
    return {nodes, maxSelected, branchExcluded: optimisticExtension === null,
        optimisticExtension};
}

const unresolved = coreOrbits.filter(r => !r.degreeOneForced && r.oldCover === null && !r.branchExcluded);
const sizes = coreOrbits.reduce((n, r) => n + r.orbitSize, 0);
console.log(JSON.stringify({orbits: coreOrbits.length,
    sizes,
    degreeOneExcluded: coreOrbits.filter(r => r.degreeOneForced).length,
    oldCoverExcluded: coreOrbits.filter(r => Array.isArray(r.oldCover)).length,
    branchExcluded: coreOrbits.filter(r => r.branchExcluded).length,
    branchNodes: coreOrbits.reduce((n, r) => n + (r.nodes || 0), 0),
    unresolved: unresolved.slice(0, 8),
    examples: k === 14 ? coreOrbits.filter(r => !r.degreeOneForced) : undefined,
    records: k === 15 ? coreOrbits : undefined}));
if (sizes !== directionCounts[6] || unresolved.length) process.exitCode = 1;
