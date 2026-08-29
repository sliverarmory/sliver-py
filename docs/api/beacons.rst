Beacons
=======

``InteractiveBeacon`` exposes commands for an asynchronous beacon. ``BaseBeacon``
contains the routing and task machinery used by beacon implementations.
Command results resolve to Pydantic models, and arguments are Pydantic models
or ordinary Python types such as ``str``, ``int``, ``bool``, ``bytes``, and
``list[str]``.

Beacons obtained from :meth:`sliver.Client.use_beacon` share the parent
client's single lazy event/task dispatcher. A command is queued as a remote
beacon task and resolves after the dispatcher observes its completion event and
fetches its typed Pydantic result. Fast completion events that precede waiter
registration are retained in a bounded cache.

Result waiters are removed after success, command error, timeout, or local
cancellation. A timeout raises :class:`sliver.SliverTimeoutError`; local
cancellation preserves ``asyncio.CancelledError``. In either case SliverPy asks
the server to cancel the remote task when supported. The event stream reconnects
after unexpected interruption, but the command's configured deadline remains
authoritative.

``InteractiveBeacon.close()`` is retained for compatibility. For a
client-created wrapper it closes the wrapper without stopping the shared
dispatcher or other subscribers; closing the parent client owns dispatcher and
channel cleanup. Closing an interaction does not terminate or remove the remote
beacon. Use ``client.kill_beacon()`` to queue termination and
``client.beacons_rm()`` to remove only the server record. Shared command
signatures are documented under :doc:`commands`.

The ``beacon`` property returns a defensive copy of the complete
``sliver.models.clientpb.Beacon`` model captured when the interaction was
created.
Convenience properties expose its commonly used scalar fields: ``beacon_id``,
``name``, ``hostname``, ``uuid``, ``username``, ``uid``, ``gid``, ``os``,
``arch``, ``transport``, ``remote_address``, ``pid``, ``filename``,
``last_checkin``, ``active_c2``, ``version``, and ``reconnect_interval``.


BaseBeacon
^^^^^^^^^^

.. autoclass:: sliver.beacon.BaseBeacon
    :members:
    :undoc-members:

InteractiveBeacon
^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.InteractiveBeacon
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: interactive_session

