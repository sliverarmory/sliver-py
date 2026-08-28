Sessions
========

``InteractiveSession`` exposes commands for a connected session. ``BaseSession``
contains shared session behavior for other implementations. Command results are
Pydantic models, and command arguments are Pydantic models or ordinary Python
types such as ``str``, ``int``, ``bool``, ``bytes``, and ``list[str]``.

Interactive sessions share the parent client's gRPC channel and do not own a
background watcher. Close the parent client with ``await client.close()`` when
finished. Shared command signatures are documented under :doc:`commands`.

The ``session`` property returns a defensive copy of the complete
``models.clientpb.Session`` model captured when the interaction was created.
Convenience properties expose its commonly used scalar fields: ``session_id``,
``name``, ``hostname``, ``uuid``, ``username``, ``uid``, ``gid``, ``os``,
``arch``, ``transport``, ``remote_address``, ``pid``, ``filename``,
``last_checkin``, ``active_c2``, ``version``, ``is_dead``,
``reconnect_interval``, and ``proxy_url``.

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
