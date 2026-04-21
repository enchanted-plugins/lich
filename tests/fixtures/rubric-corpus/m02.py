# rubric corpus m02 — IO wrapper, uses context managers but silent on bad input.
# Serviceable: closes handles; still forgives malformed lines without warning.

import os


def read_config(path):
    """Parse simple key=value file into a dict; skip malformed lines silently."""
    result = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def write_config(path, cfg):
    with open(path, "w", encoding="utf-8") as fh:
        for key, value in cfg.items():
            fh.write(f"{key}={value}\n")


def load_or_default(path, default=None):
    if not os.path.exists(path):
        return default or {}
    return read_config(path)
