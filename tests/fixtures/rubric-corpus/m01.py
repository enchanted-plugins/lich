# rubric corpus m01 — data transform, readable but not idiomatic.
# Serviceable: names are fine, logic is clear; could use defaultdict / itertools.

from collections import defaultdict


def group_pairs(pairs):
    """Group (key, value) tuples into {key: [values]}."""
    groups = defaultdict(list)
    for key, value in pairs:
        groups[key].append(value)
    return dict(groups)


def flatten(nested):
    """One level of flattening."""
    out = []
    for inner in nested:
        for item in inner:
            out.append(item)
    return out


if __name__ == "__main__":
    pairs = [("a", 1), ("b", 2), ("a", 3), ("c", 4), ("a", 5)]
    print(group_pairs(pairs))
    print(flatten([[1, 2], [3, 4], [5]]))
