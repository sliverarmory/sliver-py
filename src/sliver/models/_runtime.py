"""Runtime support for generated Pydantic models.

Public message and enum classes are declared in the generated ``commonpb``,
``sliverpb``, and ``clientpb`` modules. This module only owns their private
descriptor bindings and wire conversion at the gRPC boundary.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from enum import IntEnum
from types import MappingProxyType, ModuleType
from typing import Any, NamedTuple, TypeVar, cast, overload

from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor import Descriptor as _Descriptor
from google.protobuf.descriptor import EnumDescriptor as _EnumDescriptor
from google.protobuf.descriptor import FieldDescriptor as _FieldDescriptor
from google.protobuf.message import Message as _Message
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticUndefined

from ._naming import python_field_name as _python_field_name

_ModelT = TypeVar("_ModelT", bound="ProtobufModel")
_EnumT = TypeVar("_EnumT", bound="ProtobufEnum")


class ProtobufEnum(IntEnum):
    """Base class for concrete enums generated from Sliver descriptors."""

    @classmethod
    def _missing_(cls, value: object) -> ProtobufEnum | None:
        descriptor = _ENUM_DESCRIPTOR_BY_MODEL.get(cls)
        syntax = getattr(descriptor.file, "syntax", "proto3") if descriptor else None
        if descriptor is None or syntax == "proto2" or not isinstance(value, int):
            return None

        member = int.__new__(cls, value)
        member._name_ = f"UNRECOGNIZED_{value}"
        member._value_ = value
        cls._value2member_map_[value] = member
        return member


class ProtobufModel(BaseModel):
    """Base class shared by every concrete generated Pydantic model."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        protected_namespaces=(),
        ser_json_bytes="base64",
        val_json_bytes="base64",
        validate_assignment=True,
    )

    @model_validator(mode="after")
    def _validate_oneofs(self) -> ProtobufModel:
        binding = _MODEL_BINDINGS.get(type(self))
        if binding is None:
            return self

        for oneof in binding.descriptor.oneofs:
            active = [
                field.name
                for field in oneof.fields
                if getattr(self, binding.protobuf_to_python_fields[field.name])
                is not None
            ]
            if len(active) > 1:
                joined = ", ".join(active)
                raise ValueError(
                    f"protobuf oneof {oneof.full_name!r} accepts at most one field; "
                    f"got {joined}"
                )
        return self


class _ModelBinding(NamedTuple):
    descriptor: _Descriptor
    protobuf_class: type[_Message]
    protobuf_to_python_fields: Mapping[str, str]


_MODEL_REGISTRY: dict[str, type[ProtobufModel]] = {}
_ENUM_REGISTRY: dict[str, type[ProtobufEnum]] = {}
_PACKAGE_NAMESPACES: dict[str, ModuleType] = {}
_MODEL_BINDINGS: dict[type[ProtobufModel], _ModelBinding] = {}
_MODEL_BY_DESCRIPTOR: dict[_Descriptor, type[ProtobufModel]] = {}
_MODEL_BY_PROTOBUF_CLASS: dict[type[_Message], type[ProtobufModel]] = {}
_ENUM_BY_DESCRIPTOR: dict[_EnumDescriptor, type[ProtobufEnum]] = {}
_ENUM_DESCRIPTOR_BY_MODEL: dict[type[ProtobufEnum], _EnumDescriptor] = {}

MODEL_REGISTRY: Mapping[str, type[ProtobufModel]] = MappingProxyType(
    _MODEL_REGISTRY
)
ENUM_REGISTRY: Mapping[str, type[ProtobufEnum]] = MappingProxyType(_ENUM_REGISTRY)
def _protobuf_field(
    protobuf_name: str,
    json_name: str,
    full_name: str,
    number: int,
    *,
    default: Any = PydanticUndefined,
    default_factory: Callable[[], Any] | None = None,
) -> Any:
    aliases = list(dict.fromkeys((protobuf_name, json_name)))
    metadata = {
        "serialization_alias": protobuf_name,
        "validation_alias": AliasChoices(*aliases),
        "json_schema_extra": {
            "protobuf_field": full_name,
            "protobuf_number": number,
        },
    }
    if default_factory is not None:
        return Field(default_factory=default_factory, **metadata)
    if default is PydanticUndefined:
        return Field(..., **metadata)
    return Field(default, **metadata)


def _register_model(full_name: str) -> Callable[[type[_ModelT]], type[_ModelT]]:
    def register(model: type[_ModelT]) -> type[_ModelT]:
        if full_name in _MODEL_REGISTRY:
            raise TypeError(f"duplicate generated model {full_name!r}")
        _MODEL_REGISTRY[full_name] = model
        return model

    return register


def _register_enum(full_name: str) -> Callable[[type[_EnumT]], type[_EnumT]]:
    def register(enum: type[_EnumT]) -> type[_EnumT]:
        if full_name in _ENUM_REGISTRY:
            raise TypeError(f"duplicate generated enum {full_name!r}")
        _ENUM_REGISTRY[full_name] = enum
        return enum

    return register


