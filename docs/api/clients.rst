Clients
=======

This module connects to the Sliver gRPC API. Most users should use the concise
:class:`sliver.Client`; :class:`sliver.SliverClient` remains the longer
compatibility name. ``BaseClient`` provides shared connection behavior for
client implementations. Public request and response values are Pydantic models,
Python primitives, and normal containers.

Prefer ``async with Client.from_config_file() as client`` so one context owns
connection and cleanup. Manual ``connect()`` and ``close()`` remain supported;
``connect()`` returns a ``sliver.models.clientpb.Version`` model, ``close()`` is
idempotent, and a closed client can reconnect.

``client.rpc`` is the supported low-level extension point for an RPC that lacks
a convenience method. It accepts the Pydantic request model declared for that
RPC and returns its Pydantic response model, including for streaming RPCs.
Generated transport objects are not part of the public client API. The property
raises :class:`sliver.NotConnectedError` while disconnected;
``pydantic_stub`` is its compatibility alias.

Collection helpers such as ``sessions()``, ``beacons()``, and ``jobs()`` return
normal Python lists containing Pydantic models rather than transport wrapper
objects.

``events()`` and every interactive beacon share one lazy client-owned event/task
dispatcher. Closing the client stops subscribers and task waiters before it
closes the channel. See :doc:`../getting-started` for buffering, reconnect, and
deadline semantics.


BaseClient
^^^^^^^^^^

.. autoclass:: sliver.client.BaseClient
    :members:
    :undoc-members:

SliverClient
^^^^^^^^^^^^

.. autoclass:: sliver.SliverClient
    :members:
    :undoc-members:
    :show-inheritance:

Client
^^^^^^

.. autoclass:: sliver.Client
    :members:
    :undoc-members:
    :show-inheritance:
