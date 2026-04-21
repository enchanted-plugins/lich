# rubric corpus b02 — IO wrapper, low correctness_at_glance.
# Primary concern: no error handling, resource leak, silent fallbacks.

import os


def read_config(path):
    f = open(path)
    data = f.read()
    lines = data.split("\n")
    out = {}
    for line in lines:
        parts = line.split("=")
        out[parts[0]] = parts[1]
    return out


def write_config(path, cfg):
    f = open(path, "w")
    for k in cfg:
        f.write(k + "=" + cfg[k] + "\n")


def load_or_default(path):
    if os.path.exists(path):
        return read_config(path)
    return {}
