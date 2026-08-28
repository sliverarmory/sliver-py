Getting started
===============

SliverPy connects to a Sliver server's multiplayer gRPC endpoint. The v0.1 API
is generated from the Sliver protobuf definitions at the submodule commit
pinned by this release. For strict compatibility, build the server from that
commit rather than assuming a later Sliver release or ``master`` revision has
the same API.

Create an operator configuration
--------------------------------

An operator configuration contains the per-user private key, TLS certificate,
and connection metadata used for mutual TLS authentication. Treat the file as a
credential and do not commit it to source control.

From the Sliver interactive console, create an operator and start multiplayer
mode:

.. code-block:: console

    $ ./sliver-server

    sliver > new-operator --name zer0cool --lhost localhost --save ./zer0cool.cfg
    [*] Generating new client certificate, please wait ...
    [*] Saved new client config to: /Users/zer0cool/zer0cool.cfg

    sliver > multiplayer
    [*] Multiplayer mode enabled!

The server command-line interface can perform the same setup without entering
the interactive console:

.. code-block:: console

    $ ./sliver-server operator --name zer0cool --lhost localhost --save ./zer0cool.cfg
    $ ./sliver-server daemon

Connect from Python
-------------------

SliverPy uses ``asyncio``. Pair :class:`sliver.SliverClient` with an operator
configuration, then await ``connect()`` before making API calls:

.. code-block:: python

    #!/usr/bin/env python3

    import asyncio
    from pathlib import Path

    from sliver import SliverClient, SliverClientConfig

    CONFIG_PATH = Path.home() / ".sliver-client" / "configs" / "default.cfg"


    async def main():
        config = SliverClientConfig.parse_config_file(CONFIG_PATH)
        client = SliverClient(config)
        try:
            version = await client.connect()
            print(
                f"Connected to Sliver "
                f"{version.major}.{version.minor}.{version.patch}"
            )

            sessions = await client.sessions()
            for session in sessions:
                print(session.id, session.name, session.remote_address)
        finally:
            await client.close()


    if __name__ == "__main__":
        asyncio.run(main())

Pydantic models
---------------

Public request and response objects are Pydantic models generated from the
bundled protobuf descriptors. Each type lives at
``sliver.models.<package>.<Type>`` and exposes ``snake_case`` fields. Import the
``models`` object itself; ``clientpb``, ``commonpb``, and ``sliverpb`` are
runtime attribute namespaces, not importable Python submodules:

.. code-block:: python

    from sliver import models

    request = models.clientpb.RenameReq(
        session_id="session-id",
        name="web-server",
    )
    print(request.session_id, request.name)

At validation boundaries, the original protobuf names are aliases. This is
useful when migrating existing protobuf-shaped input:

.. code-block:: python

    request = models.clientpb.RenameReq.model_validate(
        {"SessionID": "session-id", "Name": "web-server"}
    )
    assert request.session_id == "session-id"

Normal client calls automatically convert models to protobuf before an RPC and
convert protobuf responses back to models. Use ``to_protobuf()`` and
``from_protobuf()`` when an explicit conversion is needed:

.. code-block:: python

    protobuf_request = request.to_protobuf()
    restored = models.clientpb.RenameReq.from_protobuf(protobuf_request)

See :doc:`models` for model namespaces, serialization, automatic RPC-boundary
conversion, and the raw protobuf escape hatch.

Nested models and enums
-----------------------

Construct nested messages and generated enums with the same namespace. For
example, :meth:`sliver.SliverClient.generate_implant` accepts a Pydantic
``ImplantConfig`` and returns a Pydantic ``Generate`` model:

.. code-block:: python

    from sliver import models

    implant_config = models.clientpb.ImplantConfig(
        goos="linux",
        goarch="amd64",
        format=models.clientpb.OutputFormat.EXECUTABLE,
        c2=[models.clientpb.ImplantC2(url="mtls://127.0.0.1:8888")],
        include_mtls=True,
    )
    generated = await client.generate_implant(implant_config)
    print(generated.implant_name)
    if generated.file is not None:
        print(generated.file.name, len(generated.file.data))

Interactive sessions
--------------------

Pass a session model's ``id`` to ``interact_session()`` to create an
:class:`sliver.InteractiveSession`:

.. code-block:: python

    sessions = await client.sessions()
    if not sessions:
        print("No sessions")
        return

    session = await client.interact_session(sessions[0].id)
    if session is None:
        print("Session disconnected")
        return

    listing = await session.ls()
    print(f"Listing directory contents of {listing.path}")
    for file_info in listing.files:
        print(
            f"{file_info.name} "
            f"(dir={file_info.is_dir}, size={file_info.size})"
        )

The session model at ``sliver.models.clientpb.Session`` contains metadata about
the connection. ``InteractiveSession`` performs commands against that session
and shares the client's channel, so closing the client releases its resources.

Interactive beacons
-------------------

Pass a beacon model's ``id`` to ``interact_beacon()``. SliverPy waits for the
asynchronous beacon task internally, so each command needs only one ``await``:

.. code-block:: python

    beacons = await client.beacons()
    if not beacons:
        print("No beacons")
        return

    beacon = await client.interact_beacon(beacons[0].id)
    if beacon is None:
        print("Beacon disappeared")
        return

    try:
        listing = await beacon.ls()

        print(f"Listing directory contents of {listing.path}")
        for file_info in listing.files:
            print(
                f"{file_info.name} "
                f"(dir={file_info.is_dir}, size={file_info.size})"
            )
    finally:
        await beacon.close()

``InteractiveBeacon.close()`` stops the local task-result watcher and cancels
pending local commands. It does not terminate or remove the remote beacon.

Realtime events
---------------

``client.events()`` is an async generator of
``sliver.models.clientpb.Event`` objects. ``client.on()`` filters that stream by
one event type or a list of event types. Event payload fields depend on the
producer, so check optional fields such as ``event.session`` before using them.

Common event types include:

==========================  ================================================
Event type                  Description
==========================  ================================================
``session-connected``       A new session connected
``session-disconnected``    An existing session was lost
``session-updated``         Session metadata changed
``job-started``             A server job started
``job-stopped``             A server job stopped
``client-joined``           An operator client connected
``client-left``             An operator client disconnected
``canary``                  A canary was triggered
``build``                   An implant build changed
``build-completed``         An implant build completed
``profile``                 An implant profile changed
``website``                 Website content changed
``beacon-registered``       A beacon connected
``beacon-taskresult``       A beacon task completed
==========================  ================================================

For example, automatically interact with newly connected sessions:

.. code-block:: python

    import asyncio
    from pathlib import Path

    from sliver import SliverClient, SliverClientConfig

    CONFIG_PATH = Path.home() / ".sliver-client" / "configs" / "default.cfg"


    async def main():
        config = SliverClientConfig.parse_config_file(CONFIG_PATH)
        client = SliverClient(config)
        try:
            await client.connect()

            async for event in client.on("session-connected"):
                if event.session is None:
                    continue
                print(f"Interacting with session {event.session.id}")
                session = await client.interact_session(event.session.id)
                if session is not None:
                    result = await session.execute("whoami", [], output=True)
                    print(result)
        finally:
            await client.close()


    if __name__ == "__main__":
        asyncio.run(main())
