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

import getpass
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


def connect(server, user=None, password=None, verify=True, netrc_file=None, debug=False):
    """
    Connect to a server and generate the correct classed based on the servers xnat.xsd
    This function returns an object that can be used as a context operator. It will call
    disconnect automatically when the context is left. If it is used as a function, then
    the user should call ``.disconnect()`` to destroy the session and temporary code file.

    :param str server: uri of the server to connect to (including http:// or https://)
    :param str user: username to use, leave empty to use netrc entry or anonymous login.
    :param str password: password to use with the username, leave empty when using netrc.
                         If a username is given and no password, there will be a prompt
                         on the console requesting the password.
    :param bool verify: verify the https certificates, if this is false the connection will
                        be encrypted with ssl, but the certificates are not checked. This is
                        potentially dangerous, but required for self-signed certificates.
    :param str netrc_file: alternative location to use for the netrc file (path pointing to
                           a file following the netrc syntax)
    :param debug bool: Set debug information printing on
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
    print('[INFO] Retrieving schema from {}'.format(schema_uri))
    parsed_server = urlparse.urlparse(server)

    if user is None and password is None:
        print('[INFO] Retrieving login info for {}'.format(parsed_server.netloc))
        try:
            if netrc_file is None:
                netrc_file = os.path.join('~', '_netrc' if os.name == 'nt' else '.netrc')
                netrc_file = os.path.expanduser(netrc_file)
            user, _, password = netrc.netrc(netrc_file).authenticators(parsed_server.netloc)
        except (TypeError, IOError):
            print('[INFO] Could not found login, continuing without login')

    if user is not None and password is None:
        password = getpass.getpass(prompt="Please enter the password for user '{}':".format(user))

    requests_session = requests.Session()

    if user is not None:
        requests_session.auth = (user, password)

    if not verify:
        requests_session.verify = False

    if debug:
        print('[DEBUG] GET SCHEMA {}'.format(schema_uri))
    resp = requests_session.get(schema_uri, headers={'Accept-Encoding': None})

    try:
        root = ElementTree.fromstring(resp.text)
    except ElementTree.ParseError as exception:
        if len(resp.text) > 2000:
            excerpt = resp.text[:1000] + '\n ... [CUT] ... \n' + resp.text[-1000:]
        else:
            excerpt = resp.text
        raise ValueError('Could not parse xnat.xsd, server response was ({}):\n"{}"\nOriginal exception: {}'.format(resp.status_code, excerpt, exception))

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

    if debug:
        print('[DEBUG] Code file written to: {}'.format(code_file.name))

    # Import temp file as a module
    xnat_module = imp.load_source('xnat', code_file.name)
    xnat_module._SOURCE_CODE_FILE = code_file.name

    if debug:
        print('[DEBUG] Loaded generated module')

    # Add classes to the __all__
    __all__.extend(['XNAT', 'XNATObject', 'XNATListing', 'Services', 'Prearchive', 'PrearchiveSession', 'PrearchiveScan', 'FileData',])

    # Register all types parsed
    for cls in parser:
        if not (cls.name is None or cls.baseclass.startswith('xs:')):
            XNAT.XNAT_CLASS_LOOKUP['xnat:{}'.format(cls.name)] = getattr(xnat_module, cls.python_name)

            # Add classes to the __all__
            __all__.append(cls.python_name)

    # Create the XNAT connection and return it
    session = xnat_module.XNAT(server=server, interface=requests_session, debug=debug)
    session._source_code_file = code_file.name
    return session

