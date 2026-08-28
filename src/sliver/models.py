"""Descriptor-driven Pydantic models for Sliver's protobuf API.

The classes in this module are created from the descriptors in ``sliver.pb`` at
import time.  They deliberately keep protobuf generation and application models
separate: generated ``*_pb2.py`` files remain the wire implementation, while
the models exposed here provide validation, ergonomic field names, and normal
Python serialization.
"""

from __future__ import annotations

import importlib
import keyword
import pkgutil
import re
from collections.abc import Mapping
from enum import IntEnum
from types import MappingProxyType
from typing import Annotated, Any, ClassVar, ForwardRef, Optional, TypeVar, cast

from google.protobuf import message_factory
from google.protobuf.descriptor import Descriptor, EnumDescriptor, FieldDescriptor
from google.protobuf.message import Message
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    create_model,
    model_validator,
)

_ModelT = TypeVar("_ModelT", bound="ProtobufModel")


class ProtobufEnum(IntEnum):
    """Base class for enums derived from protobuf enum descriptors.

    Proto3 enums are open, so unknown integer values are represented by a
    synthetic enum member rather than being rejected during validation.
    """

    __protobuf_descriptor__: ClassVar[EnumDescriptor | None] = None

    @classmethod
    def _missing_(cls, value: object) -> ProtobufEnum | None:
        descriptor = cls.__protobuf_descriptor__
        syntax = getattr(descriptor.file, "syntax", "proto3") if descriptor else None
        if descriptor is None or syntax == "proto2" or not isinstance(value, int):
            return None

        # Open enums may receive values added by a newer server.  Caching the
        # pseudo-member also makes repeated validation preserve identity.
        member = int.__new__(cls, value)
        member._name_ = f"UNRECOGNIZED_{value}"
        member._value_ = value
        cls._value2member_map_[value] = member
        return member


