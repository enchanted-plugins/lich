# rubric corpus b04 — pure function, low simplicity.
# Primary concern: over-engineered branching for a trivial task.


def is_even(n):
    if n == 0:
        return True
    else:
        if n < 0:
            n = n * -1
            if n == 0:
                return True
            else:
                if n % 2 == 0:
                    return True
                else:
                    return False
        else:
            if n % 2 == 0:
                return True
            else:
                return False


def classify_number(n):
    result = ""
    if is_even(n) == True:
        result = result + "even"
    else:
        result = result + "odd"
    return result
