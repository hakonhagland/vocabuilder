from pathlib import Path
import pytest
import re
from ..vocabuilder import Database, TimeMixin, Config

def test_additem(tmp_path):
    #logging.basicConfig(level=logging.INFO)
    #config = Config()
    #db = Database(config)
    assert Path.cwd() == 1
    #assert tmp_path == 1

