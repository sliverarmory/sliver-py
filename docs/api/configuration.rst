Configuration
=============

Operator configurations are validated Pydantic models. New code should use
:class:`sliver.OperatorConfig`; :class:`sliver.SliverClientConfig` remains its
compatibility base name. These models describe configuration files rather than
the RPC schema and ignore unknown keys so newer Sliver configurations remain
loadable.

Credential fields are hidden from ``repr()``, but ``model_dump()`` still
contains certificates, private keys, and tokens. Treat dumped data as a secret.

Use :meth:`sliver.Client.from_config_file` when constructing a client. With no
argument it checks ``SLIVER_CONFIG`` and then
``~/.sliver-client/configs/default.cfg``:

.. code-block:: python

    from sliver import Client

    client = Client.from_config_file()

Pass an explicit path to override both sources:

.. code-block:: python

    from pathlib import Path

    from sliver import Client

    client = Client.from_config_file(
        Path.home() / ".sliver-client" / "configs" / "default.cfg"
    )

For programmatic ownership or validation without constructing a client, use
``OperatorConfig.from_file()``. It follows the same resolution rules:

.. code-block:: python

    from sliver import OperatorConfig

    config = OperatorConfig.from_file()
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

OperatorConfig
^^^^^^^^^^^^^^

.. autoclass:: sliver.OperatorConfig
    :members:
    :undoc-members:
    :show-inheritance:

SliverWireGuardConfig
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: sliver.config.SliverWireGuardConfig
    :members:
    :undoc-members:
