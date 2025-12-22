"""Expose lpy_autocomplete's API for IDE and metaprogramming use-cases."""

from typing import Callable, Dict, Optional, Tuple

from .inspection import Inspect
from .models import Candidate, Namespace, Prefix


class API:
    """Main API for lispython autocompletion and introspection.

    Usage:
        api = API()
        api.set_namespace(globals_=globals(), macros_=__macro_namespace)

        # Completion
        api.complete("pr")          # -> ("print", ...)
        api.complete("print.")      # -> ("print.__call__", "print.__str__", ...)

        # Documentation
        api.docs("itertools")       # -> "Functional tools..."
        api.docs("Foo")             # -> "Foo: (x y) - A class"

        # Annotation
        api.annotate("itertools")   # -> "<module itertools>"
    """

    def __init__(
        self,
        globals_: Optional[Dict] = None,
        locals_: Optional[Dict] = None,
        macros_: Optional[Dict[str, Callable]] = None,
    ):
        self.set_namespace(globals_, locals_, macros_)
        self._cached_prefix: Optional[Prefix] = None

    def set_namespace(
        self,
        globals_: Optional[Dict] = None,
        locals_: Optional[Dict] = None,
        macros_: Optional[Dict[str, Callable]] = None,
    ) -> None:
        """Rebuild namespace for possibly given globals_, locals_, and macros_.

        Typically, the values passed are:
            globals_ -> globals()
            locals_  -> locals()
            macros_  -> __macro_namespace
        """
        self.namespace = Namespace(globals_, locals_, macros_)

    def complete(self, prefix_str: str) -> Tuple[str, ...]:
        """Get completions for a prefix string."""
        cached_prefix = self._cached_prefix
        prefix = Prefix(prefix_str, namespace=self.namespace)
        self._cached_prefix = prefix

        return prefix.complete(cached_prefix=cached_prefix)

    def annotate(self, candidate_str: str) -> str:
        """Annotate a candidate string."""
        candidate = Candidate(candidate_str, namespace=self.namespace)
        return candidate.annotate()

    def _inspect(self, candidate_str: str) -> Inspect:
        """Inspect a candidate string."""
        candidate = Candidate(candidate_str, namespace=self.namespace)
        obj = candidate.get_obj()
        return Inspect(obj)

    def docs(self, candidate_str: str) -> str:
        """Get docstring for a candidate string."""
        return self._inspect(candidate_str).docs()

    def full_docs(self, candidate_str: str) -> str:
        """Get full documentation for a candidate string."""
        return self._inspect(candidate_str).full_docs()
