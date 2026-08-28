from __future__ import annotations

from functools import cache
from typing import Any

import pytest
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from google.protobuf.descriptor import FieldDescriptor
from pydantic import ValidationError

from sliver import models
from sliver._pb.commonpb import common_pb2
from sliver.models import (
    MODEL_REGISTRY,
    ProtobufEnum,
    ProtobufModel,
    _get_pydantic_model,
    _model_to_protobuf,
    _protobuf_to_pydantic,
    get_pydantic_model,
)


def _add_field(
    message: descriptor_pb2.DescriptorProto,
    *,
    name: str,
    number: int,
    type_: int,
    label: int = FieldDescriptor.LABEL_OPTIONAL,
    type_name: str | None = None,
    oneof_index: int | None = None,
    proto3_optional: bool = False,
) -> None:
    field = message.field.add()
    field.name = name
    field.number = number
    field.type = type_
    field.label = label
    if type_name is not None:
        field.type_name = type_name
    if oneof_index is not None:
        field.oneof_index = oneof_index
    field.proto3_optional = proto3_optional


@cache
def _feature_message_type() -> type[Any]:
    file_proto = descriptor_pb2.FileDescriptorProto(
        name="sliver_py_model_features.proto",
        package="featurepb",
        syntax="proto3",
    )

    state = file_proto.enum_type.add(name="State")
    state.value.add(name="STATE_UNKNOWN", number=0)
    state.value.add(name="STATE_RUNNING", number=1)

    child = file_proto.message_type.add(name="Child")
    _add_field(
        child,
        name="ValueText",
        number=1,
        type_=FieldDescriptor.TYPE_STRING,
    )

    feature = file_proto.message_type.add(name="Feature")
    feature.oneof_decl.add(name="Choice")
    feature.oneof_decl.add(name="_OptionalCount")

    child_map = feature.nested_type.add(name="ChildrenByNameEntry")
    child_map.options.map_entry = True
    _add_field(
        child_map,
        name="key",
        number=1,
        type_=FieldDescriptor.TYPE_STRING,
    )
    _add_field(
        child_map,
        name="value",
        number=2,
        type_=FieldDescriptor.TYPE_MESSAGE,
        type_name=".featurepb.Child",
    )

    bytes_map = feature.nested_type.add(name="BytesByNameEntry")
    bytes_map.options.map_entry = True
    _add_field(
        bytes_map,
        name="key",
        number=1,
        type_=FieldDescriptor.TYPE_STRING,
    )
    _add_field(
        bytes_map,
        name="value",
        number=2,
        type_=FieldDescriptor.TYPE_BYTES,
    )

    _add_field(
        feature,
        name="PayloadData",
        number=1,
        type_=FieldDescriptor.TYPE_BYTES,
    )
    _add_field(
        feature,
        name="ChildItems",
        number=2,
        type_=FieldDescriptor.TYPE_MESSAGE,
        label=FieldDescriptor.LABEL_REPEATED,
        type_name=".featurepb.Child",
    )
    _add_field(
        feature,
        name="ChildrenByName",
        number=3,
        type_=FieldDescriptor.TYPE_MESSAGE,
        label=FieldDescriptor.LABEL_REPEATED,
        type_name=".featurepb.Feature.ChildrenByNameEntry",
    )
    _add_field(
        feature,
        name="State",
        number=4,
        type_=FieldDescriptor.TYPE_ENUM,
        type_name=".featurepb.State",
    )
    _add_field(
        feature,
        name="OptionalCount",
        number=5,
        type_=FieldDescriptor.TYPE_INT32,
        oneof_index=1,
        proto3_optional=True,
    )
    _add_field(
        feature,
        name="TextValue",
        number=6,
        type_=FieldDescriptor.TYPE_STRING,
        oneof_index=0,
    )
    _add_field(
        feature,
        name="ChildValue",
        number=7,
        type_=FieldDescriptor.TYPE_MESSAGE,
        type_name=".featurepb.Child",
        oneof_index=0,
    )
    _add_field(
        feature,
        name="Next",
        number=8,
        type_=FieldDescriptor.TYPE_MESSAGE,
        type_name=".featurepb.Feature",
    )
    _add_field(
        feature,
        name="Numbers",
        number=9,
        type_=FieldDescriptor.TYPE_INT32,
        label=FieldDescriptor.LABEL_REPEATED,
    )
    _add_field(
        feature,
        name="BytesByName",
        number=10,
        type_=FieldDescriptor.TYPE_MESSAGE,
        label=FieldDescriptor.LABEL_REPEATED,
        type_name=".featurepb.Feature.BytesByNameEntry",
    )

    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_proto)
    descriptor = pool.FindMessageTypeByName("featurepb.Feature")
    return message_factory.GetMessageClass(descriptor)


def test_generated_sliver_models_use_snake_case_and_protobuf_aliases() -> None:
    message = common_pb2.File(Name="payload.bin", Data=b"\x00\xff")

    model = _protobuf_to_pydantic(message)

    assert isinstance(model, models.commonpb.File)
    assert model.name == "payload.bin"
    assert model.data == b"\x00\xff"
    assert model.model_dump(by_alias=True) == {
        "Name": "payload.bin",
        "Data": b"\x00\xff",
    }

    alias_model = models.commonpb.File(Name="alias.bin", Data=b"data")
    assert alias_model.name == "alias.bin"
    assert _model_to_protobuf(alias_model) == common_pb2.File(
        Name="alias.bin", Data=b"data"
    )


def test_generated_models_validate_protobuf_integer_ranges() -> None:
    assert models.clientpb.MTLSListenerReq(port=(2**32) - 1).port == (2**32) - 1
    assert models.commonpb.Process(pid=-(2**31)).pid == -(2**31)

    with pytest.raises(ValidationError):
        models.clientpb.MTLSListenerReq(port=-1)
    with pytest.raises(ValidationError):
        models.clientpb.MTLSListenerReq(port=2**32)
    with pytest.raises(ValidationError):
        models.commonpb.Process(pid=2**31)


def test_public_registry_and_lookup_only_expose_pydantic_types() -> None:
    model_class = models.commonpb.File

    assert MODEL_REGISTRY["commonpb.File"] is model_class
    assert get_pydantic_model("commonpb.File") is model_class
    assert get_pydantic_model("File") is model_class
    assert get_pydantic_model(model_class) is model_class
    assert all(issubclass(value, ProtobufModel) for value in MODEL_REGISTRY.values())


@pytest.mark.parametrize(
    "wire_type",
    [common_pb2.File.DESCRIPTOR, common_pb2.File, common_pb2.File()],
)
def test_public_model_lookup_rejects_wire_types(wire_type: object) -> None:
    with pytest.raises(TypeError, match="model name or ProtobufModel class"):
        get_pydantic_model(wire_type)  # type: ignore[arg-type]

    assert _get_pydantic_model(wire_type) is models.commonpb.File


def test_dynamic_descriptor_round_trip_covers_composite_field_kinds() -> None:
    message_type = _feature_message_type()
    message = message_type(
        PayloadData=b"\x00binary\xff",
        State=1,
        OptionalCount=0,
        TextValue="selected",
        Numbers=[1, 2, 3],
        BytesByName={"raw": b"\x01\x02"},
    )
    message.ChildItems.add(ValueText="first")
    message.ChildrenByName["primary"].ValueText = "mapped"
    message.Next.SetInParent()

    model_class = _get_pydantic_model(message_type.DESCRIPTOR)
    model = _protobuf_to_pydantic(message)

    assert isinstance(model, model_class)
    assert isinstance(model, ProtobufModel)
    assert model.payload_data == b"\x00binary\xff"
    assert model.child_items[0].value_text == "first"
    assert model.children_by_name["primary"].value_text == "mapped"
    assert isinstance(model.state, ProtobufEnum)
    assert model.state.name == "STATE_RUNNING"
    assert model.optional_count == 0
    assert "optional_count" in model.model_fields_set
    assert model.text_value == "selected"
    assert model.child_value is None
    assert model.next is not None
    assert model.next.model_fields_set == set()
    assert model.numbers == [1, 2, 3]
    assert model.bytes_by_name == {"raw": b"\x01\x02"}
    assert _model_to_protobuf(model) == message

    assert MODEL_REGISTRY["featurepb.Feature"] is model_class
    assert models.PACKAGE_NAMESPACES["featurepb"].Feature is model_class


def test_presence_oneof_and_open_enum_validation() -> None:
    message_type = _feature_message_type()
    model_class = _get_pydantic_model(message_type.DESCRIPTOR)

    empty = model_class()
    assert empty.optional_count is None
    assert empty.next is None
    empty_message = _model_to_protobuf(empty)
    assert not empty_message.HasField("OptionalCount")
    assert not empty_message.HasField("Next")

    present_default = model_class(OptionalCount=0)
    assert _model_to_protobuf(present_default).HasField("OptionalCount")

    unknown_enum = model_class(State=31337)
    assert isinstance(unknown_enum.state, ProtobufEnum)
    assert unknown_enum.state.name == "UNRECOGNIZED_31337"
    assert _model_to_protobuf(unknown_enum).State == 31337

    with pytest.raises(ValidationError, match="oneof"):
        model_class(TextValue="text", ChildValue={"ValueText": "child"})


def test_recursive_wire_decoder_preserves_ordinary_container_shapes() -> None:
    message = common_pb2.File(Name="nested", Data=b"data")
    original = {
        "list": [message, "unchanged"],
        "tuple": (message,),
        "number": 42,
    }

    converted = _protobuf_to_pydantic(original)

    assert isinstance(converted, dict)
    assert isinstance(converted["list"], list)
    assert isinstance(converted["tuple"], tuple)
    assert isinstance(converted["list"][0], models.commonpb.File)
    assert converted["list"][1] == "unchanged"
    assert converted["number"] == 42
    assert _model_to_protobuf(converted["list"][0]) == message
    assert _model_to_protobuf(converted["tuple"][0]) == message


def test_wire_conversion_is_private_and_rejects_raw_messages_in_model_encoder() -> None:
    model = models.commonpb.File(name="payload.bin", data=b"payload")

    assert not hasattr(model, "to_protobuf")
    assert not hasattr(type(model), "from_protobuf")
    assert not hasattr(type(model), "__protobuf_class__")
    assert not hasattr(type(model), "__protobuf_descriptor__")

    with pytest.raises(TypeError, match="not bound to a protobuf descriptor"):
        _model_to_protobuf(common_pb2.File())  # type: ignore[arg-type]
