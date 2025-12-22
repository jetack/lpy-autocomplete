# lpy-autocomplete

Autocompletion and introspection tools for [lispython](https://github.com/jetack/lispython).

## Installation

```bash
pip install lpy-autocomplete
```

## Usage

```python
from lpy_autocomplete import API

api = API()
api.set_namespace(globals_=globals())  # macros found automatically from __macro_namespace

# Completion
api.complete("pr")          # -> ("print", ...)
api.complete("print.")      # -> ("print.__call__", "print.__str__", ...)

# Documentation
api.docs("itertools")       # -> "Functional tools..."

# Annotation
api.annotate("itertools")   # -> "<module itertools>"
```

## Development

```bash
uv sync --extra dev
uv run -m pytest tests/
```

## License

MIT
