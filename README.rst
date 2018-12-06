XNATPY
======

A new XNAT client that exposes XNAT objects/functions as python
objects/functions. The aim is to abstract as much of the REST API
away as possible and make xnatpy feel like native Python code. This
reduces the need for the user to know the details of the REST API.
Low level functionality can still be accessed via the connection object
which has `get`, `head`, `put`, `post`, `delete` methods for more
directly calling the REST API.

Disclaimer
----------

This is NOT pyxnat, but a new module which uses a
different philosophy for the user interface. Pyxnat is located at:
`https://pythonhosted.org/pyxnat/ <https://pythonhosted.org/pyxnat/>`_

Getting started
---------------

To install just use the setup.py normally::

  python setup.py install

or install directly using pip::

  pip install xnat

To get started, create a connection and start querying::

  >>> import xnat
  >>> session = xnat.connect('https://central.xnat.org', user="", password="")
  >>> session.projects['Sample_DICOM'].subjects

when using IPython most functionality can be figured out by looking at the
available attributes/methods of the returned objects.

Credentials
-----------

To store credentials this module uses the .netrc file. This file contains login
information and should be accessible ONLY by the user (if not, the module with
throw an error to let you know the file is unsafe).

Documentation
-------------

The official documentation can be found at `xnat.readthedocs.org <http://xnat.readthedocs.org>`_
This documentation is a stub, but shows the classes and methods available.

Status
------

Currently we have basic support for almost all data on XNAT servers. Also it is 
possible to import data via the import service (upload a zip file). There is
also some support for working with the prearchive (reading, moving, deleting and
archiving).

Any function not exposed by the object-oriented API of xnatpy, but exposed in the
XNAT REST API can be called via the generic get/put/post methods in the session
object.

There is at the moment still a lack of proper tests in the code base and the documentation
is somewhat sparse, this is a known limitation and can hopefully be addressed in the future.
