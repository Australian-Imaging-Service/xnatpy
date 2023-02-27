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

To store credentials this xnatpy uses the .netrc file on Linux and the _netrc
file on Windows. On linux the file is located in ``~/.netrc`` and on Windows
the file is located in ``%USERPROFILE%\_netrc`` (which typically resolves to
``C:\Users\YourUsername\_netrc``). This file contains login information and
should be accessible ONLY by the user (if not, the module with throw an error
to let you know the file is unsafe). For example, on Linux use::

  echo "machine images.xnat.org
  >     login USERNAME
  >     password PASSWORD" > ~/.netrc
  chmod 600 ~/.netrc

This will create the netrc file with the correct contents and set the
permission correct.

On Windows you can use the command prompt to do the same::

  (echo machine images.xnat.org & echo login USERNAME & echo password PASSWORD) > %userprofile%/_netrc

.. note::

    Replace 'images.xnat.org' with your XNAT server, 'USERNAME' with your username and 'PASSWORD' with your password

Self-closing sessions
^^^^^^^^^^^^^^^^^^^^^

When in a script where there is a possibility for unforeseen errors it is safest
to use a context operator in Python. This can be achieved by using the
following::

  >>> with xnat.connect('http://my.xnat.server') as session:
  ...     print session.projects

As soon as the scope of the with exists (even if because of an exception thrown!)
the session will be disconnected automatically.

Low level REST directives
-------------------------

Though xnatpy is designed to offer a high level pythonic interface, it also easily
exposes all default REST verbs using the following functions:

* :py:meth:`xnat.session.BaseXNATSession.get`
* :py:meth:`xnat.session.BaseXNATSession.head`
* :py:meth:`xnat.session.BaseXNATSession.put`
* :py:meth:`xnat.session.BaseXNATSession.post`
* :py:meth:`xnat.session.BaseXNATSession.delete`

These methods take a (partial) uri and return a requests response. However they do
make use of the session established by xnatpy, so user auth and default error checking
are still in place, for example::

  >>> connection.get('/data/projects')
  # Note that 'https://xnat.example.com/data/projects' would also work but is not needed
  # as the connection already knows the server connected to
  <Response [200]>

These methods also accept arguments for query strings and data (for ``put`` and ``post``). The details
can be found in the documentation of the separate methods.

There is also a useful helper method that gets and unpacks json data :py:meth:`xnat.session.BaseXNATSession.get_json`::

  >>> connection.get_json('/data/project/PROJECT_ID')
  {'items': [{'children':  ..... }]}

Finally there are also methods for data upload and download:

* :py:meth:`xnat.session.BaseXNATSession.download`
* :py:meth:`xnat.session.BaseXNATSession.download_zip`
* :py:meth:`xnat.session.BaseXNATSession.download_stream`
* :py:meth:`xnat.session.BaseXNATSession.upload`

These methods can help you implement arbitrary functionality without limitations.

.. warning::
  A lot of functionality has higher level interfaces which are easier to use and
  it is recommended to use those instead.

.. note::
  The requests session used by xnatpy can be accessed via ``connection.interface``.
  This allows you to anything that requests can but bypasses all error checking of
  xnatpy and is not recommended.


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

Selecting an object based on its uri
------------------------------------

If you already have the uri for an object you can easily fetch the correct xnatpy
object. For example::

  >>> experiment_object = connection.create_object('/data/projects/$PROJECT_ID/experiments/$EXPERIMENT_ID')
  >>> experiment_object
  <MrSessionData EXPERIMENT_LABEL (EXPERIMENT_ID)>

This object is exactly the same as if it would be acquired from a listing, so you can
reference the parameters, fields, etc.

This works for any valid url of which xnatpy can retrieve the data and figure out the xsitype, see
:py:meth:`xnat.session.BaseXNATSession.create_object` for details.

.. note::
    xnatpy can also be called using urls that start with the uri connected to, e.g. if
    given ``https://xnat.example.com`` as argument when connecting, using the uri
    ``https://xnat.example.com/data/projects/$PROJECT_ID/experiments/$EXPERIMENT_ID`` would
    also work.

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

