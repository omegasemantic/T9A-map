#!/usr/bin/env python3
# result.py — filter steps before rendering
# formatting/presentation now lives in result.tpl, not here

def filter_short_walks(steps):
    """Drop WALK steps under ~29m, same threshold as the old grep:
    grep -vE 'WALK.*\\([1-9] m\\)|WALK.*\\([12][0-9] m\\)'
    i.e. drops any walk instruction whose distance is 1-29 metres."""

    def is_negligible_walk(step):
        if step['type'] != 'WALK':
            return False
        dist = step.get('distance', '')
        # distance strings look like "12 m", "1.2 km" etc.
        if not dist.endswith(' m'):
            return False  # km distances always kept
        try:
            metres = int(dist.split()[0])
        except ValueError:
            return False
        return 1 <= metres <= 29

    return [s for s in steps if not is_negligible_walk(s)]
