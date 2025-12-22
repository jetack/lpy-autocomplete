"""Tests for lpy_autocomplete.inspection"""

import pytest
from lpy_autocomplete.inspection import (
    Parameter,
    Signature,
    Inspect,
    builtin_docs_to_lispy_docs,
)


class TestParameter:
    """Tests for Parameter class."""

    def test_parameter_without_default(self):
        p = Parameter("arg")
        assert str(p) == "arg"

    def test_parameter_with_default(self):
        p = Parameter("arg", 42)
        assert str(p) == "[arg 42]"

    def test_parameter_unmangled(self):
        p = Parameter("my_arg")
        assert p.symbol == "my-arg"


class TestSignature:
    """Tests for Signature class."""

    def test_no_args(self):
        def func():
            pass
        sig = Signature(func)
        assert str(sig) == ""

    def test_single_arg(self):
        def func(a):
            pass
        sig = Signature(func)
        assert str(sig) == "a"

    def test_multiple_args(self):
        def func(a, b, c):
            pass
        sig = Signature(func)
        assert str(sig) == "a b c"

    def test_with_defaults(self):
        def func(a, b=1, c=2):
            pass
        sig = Signature(func)
        assert str(sig) == "a &optional [b 1] [c 2]"

    def test_only_defaults(self):
        def func(a=1, b=2):
            pass
        sig = Signature(func)
        assert str(sig) == "&optional [a 1] [b 2]"

    def test_with_varargs(self):
        def func(a, *args):
            pass
        sig = Signature(func)
        assert str(sig) == "a * args"

    def test_with_kwargs(self):
        def func(a, **kwargs):
            pass
        sig = Signature(func)
        assert str(sig) == "a ** kwargs"

    def test_with_kwonly(self):
        def func(a, *, b, c=1):
            pass
        sig = Signature(func)
        assert "&kwonly" in str(sig)
        assert "b" in str(sig)
        assert "[c 1]" in str(sig)

    def test_maximal(self):
        def func(a, b, c=0, d=1, *args, e, f=2, **kwargs):
            pass
        sig = Signature(func)
        sig_str = str(sig)
        assert "a b" in sig_str
        assert "&optional" in sig_str
        assert "[c 0]" in sig_str
        assert "* args" in sig_str
        assert "** kwargs" in sig_str
        assert "&kwonly" in sig_str

    def test_unsupported_callable(self):
        with pytest.raises(TypeError):
            Signature(42)


class TestBuiltinDocsToLispyDocs:
    """Tests for builtin_docs_to_lispy_docs function."""

    def test_basic_conversion(self):
        result = builtin_docs_to_lispy_docs("func(a, b) - description")
        assert "func:" in result
        assert "a b" in result
        assert "description" in result

    def test_with_optional(self):
        result = builtin_docs_to_lispy_docs("func(a, b=1) - desc")
        assert "&optional" in result
        assert "[b 1]" in result

    def test_with_none_default(self):
        result = builtin_docs_to_lispy_docs("func(a, b=None) - desc")
        assert "&optional" in result
        assert "b" in result
        # None defaults should just show the arg name without value
        assert "[b None]" not in result

    def test_with_ellipsis(self):
        result = builtin_docs_to_lispy_docs("func(a, ...) - desc")
        assert "* args" in result

    def test_with_varargs(self):
        result = builtin_docs_to_lispy_docs("func(a, *args) - desc")
        assert "* args" in result

    def test_with_kwargs(self):
        result = builtin_docs_to_lispy_docs("func(a, **kwargs) - desc")
        assert "** kwargs" in result

    def test_arrow_conversion(self):
        result = builtin_docs_to_lispy_docs("func(a) --> return value")
        assert "- return" in result

    def test_nonstandard_format(self):
        # Should return unchanged if no parens
        result = builtin_docs_to_lispy_docs("foo[ok] bar")
        assert result == "foo[ok] bar"

    def test_no_args(self):
        result = builtin_docs_to_lispy_docs("func() - desc")
        assert "func:" in result
        assert "desc" in result


class TestInspect:
    """Tests for Inspect class."""

    def test_obj_name(self):
        def my_func():
            pass
        insp = Inspect(my_func)
        assert insp.obj_name == "my-func"

    def test_obj_name_with_underscores(self):
        def func_with_underscores():
            pass
        insp = Inspect(func_with_underscores)
        assert insp.obj_name == "func-with-underscores"

    def test_is_lambda(self):
        insp = Inspect(lambda: None)
        assert insp.is_lambda is True

    def test_is_not_lambda(self):
        def func():
            pass
        insp = Inspect(func)
        assert insp.is_lambda is False

    def test_is_class(self):
        class MyClass:
            pass
        insp = Inspect(MyClass)
        assert insp.is_class is True

    def test_is_not_class(self):
        def func():
            pass
        insp = Inspect(func)
        assert insp.is_class is False

    def test_is_method_wrapper(self):
        insp = Inspect(print.__str__)
        assert insp.is_method_wrapper is True

    def test_signature(self):
        def func(a, b=1):
            pass
        insp = Inspect(func)
        sig = insp.signature()
        assert sig is not None
        assert "a" in str(sig)

    def test_signature_builtin(self):
        insp = Inspect(print)  # built-in now has signature via inspect.signature
        sig = insp.signature()
        assert sig is not None
        assert "args" in str(sig)

    def test_docs_function(self):
        def my_func(a, b):
            """A test function."""
            pass
        insp = Inspect(my_func)
        docs = insp.docs()
        assert "my-func:" in docs
        assert "a b" in docs
        assert "A test function" in docs

    def test_docs_class(self):
        class MyClass:
            """A test class."""
            def __init__(self, x, y):
                pass
        insp = Inspect(MyClass)
        docs = insp.docs()
        assert "MyClass:" in docs
        assert "x y" in docs
        # self should be removed
        assert "self" not in docs

    def test_docs_module(self):
        import itertools
        insp = Inspect(itertools)
        docs = insp.docs()
        assert len(docs) > 0

    def test_docs_builtin(self):
        insp = Inspect(print)
        docs = insp.docs()
        assert "print:" in docs

    def test_full_docs(self):
        def my_func():
            """First line.

            More details here.
            """
            pass
        insp = Inspect(my_func)
        full = insp.full_docs()
        assert "First line" in full
        assert "More details" in full

    def test_full_docs_no_rest(self):
        def my_func():
            """Just one line."""
            pass
        insp = Inspect(my_func)
        full = insp.full_docs()
        assert full == insp.docs()

    def test_cut_self_from_class(self):
        class Foo:
            def __init__(self, x):
                pass
        insp = Inspect(Foo)
        docs = insp.docs()
        assert "self" not in docs
