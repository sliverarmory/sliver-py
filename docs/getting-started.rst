Getting started
===============

SliverPy connects to a Sliver server's multiplayer gRPC endpoint. The v0.1 API
is generated from the Sliver definitions at the exact submodule commit recorded
by this repository. For reproducible development and testing, build the server
from that pinned commit rather than assuming another Sliver revision has the
same API.

Create an operator configuration
--------------------------------

An operator configuration contains a per-user private key, TLS certificate,
token, and connection metadata. Treat the file as a credential and do not
commit it to source control.

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

Connect with an owned client
----------------------------

SliverPy uses ``asyncio``. :meth:`sliver.Client.from_config_file` constructs a
validated client and resolves the configuration path in this order:

#. an explicit path passed to the factory;
#. the ``SLIVER_CONFIG`` environment variable; and
#. ``~/.sliver-client/configs/default.cfg``.

Use the client as an async context manager. Entering connects it; exiting stops
its event/task dispatcher before closing the gRPC channel, even if the body
raises:

.. code-block:: python

    #!/usr/bin/env python3

    import asyncio

    from sliver import Client


    async def main() -> None:
        async with Client.from_config_file() as client:
            version = await client.version()
            print(
                f"Connected to Sliver "
                f"{version.major}.{version.minor}.{version.patch}"
            )

            inventory = await client.inventory()
            for session in inventory.sessions:
                print(session.id, session.name, session.remote_address)


    if __name__ == "__main__":
        asyncio.run(main())

For dependency injection or programmatic configuration, construct an
:class:`sliver.OperatorConfig` and pass it to :class:`sliver.Client`. Manual
ownership also remains supported with ``await client.connect()`` and
``await client.close()``; ``close()`` and ``aclose()`` are idempotent, and a
closed client can be connected again.

Use enums and domain models
---------------------------

The package root exports typed constants for operating systems, architectures,
event names, protocols, output formats, encoders, registry values, and other
closed sets. String-valued enums also subclass ``str`` for compatibility with
existing validation and serialization boundaries. Prefer members such as
:attr:`sliver.GOOS.LINUX`, :attr:`sliver.GOARCH.AMD64`, and
:attr:`sliver.EventType.SESSION_CONNECTED` over repeated literal strings.

Common multi-field workflows use small Pydantic domain models. For example,
:class:`sliver.ImplantSpec` validates a target, C2 endpoints, beacon timing, and
output settings before converting them to Sliver's generated request models:

.. code-block:: python

    import asyncio
    from pathlib import Path

    from sliver import (
        BeaconOptions,
        C2Endpoint,
        Client,
        GOARCH,
        GOOS,
        ImplantSpec,
        OutputFormat,
        Target,
    )


    async def main() -> None:
        async with Client.from_config_file() as client:
            result = await client.generate(
                ImplantSpec(
                    target=Target(os=GOOS.LINUX, arch=GOARCH.AMD64),
                    c2=[C2Endpoint.mtls("c2.example.test")],
                    output_format=OutputFormat.EXECUTABLE,
                    beacon=BeaconOptions(),
                ),
                name="web-server",
            )
            destination = result.save(Path("artifacts") / result.filename)
            print(destination)


    asyncio.run(main())

The generated :class:`sliver.GeneratedImplant` contains the artifact and build
metadata. Its ``save()`` method creates the destination exclusively by default;
pass ``overwrite=True`` only when replacement is intentional. Advanced fields
that are not represented by :class:`sliver.ImplantSpec` can be supplied through
``generate(..., base_config=...)``. The concise fields always take precedence.

See :doc:`api/domain` and :doc:`api/enums` for the complete human-facing model
and constant surface. See :doc:`models` for descriptor-generated Pydantic
models.

Find, get, and use resources
----------------------------

Collection commands such as :meth:`sliver.Client.sessions`,
:meth:`sliver.Client.beacons`, and :meth:`sliver.Client.jobs` return normal
lists of generated Pydantic models. The lookup verbs encode absence explicitly:

* ``find_session()``, ``find_beacon()``, and ``find_job()`` return ``None``;
* ``get_session()``, ``get_beacon()``, and ``get_job()`` raise
  :class:`sliver.ResourceNotFoundError`; and
* ``use_session()``, ``use_beacon()``, and ``use(model)`` return an interactive
  wrapper or raise :class:`sliver.ResourceNotFoundError`.

For example:

.. code-block:: python

    sessions = await client.sessions()
    if sessions:
        session = await client.use(sessions[0])
        listing = await session.ls()
        for entry in listing.files:
            print(entry.name, entry.is_dir, entry.size)

An interaction's ``session`` or ``beacon`` property returns a defensive copy of
the complete metadata model. Convenience properties expose common fields such
as IDs, hostnames, operating systems, architectures, and process IDs. Both
interaction types share the parent client's channel.

Beacon tasks and lifecycle commands
-----------------------------------

An :class:`sliver.InteractiveBeacon` command queues a remote task and awaits its
typed result, so callers use the same one-``await`` shape as a session command:

.. code-block:: python

    beacons = await client.beacons()
    if beacons:
        beacon = await client.use(beacons[0])
        listing = await beacon.ls()
        print(listing.path)

The client owns one lazy event dispatcher shared by all beacon task waiters and
event subscribers. Completion events that arrive just before waiter
registration are retained in a bounded orphan cache so fast tasks are not lost.
Success, command error, timeout, and cancellation all remove the local waiter.
On timeout or local cancellation, SliverPy also asks the server to cancel the
remote task when that RPC is supported. A deadline raises
:class:`sliver.SliverTimeoutError`; cancelling the caller preserves
``asyncio.CancelledError``.

``InteractiveBeacon.close()`` remains safe for compatibility. A wrapper
obtained from :class:`sliver.Client` does not own the shared dispatcher, so
closing that wrapper does not stop other subscriptions or task waits. Closing
an interaction never kills or removes the remote beacon.

The command-aligned lifecycle methods have intentionally different meanings:

* ``kill_beacon(beacon_id, force=False)`` queues Sliver's ``kill`` command for
  the beacon and terminates the implant process when it executes; and
* ``beacons_rm(beacon_id)`` invokes ``beacons rm`` and removes the server record
  without terminating a running implant.

Use ``tasks(beacon_id)``, ``tasks_fetch(task_id)``, and
``tasks_cancel(task_id)`` for Sliver's task-management command paths.

Subscribe to realtime events
----------------------------

:meth:`sliver.Client.events` is an async generator of
``sliver.models.clientpb.Event`` objects. It accepts one
:class:`sliver.EventType`, a string, a collection of either, or no filter:

.. code-block:: python

    from sliver import EventType

    async for event in client.events(EventType.SESSION_CONNECTED):
        if event.session is not None:
            session = await client.use(event.session)
            print(await session.execute("whoami"))

For a bounded result, :meth:`sliver.Client.collect_events` owns and closes the
subscription:

.. code-block:: python

    events = await client.collect_events(
        EventType.JOB_STARTED,
        EventType.JOB_STOPPED,
        limit=2,
        timeout=30,
    )

All subscribers share one underlying ``Events`` RPC. Each subscriber has a
bounded queue; if it falls behind, the oldest queued event is discarded in
favor of the newest, so this stream is not a durable replay log. Closing an
async generator unregisters its subscriber. Closing the client closes every
subscriber. An unexpected stream interruption is retried with capped
exponential backoff; pending beacon command deadlines remain authoritative.

The older ``on(event_types)`` spelling is a compatibility alias for filtered
``events(event_types)`` iteration.

Use the Pydantic RPC escape hatch
---------------------------------

If an RPC has no command-oriented convenience method, use ``client.rpc`` after
connecting. It exposes every Sliver RPC with a snake-case Python name, validates
the declared Pydantic request type, and returns the declared Pydantic response:

.. code-block:: python

    from sliver.models.clientpb import RenameReq

    request = RenameReq(
        session_id="session-id",
        name="web-server",
    )
    await client.rpc.rename(request)

The generated wire implementation remains private: external callers neither
pass nor receive transport messages. Accessing ``rpc`` before connecting or
after closing raises :class:`sliver.NotConnectedError`. The historical
``pydantic_stub`` property and PascalCase RPC names remain compatibility
aliases; new code should use ``rpc`` and snake_case.

Handle high-level errors
------------------------

All handwritten exceptions derive from :class:`sliver.SliverError`:

* :class:`sliver.NotConnectedError` means an operation needs a connected
  client;
* :class:`sliver.RPCError` normalizes a gRPC transport failure and records the
  operation, status, and details while retaining the native exception as its
  cause;
* :class:`sliver.ResourceNotFoundError` means a required lookup failed;
* :class:`sliver.CommandError` means Sliver completed a session or beacon
  command with an error in its response model;
* :class:`sliver.SliverTimeoutError` means a library-owned event or beacon-task
  deadline expired and also subclasses the built-in ``TimeoutError``;
* :class:`sliver.CleanupError` groups failures while releasing an owned
  resource; and
* :class:`sliver.UnsupportedTargetError` means the current host cannot be
  represented as a supported target.

Pydantic validation errors and ``asyncio.CancelledError`` retain their native
types. See :doc:`api/errors` for attributes that support structured handling.

Compatibility
-------------

The concise API is additive. Existing public spellings remain available while
new code moves to command-aligned names and typed domain inputs. Compatibility
aliases do not currently emit deprecation warnings. See :doc:`compatibility`
for the mapping and the limits of the guarantee.
