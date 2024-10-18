import time
from functools import wraps
from itertools import zip_longest


def grouper(iterable, n, fillvalue=None):
    """Collect data into non-overlapping fixed-length chunks or blocks"""
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def delay_by(amount):
    def decorator_delay_by(func):
        @wraps(func)
        def inner(*args, **kwargs):
            begin = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            to_sleep = max(amount - (end - begin), 0)
            if to_sleep > 0:
                time.sleep(to_sleep)
            return result

        return inner

    return decorator_delay_by
