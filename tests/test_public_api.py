from __future__ import annotations

import importlib.util
import inspect
from collections.abc import Mapping, Sequence
from enum import IntEnum
from typing import Any, get_args, get_origin, get_type_hints

import pytest
from google.protobuf.descriptor import Descriptor
from google.protobuf.message import Message
from pydantic import BaseModel

import sliver
from sliver import InteractiveBeacon, InteractiveSession, SliverClient, models
from sliver._pb.clientpb import client_pb2
from sliver.client import BaseClient

CLIENT_FEATURES = {
    "__aenter__",
    "__aexit__",
    "aclose",
    "add_website_content",
    "beacon_by_id",
    "beacon_task_content",
    "beacon_tasks",
    "beacons",
    "beacons_rm",
    "canaries",
    "cancel_task",
    "close",
    "collect_events",
    "connect",
    "delete_implant_build",
    "delete_implant_profile",
    "events",
    "fetch_task",
    "find_beacon",
    "find_job",
    "find_session",
    "from_config_file",
    "generate",
    "generate_implant",
    "generate_stage",
    "generate_wg_client_config",
    "generate_wg_ip",
    "get_beacon",
    "get_job",
    "get_session",
    "http",
    "https",
    "implant_builds",
    "implant_profiles",
    "implants",
    "implants_rm",
    "interact_beacon",
    "interact_session",
    "inventory",
    "is_connected",
    "job_by_id",
    "job_by_port",
    "jobs",
    "kill_beacon",
    "kill_job",
    "kill_session",
    "mtls",
    "new_profile",
    "on",
    "operators",
    "profiles",
    "profiles_generate",
    "profiles_new",
    "profiles_rm",
    "profiles_stage",
    "regenerate",
    "regenerate_implant",
    "remove_website",
    "remove_website_content",
    "rename_beacon",
    "rename_session",
    "rm_beacon",
    "rm_implant",
    "rm_profile",
    "rm_website",
    "rm_website_content",
    "save_implant_profile",
    "session_by_id",
    "sessions",
    "shellcode",
    "shellcode_rdi",
    "show_website",
    "start_dns_listener",
    "start_http_listener",
    "start_https_listener",
    "start_mtls_listener",
    "start_tcp_stager_listener",
    "start_wg_listener",
    "stage_listener",
    "tasks",
    "tasks_cancel",
    "tasks_fetch",
    "temporary_mtls",
    "update_website_content",
    "update_website",
    "use",
    "use_beacon",
    "use_session",
    "version",
    "website",
    "websites",
    "websites_rm",
    "websites_rm_content",
    "websites_show",
    "wg",
    "wg_config",
}

INTERACTIVE_FEATURES = {
    "call_extension",
    "cd",
    "download",
    "env",
    "env_set",
    "env_unset",
    "execute",
    "execute_assembly",
    "execute_shellcode",
    "get_env",
    "get_system",
    "ifconfig",
    "impersonate",
    "list_extensions",
    "ls",
    "make_token",
    "migrate",
    "mkdir",
    "msf",
    "msf_inject",
    "msf_remote",
    "netstat",
    "ping",
    "procdump",
    "process_dump",
    "ps",
    "pwd",
    "register_extension",
    "registry_create",
    "registry_create_key",
    "registry_read",
    "registry_write",
    "rev2self",
    "revert_to_self",
    "rm",
    "run_as",
    "runas",
    "screenshot",
    "set_env",
    "sideload",
    "spawn_dll",
    "spawndll",
    "terminate",
    "unset_env",
    "upload",
}

SESSION_ONLY_FEATURES = {
    "backdoor",
    "extensions_list",
    "getsystem",
    "pivot_listeners",
    "pivots",
    "remove_service",
    "services_start",
    "services_stop",
    "start_service",
    "stop_service",
}


def _nested_types(annotation: object) -> list[object]:
    origin = get_origin(annotation)
    if origin is None:
        return [annotation]
    nested = [origin]
    for argument in get_args(annotation):
        nested.extend(_nested_types(argument))
    return nested


def _assert_annotation_has_no_wire_types(annotation: object) -> None:
    for candidate in _nested_types(annotation):
        assert candidate is not Any, "public annotations must not use Any"
        if inspect.isclass(candidate):
            assert not issubclass(candidate, Message), (
                f"public annotation leaks protobuf type {candidate!r}"
            )
            assert not issubclass(candidate, Descriptor), (
                f"public annotation leaks protobuf descriptor {candidate!r}"
            )


def _assert_public_method_contract(cls: type[object], names: set[str]) -> None:
    for name in names:
        method = getattr(cls, name)
        signature = inspect.signature(method)
        hints = get_type_hints(method)
        for parameter in signature.parameters.values():
            if parameter.name in {"self", "cls"}:
                continue
            assert parameter.name in hints, (
                f"{cls.__name__}.{name} lacks an argument type"
            )
            _assert_annotation_has_no_wire_types(hints[parameter.name])
        assert "return" in hints, f"{cls.__name__}.{name} lacks a return type"
        _assert_annotation_has_no_wire_types(hints["return"])


def _assert_all_public_members_are_typed(cls: type[object]) -> None:
    for name in dir(cls):
        if name.startswith("_"):
            continue
        member = inspect.getattr_static(cls, name)
        if isinstance(member, property):
            assert member.fget is not None
            hints = get_type_hints(member.fget)
            assert "return" in hints, f"{cls.__name__}.{name} lacks a return type"
            _assert_annotation_has_no_wire_types(hints["return"])
        elif inspect.isfunction(member):
            _assert_public_method_contract(cls, {name})


