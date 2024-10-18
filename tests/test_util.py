import time

import pytest

from steam2sqlite import utils


def hello():
    print("hello")


def slow_hello():
    time.sleep(0.5)


def test_delay_by():
    # we're calling the decorator directly here so that we can control the delay time
    delay_time = 0.5

    begin = time.monotonic()
    utils.delay_by(delay_time)(hello)()
    dur = time.monotonic() - begin
    assert dur > delay_time
    assert dur == pytest.approx(delay_time, rel=0.1)

    begin = time.monotonic()
    utils.delay_by(delay_time)(slow_hello)()  # takes .5 sec
    dur = time.monotonic() - begin
    assert dur > delay_time
    assert dur == pytest.approx(0.5, rel=0.1)

    delay_time = 0.25
    begin = time.monotonic()
    utils.delay_by(delay_time)(slow_hello)()  # takes 0.5 sec
    dur = time.monotonic() - begin
    assert dur > delay_time
    assert dur == pytest.approx(0.5, rel=0.1)
