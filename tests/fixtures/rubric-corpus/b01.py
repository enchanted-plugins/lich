# rubric corpus b01 — data transform, low clarity/idiom/simplicity.
# Primary concern: overloaded one-letter names, dense single-line loops.


def d(x):
    r = {}
    for i in range(len(x)):
        k = x[i][0]
        v = x[i][1]
        if k in r:
            r[k] = r[k] + [v] if type(r[k]) == list else [r[k], v]
        else:
            r[k] = v
    return r


def p(x):
    o = []
    for a in x:
        for b in a:
            o.append(b)
    return o


if __name__ == "__main__":
    s = [("a", 1), ("b", 2), ("a", 3), ("c", 4), ("a", 5)]
    print(d(s))
    print(p([[1, 2], [3, 4], [5]]))