Custom variable are exposes primiary using the ``object.custom_variables`` property.
This is a mapping that exposes the custom variable groups. Each group is a mapping
that gives access to the variables::

    In [4]: subject.custom_variables
    Out[4]: <CustomVariableMap groups: [default]>

    In [5]: subject.custom_variables['default']
    Out[5]: <CustomVariableGroup default {Notes (string): "some note", Diagnosis (string): None}>

    In [6]: subject.custom_variables['default']['Notes']
    Out[6]: "some note"

    In [7]: subject.custom_variables['default']['Notes'] = "update note"

The good thing about this way of accessing custom variables this way is that
they are casted to the right type and constraints are checked client side when
trying to update them.

The custom variables are also exposed as a ``dict``-like object in ``xnatpy``. They are located in the
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

.. note::

    Accessing custom variables via ``.fields`` is low-level and bypasses
    all typing and constraints set via the XNAT interface. Also non-defined
    fields can be added and retrieved (those will not show in the interface).

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

Searching
---------

XNATpy allows using the XNAT search via the REST API. For this XNAT expects an
XML document that specifies your query. The general information on search with
the XNAT REST API is taken from
`XNAT wiki: How to Query the XNAT Search Engine with REST API <https://wiki.xnat.org/display/XAPI/How+to+Query+the+XNAT+Search+Engine+with+REST+API>`_

To make it simple to search, XNATpy
offers its own search intertface. It is inspired by SQLAlchemy and allows using
the object model to specify your query::

    >>> SubjectData = connection.classes.SubjectData
    >>> SubjectData.query().filter(SubjectData.project == 'sandbox').all()
    [<SubjectData ANONYMIZ (BMIAXNAT03_S00525)>,
     <SubjectData case001 (BMIAXNAT07_S00009)>,
     <SubjectData SUBJECT001 (BMIAXNAT12_S00261)>,
     <SubjectData TEST_001 (BMIAXNAT15_S00874)>,
     <SubjectData Brain-0001 (BMIAXNAT34_S00001)>,
     <SubjectData Brain-0002 (BMIAXNAT34_S00002)>,
     <SubjectData TEST01 (BMIAXNAT_S17618)>]

In the example above, we use the subject data class to query. We get the generated class
from ``connection.classes`` and give it a local name for convenience. Then we create a query
for this class, so the result of our query will be subjects. Subsequently we add a filter
where we constrain the results to match a certain project id. Finally we request all matching
objects.

Multiple constraints can be used by giving multiple arguments to filter::

    >>> SubjectData.query().filter(SubjectData.project == 'sandbox', SubjectData.label.like('Brain*')).all()
    [<SubjectData Brain-0001 (BMIAXNAT34_S00001)>,
     <SubjectData Brain-0002 (BMIAXNAT34_S00002)>]

Also, filter can be called on the resulting query to stack filters::

    >>> SubjectData.query().filter(SubjectData.project == 'sandbox').filter(SubjectData.label.like('Brain*')).all()
    [<SubjectData Brain-0001 (BMIAXNAT34_S00001)>,
     <SubjectData Brain-0002 (BMIAXNAT34_S00002)>]

Finally compound constraints can be created using the ``&`` (for and) and ``|`` (for or) operators::

    >>> SubjectData.query().filter((SubjectData.project == 'sandbox') & (SubjectData.label.like('Brain*'))).all()
    [<SubjectData Brain-0001 (BMIAXNAT34_S00001)>,
     <SubjectData Brain-0002 (BMIAXNAT34_S00002)>]

The following operators can be used for creating constraints on properties:

======== ==============================
Operator Description
======== ==============================
``==``   Equals
``<=``   Smaller or equal
``<``    Smaller
``>=``   Larger or equal
``>``    Larger
``like`` Like for fuzzy string matching
======== ==============================

The following compounding multiple contstrains operators are available:

======== ==============================
Operator Description
======== ==============================
``&``    AND operator
``|``    OR operator
======== ==============================

.. note::

     Do not forget to use the correct parenthesis as the & and | operators have a high
     priority in Python, e.g. ``a == b & c == d`` will fail, use ``(a == b) & (c == d)``

