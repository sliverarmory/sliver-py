Sessions
========

``InteractiveSession`` exposes commands for a connected session. ``BaseSession``
contains shared session behavior for other implementations. Command results are
Pydantic models.

Interactive sessions share the parent client's gRPC channel and do not own a
background watcher. Close the parent client with ``await client.close()`` when
finished. Shared command signatures are documented under :doc:`commands`.

BaseSession
^^^^^^^^^^^
.. autoclass:: sliver.session.BaseSession
    :members:
    :undoc-members:

InteractiveSession
^^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.InteractiveSession
    :members:
    :undoc-members:
    :show-inheritance:
