Welcome to SliverPy's documentation!
====================================

SliverPy is an async Python client library for Sliver. It connects to Sliver's
multiplayer gRPC endpoint with operator configuration files and mutual TLS.
The concise :class:`sliver.Client` API follows Sliver's command names and uses
typed enums and Pydantic domain models for common workflows. Public requests
and responses stay within a strict boundary of Pydantic models, Python
primitives, and normal containers. Generated transport messages remain a
private implementation detail.

.. _Sliver: https://github.com/BishopFox/sliver

.. toctree::
   :maxdepth: 3
   :caption: Table of Contents

   install
   getting-started
   models
   compatibility

   api/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
