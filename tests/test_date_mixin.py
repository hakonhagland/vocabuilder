import pytest
import re
from ..vocabuilder import DateMixin

class Config:
    """Mocking the Config class in vocabuilder"""
    datefmt_str = '%Y-%m-%d %H:%M:%S'

class MyDate(DateMixin):
    config = Config()  # used by DateMixin

def test_today():
    d = MyDate()
    today = d.today_as_string()
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", today)
