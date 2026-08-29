"""Shared protobuf-to-Python identifier rules for generated models."""

from __future__ import annotations

import keyword
import re

_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_ACRONYM_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
_NON_IDENTIFIER = re.compile(r"\W")

# Pydantic and ABC class attributes cannot safely be shadowed by model fields.
# Keep this explicit so generation is deterministic across supported Pydantic
# patch releases. Both the generator and runtime descriptor verifier call the
# same function from this module.
_RESERVED_MODEL_NAMES = frozenset(
    {
        "construct",
        "copy",
        "dict",
        "from_orm",
        "json",
        "model_computed_fields",
        "model_config",
        "model_construct",
        "model_copy",
        "model_dump",
        "model_dump_json",
        "model_extra",
        "model_fields",
        "model_fields_set",
        "model_json_schema",
        "model_parametrized_name",
        "model_post_init",
        "model_rebuild",
        "model_validate",
        "model_validate_json",
        "model_validate_strings",
        "parse_file",
        "parse_obj",
        "parse_raw",
        "register",
        "schema",
        "schema_json",
        "update_forward_refs",
        "validate",
    }
)


def python_field_name(protobuf_name: str) -> str:
    """Return the stable public Pydantic field name for a protobuf field."""

    name = _CAMEL_BOUNDARY.sub(r"\1_\2", protobuf_name)
    name = _ACRONYM_BOUNDARY.sub(r"\1_\2", name)
    name = _NON_IDENTIFIER.sub("_", name).lower()
    if not name or name[0].isdigit():
        name = f"field_{name}"
    if keyword.iskeyword(name) or name in _RESERVED_MODEL_NAMES:
        name = f"{name}_"
    return name
