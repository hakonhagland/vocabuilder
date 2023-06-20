import pytest
import re
from ..vocabuilder import DateMixin

class Config:
    datefmt_str = '%Y-%m-%d %H:%M:%S'

class TestDateMixin(DateMixin):
    config = Config()

def test_today():
    d = TestDateMixin()
    today = d.today_as_string()
    assert re.match(r"^\d{4}", today)
