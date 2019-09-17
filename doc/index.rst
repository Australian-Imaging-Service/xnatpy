******************
XNAT Python Client
******************

A new XNAT client that exposes XNAT objects/functions as python
objects/functions.

The XNAT Python client is open-source (licensed under the Apache 2.0 license) and hosted on bitbucket at `https://bitbucket.org/bigr_erasmusmc/xnatpy <https://bitbucket.org/bigr_erasmusmc/xnatpy>`_

The official documentation can be found at `xnat.readthedocs.org <http://xnat.readthedocs.org>`_

To install from pypi simply use:

.. code-block:: bash

    pip install xnat

There is also a conda package available:

.. code-block:: bash

    conda install -c conda-forge xnat


Alternatively, you can get yourself a copy of the source code:

.. code-block:: bash

    hg clone https://<yourusername>@bitbucket.org/bigr_erasmusmc/xnatpy

or if you have a ssh key pair:

.. code-block:: bash

    hg clone ssh://hg@bitbucket.org/bigr_erasmusmc/xnatpy

.. note::
    The source will be moved from mercurial to git at the end of 2019!

.. note::
    This is NOT pyxnat, but a new module which is not as mature but uses a different philisophy for the user interface. Pyxnat is located at: `https://pythonhosted.org/pyxnat/ <https://pythonhosted.org/pyxnat/>`_


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
