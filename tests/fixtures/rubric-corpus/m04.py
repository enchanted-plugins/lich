# rubric corpus m04 — pure function, correct but comparison redundancy.
# Serviceable: works; still has `== True`, explicit else on early return.


def is_even(n):
    if abs(n) % 2 == 0:
        return True
    else:
        return False


def classify_number(n):
    if is_even(n) == True:
        return "even"
    return "odd"


def classify_sequence(nums):
    result = []
    for n in nums:
        result.append(classify_number(n))
    return result


if __name__ == "__main__":
    print(classify_sequence([-3, -2, -1, 0, 1, 2, 3]))
