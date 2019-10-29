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

Downloading data
----------------

If you have the following in your XNAT::

    >>> experiment.scans['T1']
    <MrScanData T1 (1001-MR3)>

In some cases you might want to download an individual scan to inspect/process locally. This
is using::

    >>> experiment.scans['T1'].download('/home/hachterberg/temp/T1.zip')
    Downloading http://127.0.0.1/xnat/data/experiments/demo_E00091/scans/1001-MR3/files?format=zip:
    13035 kb
    Saved as /home/hachterberg/temp/T1.zip...

As you can see, the scan is downloaded as a zip archive that contains all the DICOM files.

If you are interested in downloading all data of an entire subject, it is possible to use a helper function
that downloads the data and extracts it in the target directory. This will create a data structure similar to
that of XNAT on your local disk::

    >>> subject = experiment.subject

    >>> subject.download_dir('/home/hachterberg/temp/')
    Downloading http://120.0.0.1/xnat/data/experiments/demo_E00091/scans/ALL/files?format=zip:
    23736 kb
    Downloaded image session to /home/hachterberg/temp/ANONYMIZ3
    Downloaded subject to /home/hachterberg/temp/ANONYMIZ3

To see what is downloaded, we can use the linux command find from ipython::

    $ find /home/hachterberg/temp/ANONYMIZ3
    /home/hachterberg/temp/ANONYMIZ3
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR/resources
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR/resources/DICOM
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR/resources/DICOM/files
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR/resources/DICOM/files/IM2.dcm
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR/resources/DICOM/files/IM32.dcm
    /home/hachterberg/temp/ANONYMIZ3/ANONYMIZ3/scans/1001-MR2-FLAIR/resources/DICOM/files/IM11.dcm
    ...


The REST API allows for downloading of data from XNAT. The xnatpy package
includes helper functions to make the downloading of data easier. For
example, to download all experiments belonging to a subject::

  >>> subject = sandbox_project.subjects['test001']
  >>> subject.download_dir('./Downloads/test001')

This will download all the relevant experiments and unpack them in the target
folder. This is available for
:py:meth:`projects <xnat.classes.ProjectData.download_dir>`,
:py:meth:`subjects <xnat.classes.SubjectData.download_dir>`,
:py:meth:`experiments <xnat.classes.ImageSessionData.download_dir>`,
:py:meth:`scans <xnat.classes.ImageScanData.download_dir>`, and
:py:meth:`resources <xnat.classes.AbstractResource.download_dir>`.

Experiments, scans and resources can also be downloaded in a zip bundle
using the ``download`` method for :py:meth:`experiments <xnat.classes.ImageSessionData.download>`,
:py:meth:`scans <xnat.classes.ImageScanData.download>`, and
:py:meth:`resources <xnat.classes.AbstractResource.download>`.

Custom variables
----------------

The custom variables are exposed as a ``dict``-like object in ``xnatpy``. They are located in the
``field`` attribute under the objects that can have custom variables::

    In [18]: experiment = project.subjects['ANONYMIZ'].experiments['ANONYMIZ']

    In [19]: experiment.fields
    Out[19]: <VariableMap {u'brain_volume': u'0'}>

    In [20]: experiment.fields['brain_volume']
    Out[20]: u'0'

    In [21]: experiment.fields['brain_volume'] = 42.0

    In [22]: experiment.fields
    Out[22]: <VariableMap {u'brain_volume': u'42.0'}>

    In [27]: experiment.fields['brain_volume']
    Out[27]: u'42.0'

Getting external urls of an object
----------------------------------

Sometimes you want to know the full external URL of a resource in XNAT, for this
all XNAT objects have a function to retrieve this::

    >>> experiment_01.external_uri()
    'https://xnat.server.com/data/archive/projects/project/subjects/XNAT_S09618/experiments/XNAT_E36346'

You can change the query string or scheme used with extra arguments:

    >>> experiment_01.external_uri(scheme='test', query={'hello': 'world'})
    'test://xnat.server.com/data/archive/projects/project/subjects/XNAT_S09618/experiments/XNAT_E36346?hello=world'

Importing data into XNAT
------------------------

To add new data into XNAT it is possible to use the REST import service. It
allows you to upload a zip file containing an experiment and XNAT will
automatically try to store it in the correct place::

  >>> session.services.import_('/path/to/archive.zip', project='sandbox', subject='test002')

