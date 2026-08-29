Compatibility policy
====================

SliverPy v0.1 introduces a concise, command-oriented layer without changing the
public data boundary. High-level and low-level public methods continue to accept
and return Pydantic models, Python primitives, and normal containers; generated
transport messages are never compatibility types.

Preferred and retained names
----------------------------

New code should use the preferred column. The retained spellings remain
available for existing callers and do not currently emit deprecation warnings.
They are covered by the same runtime and static-type checks as the preferred
surface.

A one-token Sliver command keeps that token as its Python name. A nested or
hyphenated command path is flattened with underscores in command order: for
example ``tasks fetch`` becomes ``tasks_fetch()`` and ``stage-listener`` becomes
``stage_listener()``. Verb-object convenience names remain aliases.

.. list-table::
   :header-rows: 1
   :widths: 1 1

   * - Preferred
     - Retained compatibility spelling
   * - ``Client``
     - ``SliverClient``
   * - ``OperatorConfig``
     - ``SliverClientConfig``
   * - ``client.rpc``
     - ``client.pydantic_stub``
   * - snake-case RPC names
     - schema-style PascalCase RPC names
   * - ``use_session()`` / ``use_beacon()``
     - ``interact_session()`` / ``interact_beacon()``
   * - ``find_session()`` / ``find_beacon()``
     - ``session_by_id()`` / ``beacon_by_id()``
   * - ``find_job()``
     - ``job_by_id()``
   * - ``events(event_types)``
     - ``on(event_types)``
   * - ``tasks()`` / ``tasks_fetch()`` / ``tasks_cancel()``
     - ``beacon_tasks()`` / ``fetch_task()`` / ``cancel_task()``
   * - ``mtls()`` / ``wg()`` / ``dns()``
     - ``start_mtls_listener()`` / etc.
   * - ``http()`` / ``https()``
     - ``start_http_listener()`` / etc.
   * - ``stage_listener()``
     - ``start_tcp_stager_listener()``
   * - ``implants()`` / ``implants_rm()``
     - ``implant_builds()`` / ``rm_implant()``
   * - ``profiles()`` / ``profiles_generate()`` / ``profiles_stage()``
     - ``implant_profiles()`` / ``generate_stage()``
   * - ``profiles_new()`` / ``profiles_rm()``
     - ``new_profile()`` / ``rm_profile()``
   * - ``wg_config()``
     - ``generate_wg_client_config()``
   * - ``shellcode_rdi()``
     - ``shellcode()``
   * - ``websites_show()`` / ``websites_rm()``
     - ``show_website()`` / ``rm_website()``
   * - ``websites_rm_content()``
     - ``rm_website_content()``
   * - ``beacons_rm()``
     - ``rm_beacon()``

Interactive wrappers retain the same kind of command-spelling aliases:

.. list-table::
   :header-rows: 1
   :widths: 1 1

   * - Preferred
     - Retained spelling
   * - ``procdump()``
     - ``process_dump()``
   * - ``runas()``
     - ``run_as()``
   * - ``rev2self()``
     - ``revert_to_self()``
   * - ``getsystem()``
     - ``get_system()``
   * - ``msf_inject()``
     - ``msf_remote()``
   * - ``spawndll()``
     - ``spawn_dll()``
   * - ``extensions_list()``
     - ``list_extensions()``
   * - ``env()`` / ``env_set()`` / ``env_unset()``
     - ``get_env()`` / ``set_env()`` / ``unset_env()``
   * - ``registry_create()``
     - ``registry_create_key()``
   * - ``session.pivots()``
     - ``session.pivot_listeners()``
   * - ``session.services_start()`` [1]_
     - ``session.start_service()``
   * - ``session.services_stop()``
     - ``session.stop_service()``

.. [1] ``services_start()`` starts an existing service by name, matching the
   current Sliver command. The older ``start_service()`` creates and starts a
   service from its binary path, so it is retained but is not a direct alias.

Some preferred methods intentionally have stronger contracts rather than being
aliases:

* ``get_session()``, ``get_beacon()``, ``get_job()``, ``use_session()``, and
  ``use_beacon()`` raise :class:`sliver.ResourceNotFoundError`; their older
  lookup counterparts return ``None``.
* ``generate(ImplantSpec)``, ``profiles_generate()``, and ``profiles_stage()``
  return :class:`sliver.GeneratedImplant`, while
  ``generate_implant(ImplantConfig)`` remains the schema-level generation
  method and returns the generated ``Generate`` model.
* ``regenerate()`` returns :class:`sliver.GeneratedImplant`, while
  ``regenerate_implant()`` retains the generated result shape.
* ``runas()`` exposes Sliver's domain, password, window, and network-only
  options and follows its hidden-window default. ``run_as()`` preserves the
  historical wire default.
* ``spawndll()`` uses Sliver's process/export defaults and positive
  ``keep_alive`` option. ``spawn_dll()`` retains the historical positional
  arguments and inverted ``kill`` flag.
* ``registry_create(path, hive=..., hostname=...)`` accepts the same full path
  as Sliver's command. ``registry_create_key()`` retains the split parent/key
  arguments.

Beacon removal correction
-------------------------

``kill_beacon()`` is the one intentional semantic correction in this layer.
It now maps to Sliver's ``kill`` command and queues termination of the beacon
implant. Code that used the historical method to delete only the server record
must migrate to ``beacons_rm()`` (or its ``rm_beacon()`` convenience alias).
Termination and record removal are deliberately not
aliases:

.. code-block:: python

    await client.kill_beacon(beacon_id, force=False)  # terminate the implant
    await client.beacons_rm(beacon_id)                # remove only the record

Constants and serialization
---------------------------

String-valued constants such as :class:`sliver.GOOS`, :class:`sliver.GOARCH`,
:class:`sliver.C2Protocol`, and :class:`sliver.EventType` subclass ``str`` and
serialize to their established Sliver string values. APIs that previously
accepted a string continue to accept one where their annotation includes
``str``; enum members are the preferred spelling.

Enums already defined by Sliver's descriptors, including
:class:`sliver.OutputFormat`, :class:`sliver.ShellcodeEncoder`, and
:class:`sliver.RegistryType`, are re-exported rather than duplicated. They keep
their generated integer values and can be passed directly to generated
Pydantic models.

Domain models are adapters, not alternate wire types. :class:`sliver.Target`,
:class:`sliver.C2Endpoint`, :class:`sliver.ImplantSpec`, and related models
validate human-facing inputs and convert to the same generated Pydantic request
models used by ``client.rpc``.

Lifecycle compatibility
-----------------------

Manual ``connect()``/``close()`` ownership remains supported alongside the
preferred async context manager. ``close()`` is idempotent, ``aclose()`` is an
alias, and a closed client can reconnect.

``InteractiveBeacon.close()`` also remains callable. For a wrapper created by
``Client.use_beacon()`` it closes only that wrapper's local use; the parent
client owns the shared event/task dispatcher. It does not stop other clients or
wrappers, and it never kills or removes the remote beacon.

Generated API scope
-------------------

The model and RPC surfaces are generated from the exact Sliver submodule commit
pinned by each SliverPy release. Compatibility applies to that pinned schema;
a server built from a different Sliver revision may add, remove, or change RPCs
and fields. Upgrade the pinned submodule and generated sources together.

The command-oriented layer is maintained by hand and may grow additively. When
a retained spelling eventually becomes a removal candidate, the release notes
and this page will identify the migration; aliases in v0.1 are not silently
removed.
