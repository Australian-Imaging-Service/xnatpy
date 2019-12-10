******************
XNAT Python Client
******************

A new XNAT client that exposes XNAT objects/functions as python
objects/functions.

The XNAT Python client is open-source (licensed under the Apache 2.0 license) and hosted on gitlab at `https://gitlab.com/radiology/infrastructure/xnatpy <https://gitlab.com/radiology/infrastructure/xnatpy>`_

The official documentation can be found at `xnat.readthedocs.org <http://xnat.readthedocs.org>`_

To install from pypi simply use:

.. code-block:: bash

    pip install xnat

There is also a conda package available:

.. code-block:: bash

    conda install -c conda-forge xnat


Alternatively, you can get yourself a copy of the source code:

.. code-block:: bash

    git clone https://gitlab.com/radiology/infrastructure/xnatpy 

.. note::
    This is NOT pyxnat, but a new module which is not as mature but uses a different philisophy for the user interface. Pyxnat is located at: `https://pyxnat.github.io/pyxnat <https://pyxnat.github.io/pyxnat/>`_


XNAT Client Documentation
=========================
.. toctree::
    :maxdepth: 3

    static/introduction.rst
    static/tutorial.rst
    static/changelog.rst
    xnat
    xsd



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
