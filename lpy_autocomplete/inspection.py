"""Implements argspec inspection and formatting for various types."""

import inspect
from functools import reduce
from itertools import repeat
from typing import Any, List, Optional, Tuple

from .utils import drop_last, first, is_none, remove, unmangle


class Parameter:
    """Represents a function parameter."""

    def __init__(self, symbol: str, default: Any = None):
        self.symbol = unmangle(symbol)
        self.default = default

    def __str__(self) -> str:
        if self.default is None:
            return self.symbol
        return f"[{self.symbol} {self.default}]"


class Signature:
    """Represents a function signature in lispy format."""

    def __init__(self, func):
        try:
            argspec = inspect.getfullargspec(func)
        except TypeError:
            raise TypeError("Unsupported callable for Signature.")

        self.func = func
        self.args = self._args_from(argspec)
        self.defaults = self._defaults_from(argspec)
        self.kwargs = self._kwargs_from(argspec)
        self.varargs = self._varargs_from(argspec)
        self.varkw = self._varkw_from(argspec)

    @staticmethod
    def _parametrize(
        symbols: Optional[List[str]], defaults: Optional[List] = None
    ) -> Optional[Tuple[Parameter, ...]]:
        """Construct many Parameters for symbols with possibly defaults."""
        if not symbols:
            return None
        defaults = defaults if defaults else list(repeat(None))
        return tuple(Parameter(s, d) for s, d in zip(symbols, defaults))

    @classmethod
    def _args_from(cls, argspec) -> Optional[Tuple[Parameter, ...]]:
        """Extract args without defined defaults from argspec."""
        num_defaults = len(argspec.defaults) if argspec.defaults else 0
        symbols = drop_last(num_defaults, argspec.args)
        return cls._parametrize(symbols)

    @classmethod
    def _defaults_from(cls, argspec) -> Optional[Tuple[Parameter, ...]]:
        """Extract args with defined defaults from argspec."""
        args_without_defaults = cls._args_from(argspec)
        num_without = len(args_without_defaults) if args_without_defaults else 0
        symbols = argspec.args[num_without:]
        return cls._parametrize(symbols, argspec.defaults)

    @classmethod
    def _kwargsonly_from(cls, argspec) -> Optional[Tuple[Parameter, ...]]:
        """Extract kwargs without defined defaults from argspec."""
        kwargs_with_defaults = set(
            (argspec.kwonlydefaults or {}).keys()
        )
        symbols = [
            kw for kw in argspec.kwonlyargs if kw not in kwargs_with_defaults
        ]
        return cls._parametrize(symbols)

    @classmethod
    def _kwonlydefaults_from(cls, argspec) -> Optional[Tuple[Parameter, ...]]:
        """Extract kwargs with defined defaults from argspec."""
        if not argspec.kwonlydefaults:
            return None
        symbols, defaults = zip(*argspec.kwonlydefaults.items())
        return cls._parametrize(list(symbols), list(defaults))

    @classmethod
    def _kwargs_from(cls, argspec) -> Tuple[Parameter, ...]:
        """Chain kwargs with and without defaults."""
        kwargsonly = cls._kwargsonly_from(argspec) or ()
        kwonlydefaults = cls._kwonlydefaults_from(argspec) or ()
        return tuple(p for p in (*kwargsonly, *kwonlydefaults) if p is not None)

    @staticmethod
    def _varargs_from(argspec) -> Optional[List[str]]:
        if argspec.varargs:
            return [unmangle(argspec.varargs)]
        return None

    @staticmethod
    def _varkw_from(argspec) -> Optional[List[str]]:
        if argspec.varkw:
            return [unmangle(argspec.varkw)]
        return None

    @staticmethod
    def _format_args(args: Optional[Tuple], opener: Optional[str]) -> str:
        if not args:
            return ""
        args_str = " ".join(str(a) for a in args)
        opener_str = f"{opener} " if opener else ""
        return opener_str + args_str

    @classmethod
    def _acc_lispy_repr(cls, acc: str, args_opener: Tuple) -> str:
        args, opener = args_opener
        delim = " " if acc and args else ""
        return acc + delim + cls._format_args(args, opener)

    @property
    def _arg_opener_pairs(self) -> List[Tuple]:
        return [
            (self.args, None),
            (self.defaults, "&optional"),
            (self.varargs, "*"),
            (self.varkw, "**"),
            (self.kwargs, "&kwonly"),
        ]

    def __str__(self) -> str:
        return reduce(self._acc_lispy_repr, self._arg_opener_pairs, "")