def _register_package(package: str, module: ModuleType) -> None:
    if package in _PACKAGE_NAMESPACES:
        raise TypeError(f"duplicate generated package {package!r}")
    _PACKAGE_NAMESPACES[package] = module


def _message_class(descriptor: _Descriptor) -> type[_Message]:
    get_message_class = getattr(message_factory, "GetMessageClass", None)
    if get_message_class is not None:
        return cast(type[_Message], get_message_class(descriptor))
    factory = message_factory.MessageFactory()
    return cast(type[_Message], factory.GetPrototype(descriptor))


def _walk_messages(descriptor: _Descriptor) -> list[_Descriptor]:
    messages = [descriptor]
    for nested in descriptor.nested_types:
        if not nested.GetOptions().map_entry:
            messages.extend(_walk_messages(nested))
    return messages


def _bind_wire_types() -> None:
    # Importing the private modules loads the bundled descriptors into the
    # default pool. They never become part of a generated model's public state.
    from .._pb.clientpb import client_pb2 as _client_pb2  # noqa: F401
    from .._pb.commonpb import common_pb2 as _common_pb2  # noqa: F401
    from .._pb.sliverpb import sliver_pb2 as _sliver_pb2  # noqa: F401

    pool = descriptor_pool.Default()
    for full_name, model in _MODEL_REGISTRY.items():
        descriptor = pool.FindMessageTypeByName(full_name)
        protobuf_to_python = {
            field.name: _python_field_name(field.name) for field in descriptor.fields
        }
        expected_fields = set(protobuf_to_python.values())
        actual_fields = set(model.model_fields)
        if actual_fields != expected_fields:
            raise TypeError(
                f"generated model {full_name!r} fields differ from its descriptor: "
                f"expected {sorted(expected_fields)}, got {sorted(actual_fields)}"
            )
        protobuf_class = _message_class(descriptor)
        binding = _ModelBinding(
            descriptor,
            protobuf_class,
            MappingProxyType(protobuf_to_python),
        )
        _MODEL_BINDINGS[model] = binding
        _MODEL_BY_DESCRIPTOR[descriptor] = model
        _MODEL_BY_PROTOBUF_CLASS[protobuf_class] = model

    for full_name, enum in _ENUM_REGISTRY.items():
        descriptor = pool.FindEnumTypeByName(full_name)
        expected_values = {value.name: value.number for value in descriptor.values}
        actual_values = {name: int(member) for name, member in enum.__members__.items()}
        if actual_values != expected_values:
            raise TypeError(
                f"generated enum {full_name!r} differs from its descriptor"
            )
        _ENUM_BY_DESCRIPTOR[descriptor] = enum
        _ENUM_DESCRIPTOR_BY_MODEL[enum] = descriptor


def _rebuild_models() -> None:
    for model in _MODEL_REGISTRY.values():
        module = sys.modules[model.__module__]
        namespace = dict(vars(module))
        namespace.update(_PACKAGE_NAMESPACES)
        model.model_rebuild(force=True, _types_namespace=namespace)


@overload
def get_pydantic_model(source: type[_ModelT]) -> type[_ModelT]: ...


@overload
def get_pydantic_model(source: str) -> type[ProtobufModel]: ...


def get_pydantic_model(
    source: str | type[ProtobufModel],
) -> type[ProtobufModel]:
    """Return one concrete generated Pydantic class by name."""

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
    raise TypeError("source must be a model name or ProtobufModel class")


def _get_pydantic_model(
    source: _Descriptor | type[_Message] | _Message,
) -> type[ProtobufModel]:
    if isinstance(source, _Descriptor):
        descriptor = source
    else:
        descriptor = getattr(source, "DESCRIPTOR", None)
        if not isinstance(descriptor, _Descriptor):
            raise TypeError("source must be a protobuf descriptor, class, or message")
    try:
        return _MODEL_BY_DESCRIPTOR[descriptor]
    except KeyError as exc:
        raise TypeError(
            f"no concrete Pydantic model for {descriptor.full_name!r}"
        ) from exc


def _is_map(field: _FieldDescriptor) -> bool:
    return (
        _is_repeated(field)
        and field.type == _FieldDescriptor.TYPE_MESSAGE
        and field.message_type is not None
        and field.message_type.GetOptions().map_entry
    )


def _is_repeated(field: _FieldDescriptor) -> bool:
    is_repeated = getattr(field, "is_repeated", None)
    if is_repeated is not None:
        return bool(is_repeated)
    return field.label == _FieldDescriptor.LABEL_REPEATED


def _has_presence(field: _FieldDescriptor) -> bool:
    has_presence = getattr(field, "has_presence", None)
    if has_presence is not None:
        return bool(has_presence)
    return (
        field.type in (_FieldDescriptor.TYPE_MESSAGE, _FieldDescriptor.TYPE_GROUP)
        or field.containing_oneof is not None
        or getattr(field.file, "syntax", "proto3") == "proto2"
    )


