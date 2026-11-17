"""Fail-closed data-quality checks; never invent redistribution weights."""
import math

class AllocationDataError(ValueError):
    pass

def validate_destinations(counts, weights, closed, names):
    n = len(counts)
    if len(weights) != n or any(len(row) != n for row in weights):
        raise AllocationDataError("Redistribution data does not match the school list.")
    if any(not math.isfinite(float(x)) or float(x) < 0 for x in counts):
        raise AllocationDataError("Enrollment contains missing, negative, or invalid values.")
    if any(not math.isfinite(float(x)) or float(x) < 0 for row in weights for x in row):
        raise AllocationDataError("Redistribution weights contain missing, negative, or invalid values.")
    closed = set(closed)
    if any(i < 0 or i >= n for i in closed):
        raise AllocationDataError("A selected school is missing from the enrollment data.")
    unsupported = [str(names[i]) for i in sorted(closed)
                   if float(counts[i]) > 0 and not any(float(weights[i][j]) > 0
                   for j in range(n) if j not in closed)]
    if unsupported:
        raise AllocationDataError("No supported open-school destination for: " +
            ", ".join(unsupported) + ". Remove these closures or supply reviewed destination data. No estimate is shown.")

def validate_totals(before, after, displayed, closed):
    if len(before) != len(after) or len(before) != len(displayed):
        raise AllocationDataError("Enrollment result dimensions do not match. No estimate is shown.")
    for values in (after, displayed):
        if any(not math.isfinite(float(x)) or float(x) < 0 for x in values):
            raise AllocationDataError("Redistribution produced invalid enrollment. No estimate is shown.")
    expected = math.fsum(float(x) for x in before)
    if not math.isclose(math.fsum(float(x) for x in after), expected, rel_tol=0, abs_tol=1e-7):
        raise AllocationDataError("Redistribution does not conserve total enrollment. No estimate is shown.")
    if any(abs(float(after[i])) > 1e-7 or abs(float(displayed[i])) > 1e-7 for i in closed):
        raise AllocationDataError("A closed school still has students assigned. No estimate is shown.")
    if not math.isclose(math.fsum(float(x) for x in displayed), expected, rel_tol=0, abs_tol=1e-7):
        raise AllocationDataError("Whole-student rounding does not conserve total enrollment. This scenario needs a reviewed rounding method; no estimate is shown.")

def apportion_whole_students(before, after, closed, names):
    """Largest remainder on existing estimates, never new destination weights.

    Floor each open-school estimate, then assign remaining whole students to
    largest fractional remainders. Exact ties use school name, then source row.
    Closed schools remain zero. Validate raw conservation before rounding.
    """
    closed = set(closed)
    validate_totals(before, after, after, closed)
    expected = math.fsum(float(x) for x in before)
    target = round(expected)
    if not math.isclose(expected, target, rel_tol=0, abs_tol=1e-7):
        raise AllocationDataError('Source enrollment total is not a whole number. No estimate is shown.')
    if len(names) != len(after):
        raise AllocationDataError('School names do not match enrollment results.')
    values = [float(x) for x in after]
    result = [0 if i in closed else math.floor(x) for i, x in enumerate(values)]
    remaining = target - sum(result)
    eligible = [i for i, x in enumerate(values) if i not in closed and x > result[i]]
    eligible.sort(key=lambda i: (-(values[i] - result[i]), str(names[i]), i))
    if remaining < 0 or remaining > len(eligible):
        raise AllocationDataError('Whole-student apportionment is inconsistent. No estimate is shown.')
    for i in eligible[:remaining]:
        result[i] += 1
    validate_totals(before, after, result, closed)
    return result
