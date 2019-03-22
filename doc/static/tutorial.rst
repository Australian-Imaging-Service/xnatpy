XNATpy Tutorial
===============

XNAT REST API
-------------

The XNAT REST API allows users to work with xnat via scripts. The REST API is
an interface that is language independent and is build on top of HTTP. Operations
are carried out by HTTP requests with one of the verbs ``GET``, ``PUT``,
``POST`` or ``DELETE``. The ``GET`` request is generally used for retrieving
data, whereas the ``PUT``, ``POST``, and ``DELETE`` are used for modifying data.

A simple ``GET`` request can be send by simply putting the target url in a web
browser and looking at the result. For a sending more complex HTTP requests,
you can for example use ``curl`` (a command-line tool for linux), ``postman``
(an extension for the chrome browser), or the ``requests`` package for Python
(on top of which this package as well as pyxnat is build)

To get an idea of how the XNAT REST API works it is helpful to visit the
following URLs in your browser:

*  `https://central.xnat.org/data/archive/projects <https://central.xnat.org/data/archive/projects>`_
*  `https://central.xnat.org/data/archive/projects?format=xml <https://central.xnat.org/data/archive/projects?format=xml>`_
*  `https://central.xnat.org/data/archive/projects?format=json <https://central.xnat.org/data/archive/projects?format=json>`_

The first URL give you a table with an overview of all projects you can access
on XNAT central. The second and third URL give the same information, but in
different machine readable formats (XML and JSON respectively). This is
extremely useful when creating scripts to automatically retrieve or store data
from XNAT.

Installation
------------

The easiest way to install xnat is via to python package index via pip::

  pip install xnat

However, if you do not have pip or want to install from source just use the
setup.py normally::

  python setup.py install


Connecting to a server
----------------------

To get started, create a connection::

  >>> import xnat
  >>> session = xnat.connect('https://central.xnat.org')

To see all options for creating connections see the :py:func:`xnat.connect`.
The connection holds your login information, the server information and a
session. It will also send a heartbeat every 14 minutes to keep the connection
alive.

When working with a session it is always important to disconnect when done::

  >>> session.disconnect()

Credentials
^^^^^^^^^^^

It is possible to pass your credentials for the session when connecting. This
would look like::

  >>> session = xnat.connect('http://my.xnat.server', user='admin', password='secret')

This would work and log in fine, but your password might be visible in your
source code, command history or just on your screen. If you only give a
user, but not a password xnatpy will prompt you for your password. This is
fine for interactive use, but for automated scripts this is useless.

To store credentials this xnatpy uses the .netrc file. On linux the file is
located in ``~/.netrc``. This file contains login information and should be
accessible ONLY by the user (if not, the module with throw an error to let
you know the file is unsafe). For example::

  echo "machine images.xnat.org
  >     login admin
  >     password admin" > ~/.netrc
  chmod 600 ~/.netrc

This will create the netrc file with the correct contents and set the
permission correct.

Self-closing sessions
^^^^^^^^^^^^^^^^^^^^^

When in a script where there is a possibility for unforeseen errors it is safest
to use a context operator in Python. This can be achieved by using the
following::

  >>> with xnat.connect('http://my.xnat.server') as session:
  ...     print session.projects

As soon as the scope of the with exists (even if because of an exception thrown!)
the session will be disconnected automatically.

Exploring your xnat server
--------------------------

When a session is established, it is fairly easy to explore the data on the
XNAT server. The data structure of XNAT is mimicked as Python objects. The
connection gives access to a listing of all projects, subjects, and experiments
on the server.

  >>> import xnat
  >>> session = xnat.connect('http://images.xnat.org', user='admin', password='admin')
  >>> session.projects
  <XNATListing (sandbox, sandbox project): <ProjectData sandbox project (sandbox)>>

The XNATListing is a special type of mapping in which you can access elements
by a primary key (usually the *ID* or *Accession #*) and a secondary key (e.g.
the label for a subject or experiment). Selection can be performed the same as
a Python dict::

  >>> sandbox_project = session.projects["sandbox"]
  >>> sandbox_project.subjects
  <XNATListing (XNAT_S00001, test001): <SubjectData test001 (XNAT_S00001)>>

You can browse the following levels on the XNAT server: projects, subjects,
experiments, scans, resources, files. Also under experiments you have assessors
which again can contain resources and files. This all following the same
structure as XNAT.

.. warning::
    Loading all subjects/experiments on a server can take very long if there
    is a lot of data. Going down through the project level is more efficient.

