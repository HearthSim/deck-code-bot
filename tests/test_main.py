import os
import sys

from deck_code_bot.main import find_and_decode_deckstrings


def _get_comment(filename):
    return os.path.join(os.path.dirname(__file__), filename)


def test_hello_world():
    assert True


def test_find_and_decode():
    with open(_get_comment("comment1.txt"), "r") as f:
        assert len(find_and_decode_deckstrings(f.read())) == 2
    with open(_get_comment("comment2.txt"), "r") as f:
        assert len(find_and_decode_deckstrings(f.read())) == 1
    with open(_get_comment("comment3.txt"), "r") as f:
        assert len(find_and_decode_deckstrings(f.read())) == 0
