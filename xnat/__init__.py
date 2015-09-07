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


def connect(server, user=None, password=None):
    # Retrieve schema from XNAT server
    schema_uri = '{}/schemas/xnat/xnat.xsd'.format(server.rstrip('/'))
    print('Retrieving schema from {}'.format(schema_uri))
    parsed_server = urlparse.urlparse(server)

    if user is None and password is None:
        print('[INFO] Retrieving login info for {}'.format(parsed_server.netloc))
        try:
            user, _, password = netrc.netrc().authenticators(parsed_server.netloc)
        except TypeError:
            raise ValueError('Could not retrieve login info for "{}" from the .netrc file!'.format(server))

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

    # Register all types parsed
    for cls in parser:
        if not (cls.name is None or cls.baseclass.startswith('xs:')):
            XNAT.XNAT_CLASS_LOOKUP['xnat:{}'.format(cls.name)] = getattr(xnat_module, cls.python_name)

    # Create the XNAT connection and return it
    session = xnat_module.XNAT(server=server, interface=requests_session)
    session._source_code_file = code_file.name
    return session

