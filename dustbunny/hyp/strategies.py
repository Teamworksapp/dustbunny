"""
Define a bounded date strategy for Hypothesis.
"""

from hypothesis.errors import InvalidArgument
from hypothesis.searchstrategy import SearchStrategy
from hypothesis.strategies import defines_strategy, composite
from hypothesis import assume, strategies as st
import hypothesis.internal.conjecture.utils as cu

import pytz
import datetime as dt
import random
import time
from functools import partial
import os


ALPHANUM='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz9123456789'
WORDCHARS=ALPHANUM+'-_'

__all__ = (
    'words',
    'gfywords',
    'gfycodes',
    'first_names',
    'last_names',
    'alphanumeric',
    'datetimes_in_range',
)

words = partial(st.text, alphabet=WORDCHARS)
alphanumeric = partial(st.text, alphabet=ALPHANUM)

with open(os.path.join(os.path.dirname(__file__), 'assets', 'first_names.txt')) as names:
    first_names = partial(st.sampled_from, [x.strip().title() for x in names.readlines()])

with open(os.path.join(os.path.dirname(__file__), 'assets', 'last_names.txt')) as names:
    last_names = partial(st.sampled_from, [x.strip().title() for x in names.readlines()])

with open(os.path.join(os.path.dirname(__file__), 'assets', 'adjectives.txt')) as names:
    adjectives = [x.strip().title().replace(' ', '') for x in names.readlines()]

with open(os.path.join(os.path.dirname(__file__), 'assets', 'animals.txt')) as names:
    animals = [x.strip().title().replace(' ', '') for x in names.readlines()]
    
@composite
def gfywords(draw):
    x = adjectives[draw(st.integers(min_value=0, max_value=len(adjectives)-1))]
    y = adjectives[draw(st.integers(min_value=0, max_value=len(adjectives)-1))]
    z = animals[draw(st.integers(min_value=0, max_value=len(animals)-1))]
    assume(x != y)
    return ' '.join((x, y, z))    
    
@composite
def gfycodes(draw):
    x = adjectives[draw(st.integers(min_value=0, max_value=len(adjectives)))]
    y = adjectives[draw(st.integers(min_value=0, max_value=len(adjectives)))]
    z = animals[draw(st.integers(min_value=0, max_value=len(animals)))]
    assume(x != y)
    return ''.join((x, y, z))
    



class DatetimeStrategy(SearchStrategy):
    def __init__(self, allow_naive, timezones, start_date=None, end_date=None, start_inclusive=True, end_inclusive=True):
        self.allow_naive = allow_naive
        self.timezones = timezones
        self.start_date = (start_date or dt.datetime(year=dt.MINYEAR)).timestamp()
        self.end_date = (end_date or dt.datetime(year=dt.MAXYEAR)).timestamp()
        self.r = self.end_date - self.start_date

        if not start_inclusive:
            self.start_date += 1  # second

        if not end_inclusive:
            self.end_date -= 1  # second


    def do_draw(self, data):
        while True:
            try:
                result = dt.datetime.fromtimestamp(self.start_date + random.uniform(0, self.r))

                if (
                    not self.allow_naive or
                    (self.timezones and cu.boolean(data))
                ):
                    result = cu.choice(data, self.timezones).localize(result)
                return result

            except (OverflowError, ValueError):
                pass


@defines_strategy
def datetimes_in_range(allow_naive=None, timezones=None, start_date=None, end_date=None, start_inclusive=True, end_inclusive=True):
    """Return a strategy for generating datetimes.

    allow_naive=True will cause the values to sometimes be naive.
    timezones is the set of permissible timezones. If set to an empty
    collection all timezones must be naive. If set to None all available
    timezones will be used.

    """
    if timezones is None:
        timezones = list(pytz.all_timezones)
        timezones.remove(u'UTC')
        timezones.insert(0, u'UTC')
    timezones = [
        tz if isinstance(tz, dt.tzinfo) else pytz.timezone(tz)
        for tz in timezones
    ]
    if allow_naive is None:
        allow_naive = not timezones
    if not (timezones or allow_naive):
        raise InvalidArgument(
            u'Cannot create non-naive datetimes with no timezones allowed'
        )
    return DatetimeStrategy(
        allow_naive=allow_naive, timezones=timezones,
        start_date=start_date,
        end_date=end_date,
        start_inclusive=start_inclusive,
        end_inclusive=end_inclusive
    )

