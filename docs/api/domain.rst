Domain models
=============

The human-facing domain layer turns common Sliver concepts into concise,
validated Pydantic models. Conversion methods produce the descriptor-generated
models accepted by :attr:`sliver.Client.rpc`; the domain layer never exposes or
wraps generated transport messages.

Target
------

Use typed operating-system and architecture members instead of raw strings.
``Target.current()`` maps a supported Python host to its Sliver compiler target
and raises :class:`sliver.UnsupportedTargetError` otherwise. ``goos`` and
``goarch`` remain read-only compatibility views of ``os`` and ``arch``.

.. autoclass:: sliver.Target
    :members:

C2Endpoint
----------

``from_url()`` validates an existing canonical URL. Protocol-specific
constructors apply default ports and normalize IPv4, IPv6, query, named-pipe,
and pivot syntax. ``to_implant_c2()`` returns the generated Pydantic
``ImplantC2`` model.

.. autoclass:: sliver.C2Endpoint
    :members:

BeaconOptions
-------------

Durations use ``datetime.timedelta``. The default interval is 60 seconds and
the default jitter is 30 seconds; an interval shorter than five seconds is
rejected.

.. autoclass:: sliver.BeaconOptions
    :members:

ShellcodeOptions
----------------

Shellcode-specific values use typed integer enums and convert to Sliver's
generated ``ShellcodeConfig`` model.

.. autoclass:: sliver.ShellcodeOptions
    :members:

ImplantSpec
-----------

An implant specification requires at least one C2 endpoint. It validates target
and output compatibility, normalizes canary domains, derives the generated
protocol flags, and converts ``timedelta`` values to the nanosecond durations
used by Sliver.

``to_implant_config(base=...)`` copies an optional generated configuration and
then applies every field represented by the spec. ``to_generate_request()``
wraps that configuration with an optional implant name.

.. autoclass:: sliver.ImplantSpec
    :members:

GeneratedImplant
----------------

The rich generation result validates that Sliver returned non-empty file data
and a usable basename. ``save()`` creates the file exclusively by default,
creates parent directories by default, and applies mode ``0o700`` unless the
caller selects another mode or ``None``.

.. autoclass:: sliver.GeneratedImplant
    :members:

Inventory
---------

``Client.inventory()`` concurrently collects the server version, sessions,
beacons, jobs, and operators into one snapshot.

.. autoclass:: sliver.Inventory
    :members:
