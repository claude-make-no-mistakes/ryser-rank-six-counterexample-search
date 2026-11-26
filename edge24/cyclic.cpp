#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

using Mask = uint64_t;
using Row = uint32_t;
constexpr int sides = 6;
constexpr int labels = 10;
constexpr int vertex_count = sides * labels;
constexpr Row one_per_side = 0x111111;

Row step(Row a) { return (a >> 4) | ((a & 15) << 20); }
int common(Row a, Row b) {
    const Row z = a ^ b;
    return std::popcount(~(z | (z >> 1) | (z >> 2) | (z >> 3)) & one_per_side);
}
int symbol(Row a, int i) { return (a >> (4 * i)) & 15; }
int bottom(Mask a) { return std::countr_zero(a); }

std::vector<Row> rotation_orbit(Row a) {
    std::vector<Row> result{a};
    for (Row next = step(a); next != a; next = step(next)) result.push_back(next);
    return result;
}
Mask mask(Row a) {
    Mask result = 0;
    for (int i = 0; i < sides; i++) result |= Mask(1) << (labels * i + symbol(a, i));
    return result;
}
Row normalized_orbit(Row a) {
    Row least = uint32_t(-1);
    for (const Row r : rotation_orbit(a)) {
        std::array<int, labels> next_label;
        next_label.fill(-1);
        Row renamed = 0;
        int used = 0;
        for (int i = 0; i < sides; i++) {
            const int s = symbol(r, i);
            if (next_label[s] == -1) next_label[s] = used++;
            renamed |= next_label[s] << (4 * i);
        }
        const auto rotated = rotation_orbit(renamed);
        least = std::min(least, *std::min_element(rotated.begin(), rotated.end()));
    }
    return least;
}

struct Orbit {
    std::vector<Row> rows;
    std::vector<Mask> masks;
    std::array<int, labels> histogram{};
};
struct Search {
    std::vector<Orbit> orbits;
    std::vector<std::vector<Mask>> compatible;
    std::vector<int> current;
    int nodes = 0, roots = 0, largest = 0, prunes = 0;
    std::mt19937 rng{32421};