The search query can be executed using the ``all()`` method to find all matching objects.
There are other options available as well ways to create a table of results similar to the
original XNAT search. For example::

    >>> query = SubjectData.query().filter((SubjectData.project == 'sandbox') & (SubjectData.label.like('Brain*')))
    >>> query.all()
    [<SubjectData Brain-0001 (BMIAXNAT34_S00001)>,
     <SubjectData Brain-0002 (BMIAXNAT34_S00002)>]

    >>> query.first()
    <SubjectData Brain-0001 (BMIAXNAT34_S00001)>

    >>> query.last()
    <SubjectData Brain-0002 (BMIAXNAT34_S00002)>

    >>> query.tabulate_csv()
    'subject_label,subjectid,insert_user,insert_date,projects,project,gender,handedness,dob,educ,ses,quarantine_status\nBrain-0001,BMIAXNAT34_S00001,ibocharov,2022-11-15 22:26:38.676,",<sandbox>",sandbox,,,,,,active\nBrain-0002,BMIAXNAT34_S00002,ibocharov,2022-11-15 22:42:20.324,",<sandbox>",sandbox,,,,,,active\n'

    >>> query.tabulate_dict()
    [{'subject_label': 'Brain-0001',
      'subjectid': 'BMIAXNAT34_S00001',
      'insert_user': 'ibocharov',
      'insert_date': '2022-11-15 22:26:38.676',
      'projects': ',<sandbox>',
      'project': 'sandbox',
      'gender': '',
      'handedness': '',
      'dob': '',
      'educ': '',
      'ses': '',
      'quarantine_status': 'active'},
     {'subject_label': 'Brain-0002',
      'subjectid': 'BMIAXNAT34_S00002',
      'insert_user': 'ibocharov',
      'insert_date': '2022-11-15 22:42:20.324',
      'projects': ',<sandbox>',
      'project': 'sandbox',
      'gender': '',
      'handedness': '',
      'dob': '',
      'educ': '',
      'ses': '',
      'quarantine_status': 'active'}]

    # This requires pandas to be installed
    >>> query.tabulate_pandas()
      subject_label          subjectid insert_user              insert_date  ... dob educ  ses  quarantine_status
    0    Brain-0001  BMIAXNAT34_S00001   ibocharov  2022-11-15 22:26:38.676  ... NaN  NaN  NaN             active
    1    Brain-0002  BMIAXNAT34_S00002   ibocharov  2022-11-15 22:42:20.324  ... NaN  NaN  NaN             active

    [2 rows x 12 columns]

As you can see there are quite some ways to request the result from a query,
for completeness see the following table:

=================== =================================================================
Method              Description
=================== =================================================================
``all``             Get all objects
``first``           Get first matching object
``last``            Get last matching object
``one``             Get one object, throws error if not exactly one object is matched
``one_or_none``     Get one object or return None if no match is found. Throws error
                    if not exactly zero or one objects are matched.
``tabulate_csv``    Return a string containing a CSV tabulation of the data
``tabulate_dict``   Return a list of dicts representing a tabulation of the data
``tabulate_json``   Return a string with the JSON response from the server
``tabulate_pandas`` Return a pandas DataFrame with the tabulation of the data
=================== =================================================================


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

Re-using XNAT jsession
----------------------

In same cases you might want multiple instance of xnatpy share a login session
on the XNAT server. This can be achieved by supplying the `jsession` argument on `connect`.
This will bypass all login logic and create a JSESSION cookie.

By default xnatpy actived closes a jsession on disconnect. If you want to be able to re-use
the session after you disconnected xnatpy, you can set `cli=True` when creating the connection.
However, if you do this, you have to actively destroy the jsession or it will time out after a
set time (15 minutes by default).

For example::

    # Create a connection and get the JSESSION
    >>> connection = xnat.connect('htpps://xnat.example.com', user=...)
    >>> connection.JSESSION
    '24FA18BFA3DD4EB9C634AD79FE050339'

    # Create a connection with a shared JSESSION
    >>> connection2 = xnat.connect('https://xnat.example.com', jsession=connection.JSESSION, cli=True)

    # If the jsession is still alive it should be the same (if not an error will be raised)
    >>> connection2.JSESSION
    '24FA18BFA3DD4EB9C634AD79FE050339'

    # We can close connection2 safely without affecting connection because of
    # the cli=True, however closing connection will destroy the JSESSION on
    # server and make connection2 fail
    >>> connection2.disconnect()

    # This should still work
    >>> connection.projects[...].subjects
    ...

    >>> connection.disconnect


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
