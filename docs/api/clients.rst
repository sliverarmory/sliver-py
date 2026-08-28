Clients
=======

This module connects to the Sliver gRPC API. Most users should use
``SliverClient``; ``BaseClient`` provides shared connection behavior for client
implementations. Public request and response values are Pydantic models.

Call ``await client.connect()`` before using high-level methods or
``client.pydantic_stub``. ``connect()`` returns a
``models.clientpb.Version`` model. Always release the gRPC channel with
``await client.close()``; the Pydantic-only stub becomes unavailable again
after closing.

``client.pydantic_stub`` is the supported low-level extension point for an RPC
that lacks a convenience method. It accepts the Pydantic request model declared
for that RPC and returns its Pydantic response model, including for streaming
RPCs. Generated transport objects are not part of the public client API.

Collection helpers such as ``sessions()``, ``beacons()``, and ``jobs()`` return
normal Python lists containing Pydantic models rather than transport wrapper
objects.


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
