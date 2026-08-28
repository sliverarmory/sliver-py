Pydantic models and protobuf interoperability
=============================================

SliverPy v0.1 exposes Pydantic models at its public API. The model classes are
created automatically from the protobuf descriptors shipped with the package,
so the validation layer tracks the exact Sliver definitions at the submodule
commit pinned by this release.

Model namespaces
----------------

Every top-level message and enum is available as
``sliver.models.<package>.<Type>``. The three primary namespaces are:

* ``sliver.models.clientpb`` for messages exchanged between an operator client
  and the Sliver server;
* ``sliver.models.commonpb`` for messages shared by multiple protobuf packages;
* ``sliver.models.sliverpb`` for messages exchanged with implants.

These are read-only runtime attribute namespaces. Import them through
``from sliver import models`` rather than trying to import ``clientpb``,
``commonpb``, or ``sliverpb`` as Python submodules. Nested messages and enums
remain on their containing model, for example
``models.sliverpb.SockTabEntry.SockAddr``. Synthetic protobuf map-entry
messages become normal Python dictionaries and are not published as models.

For example, construct request and nested models directly:

.. code-block:: python

    from sliver import models

    request = models.clientpb.RenameReq(
        session_id="session-id",
        name="web-server",
    )
    listing = models.sliverpb.Ls(
        path="/tmp",
        files=[
            models.sliverpb.FileInfo(
                name="payload.bin",
                is_dir=False,
                size=4096,
            )
        ],
    )
    address = models.sliverpb.SockTabEntry.SockAddr(
        ip="127.0.0.1",
        port=8888,
    )

The generated classes inherit from :class:`sliver.models.ProtobufModel`, which
in turn inherits from Pydantic's ``BaseModel``. Standard Pydantic operations
such as ``model_validate()``, ``model_dump()``, ``model_dump_json()``, and
``model_json_schema()`` are therefore available.

Generated enums live in the same namespaces and inherit from
:class:`sliver.models.ProtobufEnum`, which is an ``IntEnum``. Use an enum member
or its integer value when validating an enum field; enum-name strings are not
accepted.

.. code-block:: python

    config = models.clientpb.ImplantConfig(
        goos="linux",
        goarch="amd64",
        format=models.clientpb.OutputFormat.EXECUTABLE,
        c2=[models.clientpb.ImplantC2(url="mtls://127.0.0.1:8888")],
        include_mtls=True,
    )

Python field names and protobuf aliases
---------------------------------------

Model attributes use ``snake_case`` even when Sliver's protobuf field uses a
different spelling. Common mappings include ``ID`` to ``id``, ``SessionID`` to
``session_id``, ``RemoteAddress`` to ``remote_address``, and
``timezoneOffset`` to ``timezone_offset``.

Use the Python spelling when constructing or reading a model:

.. code-block:: python

    session = models.clientpb.Session(
        id="session-id",
        name="web-server",
        remote_address="192.0.2.10:31337",
    )
    print(session.id, session.name)

The original protobuf field name and its protobuf JSON name are accepted as
validation aliases. This makes existing protobuf-shaped dictionaries useful at
input boundaries without exposing those names as Python attributes:

.. code-block:: python

    request = models.clientpb.RenameReq.model_validate(
        {"SessionID": "session-id", "Name": "web-server"}
    )
    assert request.session_id == "session-id"

``model_dump()`` uses ``snake_case`` keys by default. Pass ``by_alias=True``
when a mapping must use the original protobuf field names:

.. code-block:: python

    python_data = request.model_dump()
    protobuf_shaped_data = request.model_dump(by_alias=True)

The alias dump is a Pydantic mapping with protobuf-shaped keys, not canonical
protobuf JSON. In particular, normal ``model_dump()`` values retain Python
``bytes`` and enum objects, while ``model_dump_json()`` encodes bytes as
URL-safe base64 and enums as integers:

.. code-block:: python

    import json

    artifact = models.commonpb.File(name="payload.bin", data=b"\x00\xff")
    assert artifact.model_dump()["data"] == b"\x00\xff"
    assert json.loads(artifact.model_dump_json())["data"] == "AP8="

Use ``to_protobuf()`` when code needs protobuf binary serialization or canonical
protobuf JSON behavior.

Field shapes and validation
---------------------------

The generated annotations mirror protobuf field semantics:

