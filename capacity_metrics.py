"""Consistent capacity categories, counts and transitions without display rounding."""
import numpy as np

BUCKETS = ('< 75', '75-100', '> 100')

def capacity_summary(before_enrollment, after_enrollment, capacities, closed_indices):
    before = np.asarray(before_enrollment, dtype=float)
    after = np.asarray(after_enrollment, dtype=float)
    capacity = np.asarray(capacities, dtype=float)
    if before.ndim != 1 or before.shape != after.shape or before.shape != capacity.shape:
        raise ValueError('Enrollment and capacity arrays must have matching one-dimensional shapes.')
    if not np.all(np.isfinite(capacity)) or np.any(capacity <= 0):
        raise ValueError('Capacity must be finite and positive.')
    if not np.all(np.isfinite(before)) or not np.all(np.isfinite(after)) or np.any(before < 0) or np.any(after < 0):
        raise ValueError('Enrollment must be finite and nonnegative.')
    closed = np.zeros(len(before), dtype=bool)
    closed[list(closed_indices)] = True
    def classify(enrollment):
        ratio = enrollment / capacity
        return np.where(ratio < .75, 0, np.where(ratio <= 1, 1, 2))
    initial = classify(before)
    final = classify(after)
    final[closed] = -1
    counts = {}
    deltas = {}
    transitions = {}
    for i, name in enumerate(BUCKETS):
        was, now = initial == i, final == i
        counts[name] = int(now.sum())
        deltas[name] = int(now.sum() - was.sum())
        transitions['delta ' + name] = np.where(now & ~was, 'in', np.where(was & ~now, 'out', ''))
    transitions['delta closed'] = np.where(closed, 'in', '')
    return counts, deltas, transitions
