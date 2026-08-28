Clients
=======

This module connects to the Sliver gRPC API. Most users should use
``SliverClient``; ``BaseClient`` provides shared connection behavior for client
implementations. Public request and response values are Pydantic models.

Call ``await client.connect()`` before using either high-level methods or the
low-level stubs, and release the gRPC channel with ``await client.close()``.
``client.pydantic_stub`` automatically converts descriptor-generated Pydantic
requests and protobuf responses. ``client.raw_stub`` intentionally performs no
conversion. Both properties are unavailable while disconnected.

Collection helpers such as ``sessions()``, ``beacons()``, and ``jobs()`` return
normal Python lists containing Pydantic models rather than protobuf container
messages.


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
