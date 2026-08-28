Pydantic model API
==================

SliverPy v0.1 has a strict Pydantic-only public boundary. Client, session,
beacon, event, and low-level RPC methods accept and return Pydantic models,
standard Python containers, or primitive Python values. The model classes are
generated from the Sliver descriptors shipped at the exact submodule commit
pinned by this repository, while generated transport messages remain private
implementation details.

Model modules
-------------

Every top-level message and enum is a concrete class in one of three importable
Python modules:

* ``sliver.models.clientpb`` for server and operator-client models;
* ``sliver.models.commonpb`` for models shared across the API; and
* ``sliver.models.sliverpb`` for implant command and result models.

Import classes directly when writing annotations or constructing values. This
gives static type checkers the real class definition instead of an untyped
dynamic lookup. Nested messages and enums remain attributes of their containing
model, for example ``SockTabEntry.SockAddr``. Synthetic map-entry messages
become normal Python dictionaries and are not published as separate model
classes.

Construct top-level and nested models directly:

.. code-block:: python

    from sliver.models.clientpb import RenameReq
    from sliver.models.sliverpb import FileInfo, Ls, SockTabEntry

    request = RenameReq(
        session_id="session-id",
        name="web-server",
    )
    listing = Ls(
        path="/tmp",
        files=[
            FileInfo(
                name="payload.bin",
                is_dir=False,
                size=4096,
            )
        ],
    )
    address = SockTabEntry.SockAddr(
        ip="127.0.0.1",
        port=8888,
    )

Generated classes inherit from :class:`sliver.models.ProtobufModel`, which
inherits from Pydantic's ``BaseModel``. Standard operations such as
``model_validate()``, ``model_dump()``, ``model_dump_json()``, and
``model_json_schema()`` are available.

Enums and structured arguments
------------------------------

Generated enums live in the same modules and inherit from
:class:`sliver.models.ProtobufEnum`, an ``IntEnum``. Use an enum member or its
integer value when validating an enum field; enum-name strings are not
accepted. Structured client and interactive arguments use generated model or
enum types rather than untyped mappings.

For example, :meth:`sliver.SliverClient.generate_implant` accepts a Pydantic
``ImplantConfig`` and returns a Pydantic ``Generate`` model:

.. code-block:: python

    from sliver.models.clientpb import ImplantC2, ImplantConfig, OutputFormat

    config = ImplantConfig(
        goos="linux",
        goarch="amd64",
        format=OutputFormat.EXECUTABLE,
        c2=[ImplantC2(url="mtls://127.0.0.1:8888")],
        include_mtls=True,
    )
    generated = await client.generate_implant(config)
    print(generated.implant_name)

Open enums retain unknown integer values as synthetic members named
``UNRECOGNIZED_<value>``. This lets a model represent a value added by a newer
server without silently replacing it.

Python field names and validation aliases
-----------------------------------------

Model attributes use ``snake_case`` even when the Sliver schema uses another
spelling. Common mappings include ``ID`` to ``id``, ``SessionID`` to
``session_id``, ``RemoteAddress`` to ``remote_address``, and
``timezoneOffset`` to ``timezone_offset``.

Use Python spelling when constructing or reading a model:

.. code-block:: python

    from sliver.models.clientpb import Session

    session = Session(
        id="session-id",
        name="web-server",
        remote_address="192.0.2.10:31337",
    )
    print(session.id, session.name)

Original schema field names and their JSON spellings are accepted as validation
aliases. They are input aliases, not Python attributes:

.. code-block:: python

    from sliver.models.clientpb import RenameReq

    request = RenameReq.model_validate(
        {"SessionID": "session-id", "Name": "web-server"}
    )
    assert request.session_id == "session-id"

``model_dump()`` uses ``snake_case`` keys by default. Pass ``by_alias=True``
only when a mapping needs schema-shaped keys:

.. code-block:: python

    python_data = request.model_dump()
    schema_shaped_data = request.model_dump(by_alias=True)

The alias dump is still a normal Pydantic mapping. It is not a transport
message or a special wire serialization.

