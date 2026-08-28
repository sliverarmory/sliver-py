Beacons
=======

``InteractiveBeacon`` exposes commands for an asynchronous beacon. ``BaseBeacon``
contains the shared task and event machinery used by beacon implementations.
Command results resolve to Pydantic models, and arguments are Pydantic models
or ordinary Python types such as ``str``, ``int``, ``bool``, ``bytes``, and
``list[str]``.

Each interactive beacon owns a background task-result watcher. Call
``await beacon.close()`` when finished, before closing the parent client.
Closing the interaction affects only local bookkeeping; it does not terminate
or remove the remote beacon. Shared command signatures are documented under
:doc:`commands`.

The ``beacon`` property returns a defensive copy of the complete
``models.clientpb.Beacon`` model captured when the interaction was created.
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

