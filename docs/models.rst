Pydantic models and protobuf interoperability
=============================================

SliverPy v0.1 exposes Pydantic models at its public API. The model classes are
created automatically from the protobuf descriptors shipped with the package,
so the validation layer tracks the exact Sliver ``master`` definitions used to
generate the bundled gRPC client.

Model namespaces
----------------

Every message is available as ``sliver.models.<package>.<Message>``. The three
primary namespaces are:

* ``sliver.models.clientpb`` for messages exchanged between an operator client
  and the Sliver server;
* ``sliver.models.commonpb`` for messages shared by multiple protobuf packages;
* ``sliver.models.sliverpb`` for messages exchanged with implants.

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

The generated classes inherit from :class:`sliver.models.ProtobufModel`, which
in turn inherits from Pydantic's ``BaseModel``. Standard Pydantic operations
such as ``model_validate()``, ``model_dump()``, ``model_dump_json()``, and
``model_json_schema()`` are therefore available.

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

Explicit conversion
-------------------

Every model supports lossless conversion to and from its generated protobuf
message class. Conversion recursively handles nested messages, repeated fields,
maps, enums, optional fields, and ``oneof`` validation.

.. code-block:: python

    request = models.sliverpb.LsReq(path="/tmp")
    protobuf_request = request.to_protobuf()
    restored = models.sliverpb.LsReq.from_protobuf(protobuf_request)

    assert restored == request

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

The client's converted low-level stub follows the same rule, which is useful
for an RPC that does not yet have a high-level convenience method:

.. code-block:: python

    request = models.clientpb.RenameReq(
        session_id="session-id",
        name="web-server",
    )
    await client._stub.Rename(request)

The converted and raw stubs are initialized by ``await client.connect()``.

Raw protobuf escape hatch
-------------------------

Use :attr:`sliver.SliverClient.raw_stub` when exact generated protobuf behavior
is required. Raw RPC methods accept and return generated protobuf messages;
they do not perform Pydantic conversion.

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
