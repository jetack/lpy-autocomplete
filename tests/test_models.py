"""Tests for lpy_autocomplete.models"""

import pytest
from lpy_autocomplete.models import Namespace, Candidate, Prefix


class TestNamespace:
    """Tests for Namespace class."""

    def test_namespace_has_builtins(self):
        ns = Namespace()
        assert "print" in ns.names
        assert "len" in ns.names

    def test_namespace_with_locals(self):
        x = 42
        def foo():
            pass
        ns = Namespace(locals_=locals())
        assert "x" in ns.names
        assert "foo" in ns.names

    def test_namespace_with_macros(self):
        macros = {"my_macro": lambda x: x, "another_macro": lambda: None}
        globals_with_macros = {"__macro_namespace": macros}
        ns = Namespace(globals_=globals_with_macros)
        assert "my-macro" in ns.macros
        assert "another-macro" in ns.macros

    def test_namespace_eval_builtin(self):
        ns = Namespace()
        assert ns.eval("print") is print
        assert ns.eval("len") is len

    def test_namespace_eval_nonexistent(self):
        ns = Namespace()
        assert ns.eval("nonexistent_symbol_xyz") is None

    def test_namespace_eval_empty(self):
        ns = Namespace()
        assert ns.eval("") is None

    def test_namespace_eval_locals(self):
        my_var = "hello"
        ns = Namespace(locals_=locals())
        assert ns.eval("my_var") == "hello"


class TestCandidate:
    """Tests for Candidate class."""

    def test_candidate_symbol_unmangled(self):
        c = Candidate("some_func")
        assert c.symbol == "some-func"

    def test_candidate_mangled(self):
        c = Candidate("some-func")
        assert c.mangled == "some_func"

    def test_candidate_str(self):
        c = Candidate("print")
        assert str(c) == "print"

    def test_candidate_bool_true(self):
        c = Candidate("print")
        assert bool(c) is True

    def test_candidate_bool_false(self):
        c = Candidate("")
        assert bool(c) is False

    def test_candidate_evaled_builtin(self):
        c = Candidate("print")
        assert c.evaled() is print

    def test_candidate_evaled_nonexistent(self):
        c = Candidate("doesnt_exist_xyz")
        assert c.evaled() is None

    def test_candidate_evaled_with_locals(self):
        my_obj = {"key": "value"}
        ns = Namespace(locals_=locals())
        c = Candidate("my_obj", namespace=ns)
        assert c.evaled() == {"key": "value"}

    def test_candidate_attributes_builtin(self):
        c = Candidate("print")
        attrs = c.attributes()
        assert attrs is not None
        assert "__call__" in attrs
        assert "__str__" in attrs

    def test_candidate_attributes_nonexistent(self):
        c = Candidate("doesnt_exist")
        assert c.attributes() is None

    def test_candidate_attributes_module(self):
        import builtins
        ns = Namespace(locals_=locals())
        c = Candidate("builtins", namespace=ns)
        attrs = c.attributes()
        assert attrs is not None
        assert "print" in attrs
        assert "len" in attrs

    def test_candidate_macro(self):
        macros = {"my-macro": lambda x: x * 2}
        ns = Namespace(globals_={"__macro_namespace": macros})
        c = Candidate("my-macro", namespace=ns)
        assert c.macro() is not None

    def test_candidate_macro_not_found(self):
        c = Candidate("not-a-macro")
        assert c.macro() is None

    def test_candidate_get_obj_evaled(self):
        c = Candidate("print")
        assert c.get_obj() is print

    def test_candidate_get_obj_macro(self):
        macro_fn = lambda x: x
        macros = {"test-macro": macro_fn}
        ns = Namespace(globals_={"__macro_namespace": macros})
        c = Candidate("test-macro", namespace=ns)
        assert c.get_obj() is macro_fn

    def test_annotate_function(self):
        c = Candidate("print")
        assert c.annotate() == "<function print>"

    def test_annotate_class(self):
        class MyClass:
            pass
        ns = Namespace(locals_=locals())
        c = Candidate("MyClass", namespace=ns)
        assert c.annotate() == "<class MyClass>"

    def test_annotate_module(self):
        import itertools
        ns = Namespace(locals_=locals())
        c = Candidate("itertools", namespace=ns)
        assert c.annotate() == "<module itertools>"

    def test_annotate_instance(self):
        xx = 42
        ns = Namespace(locals_=locals())
        c = Candidate("xx", namespace=ns)
        assert c.annotate() == "<instance xx>"

    def test_annotate_macro(self):
        macros = {"my-macro": lambda: None}
        ns = Namespace(globals_={"__macro_namespace": macros})
        c = Candidate("my-macro", namespace=ns)
        assert c.annotate() == "<macro my-macro>"

    def test_annotate_unknown(self):
        c = Candidate("nonexistent_xyz")
        assert c.annotate() == "<unknown nonexistent-xyz>"


class TestPrefix:
    """Tests for Prefix class."""

    def test_prefix_simple(self):
        p = Prefix("obj")
        assert p.candidate.symbol == ""
        assert p.attr_prefix == "obj"

    def test_prefix_with_dot(self):
        p = Prefix("obj.attr")
        assert p.candidate.symbol == "obj"
        assert p.attr_prefix == "attr"

    def test_prefix_trailing_dot(self):
        p = Prefix("obj.")
        assert p.candidate.symbol == "obj"
        assert p.attr_prefix == ""

    def test_prefix_nested(self):
        p = Prefix("obj.attr.")
        assert p.candidate.symbol == "obj.attr"
        assert p.attr_prefix == ""

    def test_prefix_empty(self):
        p = Prefix("")
        assert p.candidate.symbol == ""
        assert p.attr_prefix == ""

    def test_has_attr_true(self):
        p = Prefix("obj.attr")
        assert p.has_attr is True

    def test_has_attr_false(self):
        p = Prefix("obj")
        assert p.has_attr is False

    def test_complete_builtins(self):
        p = Prefix("prin")
        completions = p.complete()
        assert "print" in completions

    def test_complete_builtins_prefix(self):
        p = Prefix("Ar")
        completions = p.complete()
        assert "ArithmeticError" in completions

    def test_complete_method_attributes(self):
        p = Prefix("print.")
        completions = p.complete()
        assert "print.__call__" in completions

    def test_complete_method_attributes_with_prefix(self):
        p = Prefix("print.__c")
        completions = p.complete()
        assert "print.__call__" in completions
        assert "print.__class__" in completions

    def test_complete_nonexistent_candidate(self):
        p = Prefix("gibberish_xyz.")
        completions = p.complete()
        assert completions == ()

    def test_complete_module(self):
        import itertools
        ns = Namespace(locals_=locals())
        p = Prefix("itertools.t", namespace=ns)
        completions = p.complete()
        assert "itertools.tee" in completions

    def test_complete_candidate_attachment(self):
        p = Prefix("print.__c")
        completions = p.complete()
        for c in completions:
            assert c.startswith("print.")

    def test_complete_caching(self):
        p1 = Prefix("print.")
        completions1 = p1.complete()

        p2 = Prefix("print.__c")
        completions2 = p2.complete(cached_prefix=p1)

        # Should use cached completions and filter
        assert len(completions2) < len(completions1)
        assert all("__c" in c or "__C" in c.upper() for c in completions2)
