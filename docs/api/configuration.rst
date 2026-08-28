Configuration
=============

Operator configurations are validated Pydantic models. They are authored for
configuration files rather than generated from the RPC schema, and they ignore
unknown keys so newer Sliver configuration files remain loadable.

Credential fields are hidden from ``repr()``, but ``model_dump()`` still
contains certificates, private keys, and tokens. Treat dumped data as a secret.

Parse the complete operator file rather than copying credential values into
source code:

.. code-block:: python

    from pathlib import Path

    from sliver import SliverClientConfig

    config = SliverClientConfig.parse_config_file(
        Path.home() / ".sliver-client" / "configs" / "default.cfg"
    )
    print(config)  # operator@host:port; credentials are omitted

Newer configurations can contain a nested
:class:`sliver.SliverWireGuardConfig`. It is available as ``config.wg`` and can
also be constructed as an ordinary Pydantic model:

.. code-block:: python

    from sliver import SliverWireGuardConfig

    wg = SliverWireGuardConfig(
        server_pub_key="server-public-key",
        client_private_key="client-private-key",
        client_pub_key="client-public-key",
        client_ip="100.64.0.2",
        server_ip="100.64.0.1",
    )

``repr(config)`` and ``repr(wg)`` hide credential fields. Pydantic serialization
does not: never log, publish, or commit ``model_dump()`` or
``model_dump_json()`` output from either configuration model.

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