Serialization
-------------

``model_dump()`` preserves Python values such as ``bytes`` and enum members.
``model_dump_json()`` emits JSON, encoding bytes as URL-safe base64 and enums as
integers:

.. code-block:: python

    import json

    from sliver.models.commonpb import File

    artifact = File(name="payload.bin", data=b"\x00\xff")
    assert artifact.model_dump()["data"] == b"\x00\xff"
    assert json.loads(artifact.model_dump_json())["data"] == "AP8="

``model_validate_json()`` accepts the same base64 representation and restores a
``bytes`` value.

Field shapes, presence, and validation
--------------------------------------

Generated annotations follow the source schema:

* repeated fields are independent ``list`` values;
* map fields are independent ``dict`` values;
* nested-message fields, explicit optional fields, and one-of members use
  ``T | None`` where field presence matters;
* ordinary scalar fields use their declared default values; and
* integer bit-width bounds are enforced.

At most one member of a one-of group may be populated. For a presence-bearing
scalar, assigning its default value is distinct from leaving it as ``None``.
Unknown fields are rejected, and assignment to an existing field is validated:

.. code-block:: python

    from sliver.models.commonpb import Request

    request = Request(timeout=30)
    request.timeout = 60

    # Raises a Pydantic validation error: timeout must remain an integer.
    request.timeout = "soon"

Names that conflict with Python keywords or Pydantic attributes gain a trailing
underscore. For example, construct Sliver's ``Async`` field as ``async_``:

.. code-block:: python

    from sliver.models.commonpb import Request

    routing = Request(
        beacon_id="beacon-id",
        timeout=30,
        async_=True,
    )

Looking up model classes
------------------------

:func:`sliver.get_pydantic_model` returns a generated model class from its
fully qualified name, a unique unqualified name, or an existing
:class:`sliver.models.ProtobufModel` subclass:

.. code-block:: python

    from sliver import get_pydantic_model
    from sliver.models.clientpb import Session

    session_type = get_pydantic_model("clientpb.Session")
    assert session_type is Session
    assert get_pydantic_model(session_type) is session_type

Ambiguous short names raise ``KeyError``; callers can resolve them with the
fully qualified name.

Automatic RPC boundary
----------------------

Normal :class:`sliver.SliverClient`, :class:`sliver.InteractiveSession`, and
:class:`sliver.InteractiveBeacon` methods use Pydantic model annotations for
structured arguments and results. Collection helpers such as ``sessions()``,
``beacons()``, and ``jobs()`` return normal Python lists of Pydantic models.
Other high-level methods return one Pydantic model, a standard container, a
primitive value, or ``None`` exactly as declared by their type annotation.

The client's :attr:`sliver.client.BaseClient.pydantic_stub` is the supported
low-level extension point for an RPC without a convenience method. It requires
that RPC's Pydantic request model and returns its Pydantic response model:

.. code-block:: python

    from sliver.models.clientpb import RenameReq

    request = RenameReq(
        session_id="session-id",
        name="web-server",
    )
    response = await client.pydantic_stub.Rename(request)

The stub supports unary and streaming calls while preserving the Pydantic-only
request and response boundary. It is available only after
``await client.connect()`` and becomes unavailable after
``await client.close()``. Passing a generated transport message is a type error.

Session and beacon model snapshots
----------------------------------

An :class:`sliver.InteractiveSession` is constructed from a
``sliver.models.clientpb.Session``. Its ``session`` property returns a
defensive copy of that complete Pydantic model, and convenience properties
expose common scalar fields. The interaction owns no separate channel; close
its parent client when finished.

An :class:`sliver.InteractiveBeacon` similarly exposes a defensive copy through
its ``beacon`` property. It also owns a local task-result watcher. Call
``await beacon.close()`` before closing the parent client; this cancels pending
local commands but does not terminate or delete the remote beacon.

Model API reference
-------------------

.. autoclass:: sliver.models.ProtobufModel
   :members:

.. autoclass:: sliver.models.ProtobufEnum
   :members:

.. autofunction:: sliver.get_pydantic_model
