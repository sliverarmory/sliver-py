Commands
========

This module contains commands shared by ``InteractiveBeacon`` and
``InteractiveSession``. Request and response values use the models described in
:doc:`../models`. Both interaction classes inherit these exact method
signatures: simple arguments use ordinary Python types, structured arguments
such as implant configurations and registry enums use generated Pydantic model
types, and every structured result is a Pydantic model.


BaseInteractiveCommands
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.interactive.BaseInteractiveCommands
    :members:
    :undoc-members:
