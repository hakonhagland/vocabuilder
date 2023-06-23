import re
from ..vocabuilder import TimeMixin

class MyTimer(TimeMixin):
    pass

def test_today():
    d = MyTimer()
    now = d.epoch_in_seconds()
    assert re.match(r"^\d+$", now)