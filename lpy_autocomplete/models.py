"""Implements Namespace-dependent methods and structures for lpy_autocomplete."""

from typing import Any, Callable, Dict, Optional, Tuple

from .utils import (
    allkeys,
    butlast,
    chain,
    distinct,
    first,
    flip,
    last,
    mangle,
    unmangle,
)


class Namespace:
    """Represents the execution namespace for completion."""

    def __init__(
        self,
        globals_: Optional[Dict] = None,
        locals_: Optional[Dict] = None,
        macros_: Optional[Dict[str, Callable]] = None,
    ):
        # Components
        self.globals = globals_ if globals_ is not None else globals()
        self.locals = locals_ if locals_ is not None else locals()

        # Macros are stored in __macro_namespace in lispython
        if macros_ is not None:
            self.macros = {unmangle(k): v for k, v in macros_.items()}
        else:
            # Try to get from globals
            macro_ns = self.globals.get("__macro_namespace", {})
            self.macros = {unmangle(k): v for k, v in macro_ns.items()}

        # Collected names
        self.names = self._collect_names()

    @staticmethod
    def _to_names(key: Any) -> str:
        """Convert keys (strs, functions, modules...) to names."""
        if isinstance(key, str):
            return unmangle(key)
        return unmangle(key.__name__)

    def _collect_names(self) -> Tuple[str, ...]:
        """Collect all names from all places."""
        all_keys = chain(
            allkeys(self.globals),
            allkeys(self.locals),
            self.macros.keys(),
        )
        return tuple(distinct(map(self._to_names, all_keys)))

    def eval(self, mangled_symbol: str) -> Any:
        """Evaluate mangled_symbol within the Namespace."""
        # Short circuit common case (completing without "." present)
        if not mangled_symbol:
            return None

        try:
            return eval(mangled_symbol, self.globals)
        except NameError:
            try:
                return eval(mangled_symbol, self.locals)
            except Exception:
                return None
        except Exception:
            return None


class Candidate:
    """Represents a completion candidate."""

    def __init__(self, symbol: str, namespace: Optional[Namespace] = None):
        self.symbol = unmangle(symbol)
        self.mangled = mangle(symbol)
        self.namespace = namespace if namespace is not None else Namespace()

    def __str__(self) -> str:
        return self.symbol

    def __repr__(self) -> str:
        return f"Candidate<symbol={self.symbol}>"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Candidate):
            return self.symbol == other.symbol
        return False

    def __bool__(self) -> bool:
        return bool(self.symbol)

    def macro(self) -> Optional[Callable]:
        """Is candidate a macro? Return it if so."""
        return self.namespace.macros.get(self.symbol)

    def evaled(self) -> Any:
        """Is candidate evaluatable? Return it if so."""
        try:
            return self.namespace.eval(self.mangled)
        except Exception:
            return None

    def get_obj(self) -> Any:
        """Get object for underlying candidate."""
        return self.macro() or self.evaled()

    def attributes(self) -> Optional[Tuple[str, ...]]:
        """Return attributes for obj if they exist."""
        obj = self.evaled()
        if obj is not None:
            return tuple(unmangle(attr) for attr in dir(obj))
        return None

    @staticmethod
    def _translate_class(klass: str) -> str:
        """Return annotation given a name of a class."""
        if klass in ("function", "builtin_function_or_method"):
            return "function"
        elif klass == "type":
            return "class"
        elif klass == "module":
            return "module"
        else:
            return "instance"

    def annotate(self) -> str:
        """Return annotation for a candidate."""
        obj = self.evaled()
        obj_exists = obj is not None

        if obj_exists:
            annotation = self._translate_class(obj.__class__.__name__)
        elif self.macro():
            annotation = "macro"
        else:
            annotation = "unknown"

        return f"<{annotation} {self}>"


class Prefix:
    """A completion prefix."""

    def __init__(self, prefix: str, namespace: Optional[Namespace] = None):
        self.prefix = prefix
        self.namespace = namespace if namespace is not None else Namespace()

        self.candidate = self._prefix_to_candidate(prefix, self.namespace)
        self.attr_prefix = self._prefix_to_attr_prefix(prefix)

        self.completions: Tuple[str, ...] = tuple()

    def __repr__(self) -> str:
        return f"Prefix<prefix={self.prefix}>"

    @staticmethod
    def _prefix_to_candidate(prefix: str, namespace: Namespace) -> Candidate:
        """Extract candidate from prefix (everything before last dot)."""
        parts = prefix.split(".")
        candidate_str = ".".join(butlast(parts))
        return Candidate(candidate_str, namespace=namespace)

    @staticmethod
    def _prefix_to_attr_prefix(prefix: str) -> str:
        """Get prefix as str of everything after last dot."""
        return unmangle(last(prefix.split(".")))

    @property
    def has_attr(self) -> bool:
        """Does prefix reference an attr?"""
        return "." in self.prefix

    @property
    def has_obj(self) -> bool:
        """Is the prefix's candidate an object?"""
        return bool(self.candidate.get_obj())

    def complete_candidate(self, completion: str) -> str:
        """Given a potential string completion, attach to candidate."""
        if self.candidate:
            return f"{self.candidate}.{completion}"
        return completion

    def complete(self, cached_prefix: Optional["Prefix"] = None) -> Tuple[str, ...]:
        """Get candidates for a given Prefix."""
        # Short circuit case: "1+nonsense.real-attr" eg. "foo.__prin"
        if self.has_attr and not self.has_obj:
            self.completions = tuple()
            return self.completions

        # Complete on relevant top-level names or candidate-dependent names
        if cached_prefix and self.candidate == cached_prefix.candidate:
            self.completions = cached_prefix.completions
        else:
            attrs = self.candidate.attributes()
            self.completions = attrs if attrs else self.namespace.names

        # Filter by prefix and attach to candidate
        filtered = filter(
            lambda c: c.startswith(self.attr_prefix),
            self.completions,
        )
        return tuple(map(self.complete_candidate, filtered))
