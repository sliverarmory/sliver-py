from __future__ import annotations

import importlib
import inspect
import pickle
from types import ModuleType
from typing import get_type_hints

import pytest
from pydantic import BaseModel, ValidationError

from sliver import models
from sliver._pb.clientpb import client_pb2
from sliver._pb.commonpb import common_pb2
from sliver._pb.sliverpb import sliver_pb2
from sliver.models import (
    MODEL_REGISTRY,
    ProtobufEnum,
    ProtobufModel,
    _get_pydantic_model,
    _model_to_protobuf,
    _protobuf_to_pydantic,
    get_pydantic_model,
)
from sliver.models.clientpb import Event, Session


def test_model_packages_are_real_importable_python_modules() -> None:
    client_models = importlib.import_module("sliver.models.clientpb")

    assert isinstance(models.clientpb, ModuleType)
    assert client_models is models.clientpb
    assert client_models.Event is Event
    assert Event.__module__ == "sliver.models.clientpb"
    assert issubclass(Event, BaseModel)
    assert "class Event(ProtobufModel):" in inspect.getsource(Event)
    assert get_type_hints(Event)["event_type"] is str


def test_concrete_models_are_picklable_and_preserve_nested_model_types() -> None:
    event = Event(
        event_type="session-opened",
        session=Session(id="session-id", name="operator-session"),
    )

    restored = pickle.loads(pickle.dumps(event))

    assert type(restored) is Event
    assert type(restored.session) is Session
    assert restored == event


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


def test_public_registry_and_lookup_only_expose_concrete_pydantic_types() -> None:
    model_class = models.commonpb.File

    assert MODEL_REGISTRY["commonpb.File"] is model_class
    assert get_pydantic_model("commonpb.File") is model_class
    assert get_pydantic_model("File") is model_class
    assert get_pydantic_model(model_class) is model_class
    assert all(issubclass(value, ProtobufModel) for value in MODEL_REGISTRY.values())
    assert not hasattr(models, "PACKAGE_NAMESPACES")


@pytest.mark.parametrize(
    "wire_type",
    [common_pb2.File.DESCRIPTOR, common_pb2.File, common_pb2.File()],
)
def test_public_model_lookup_rejects_wire_types(wire_type: object) -> None:
    with pytest.raises(TypeError, match="model name or ProtobufModel class"):
        get_pydantic_model(wire_type)  # type: ignore[arg-type]

    assert _get_pydantic_model(wire_type) is models.commonpb.File


def test_concrete_models_round_trip_maps_repeated_and_nested_messages() -> None:
    message = sliver_pb2.ExecuteReq(
        Path="/bin/sh",
        Args=["-c", "whoami"],
        Env={"LANG": "C", "TERM": "xterm"},
        Request=common_pb2.Request(SessionID="session-id"),
    )

    model = _protobuf_to_pydantic(message)

    assert isinstance(model, models.sliverpb.ExecuteReq)
    assert model.args == ["-c", "whoami"]
    assert model.env == {"LANG": "C", "TERM": "xterm"}
    assert isinstance(model.request, models.commonpb.Request)
    assert model.request.session_id == "session-id"
    assert _model_to_protobuf(model) == message


def test_concrete_recursive_models_round_trip_without_dynamic_fallbacks() -> None:
    message = client_pb2.PivotGraphEntry(
        PeerID=1,
        Name="root",
        Children=[client_pb2.PivotGraphEntry(PeerID=2, Name="child")],
    )

    model = _protobuf_to_pydantic(message)

    assert isinstance(model, models.clientpb.PivotGraphEntry)
    assert isinstance(model.children[0], models.clientpb.PivotGraphEntry)
    assert model.children[0].name == "child"
    assert _model_to_protobuf(model) == message


def test_presence_and_open_enum_values_use_real_generated_types() -> None:
    absent = models.clientpb.AIConversationMessage()
    present_default = models.clientpb.AIConversationMessage(include_in_context=False)

    assert absent.include_in_context is None
    assert not _model_to_protobuf(absent).HasField("IncludeInContext")
    assert _model_to_protobuf(present_default).HasField("IncludeInContext")

    wire = client_pb2.ImplantConfig(Format=31337)
    config = _protobuf_to_pydantic(wire)
    assert isinstance(config, models.clientpb.ImplantConfig)
    assert isinstance(config.format, ProtobufEnum)
    assert config.format.name == "UNRECOGNIZED_31337"
    assert _model_to_protobuf(config).Format == 31337


def test_reserved_model_names_have_stable_python_fields_and_wire_aliases() -> None:
    request = models.commonpb.Request(Async=True)
    registration = models.sliverpb.BeaconRegister(
        Register=models.sliverpb.Register(name="implant")
    )

    assert request.async_ is True
    assert registration.register_ is not None
    assert registration.register_.name == "implant"
    assert _model_to_protobuf(request).Async is True
    assert _model_to_protobuf(registration).Register.Name == "implant"


def test_nested_message_is_a_concrete_class_on_its_parent() -> None:
    address = models.sliverpb.SockTabEntry.SockAddr(ip="127.0.0.1", port=4444)
    entry = models.sliverpb.SockTabEntry(local_addr=address)

    assert isinstance(address, ProtobufModel)
    assert type(address).__module__ == "sliver.models.sliverpb"
    assert entry.local_addr is not None
    assert entry.local_addr.port == 4444
    assert _model_to_protobuf(entry).LocalAddr.Port == 4444


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

    with pytest.raises(TypeError, match="no internal wire binding"):
        _model_to_protobuf(common_pb2.File())  # type: ignore[arg-type]
