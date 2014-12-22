import collections
STATS = collections.defaultdict(int)

def as_text():
    return '<pre>' + '\n'.join('{} {}'.format(k, v) for k, v in STATS.items())

def inc(key):
    STATS[key] += 1