class ProtobufModel(BaseModel):
    """Base class shared by every descriptor-derived Pydantic model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        protected_namespaces=(),
        ser_json_bytes="base64",
        val_json_bytes="base64",
        validate_assignment=True,
    )

    __protobuf_descriptor__: ClassVar[Descriptor | None] = None
    __protobuf_class__: ClassVar[type[Message] | None] = None
    __protobuf_to_python_fields__: ClassVar[Mapping[str, str]] = MappingProxyType({})

    @classmethod
    def from_protobuf(cls: type[_ModelT], message: Message) -> _ModelT:
        """Build this Pydantic model from its corresponding protobuf message."""

        expected = cls.__protobuf_class__
        if expected is None or not isinstance(message, expected):
            expected_name = (
                cls.__protobuf_descriptor__.full_name
                if cls.__protobuf_descriptor__ is not None
                else cls.__name__
            )
            actual_name = getattr(
                getattr(message, "DESCRIPTOR", None), "full_name", None
            )
            raise TypeError(
                f"{cls.__name__}.from_protobuf() expected {expected_name!r}, "
                f"got {actual_name or type(message).__name__!r}"
            )
        return _model_from_protobuf(cls, message)

    def to_protobuf(self) -> Message:
        """Convert this model to a new generated protobuf message instance."""

        return _model_to_protobuf(self)

    @model_validator(mode="after")
    def _validate_oneofs(self) -> ProtobufModel:
        descriptor = self.__protobuf_descriptor__
        if descriptor is None:
            return self

        field_names = self.__protobuf_to_python_fields__
        for oneof in descriptor.oneofs:
            active = [
                field.name
                for field in oneof.fields
                if getattr(self, field_names[field.name]) is not None
            ]
            if len(active) > 1:
                joined = ", ".join(active)
                raise ValueError(
                    f"protobuf oneof {oneof.full_name!r} accepts at most one field; "
                    f"got {joined}"
                )
        return self


class ModelNamespace:
    """Read-only attribute namespace for one protobuf package's model types."""

    __slots__ = ("_members", "package")

    def __init__(self, package: str, members: dict[str, Any]) -> None:
        object.__setattr__(self, "package", package)
        object.__setattr__(self, "_members", members)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._members[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __dir__(self) -> list[str]:
        return sorted(self._members)

    def __repr__(self) -> str:
        return f"ModelNamespace(package={self.package!r})"

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("protobuf model namespaces are read-only")


_MODEL_REGISTRY: dict[str, type[ProtobufModel]] = {}
_MODEL_BY_DESCRIPTOR: dict[Descriptor, type[ProtobufModel]] = {}
_MODEL_BY_PROTOBUF_CLASS: dict[type[Message], type[ProtobufModel]] = {}
_ENUM_REGISTRY: dict[str, type[ProtobufEnum]] = {}
_ENUM_BY_DESCRIPTOR: dict[EnumDescriptor, type[ProtobufEnum]] = {}
_PACKAGE_MEMBERS: dict[str, dict[str, Any]] = {}
_PACKAGE_NAMESPACES: dict[str, ModelNamespace] = {}
_BUILDING: set[Descriptor] = set()
_FORWARD_NAMESPACE: dict[str, Any] = {}

# Public read-only views stay live if a caller registers a descriptor from a
# separate DescriptorPool through ``get_pydantic_model()``.
MODEL_REGISTRY: Mapping[str, type[ProtobufModel]] = MappingProxyType(_MODEL_REGISTRY)
MODEL_BY_DESCRIPTOR: Mapping[Descriptor, type[ProtobufModel]] = MappingProxyType(
    _MODEL_BY_DESCRIPTOR
)
MODEL_BY_PROTOBUF_CLASS: Mapping[type[Message], type[ProtobufModel]] = MappingProxyType(
    _MODEL_BY_PROTOBUF_CLASS
)
ENUM_REGISTRY: Mapping[str, type[ProtobufEnum]] = MappingProxyType(_ENUM_REGISTRY)
ENUM_BY_DESCRIPTOR: Mapping[EnumDescriptor, type[ProtobufEnum]] = MappingProxyType(
    _ENUM_BY_DESCRIPTOR
)
PACKAGE_NAMESPACES: Mapping[str, ModelNamespace] = MappingProxyType(_PACKAGE_NAMESPACES)


_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_ACRONYM_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
_NON_IDENTIFIER = re.compile(r"\W")


def _python_field_name(protobuf_name: str) -> str:
    name = _CAMEL_BOUNDARY.sub(r"\1_\2", protobuf_name)
    name = _ACRONYM_BOUNDARY.sub(r"\1_\2", name)
    name = _NON_IDENTIFIER.sub("_", name).lower()
    if not name or name[0].isdigit():
        name = f"field_{name}"
    if keyword.iskeyword(name) or hasattr(ProtobufModel, name):
        name = f"{name}_"
    return name


def _forward_name(descriptor: Descriptor) -> str:
    return "_protobuf_model_" + _NON_IDENTIFIER.sub("_", descriptor.full_name)


def _message_class(descriptor: Descriptor) -> type[Message]:
    get_message_class = getattr(message_factory, "GetMessageClass", None)
    if get_message_class is not None:
        return cast(type[Message], get_message_class(descriptor))

    # Compatibility with protobuf runtimes predating GetMessageClass().
    factory = message_factory.MessageFactory()
    return cast(type[Message], factory.GetPrototype(descriptor))


def _enum_model(enum_descriptor: EnumDescriptor) -> type[ProtobufEnum]:
    existing = _ENUM_BY_DESCRIPTOR.get(enum_descriptor)
    if existing is not None:
        return existing

    enum_model = cast(
        type[ProtobufEnum],
        IntEnum(
            enum_descriptor.name,
            {value.name: value.number for value in enum_descriptor.values},
            module=__name__,
            type=ProtobufEnum,
        ),
    )
    enum_model.__protobuf_descriptor__ = enum_descriptor
    enum_model.__doc__ = f"Pydantic enum for ``{enum_descriptor.full_name}``."
    _ENUM_BY_DESCRIPTOR[enum_descriptor] = enum_model
    _ENUM_REGISTRY[enum_descriptor.full_name] = enum_model
    _publish_package_member(enum_descriptor, enum_model)
    return enum_model


_SCALAR_TYPES: dict[int, type[Any]] = {
    FieldDescriptor.TYPE_DOUBLE: float,
    FieldDescriptor.TYPE_FLOAT: float,
    FieldDescriptor.TYPE_INT64: int,
    FieldDescriptor.TYPE_UINT64: int,
    FieldDescriptor.TYPE_INT32: int,
    FieldDescriptor.TYPE_FIXED64: int,
    FieldDescriptor.TYPE_FIXED32: int,
    FieldDescriptor.TYPE_BOOL: bool,
    FieldDescriptor.TYPE_STRING: str,
    FieldDescriptor.TYPE_BYTES: bytes,
    FieldDescriptor.TYPE_UINT32: int,
    FieldDescriptor.TYPE_SFIXED32: int,
    FieldDescriptor.TYPE_SFIXED64: int,
    FieldDescriptor.TYPE_SINT32: int,
    FieldDescriptor.TYPE_SINT64: int,
}

_INTEGER_BOUNDS: dict[int, tuple[int, int]] = {
    FieldDescriptor.TYPE_INT32: (-(2**31), (2**31) - 1),
    FieldDescriptor.TYPE_SINT32: (-(2**31), (2**31) - 1),
    FieldDescriptor.TYPE_SFIXED32: (-(2**31), (2**31) - 1),
    FieldDescriptor.TYPE_UINT32: (0, (2**32) - 1),
    FieldDescriptor.TYPE_FIXED32: (0, (2**32) - 1),
    FieldDescriptor.TYPE_INT64: (-(2**63), (2**63) - 1),
    FieldDescriptor.TYPE_SINT64: (-(2**63), (2**63) - 1),
    FieldDescriptor.TYPE_SFIXED64: (-(2**63), (2**63) - 1),
    FieldDescriptor.TYPE_UINT64: (0, (2**64) - 1),
    FieldDescriptor.TYPE_FIXED64: (0, (2**64) - 1),
}


def _is_map(field: FieldDescriptor) -> bool:
    return (
        _is_repeated(field)
        and field.type == FieldDescriptor.TYPE_MESSAGE
        and field.message_type is not None
        and field.message_type.GetOptions().map_entry
    )


def _is_repeated(field: FieldDescriptor) -> bool:
    is_repeated = getattr(field, "is_repeated", None)
    if is_repeated is not None:
        return bool(is_repeated)
    return field.label == FieldDescriptor.LABEL_REPEATED


def _is_required(field: FieldDescriptor) -> bool:
    is_required = getattr(field, "is_required", None)
    if is_required is not None:
        return bool(is_required)
    return field.label == FieldDescriptor.LABEL_REQUIRED


def _has_presence(field: FieldDescriptor) -> bool:
    has_presence = getattr(field, "has_presence", None)
    if has_presence is not None:
        return bool(has_presence)
    return (
        field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP)
        or field.containing_oneof is not None
        or getattr(field.file, "syntax", "proto3") == "proto2"
    )