def _from_protobuf_value(field: _FieldDescriptor, value: Any) -> Any:
    if field.type in (_FieldDescriptor.TYPE_MESSAGE, _FieldDescriptor.TYPE_GROUP):
        assert field.message_type is not None
        return _model_from_protobuf(_get_pydantic_model(field.message_type), value)
    if field.type == _FieldDescriptor.TYPE_ENUM:
        assert field.enum_type is not None
        return _ENUM_BY_DESCRIPTOR[field.enum_type](value)
    return value


def _from_protobuf_field(field: _FieldDescriptor, value: Any) -> Any:
    if _is_map(field):
        assert field.message_type is not None
        value_field = field.message_type.fields_by_name["value"]
        return {
            key: _from_protobuf_value(value_field, item) for key, item in value.items()
        }
    if _is_repeated(field):
        return [_from_protobuf_value(field, item) for item in value]
    return _from_protobuf_value(field, value)


def _model_from_protobuf(model_class: type[_ModelT], message: _Message) -> _ModelT:
    binding = _MODEL_BINDINGS.get(model_class)
    if binding is None or not isinstance(message, binding.protobuf_class):
        expected_name = binding.descriptor.full_name if binding else model_class.__name__
        actual_name = getattr(getattr(message, "DESCRIPTOR", None), "full_name", None)
        raise TypeError(
            f"internal conversion expected {expected_name!r}, "
            f"got {actual_name or type(message).__name__!r}"
        )
    values = {
        binding.protobuf_to_python_fields[field.name]: _from_protobuf_field(
            field, value
        )
        for field, value in message.ListFields()
    }
    return model_class.model_validate(values)


def _to_protobuf_value(field: _FieldDescriptor, value: Any) -> Any:
    if field.type in (_FieldDescriptor.TYPE_MESSAGE, _FieldDescriptor.TYPE_GROUP):
        if not isinstance(value, ProtobufModel):
            raise TypeError(
                f"{field.full_name} requires ProtobufModel, got {type(value).__name__}"
            )
        message = _model_to_protobuf(value)
        assert field.message_type is not None
        if message.DESCRIPTOR.full_name != field.message_type.full_name:
            raise TypeError(
                f"{field.full_name} requires {field.message_type.full_name}, "
                f"got {message.DESCRIPTOR.full_name}"
            )
        return message
    if field.type == _FieldDescriptor.TYPE_ENUM:
        return int(value)
    return value


def _set_protobuf_field(message: _Message, field: _FieldDescriptor, value: Any) -> None:
    target = getattr(message, field.name)
    if _is_map(field):
        assert field.message_type is not None
        value_field = field.message_type.fields_by_name["value"]
        if value_field.type in (
            _FieldDescriptor.TYPE_MESSAGE,
            _FieldDescriptor.TYPE_GROUP,
        ):
            for key, item in value.items():
                target[key].CopyFrom(_to_protobuf_value(value_field, item))
        else:
            for key, item in value.items():
                target[key] = _to_protobuf_value(value_field, item)
        return
    if _is_repeated(field):
        if field.type in (_FieldDescriptor.TYPE_MESSAGE, _FieldDescriptor.TYPE_GROUP):
            for item in value:
                target.add().CopyFrom(_to_protobuf_value(field, item))
        else:
            target.extend(_to_protobuf_value(field, item) for item in value)
        return
    if field.type in (_FieldDescriptor.TYPE_MESSAGE, _FieldDescriptor.TYPE_GROUP):
        target.CopyFrom(_to_protobuf_value(field, value))
    else:
        setattr(message, field.name, _to_protobuf_value(field, value))


def _model_to_protobuf(model: ProtobufModel) -> _Message:
    binding = _MODEL_BINDINGS.get(type(model))
    if binding is None:
        raise TypeError(f"{type(model).__name__} has no internal wire binding")
    model._validate_oneofs()
    message = binding.protobuf_class()
    for field in binding.descriptor.fields:
        python_name = binding.protobuf_to_python_fields[field.name]
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


def _protobuf_to_pydantic(value: Any) -> Any:
    """Recursively convert private wire messages to concrete Pydantic models."""

    if isinstance(value, _Message):
        model_class = _get_pydantic_model(value)
        return _model_from_protobuf(model_class, value)
    if isinstance(value, list):
        return [_protobuf_to_pydantic(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_protobuf_to_pydantic(item) for item in value)
    if isinstance(value, dict):
        return {key: _protobuf_to_pydantic(item) for key, item in value.items()}
    return value


def _model_from_bytes(
    model_class: type[_ModelT], serialized: bytes | bytearray | memoryview
) -> _ModelT:
    binding = _MODEL_BINDINGS.get(model_class)
    if binding is None:
        raise TypeError(f"{model_class.__name__} has no internal wire binding")
    message = binding.protobuf_class()
    message.ParseFromString(bytes(serialized))
    return _model_from_protobuf(model_class, message)