    void prepare() {
        int word_count = 1;
        for (int i = 0; i < sides; ++i) word_count *= labels;
        for (int i = 0; i < word_count; ++i) {
            int z = i;
            Row a = 0;
            for (int j = 0; j < sides; j++) {
                a |= (z % labels) << (4 * j);
                z /= labels;
            }
            auto rows = rotation_orbit(a);
            if (*std::min_element(rows.begin(), rows.end()) != a) continue;
            if (std::any_of(rows.begin() + 1, rows.end(), [&](Row b) {
                    return common(a, b) == 0 || common(a, b) >= 5;
                })) continue;
            Orbit item;
            item.rows = std::move(rows);
            for (const Row r : item.rows) {
                item.masks.push_back(mask(r));
                ++item.histogram[symbol(r, 0)];
            }
            orbits.push_back(std::move(item));
        }
        int words = (orbits.size() + 63) / 64;
        compatible.assign(orbits.size(), std::vector<Mask>(words, 0));
        for (int i = 0; i < int(orbits.size()); ++i) {
            for (int j = 0; j < i; ++j) {
                const Row a = orbits[i].rows[0];
                if (std::any_of(orbits[j].rows.begin(), orbits[j].rows.end(), [&](Row b) {
                        const int x = common(a, b);
                        return x == 0 || x >= 5;
                    })) continue;
                compatible[i][j / 64] |= Mask(1) << (j % 64);
                compatible[j][i / 64] |= Mask(1) << (i % 64);
            }
        }
    }
    bool adj(int a, int b) const {
        return (compatible[a][b / 64] >> (b % 64)) & 1;
    }
    template <typename Choices>
    Mask cover(const Choices& rows, const std::array<int, vertex_count>& weights) {
        std::vector<std::pair<int, Mask>> priority;
        for (Mask row : rows) {
            int max_weight = 0;
            for (Mask bits = row; bits; bits &= bits - 1) {
                max_weight = std::max(max_weight, weights[bottom(bits)]);
            }
            priority.emplace_back(max_weight, row);
        }
        std::sort(priority.begin(), priority.end());
        auto rec = [&](auto const& self, Mask chosen, int left) -> Mask {
            Mask next = 0;
            for (auto const& p : priority) {
                if (!(p.second & chosen)) { next = p.second; break; }
            }
            if (next == 0) return chosen;
            if (left == 0) return 0;
            std::array<int, sides> viable;
            int size = 0;
            for (Mask bits = next; bits; bits &= bits - 1) viable[size++] = bottom(bits);
            std::sort(viable.begin(), viable.end(), [&](int a, int b) {
                return weights[a] > weights[b];
            });
            for (int v : viable) {
                const Mask candidate = self(self, chosen | (Mask(1) << v), left - 1);
                if (candidate) return candidate;
            }
            return 0;
        };
        return rec(rec, 0, 5);
    }
    bool unmet(int id, Mask selected) {
        return std::any_of(orbits[id].masks.begin(), orbits[id].masks.end(),
                           [&](Mask r) { return !(r & selected); });
    }
    void write() {
        std::cout << '[';
        bool first = true;
        for (int id : current) for (Row row : orbits[id].rows) {
            if (!first) std::cout << ',';
            first = false;
            std::cout << '[';
            for (int j = 0; j < sides; j++) {
                if (j) std::cout << ',';
                std::cout << symbol(row, j);
            }
            std::cout << ']';
        }
        std::cout << "]\n";
    }
    bool branch(std::vector<int> future, int m) {
        ++nodes;
        largest = std::max(largest, m);
        std::array<int, labels> degrees{};
        std::vector<Mask> words;
        for (int id : current) {
            words.insert(words.end(), orbits[id].masks.begin(), orbits[id].masks.end());
            for (int s = 0; s < labels; s++) degrees[s] += orbits[id].histogram[s];
        }
        auto possible = degrees;
        for (int id : future) for (int s = 0; s < labels; s++) possible[s] += orbits[id].histogram[s];
        std::array<int, vertex_count> weights{};
        for (int q = 0; q < vertex_count; ++q) weights[q] = possible[q % labels] + (rng() % 4);
        Mask selected = cover(words, weights);
        if (!selected) {
            write();
            return true;
        }
        if (future.empty()) return false;
        // Fill the cover to five to reduce the set of orbits that can extend it.
        while (std::popcount(selected) < 5) {
            int best = -1;
            for (int v = 0; v < vertex_count; v++) {
                if ((selected >> v) & 1) continue;
                if (best < 0 || weights[v] > weights[best]) best = v;
            }
            selected |= Mask(1) << best;
        }
        if (future.size() <= 120) {
            std::vector<Mask> union_words = words;
            for (int i : future) {
                union_words.insert(union_words.end(), orbits[i].masks.begin(), orbits[i].masks.end());
            }
            if (cover(union_words, weights)) { ++prunes; return false; }
        }
        // Put the cover-killing orbits first. Subsequent recursive branches may
        // still use all non-killing orbits and any later killing ones.
        std::vector<int> killers, others;
        for (int i : future) (unmet(i, selected) ? killers : others).push_back(i);
        for (std::size_t at = 0; at < killers.size(); ++at) {
            const int i = killers[at], total = m + orbits[i].rows.size();
            std::vector<int> next;
            for (std::size_t j = at + 1; j < killers.size(); ++j) {
                const int b = killers[j];
                if (adj(i, b)) next.push_back(b);
            }
            for (int b : others) {
                if (adj(i, b)) next.push_back(b);
            }
            current.push_back(i);
            if (branch(std::move(next), total)) return true;
            current.pop_back();
        }
        return false;
    }
    bool run() {
        std::cout << "orbits=" << orbits.size() << std::endl;
        std::vector<int> candidate_roots;
        for (int i = 0; i < int(orbits.size()); i++) {
            if (normalized_orbit(orbits[i].rows[0]) == orbits[i].rows[0]) candidate_roots.push_back(i);
        }
        std::shuffle(candidate_roots.begin(), candidate_roots.end(), rng);
        for (int i : candidate_roots) {
            ++roots;
            current = {i};
            std::vector<int> future;
            for (int j = 0; j < int(orbits.size()); ++j) if (adj(i, j)) future.push_back(j);
            std::shuffle(future.begin(), future.end(), rng);
            if (branch(std::move(future), orbits[i].rows.size())) return true;
        }
        std::cout << "nodes=" << nodes << " roots=" << roots << "/" << candidate_roots.size()
                  << " largest_prefix=" << largest << " union_covers=" << prunes << '\n';
        return false;
    }
};

int main() {
    Search search;
    search.prepare();
    if (search.run()) {
        std::cout << "A candidate was printed for independent checking.\n";
        return 1;
    }
    std::cout << "All intersecting rotation-invariant families on up to ten labels per side have a five-cover.\n";
}