def _singular_annotation(field: FieldDescriptor) -> Any:
    if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
        assert field.message_type is not None
        existing = _MODEL_BY_DESCRIPTOR.get(field.message_type)
        if existing is not None:
            return existing
        if field.message_type in _BUILDING:
            return ForwardRef(_forward_name(field.message_type))
        return _build_model(field.message_type)
    if field.type == FieldDescriptor.TYPE_ENUM:
        assert field.enum_type is not None
        return _enum_model(field.enum_type)
    if field.type in _INTEGER_BOUNDS:
        minimum, maximum = _INTEGER_BOUNDS[field.type]
        return Annotated[int, Field(ge=minimum, le=maximum)]
    try:
        return _SCALAR_TYPES[field.type]
    except KeyError as exc:
        raise TypeError(
            f"unsupported protobuf type {field.type} on {field.full_name}"
        ) from exc


def _field_annotation(field: FieldDescriptor) -> Any:
    if _is_map(field):
        assert field.message_type is not None
        key_field = field.message_type.fields_by_name["key"]
        value_field = field.message_type.fields_by_name["value"]
        return dict[_singular_annotation(key_field), _singular_annotation(value_field)]

    annotation = _singular_annotation(field)
    if _is_repeated(field):
        return list[annotation]
    if _has_presence(field) and not _is_required(field):
        # ``annotation`` may be a ForwardRef for recursive descriptors.
        # Optional[...] works with ForwardRef on every supported Python,
        # whereas ForwardRef | None requires Python 3.11 or newer.
        return Optional[annotation]  # noqa: UP045
    return annotation