* repeated fields are ``list`` values and map fields are ``dict`` values, each
  with a fresh empty default;
* message fields, explicit ``optional`` fields, and ``oneof`` members use
  ``T | None`` so field presence can be preserved;
* ordinary proto3 scalar fields use their protobuf default values;
* protobuf integer bit-width bounds are enforced; and
* assigning to an existing field is validated, while unknown fields are
  rejected.

Setting a presence-bearing scalar to its default value is different from
leaving it as ``None``: the former remains present after ``to_protobuf()`` and
the latter is omitted. A ``oneof`` accepts at most one populated member.
Unknown integer values in open proto3 enums are retained as synthetic members
named ``UNRECOGNIZED_<value>`` for forward compatibility.

Names that conflict with Python keywords or Pydantic attributes gain a trailing
underscore. For example, construct Sliver's protobuf ``Async`` field as
``async_``:

.. code-block:: python

    routing = models.commonpb.Request(
        beacon_id="beacon-id",
        timeout=30,
        async_=True,
    )

Explicit conversion
-------------------

Every model converts to and from its generated protobuf message class.
Conversion preserves all fields known to the bundled descriptors and
recursively handles nested messages, repeated fields, maps, enums, optional
fields, and ``oneof`` validation.

.. code-block:: python

    request = models.sliverpb.LsReq(path="/tmp")
    protobuf_request = request.to_protobuf()
    restored = models.sliverpb.LsReq.from_protobuf(protobuf_request)

    assert restored == request

Unknown protobuf fields are not retained after conversion through a Pydantic
model. Use the raw protobuf API when exact preservation of a wire message from a
newer server is required.

Use :func:`sliver.get_pydantic_model` when code starts with a protobuf class,
instance, descriptor, or fully qualified protobuf message name and needs the
corresponding Pydantic class. The recursive :func:`sliver.protobuf_to_pydantic`
and :func:`sliver.pydantic_to_protobuf` helpers are also available for adapter
code.

Automatic RPC conversion
------------------------

Normal :class:`sliver.SliverClient`, :class:`sliver.InteractiveSession`, and
:class:`sliver.InteractiveBeacon` methods use Pydantic models. At the gRPC
boundary, SliverPy automatically converts request models to generated protobuf
messages and converts unary or streamed protobuf responses back to models.

Collection helpers such as ``sessions()``, ``beacons()``, and ``jobs()`` unwrap
protobuf container messages into normal Python lists of Pydantic models. Other
high-level methods return one Pydantic response model or ``None`` as documented
by their type annotation.

The client's public :attr:`sliver.client.BaseClient.pydantic_stub` follows the
same rule, which is useful for an RPC that does not yet have a high-level
convenience method:

.. code-block:: python

    request = models.clientpb.RenameReq(
        session_id="session-id",
        name="web-server",
    )
    await client.pydantic_stub.Rename(request)

The converted and raw stubs are initialized by ``await client.connect()`` and
become unavailable again after ``await client.close()``.

Raw protobuf escape hatch
-------------------------

Use :attr:`sliver.client.BaseClient.raw_stub` when exact generated protobuf
behavior is required. Raw RPC methods accept and return generated protobuf
messages; they do not perform Pydantic conversion.

.. code-block:: python

    from sliver.pb.clientpb import client_pb2

    raw_request = client_pb2.RenameReq(
        SessionID="session-id",
        Name="web-server",
    )
    await client.raw_stub.Rename(raw_request)

The generated modules live under ``sliver.pb``:

* ``sliver.pb.clientpb.client_pb2``;
* ``sliver.pb.commonpb.common_pb2``;
* ``sliver.pb.sliverpb.sliver_pb2``;
* ``sliver.pb.rpcpb.services_pb2_grpc``.

These modules are the low-level wire implementation and intentionally retain
protobuf field spellings such as ``SessionID`` and ``Name``. Prefer
``sliver.models`` unless integration code specifically requires protobuf
messages.

Model API reference
-------------------

.. autoclass:: sliver.models.ProtobufModel
   :members: from_protobuf, to_protobuf

.. autoclass:: sliver.models.ProtobufEnum
   :members:

.. autofunction:: sliver.get_pydantic_model

.. autofunction:: sliver.protobuf_to_pydantic

.. autofunction:: sliver.pydantic_to_protobuf
