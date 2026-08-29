Commands
========

This module contains commands shared by ``InteractiveBeacon`` and
``InteractiveSession``. Request and response values use the models described in
:doc:`../models`. Simple arguments use ordinary Python types, structured
arguments such as implant configurations use generated Pydantic model types,
and closed constant sets use enums such as :class:`sliver.GOOS`,
:class:`sliver.RegistryHive`, and :class:`sliver.LogonType`. Every structured
result is a Pydantic model.

Method names track Sliver client commands where Python identifiers permit it:
for example ``procdump()``, ``runas()``, ``rev2self()``, ``getsystem()``, and
``spawndll()``. Earlier Python-normalized spellings remain compatibility aliases
as described in :doc:`../compatibility`.

Sliver restricts ``getsystem`` and ``extensions list`` to interactive sessions,
so their canonical ``getsystem()`` and ``extensions_list()`` methods appear on
``InteractiveSession`` only. The historical ``get_system()`` and
``list_extensions()`` spellings remain inherited by both wrappers for source
compatibility.

When a returned command model contains an error in its response field, both
session and beacon interactions raise :class:`sliver.CommandError` with the
operation, target ID, message, and original result attached.


BaseInteractiveCommands
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.interactive.BaseInteractiveCommands
    :members:
    :undoc-members:
