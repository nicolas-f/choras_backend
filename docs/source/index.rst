Welcome to Room Acoustics Backend's documentation
=================================================
----

This is the backend implementation documentation for room acoustics software for research, education and industry in acoustics.

The software is using the `Acoustics Diffusion Equation (DE) Method <https://github.com/Building-acoustics-TU-Eindhoven/Diffusion>`_ and `Wave-based Room Acoustics (DG) Method <https://github.com/Building-acoustics-TU-Eindhoven/edg-acoustics>`_ as sub-modules for modeling of sound behaviour in complex geometrical spaces.

The software has been implemented in Python using the Flask framework. Currently, it has been tested only in the development environment. Future plans include support for Docker and deployment in production environments. The application supports SQLite3 as the default database, with provisions for PostgreSQL as an alternative.


.. toctree::
   :maxdepth: 1
   :caption: Setup Instructions

   includes/setup.rst

.. toctree::
   :maxdepth: 1
   :caption: API Reference

   includes/api_documentation.rst
