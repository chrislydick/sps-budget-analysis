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