def _split_docs(docs: str) -> Tuple[str, str, str]:
    """Partition docs string into pre/-/post-args strings."""
    arg_start = docs.index("(") + 1
    arg_end = docs.index(")")
    return (docs[:arg_start], docs[arg_start:arg_end], docs[arg_end:])


def _argstring_to_param(arg_string: str) -> Parameter:
    """Convert an arg string to a Parameter."""
    if "=" not in arg_string:
        return Parameter(arg_string)

    arg_name, _, default = arg_string.partition("=")
    if default == "None":
        return Parameter(arg_name)
    return Parameter(arg_name, default)


def _optional_arg_idx(args_strings: List[str]) -> Optional[int]:
    """First idx of an arg with a default in list of args strings."""
    for idx, arg in enumerate(args_strings):
        if "=" in arg:
            return idx
    return None


def _insert_optional(args: List[str]) -> List[str]:
    """Insert &optional into list of args strings."""
    optional_idx = _optional_arg_idx(args)
    if optional_idx is not None:
        args.insert(optional_idx, "&optional")
    return args


def builtin_docs_to_lispy_docs(docs: str) -> str:
    """Convert built-in-styled docs string into a lispy-format."""
    # Check if docs is non-standard
    if "(" not in docs or ")" not in docs:
        return docs

    replacements = [
        ("...", "* args"),
        ("*args", "* args"),
        ("**kwargs", "** kwargs"),
        ("\n", "newline"),
        ("-->", "- return"),
    ]

    pre_args, _, post_args = docs.partition("(")

    # Format before args and perform unconditional conversions
    formatted = f"{pre_args}: ({post_args}"
    for old, new in replacements:
        formatted = formatted.replace(old, new)

    pre_args, args, post_args = _split_docs(formatted)

    # Format and reorder args and reconstruct the string
    args_list = [a.strip() for a in args.split(",")]
    args_list = _insert_optional(args_list)
    args_formatted = " ".join(str(_argstring_to_param(a)) for a in args_list)

    return pre_args + args_formatted + post_args


class Inspect:
    """High-level introspection for objects."""

    def __init__(self, obj: Any):
        self.obj = obj

    @property
    def _docs_first_line(self) -> str:
        if self.obj.__doc__:
            return self.obj.__doc__.splitlines()[0]
        return ""

    @property
    def _docs_rest_lines(self) -> str:
        if self.obj.__doc__:
            lines = self.obj.__doc__.splitlines()[1:]
            return "\n".join(lines)
        return ""

    @property
    def _args_docs_delim(self) -> str:
        if self.obj.__doc__:
            return " - "
        return ""

    def _cut_obj_name_maybe(self, docs: str) -> str:
        if self.is_class or self.is_method_wrapper:
            return docs.replace("self ", "").replace("self", "")
        return docs

    def _cut_method_wrapper_maybe(self, docs: str) -> str:
        if self.is_method_wrapper:
            idx = docs.index(":")
            return "method-wrapper" + docs[idx:]
        return docs

    def _format_docs(self, docs: str) -> str:
        docs = self._cut_obj_name_maybe(docs)
        docs = self._cut_method_wrapper_maybe(docs)
        return docs

    @property
    def obj_name(self) -> str:
        return unmangle(self.obj.__name__)

    @property
    def is_lambda(self) -> bool:
        """Is object a lambda?"""
        return self.obj_name == "<lambda>"

    @property
    def is_class(self) -> bool:
        """Is object a class?"""
        return inspect.isclass(self.obj)

    @property
    def is_method_wrapper(self) -> bool:
        """Is object of type 'method-wrapper'?"""
        return isinstance(self.obj, type(print.__str__))

    @property
    def is_compile_table(self) -> bool:
        """Is object a compile table construct?"""
        return self._docs_first_line == "Built-in immutable sequence."

    def signature(self) -> Optional[Signature]:
        """Return object's signature if it exists."""
        try:
            return Signature(self.obj)
        except TypeError:
            return None

    def docs(self) -> str:
        """Formatted first line docs for object."""
        sig = self.signature()

        if sig and not self.is_compile_table:
            formatted = (
                f"{self.obj_name}: ({sig})"
                f"{self._args_docs_delim}{self._docs_first_line}"
            )
        elif self.is_compile_table:
            formatted = "Compile table"
        else:
            formatted = builtin_docs_to_lispy_docs(self._docs_first_line)

        return self._format_docs(formatted)

    def full_docs(self) -> str:
        """Formatted full docs for object."""
        if self.is_compile_table:
            return ""
        if self._docs_rest_lines:
            return f"{self.docs()}\n\n{self._docs_rest_lines}"
        return self.docs()
