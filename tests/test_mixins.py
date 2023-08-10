import re

from vocabuilder.vocabuilder import TimeMixin


class MyTimer(TimeMixin):
    pass


def test_time_mixin_today() -> None:
    d = MyTimer()
    now = d.epoch_in_seconds()
    assert re.match(r"^\d+$", str(now))
