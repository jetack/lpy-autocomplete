"""Tests for lpy_autocomplete.utils"""

import pytest
from lpy_autocomplete.utils import (
    mangle,
    unmangle,
    first,
    last,
    butlast,
    drop,
    drop_last,
    allkeys,
    distinct,
    flatten,
)


class TestMangle:
    def test_basic(self):
        assert mangle("some-func") == "some_func"

    def test_empty(self):
        assert mangle("") == ""

    def test_no_hyphens(self):
        assert mangle("func") == "func"

    def test_multiple_hyphens(self):
        assert mangle("my-long-name") == "my_long_name"


class TestUnmangle:
    def test_basic(self):
        assert unmangle("some_func") == "some-func"

    def test_empty(self):
        assert unmangle("") == ""

    def test_no_underscores(self):
        assert unmangle("func") == "func"

    def test_preserves_leading_underscores(self):
        assert unmangle("_private") == "_private"
        assert unmangle("__dunder__") == "__dunder__"
        assert unmangle("__init__") == "__init__"

    def test_preserves_trailing_underscores(self):
        assert unmangle("class_") == "class_"
        assert unmangle("type__") == "type__"

    def test_converts_middle_underscores(self):
        assert unmangle("some_func") == "some-func"
        assert unmangle("my_long_name") == "my-long-name"

    def test_preserves_both_leading_and_trailing(self):
        assert unmangle("__some_func__") == "__some-func__"
        assert unmangle("_my_var_") == "_my-var_"

    def test_all_underscores(self):
        assert unmangle("_") == "_"
        assert unmangle("__") == "__"
        assert unmangle("___") == "___"


class TestFirst:
    def test_list(self):
        assert first([1, 2, 3]) == 1

    def test_empty(self):
        assert first([]) is None

    def test_generator(self):
        assert first(x for x in [5, 6, 7]) == 5


class TestLast:
    def test_list(self):
        assert last([1, 2, 3]) == 3

    def test_single(self):
        assert last([42]) == 42


class TestButlast:
    def test_basic(self):
        assert butlast([1, 2, 3]) == [1, 2]

    def test_single(self):
        assert butlast([1]) == []

    def test_empty(self):
        assert butlast([]) == []


class TestDrop:
    def test_basic(self):
        assert list(drop(2, [1, 2, 3, 4])) == [3, 4]

    def test_zero(self):
        assert list(drop(0, [1, 2, 3])) == [1, 2, 3]


class TestDropLast:
    def test_basic(self):
        assert drop_last(2, [1, 2, 3, 4]) == [1, 2]

    def test_zero(self):
        assert drop_last(0, [1, 2, 3]) == [1, 2, 3]


class TestAllkeys:
    def test_flat_dict(self):
        assert set(allkeys({"a": 1, "b": 2})) == {"a", "b"}

    def test_nested_dict(self):
        result = allkeys({"a": {"b": 1, "c": 2}})
        assert "b" in result
        assert "c" in result


class TestDistinct:
    def test_basic(self):
        assert list(distinct([1, 2, 2, 3, 1, 4])) == [1, 2, 3, 4]

    def test_preserves_order(self):
        assert list(distinct([3, 1, 2, 1, 3])) == [3, 1, 2]


class TestFlatten:
    def test_basic(self):
        assert list(flatten([[1, 2], [3, 4]])) == [1, 2, 3, 4]

    def test_empty(self):
        assert list(flatten([[], []])) == []
