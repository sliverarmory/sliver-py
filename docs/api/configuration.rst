Configuration
=============

Operator configurations are validated Pydantic models. They are authored for
configuration files rather than generated from protobuf descriptors, and they
ignore unknown keys so newer Sliver configuration files remain loadable.

Credential fields are hidden from ``repr()``, but ``model_dump()`` still
contains certificates, private keys, and tokens. Treat dumped data as a secret.

SliverClientConfig
^^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.config.SliverClientConfig
    :members:
    :undoc-members:

SliverWireGuardConfig
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.config.SliverWireGuardConfig
    :members:
    :undoc-members:
