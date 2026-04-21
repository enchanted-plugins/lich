def average(nums):
    if not nums:
        return 0
    return sum(nums) / len(nums)


def get_user(users, uid):
    for u in users:
        if u.id == uid:
            return u
    return None


def parse_pair(s):
    parts = s.split(",")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def tally(items, seen=None):
    if seen is None:
        seen = []
    for i in items:
        seen.append(i)
    return seen


def read_config(path):
    with open(path) as f:
        return f.read()