def _field_info(field: FieldDescriptor, annotation: Any) -> Any:
    aliases = list(dict.fromkeys((field.name, field.json_name)))
    metadata: dict[str, Any] = {
        "serialization_alias": field.name,
        "validation_alias": AliasChoices(*aliases),
        "json_schema_extra": {
            "protobuf_field": field.full_name,
            "protobuf_number": field.number,
        },
    }

    if _is_map(field):
        return annotation, Field(default_factory=dict, **metadata)
    if _is_repeated(field):
        return annotation, Field(default_factory=list, **metadata)
    if _is_required(field):
        return annotation, Field(..., **metadata)
    if _has_presence(field):
        return annotation, Field(None, **metadata)
    if field.type == FieldDescriptor.TYPE_ENUM:
        assert field.enum_type is not None
        default = _enum_model(field.enum_type)(field.default_value)
    else:
        default = field.default_value
    return annotation, Field(default, **metadata)


def _build_model(descriptor: Descriptor) -> type[ProtobufModel]:
    existing = _MODEL_BY_DESCRIPTOR.get(descriptor)
    if existing is not None:
        return existing
    if descriptor.GetOptions().map_entry:
        raise TypeError(f"map entry {descriptor.full_name!r} is not a public model")

    _BUILDING.add(descriptor)
    try:
        used_names: set[str] = set()
        protobuf_to_python: dict[str, str] = {}
        fields: dict[str, Any] = {}
        for field in descriptor.fields:
            python_name = _python_field_name(field.name)
            while python_name in used_names:
                python_name += "_"
            used_names.add(python_name)
            protobuf_to_python[field.name] = python_name
            annotation = _field_annotation(field)
            fields[python_name] = _field_info(field, annotation)

        model = create_model(
            descriptor.name,
            __base__=ProtobufModel,
            __module__=__name__,
            **fields,
        )
    finally:
        _BUILDING.remove(descriptor)

    protobuf_class = _message_class(descriptor)
    model.__protobuf_descriptor__ = descriptor
    model.__protobuf_class__ = protobuf_class
    model.__protobuf_to_python_fields__ = MappingProxyType(protobuf_to_python)
    model.__doc__ = f"Pydantic model for ``{descriptor.full_name}``."

    _MODEL_BY_DESCRIPTOR[descriptor] = model
    _MODEL_BY_PROTOBUF_CLASS[protobuf_class] = model
    _MODEL_REGISTRY[descriptor.full_name] = model
    _FORWARD_NAMESPACE[_forward_name(descriptor)] = model
    _publish_package_member(descriptor, model)
    return model


def _publish_package_member(
    descriptor: Descriptor | EnumDescriptor, member: Any
) -> None:
    if descriptor.containing_type is not None:
        return
    package = descriptor.file.package
    members = _PACKAGE_MEMBERS.setdefault(package, {})
    members[descriptor.name] = member
    if package not in _PACKAGE_NAMESPACES:
        namespace = ModelNamespace(package, members)
        _PACKAGE_NAMESPACES[package] = namespace
        attribute = package.replace(".", "_") or "root"
        if attribute.isidentifier() and not keyword.iskeyword(attribute):
            globals()[attribute] = namespace


def _walk_messages(descriptor: Descriptor) -> list[Descriptor]:
    messages = [descriptor]
    for nested in descriptor.nested_types:
        if not nested.GetOptions().map_entry:
            messages.extend(_walk_messages(nested))
    return messages


def _walk_enums(descriptor: Descriptor) -> list[EnumDescriptor]:
    enums = list(descriptor.enum_types)
    for nested in descriptor.nested_types:
        if not nested.GetOptions().map_entry:
            enums.extend(_walk_enums(nested))
    return enums


def _attach_nested_types() -> None:
    for descriptor, model in tuple(_MODEL_BY_DESCRIPTOR.items()):
        for nested in descriptor.nested_types:
            if not nested.GetOptions().map_entry:
                setattr(model, nested.name, _MODEL_BY_DESCRIPTOR[nested])
        for enum_descriptor in descriptor.enum_types:
            setattr(model, enum_descriptor.name, _ENUM_BY_DESCRIPTOR[enum_descriptor])


