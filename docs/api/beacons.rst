Beacons
=======

``InteractiveBeacon`` exposes commands for an asynchronous beacon. ``BaseBeacon``
contains the shared task and event machinery used by beacon implementations.
Command results resolve to Pydantic models.


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

