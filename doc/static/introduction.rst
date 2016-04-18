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

Currently we do not support the creation of Projects, Subjects, Experiments, etc
via code. You can create resources and uploads files to them. Also it is
possible to import data via the import service (upload a zip file). There is
also support for working with the prearchive (reading, moving, deleting and
archiving).

There is virtuall no documentation or testing, this is a known limitation.
