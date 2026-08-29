Enums and constants
===================

Import public constants from ``sliver``. String enums subclass both ``str`` and
``Enum`` for Python 3.10 compatibility; ``str(member)`` and JSON serialization
produce the established Sliver value. Integer enums preserve the values used by
the generated Pydantic schema.

Compiler targets and protocols
------------------------------

``GOOS`` and ``GOARCH`` contain the complete active value sets from ``go tool
dist list`` for the Go toolchain pinned by this SliverPy release. Go names for
retired, broken, or future ports are intentionally excluded. Not every
Cartesian-product pair is a Go target, and Sliver distinguishes its
first-class implant targets from generic/default builds. Query the connected
server's compiler information when availability for a specific pair or output
format matters.

.. autoclass:: sliver.GOOS
    :members:

.. autoclass:: sliver.GOARCH
    :members:

.. autoclass:: sliver.C2Protocol
    :members:

.. autoclass:: sliver.ConnectionStrategy
    :members:

.. autoclass:: sliver.TargetKind
    :members:

Events, tasks, and jobs
-----------------------

.. autoclass:: sliver.EventType
    :members:

.. autoclass:: sliver.BeaconTaskState
    :members:

.. autoclass:: sliver.JobProtocol
    :members:

.. autoclass:: sliver.PortForwardProtocol
    :members:

Interactive command constants
-----------------------------

.. autoclass:: sliver.RegistryHive
    :members:

.. autoclass:: sliver.LogonType
    :members:

Shellcode options
-----------------

.. autoclass:: sliver.ShellcodeEntropy
    :members:

.. autoclass:: sliver.ShellcodeCompression
    :members:

.. autoclass:: sliver.ShellcodeExitOption
    :members:

.. autoclass:: sliver.ShellcodeBypass
    :members:

.. autoclass:: sliver.ShellcodeHeaders
    :members:

Generated enum re-exports
-------------------------

These classes come directly from the descriptor-generated Pydantic model
modules. SliverPy re-exports them instead of creating look-alike enum types, so
members can be passed directly to generated models.

.. autoclass:: sliver.OutputFormat
    :members:

.. autoclass:: sliver.FileType
    :members:

.. autoclass:: sliver.ShellcodeEncoder
    :members:

.. autoclass:: sliver.StageProtocol
    :members:

.. autoclass:: sliver.ImplantCapability
    :members:

.. autoclass:: sliver.PivotType
    :members:

.. autoclass:: sliver.RegistryType
    :members:
