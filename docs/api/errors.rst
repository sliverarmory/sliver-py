Errors
======

Handwritten high-level exceptions derive from :class:`sliver.SliverError` and
carry structured attributes in addition to a readable message. The Pydantic RPC
adapter converts native gRPC failures to :class:`sliver.RPCError` for unary and
streaming calls, recording the RPC operation, status, and details while keeping
the native exception as ``__cause__``. Pydantic validation errors and
``asyncio.CancelledError`` retain their native types.

SliverError
-----------

.. autoclass:: sliver.SliverError
    :members:

NotConnectedError
-----------------

.. autoclass:: sliver.NotConnectedError
    :members:

ResourceNotFoundError
---------------------

.. autoclass:: sliver.ResourceNotFoundError
    :members:

RPCError
--------

.. autoclass:: sliver.RPCError
    :members:

CommandError
------------

.. autoclass:: sliver.CommandError
    :members:

SliverTimeoutError
------------------

.. autoclass:: sliver.SliverTimeoutError
    :members:

CleanupError
------------

.. autoclass:: sliver.CleanupError
    :members:

UnsupportedTargetError
----------------------

.. autoclass:: sliver.UnsupportedTargetError
    :members:
