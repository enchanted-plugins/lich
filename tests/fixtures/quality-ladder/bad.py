def average(nums):
    return sum(nums) / len(nums)


def get_user(users, uid):
    return [u for u in users if u.id == uid][0]


def parse_pair(s):
    parts = s.split(",")
    return int(parts[0]) + int(parts[1])


def tally(items, seen=[]):
    for i in items:
        seen.append(i)
    return seen


def read_config(path):
    f = open(path)
    data = f.read()
    return data
