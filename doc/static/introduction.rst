Introduction
============

A new XNAT client that exposes XNAT objects/functions as python
objects/functions.

Getting started
---------------

To install just use the setup.py normally::

  python setup.py install

To get started, create a connection and start querying::

  >>> import xnat
  >>> session = xnat.connect('https://central.xnat.org', user="", password="")
  >>> session.projects['Sample_DICOM'].subjects
  >>> session.disconnect()

To see all options for creating connections see the :py:func:`xnat.connect`.

The :py:class:`XNAT session <xnat.XNAT>` is the main class for interacting with XNAT.
It contains the main communication functions.

When using IPython most functionality can be figured out by looking at the
available attributes/methods of the returned objects.

Credentials
-----------

To store credentials this module uses the .netrc file. This file contains login
information and should be accessible ONLY by the user (if not, the module with
throw an error to let you know the file is unsafe).

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
