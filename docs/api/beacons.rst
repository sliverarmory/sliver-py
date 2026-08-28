Beacons
=======

``InteractiveBeacon`` exposes commands for an asynchronous beacon. ``BaseBeacon``
contains the shared task and event machinery used by beacon implementations.
Command results resolve to Pydantic models.

Each interactive beacon owns a background task-result watcher. Call
``await beacon.close()`` when finished, before closing the parent client.
Closing the interaction affects only local bookkeeping; it does not terminate
or remove the remote beacon. Shared command signatures are documented under
:doc:`commands`.


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