def _assert_no_protobuf_value(value: object) -> None:
    assert not isinstance(value, Message), f"raw protobuf escaped: {type(value)!r}"
    if isinstance(value, BaseModel):
        for field_name in type(value).model_fields:
            _assert_no_protobuf_value(getattr(value, field_name))
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _assert_no_protobuf_value(key)
            _assert_no_protobuf_value(item)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            _assert_no_protobuf_value(item)


def test_top_level_exports_do_not_include_wire_modules_or_codecs() -> None:
    forbidden = {
        "client_pb2",
        "common_pb2",
        "sliver_pb2",
        "protobuf_to_pydantic",
        "pydantic_to_protobuf",
    }

    assert forbidden.isdisjoint(sliver.__all__)
    assert all(not hasattr(sliver, name) for name in forbidden)
    assert importlib.util.find_spec("sliver.pb") is None
    assert importlib.util.find_spec("sliver.protobuf") is None


def test_model_module_only_publishes_pydantic_models_and_python_enums() -> None:
    forbidden = {
        "MODEL_BY_DESCRIPTOR",
        "MODEL_BY_PROTOBUF_CLASS",
        "protobuf_to_pydantic",
        "pydantic_to_protobuf",
    }

    assert forbidden.isdisjoint(models.__all__)
    assert all(not hasattr(models, name) for name in forbidden)
    assert all(
        issubclass(model_type, models.ProtobufModel)
        for model_type in models.MODEL_REGISTRY.values()
    )
    assert all(
        issubclass(enum_type, IntEnum)
        for enum_type in models.ENUM_REGISTRY.values()
    )


def test_public_model_instances_have_no_wire_escape_hatches() -> None:
    model = models.clientpb.Session(id="session-id", name="session")

    for name in (
        "from_protobuf",
        "to_protobuf",
        "__protobuf_class__",
        "__protobuf_descriptor__",
    ):
        assert not hasattr(model, name)
        assert not hasattr(type(model), name)


def test_all_previously_implemented_client_and_interactive_features_remain() -> None:
    assert CLIENT_FEATURES <= set(dir(SliverClient))
    assert INTERACTIVE_FEATURES | SESSION_ONLY_FEATURES <= set(dir(InteractiveSession))
    assert INTERACTIVE_FEATURES | {"close"} <= set(dir(InteractiveBeacon))
    assert not hasattr(InteractiveBeacon, "getsystem")
    assert not hasattr(InteractiveBeacon, "extensions_list")


def test_public_method_signatures_never_reference_protobuf_or_any() -> None:
    _assert_public_method_contract(SliverClient, CLIENT_FEATURES)
    _assert_public_method_contract(
        InteractiveSession, INTERACTIVE_FEATURES | SESSION_ONLY_FEATURES
    )
    _assert_public_method_contract(InteractiveBeacon, INTERACTIVE_FEATURES | {"close"})

    for constructor in (
        BaseClient.__init__,
        InteractiveSession.__init__,
        InteractiveBeacon.__init__,
    ):
        hints = get_type_hints(constructor)
        for name, annotation in hints.items():
            if name != "return":
                _assert_annotation_has_no_wire_types(annotation)

    for public_class in (SliverClient, InteractiveSession, InteractiveBeacon):
        _assert_all_public_members_are_typed(public_class)


def test_session_and_beacon_share_the_same_typed_interactive_signatures() -> None:
    for name in INTERACTIVE_FEATURES:
        session_method = getattr(InteractiveSession, name)
        beacon_method = getattr(InteractiveBeacon, name)
        assert inspect.signature(beacon_method) == inspect.signature(session_method)
        assert get_type_hints(beacon_method) == get_type_hints(session_method)


def test_public_entity_properties_return_detached_pydantic_models() -> None:
    session = InteractiveSession.__new__(InteractiveSession)
    session._session = models.clientpb.Session(id="session-id", name="original")
    beacon = InteractiveBeacon.__new__(InteractiveBeacon)
    beacon._beacon = models.clientpb.Beacon(id="beacon-id", name="original")

    session_model = session.session
    beacon_model = beacon.beacon
    _assert_no_protobuf_value(session_model)
    _assert_no_protobuf_value(beacon_model)
    assert isinstance(session_model, models.clientpb.Session)
    assert isinstance(beacon_model, models.clientpb.Beacon)

    session_model.name = "changed"
    beacon_model.name = "changed"
    assert session.name == "original"
    assert beacon.name == "original"


@pytest.mark.parametrize(
    ("model", "wire_model"),
    [
        (
            models.clientpb.Sessions(
                sessions=[models.clientpb.Session(id="one", name="session")]
            ),
            client_pb2.Sessions(Sessions=[client_pb2.Session(ID="one")]),
        ),
        (
            models.clientpb.Beacons(
                beacons=[models.clientpb.Beacon(id="two", name="beacon")]
            ),
            client_pb2.Beacons(Beacons=[client_pb2.Beacon(ID="two")]),
        ),
    ],
)
def test_recursive_public_values_contain_no_raw_protobuf(
    model: models.ProtobufModel, wire_model: Message
) -> None:
    _assert_no_protobuf_value(model)
    with pytest.raises(AssertionError, match="raw protobuf escaped"):
        _assert_no_protobuf_value(wire_model)


def test_raw_stub_is_not_part_of_the_client_api() -> None:
    assert "raw_stub" not in dir(BaseClient)
    assert "raw_stub" not in dir(SliverClient)