Looping over data
-----------------

There are situations in which you want to perform an action for each subject or
experiment. To do this, you can think of an ``XNATListing`` as a Python ``dict``
and most things will work naturally. For example::

  >>> sandbox_project.subjects.keys()
  [u'XNAT_S00001']
  >>> sandbox_project.subjects.values()
  [<SubjectData test001 (XNAT_S00001)>]
  >>> len(sandbox_project.subjects)
  1
  >>> for subject in sandbox_project.subjects.values():
  ...     print(subject.label)
  test001

Dowloading data
---------------

The REST API allows for downloading of data from XNAT. The xnatpy package
includes helper functions to make the downloading of data easier. For
example, to download all exerpiments belonging to a subject::

  >>> subject = sandbox_project.subjects['test001']
  >>> subject.download_dir('./Downloads/test001')

This will download all the relevant experiments and unpack them in the target
folder. Experiments, scans and resources can also be downloaded in a zip bundle
using the ``download_zip`` method.

Importing data into XNAT
------------------------

To add new data into XNAT it is possible to use the REST import service. It
allows you to upload a zip file containing an experiment and XNAT will
automatically try to store it in the correct place::

  >>> session.services.import_('/path/to/archive.zip', project='sandbox', subject='test002')

Will upload the DICOM files in archive.zip and add them as scans under the subject *test002*
in project *sandbox*. For more information on importing data see
:py:meth:`import_ <xnat.services.Services.import_>`

Prearchive
----------

When scans are send to the XNAT they often end up in the prearchive pending review before 
adding them to the main archive. It is possible to view the prearchive via xnatpy::

  >>> session.prearchive.sessions()
  []

This gives a list of ``PrearchiveSessions`` in the archive. It is possible to 
archive, rebuild, more or remove the session using simple methods. For more information
see :py:class:`PrearchiveSession <xnat.prearchive.PrearchiveSession>`

Object creation
---------------

It is possible to create object on the XNAT server (such as a new subject, experiment, etc).
This is achieved by creating such an object in python and xnatpy will create a version of the
server. For example you can create a subject:

  >>> import xnat
  >>> connection = xnat.connect('https://xnat.example.com')
  >>> project = connection.projects['myproject']
  >>> subject = connection.classes.SubjectData(parent=project, label='new_subject_label')
  >>> subject
  <SubjectData new_subject_label>

.. note:: the parent need to be the correct parent for the type, so an ``MRSessionData`` would
          need a ``SubjectData`` to be the parent.

In the ``connection.classes`` are all classes known the XNAT, also
``MRSessionData``, ``CTSessionData``. To get a complete list you can do:

  >>> dir(connection.classes)

.. note:: the valid parent for a project (``ProjectData``) would be the connection object itself

Example scripts
---------------

There is a number of example scripts located in the ``examples`` folder in the source code.
The following code is a small command-line tool that prints all files for a given scan in
the XNAT archive::

  #!/usr/bin/env python

  import xnat
  import argparse
  import re


  def get_files(connection, project, subject, session, scan):
      xnat_project = connection.projects[project]
      xnat_subject = xnat_project.subjects[subject]
      xnat_experiment = xnat_subject.experiments[session]
      xnat_scan = xnat_experiment.scans[scan]
      files = xnat_scan.files.values()
      return files


  def filter_files(xnat_files, regex):
      filtered_files = []
      regex = re.compile(regex)
      for file in xnat_files:
          found = regex.match(file.name)
          if found:
              filtered_files.append(file)
      return filtered_files


  def main():
      parser = argparse.ArgumentParser(description='Prints all files from a certain scan.')
      parser.add_argument('--xnathost', type=unicode, required=True, help='xnat host name')
      parser.add_argument('--project', type=unicode, required=True, help='Project id')
      parser.add_argument('--subject', type=unicode, required=True, help='subject')
      parser.add_argument('--session', type=unicode, required=True, help='session')
      parser.add_argument('--scan', type=unicode, required=True, help='scan')
      parser.add_argument('--filter', type=unicode, required=False, default='.*', help='regex filter for file names')
      args = parser.parse_args()

      with xnat.connect(args.xnathost) as connection:
          xnat_files = get_files(connection, args.project, args.subject, args.session, args.scan)
          xnat_files = filter_files(xnat_files, args.filter)
          for file in xnat_files:
              print('{}'.format(file.name))


  if __name__ == '__main__':
      main()
