"""Polyglot fixture — PY-M1-001 div-zero.

One deliberate bug: `len(nums)` denominator can be 0 when `nums == []`.
Parses clean; M1 AST walker flags line 6.
"""


def average(nums):
    return sum(nums) / len(nums)


def main():
    print(average([]))


if __name__ == "__main__":
    main()
