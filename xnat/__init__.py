# Copyright 2011-2014 Biomedical Imaging Group Rotterdam, Departments of
# Medical Informatics and Radiology, Erasmus MC, Rotterdam, The Netherlands
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This package contains the entire client. The connect function is the only
function actually in the package. All following classes are created based on
the https://central.xnat.org/schema/xnat/xnat.xsd schema and the xnatcore and
xnatbase modules, using the convert_xsd.
"""

import imp
import os
import netrc
import tempfile
from xml.etree import ElementTree
import urlparse

import requests

from xnatcore import XNAT
from convert_xsd import SchemaParser

FILENAME = __file__

__all__ = ['connect']

def connect(server, user=None, password=None):
    """
    Connect to a server and generate the correct classed based on the servers xnat.xsd
    This function returns an object that can be used as a context operator. It will call
    disconnect automatically when the context is left. If it is used as a function, then
    the user should call ``.disconnect()`` to destroy the session and temporary code file.

    :param str server: uri of the server to connect to (including http:// or https://)
    :param str user: username to use, leave empty to use netrc entry or anonymous login.
    :param str password: password to use with the username
    :return: XNAT session object

    Preferred use::

        >>> import xnat
        >>> with xnat.connect('https://central.xnat.org') as session:
        ...    subjects = session.projects['Sample_DICOM'].subjects
        ...    print('Subjects in the SampleDICOM project: {}'.format(subjects))
        Subjects in the SampleDICOM project: <XNATListing (CENTRAL_S01894, dcmtest1): <SubjectData CENTRAL_S01894>, (CENTRAL_S00461, PACE_HF_SUPINE): <SubjectData CENTRAL_S00461>>

    Alternative use::

        >>> import xnat
        >>> session = xnat.connect('https://central.xnat.org')
        >>> subjects = session.projects['Sample_DICOM'].subjects
        >>> print('Subjects in the SampleDICOM project: {}'.format(subjects))
        Subjects in the SampleDICOM project: <XNATListing (CENTRAL_S01894, dcmtest1): <SubjectData CENTRAL_S01894>, (CENTRAL_S00461, PACE_HF_SUPINE): <SubjectData CENTRAL_S00461>>
        >>> session.disconnect()
    """
    # Retrieve schema from XNAT server
    schema_uri = '{}/schemas/xnat/xnat.xsd'.format(server.rstrip('/'))
    print('Retrieving schema from {}'.format(schema_uri))
    parsed_server = urlparse.urlparse(server)

    if user is None and password is None:
        print('[INFO] Retrieving login info for {}'.format(parsed_server.netloc))
        try:
            user, _, password = netrc.netrc().authenticators(parsed_server.netloc)
        except (TypeError, IOError):
            print('[INFO] Could not found login, continuing without login')

    requests_session = requests.Session()
    if (user is not None) or (password is not None):
        requests_session.auth = (user, password)

    resp = requests_session.get(schema_uri)
    try:
        root = ElementTree.fromstring(resp.text)
    except ElementTree.ParseError:
        raise ValueError('Could not parse xnat.xsd, server response was ({}) {}'.format(resp.status_code, resp.text))
    
    # Parse xml schema
    parser = SchemaParser()
    parser.parse(root)

    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_generated_xnat.py', delete=False) as code_file:

        header = os.path.join(os.path.dirname(FILENAME), 'xnatcore.py')
        with open(header) as fin:
            for line in fin:
                code_file.write(line)

        code_file.write('# The following code represents the data struction of {}\n# It is automatically generated using {} as input\n'.format(server, schema_uri))
        code_file.write('\n\n\n'.join(str(c).strip() for c in parser if not c.baseclass.startswith('xs:') and c.name is not None))

    print('Code file written to: {}'.format(code_file.name))

    # Import temp file as a module
    xnat_module = imp.load_source('xnat', code_file.name)
    xnat_module._SOURCE_CODE_FILE = code_file.name

    # Add classes to the __all__
    __all__.extend(['XNAT', 'XNATObject', 'XNATListing', 'Services', 'Prearchive', 'PrearchiveEntry', 'FileData',])

    # Register all types parsed
    for cls in parser:
        if not (cls.name is None or cls.baseclass.startswith('xs:')):
            XNAT.XNAT_CLASS_LOOKUP['xnat:{}'.format(cls.name)] = getattr(xnat_module, cls.python_name)

            # Add classes to the __all__
            __all__.append(cls.python_name)

    # Create the XNAT connection and return it
    session = xnat_module.XNAT(server=server, interface=requests_session)
    session._source_code_file = code_file.name
    return session

