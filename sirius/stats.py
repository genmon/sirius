import flask
import collections

STATS = collections.defaultdict(int)
blueprint = flask.Blueprint('stats', __name__)


def inc(key):
    STATS[key] += 1


@blueprint.route('/_/stats')
def showstats():
    "Render some trivial stats"
    return '<pre>' + '\n'.join('{} {}'.format(k, v) for k, v in STATS.items())
