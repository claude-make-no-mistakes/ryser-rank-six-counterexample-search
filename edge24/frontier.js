"use strict";

const fs = require("node:fs");
const {gzipSync} = require("node:zlib");
const {exam, costs, scan, scanWithCollisionGap} = require("../edge23/scout-frontier.js");

function main() {
    const edges = 24;
    const requiredPairs = edges * (edges - 1) / 2;
    // A degree-ten star would leave a forbidden fourteen-edge residual.
    const initial = exam(edges, false, 9);
    const profiles = initial.ps;
    const ids = new Map(profiles.map((profile, index) => [String(profile.p), index]));
    const tables = new Map();
    const statistics = new Map();
    const kept = [];
    console.log("transport", profiles.length, initial.total, initial.survivors.length);

    function matrixCost(table, first, second) {
        const a = ids.get(String(first));
        const b = ids.get(String(second));
        return table[Math.min(a, b)][Math.max(a, b)];
    }

    for (const row of initial.survivors) {
        const [system, score, twos, baseline] = row;
        if (!statistics.has(twos)) statistics.set(twos, [0, 0, 0]);
        const counts = statistics.get(twos);
        counts[0]++;
        if (system.some(profile => profile[0] > edges - twos - profile.filter(d => d === 2).length)) {
            continue;
        }
        counts[1]++;
        const budget = 2 * (score - requiredPairs);
        let lower = baseline;
        if (twos >= 8) {
            if (!tables.has(twos)) tables.set(twos, costs(edges, profiles, twos === 12, edges - 2 * twos));
            const table = tables.get(twos);
            lower = 0;
            for (let i = 0; i < system.length; i++) {
                for (let j = i + 1; j < system.length; j++) {
                    lower += matrixCost(table, system[i], system[j]);
                }
            }
        }
        if (lower > budget) continue;
        counts[2]++;
        kept.push(row);
    }
    console.log("degree-two vertices, transport survivors, mate survivors, codegree survivors");
    for (const [twos, counts] of [...statistics].sort((a, b) => a[0] - b[0])) {
        console.log(twos, ...counts);
    }
    console.log("profiles after mate and codegree constraints", kept.length);

    const args = process.argv.slice(2);
    let possible = kept;
    if (args.includes("--stars")) {
        const star = scan(edges, kept);
        console.log("profiles after star constraints", star.kept.length);
        const strict = costs(edges, profiles, true);
        const gap = scanWithCollisionGap(edges, star.kept, (a, b, strictMode) => {
            const table = strictMode ? strict : initial.allcost;
            return matrixCost(table, a, b);
        });
        possible = gap.kept;
        console.log("profiles after conditional collision bounds", possible.length);
    }
    const dest = args.find(arg => arg !== "--stars");
    if (dest) {
        fs.writeFileSync(dest, gzipSync(JSON.stringify(possible)));
    }
}

main();
