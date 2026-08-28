Clients
=======

This module connects to the Sliver gRPC API. Most users should use
``SliverClient``; ``BaseClient`` provides shared connection behavior for client
implementations. Public request and response values are Pydantic models.


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