def _rebuild_models() -> None:
    # Cycles in descriptors are represented with ForwardRef during construction.
    # Rebuilding after the registry is populated resolves every cycle against a
    # namespace whose keys are globally unique protobuf full names.
    pending = set(_MODEL_BY_DESCRIPTOR.values())
    for _ in range(len(pending) + 1):
        if not pending:
            return
        next_pending: set[type[ProtobufModel]] = set()
        for model in pending:
            rebuilt = model.model_rebuild(
                force=True,
                raise_errors=False,
                _types_namespace=_FORWARD_NAMESPACE,
            )
            if rebuilt is False:
                next_pending.add(model)
        if next_pending == pending:
            break
        pending = next_pending
    if pending:
        names = ", ".join(sorted(model.__name__ for model in pending))
        raise TypeError(f"failed to resolve protobuf model references: {names}")


def _load_generated_models() -> None:
    from . import pb

    module_names = sorted(
        module.name
        for module in pkgutil.walk_packages(pb.__path__, f"{pb.__name__}.")
        if module.name.endswith("_pb2")
    )
    file_descriptors = []
    for module_name in module_names:
        module = importlib.import_module(module_name)
        file_descriptors.append(module.DESCRIPTOR)

    for file_descriptor in file_descriptors:
        for enum_descriptor in file_descriptor.enum_types_by_name.values():
            _enum_model(enum_descriptor)
        for message_descriptor in file_descriptor.message_types_by_name.values():
            for enum_descriptor in _walk_enums(message_descriptor):
                _enum_model(enum_descriptor)
            for nested_descriptor in _walk_messages(message_descriptor):
                _build_model(nested_descriptor)

    _rebuild_models()
    _attach_nested_types()


def get_pydantic_model(
    source: str | Descriptor | type[Message] | Message | type[ProtobufModel],
) -> type[ProtobufModel]:
    """Return the stable Pydantic class associated with a protobuf type.

    ``source`` may be a protobuf full name, descriptor, generated message class,
    message instance, or an already generated Pydantic model class.  A unique
    unqualified protobuf message name is accepted as a convenience.
    """

    if isinstance(source, type) and issubclass(source, ProtobufModel):
        return source
    if isinstance(source, str):
        model = _MODEL_REGISTRY.get(source)
        if model is not None:
            return model
        matches = [
            candidate
            for full_name, candidate in _MODEL_REGISTRY.items()
            if full_name.rsplit(".", 1)[-1] == source
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            candidates = sorted(
                name for name in _MODEL_REGISTRY if name.rsplit(".", 1)[-1] == source
            )
            raise KeyError(
                f"ambiguous protobuf message name {source!r}; use one of {candidates}"
            )
        raise KeyError(f"unknown protobuf message {source!r}")

    if isinstance(source, Descriptor):
        descriptor = source
    else:
        descriptor = getattr(source, "DESCRIPTOR", None)
        if not isinstance(descriptor, Descriptor):
            raise TypeError(
                "source must be a protobuf name, descriptor, Message class/instance, "
                "or ProtobufModel class"
            )

    model = _MODEL_BY_DESCRIPTOR.get(descriptor)
    if model is None:
        model = _build_model(descriptor)
        _rebuild_models()
        _attach_nested_types()
    return model


def _from_protobuf_value(field: FieldDescriptor, value: Any) -> Any:
    if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
        assert field.message_type is not None
        return get_pydantic_model(field.message_type).from_protobuf(value)
    if field.type == FieldDescriptor.TYPE_ENUM:
        assert field.enum_type is not None
        return _enum_model(field.enum_type)(value)
    return value


def _from_protobuf_field(field: FieldDescriptor, value: Any) -> Any:
    if _is_map(field):
        assert field.message_type is not None
        value_field = field.message_type.fields_by_name["value"]
        return {
            key: _from_protobuf_value(value_field, item) for key, item in value.items()
        }
    if _is_repeated(field):
        return [_from_protobuf_value(field, item) for item in value]
    return _from_protobuf_value(field, value)


def _model_from_protobuf(model_class: type[_ModelT], message: Message) -> _ModelT:
    field_names = model_class.__protobuf_to_python_fields__
    values = {
        field_names[field.name]: _from_protobuf_field(field, value)
        for field, value in message.ListFields()
    }
    return model_class.model_validate(values)


def _to_protobuf_value(field: FieldDescriptor, value: Any) -> Any:
    if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
        if not isinstance(value, ProtobufModel):
            raise TypeError(
                f"{field.full_name} requires ProtobufModel, got {type(value).__name__}"
            )
        message = value.to_protobuf()
        assert field.message_type is not None
        if message.DESCRIPTOR.full_name != field.message_type.full_name:
            raise TypeError(
                f"{field.full_name} requires {field.message_type.full_name}, "
                f"got {message.DESCRIPTOR.full_name}"
            )
        return message
    if field.type == FieldDescriptor.TYPE_ENUM:
        return int(value)
    return value


def _set_protobuf_field(message: Message, field: FieldDescriptor, value: Any) -> None:
    target = getattr(message, field.name)
    if _is_map(field):
        assert field.message_type is not None
        value_field = field.message_type.fields_by_name["value"]
        if value_field.type in (
            FieldDescriptor.TYPE_MESSAGE,
            FieldDescriptor.TYPE_GROUP,
        ):
            for key, item in value.items():
                target[key].CopyFrom(_to_protobuf_value(value_field, item))
        else:
            for key, item in value.items():
                target[key] = _to_protobuf_value(value_field, item)
        return
    if _is_repeated(field):
        if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
            for item in value:
                target.add().CopyFrom(_to_protobuf_value(field, item))
        else:
            target.extend(_to_protobuf_value(field, item) for item in value)
        return
    if field.type in (FieldDescriptor.TYPE_MESSAGE, FieldDescriptor.TYPE_GROUP):
        target.CopyFrom(_to_protobuf_value(field, value))
    else:
        setattr(message, field.name, _to_protobuf_value(field, value))


def _model_to_protobuf(model: ProtobufModel) -> Message:
    descriptor = model.__protobuf_descriptor__
    protobuf_class = model.__protobuf_class__
    if descriptor is None or protobuf_class is None:
        raise TypeError(f"{type(model).__name__} is not bound to a protobuf descriptor")

    # Recheck here in case model_construct() was used to bypass Pydantic's
    # validators.
    model._validate_oneofs()
    message = protobuf_class()
    field_names = model.__protobuf_to_python_fields__
    for field in descriptor.fields:
        python_name = field_names[field.name]
        value = getattr(model, python_name)
        if value is None:
            continue
        if _is_repeated(field):
            if value:
                _set_protobuf_field(message, field, value)
            continue
        if (
            not _has_presence(field)
            and python_name not in model.model_fields_set
            and value == field.default_value
        ):
            continue
        _set_protobuf_field(message, field, value)
    return message


def protobuf_to_pydantic(value: Any) -> Any:
    """Recursively replace protobuf message leaves with Pydantic models."""

    if isinstance(value, Message):
        return get_pydantic_model(value).from_protobuf(value)
    if isinstance(value, list):
        return [protobuf_to_pydantic(item) for item in value]
    if isinstance(value, tuple):
        return tuple(protobuf_to_pydantic(item) for item in value)
    if isinstance(value, dict):
        return {key: protobuf_to_pydantic(item) for key, item in value.items()}
    return value


def pydantic_to_protobuf(value: Any) -> Any:
    """Recursively replace descriptor-derived Pydantic model leaves with protobuf."""

    if isinstance(value, ProtobufModel):
        return value.to_protobuf()
    if isinstance(value, list):
        return [pydantic_to_protobuf(item) for item in value]
    if isinstance(value, tuple):
        return tuple(pydantic_to_protobuf(item) for item in value)
    if isinstance(value, dict):
        return {key: pydantic_to_protobuf(item) for key, item in value.items()}
    return value


_load_generated_models()


__all__ = [
    "ENUM_BY_DESCRIPTOR",
    "ENUM_REGISTRY",
    "MODEL_BY_DESCRIPTOR",
    "MODEL_BY_PROTOBUF_CLASS",
    "MODEL_REGISTRY",
    "PACKAGE_NAMESPACES",
    "ModelNamespace",
    "ProtobufEnum",
    "ProtobufModel",
    "get_pydantic_model",
    "protobuf_to_pydantic",
    "pydantic_to_protobuf",
    *sorted(package.replace(".", "_") or "root" for package in _PACKAGE_NAMESPACES),
]