Will upload the DICOM files in archive.zip and add them as scans under the subject *test002*
in project *sandbox* (the project ID needs to be *sandbox*, not the label). For more information
on importing data see :py:meth:`import_ <xnat.services.Services.import_>`

As it is dangerous to add data straight into the archive due to lack of reviewing, it is possible to also upload
the data to the prearchive first. This can be achieved by adding the ``destination`` argument as follows::

    # Import via prearchive:
    >>> prearchive_session = session.services.import_('/home/hachterberg/temp/ANONYMIZ.zip', project='brainimages', destination='/prearchive')
    >>> print(prearchive_session)
    <PrearchiveSession brainimages/20161107_114859342/ANONYMIZ>

Once the data is uploaded (either via ``xnatpy`` or other means) it is possible to query the prearchive and
process the scans in it. To get a list of ``sessions`` waiting for archiving use the following::

    >>> session.prearchive.sessions()
    [<PrearchiveSession brainimages/20161107_114859342/ANONYMIZ>]

Once the data in the prearchive is located it can be archived as follows::

    >>> prearchive_session = session.prearchive.sessions()[0]
    >>> experiment = prearchive_session.archive(subject='ANONYMIZ3', experiment='ANONYMIZ3')
    >>> print(experiment)
    <MrSessionData ANONYMIZ3 (demo_E00092)>


.. note:: It is worth noting that it is possible to inspect the scan before archiving: one can look at the status,
 move it between projects, list the scans and files contained in the scans.

Prearchive
----------

When scans are send to the XNAT they often end up in the prearchive pending review before 
adding them to the main archive. It is possible to view the prearchive via xnatpy::

  >>> session.prearchive.sessions()
  []

This gives a list of ``PrearchiveSessions`` in the archive. It is possible to 
:py:meth:`archive <xnat.prearchive.PrearchiveSession.archive>`,
:py:meth:`rebuild <xnat.prearchive.PrearchiveSession.rebuild>`,
:py:meth:`move <xnat.prearchive.PrearchiveSession.move>`, or
:py:meth:`delete <xnat.prearchive.PrearchiveSession.delete>`
the session using simple methods. For more information
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

Accessing XNAT files as local files (partial read)
--------------------------------------------------

There is a helper added in xnatpy that allows you to open a remote file (FileData object)
similarly as a local file. Note that it will read the file from the start and until it is done,
seeking will download until the seek point.

For example::

    >>> import xnat
    >>> connection = xnat.connect('https://xnat.server.com')
    >>> file_obj = connection.projects['project'].subjects['S'].experiments['EXP'].scans['T1'].resources['DICOM'].files[0]
    <FileData 1.3.6.1...-18s1eb2.dcm (1.3.6.1...-18s1eb2.dcm)>
    >>> with file_obj.open() as fin:
            data = fin.read(3000)
    >>> print(len(data))
    3000

You can also use this to read the headers of a dicom file using pydicom::

    >>> import pydicom
    >>> with file_obj.open() as fin:
            data = pydicom.dcmread(fin, stop_before_pixels=True)
    
This should read the header and stop downloading once the entire header is read.

.. note:: The file is read in chucks so there might be a bit too much data downloaded

.. note:: If you open the file and not close it, the memory buffer might not be cleaned properly

Accessing DICOM headers of scan
-------------------------------

Sometimes it is desired to read DICOM headers without downloading the entire scan.
XNAT has a dicomdump service which can be used::

    >>> connection.service.dicom_dump(scan_uri)

For more details see :py:meth:`import_ <xnat.services.Services.dicom_dump>`. As
a helper we added a dicom_dump method to ScanData::

    >>> scan.dicom_dump()

See :py:meth:`ScanData.dicom_dump <xnat.mixin.ImageScanData.dicom_dump>` for the details.

A limitation of the dicomdump of XNAT is that field values are truncated under
64 characters. If you want to access the entire dicom header, a convenience method
is added that reads the header via ``pydicom``::

    >>> scan.read_dicom()

This reads only the header and not the pixel data and will only download part
of the file. To read the pixel data use::

    >>> scan.read_dicom(read_pixel_data=True)

For the details see      :py:meth:`ScanData.dicom_dump <xnat.mixin.ImageScanData.read_dicom>`

.. note::
    Only one file is loaded, so the pixel data will only contain a single slice
    unless it is a DICOM Enhanced file


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
