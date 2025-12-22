"""Tests for lpy_autocomplete.api"""

import pytest
from lpy_autocomplete import API


class TestAPI:
    """Tests for the main API class."""

    def test_init_default(self):
        api = API()
        assert api.namespace is not None

    def test_init_with_globals(self):
        api = API(globals_={"my_var": 42})
        assert "my-var" in api.namespace.names

    def test_set_namespace(self):
        api = API()
        api.set_namespace(globals_={"new_var": 1})
        assert "new-var" in api.namespace.names

    def test_complete_builtin(self):
        api = API()
        completions = api.complete("prin")
        assert "print" in completions

    def test_complete_attribute(self):
        api = API()
        completions = api.complete("print.")
        assert "print.__call__" in completions

    def test_complete_attribute_with_prefix(self):
        api = API()
        completions = api.complete("print.__c")
        assert "print.__call__" in completions
        assert "print.__class__" in completions

    def test_complete_empty(self):
        api = API()
        completions = api.complete("")
        assert len(completions) > 0

    def test_complete_nonexistent(self):
        api = API()
        completions = api.complete("xyznonexistent")
        assert len(completions) == 0

    def test_complete_with_macros(self):
        macros = {"my-macro": lambda: None, "another-macro": lambda: None}
        api = API(globals_={"__macro_namespace": macros})
        completions = api.complete("my-")
        assert "my-macro" in completions

    def test_annotate_function(self):
        api = API()
        ann = api.annotate("print")
        assert ann == "<function print>"

    def test_annotate_class(self):
        class TestClass:
            pass
        api = API(locals_=locals())
        ann = api.annotate("TestClass")
        assert ann == "<class TestClass>"

    def test_annotate_module(self):
        import itertools
        api = API(locals_=locals())
        ann = api.annotate("itertools")
        assert ann == "<module itertools>"

    def test_annotate_instance(self):
        my_var = 42
        api = API(locals_=locals())
        ann = api.annotate("my_var")
        assert ann == "<instance my-var>"

    def test_docs_function(self):
        api = API()
        docs = api.docs("print")
        assert "print:" in docs

    def test_docs_module(self):
        import itertools
        api = API(locals_=locals())
        docs = api.docs("itertools")
        assert len(docs) > 0

    def test_full_docs(self):
        def documented_func():
            """First line.

            More details.
            """
            pass
        api = API(locals_=locals())
        full = api.full_docs("documented_func")
        assert "First line" in full
        assert "More details" in full

    def test_caching(self):
        api = API()
        # First completion
        c1 = api.complete("print.")
        # Second completion with same prefix should use cache
        c2 = api.complete("print.__c")

        assert len(c2) < len(c1)
        assert all(c.startswith("print.__c") for c in c2)
