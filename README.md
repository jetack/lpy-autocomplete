# lpy-autocomplete

Autocompletion and introspection tools for [lispython](https://github.com/jethack23/lispy).

## Installation

```bash
pip install lpy-autocomplete
```

## Usage

```python
from lpy_autocomplete import API

api = API()
api.set_namespace(globals_=globals(), macros_=__macro_namespace)

# Completion
api.complete("pr")          # -> ("print", ...)
api.complete("print.")      # -> ("print.__call__", "print.__str__", ...)

# Documentation
api.docs("itertools")       # -> "Functional tools..."

# Annotation
api.annotate("itertools")   # -> "<module itertools>"
```

## License

MIT
