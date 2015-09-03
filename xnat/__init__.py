import contextlib
import imp
import re
import sys
import tempfile
from xml.etree import ElementTree
from convert_xsd import SchemaParser

import isodate
import requests

def connect(server):
    # Retrieve schema from XNAT server
    schema_uri = '{}/schemas/xnat/xnat.xsd'.format(server)
    print('Retrieving schema from {}'.format(schema_uri))
    resp = requests.get(schema_uri)
    root = ElementTree.fromstring(resp.text)
    
    # Parse xml schema
    parser = SchemaParser()
    parser.parse(root)

    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='_generated_xnat.py', delete=False) as code_file:

        with open('xnat_header.py') as fin:
            for line in fin:
                code_file.write(line)

        code_file.write('# The following code represents the data struction of {}\n# It is automatically generated using {} as input\n'.format(server, schema_uri))

        code_file.write('\n\n\n'.join(str(c).strip() for c in parser if not c.baseclass.startswith('xs:') and c.name is not None))
        code_file.write('\n\nXNAT_CLASS_LOOKUP = {')
        for cls in parser:
            if cls.name is None or cls.baseclass.startswith('xs:'):
                continue
            code_file.write('    "xnat:{}": {},\n'.format(cls.name, cls.python_name))
        code_file.write('    "xnat:fileData": FileData\n')
        code_file.write('}\n')

    print('Code file written to: {}'.format(code_file.name))

    # Import temp file as a module
    xnat_module = imp.load_source('xnat', code_file.name)
    xnat_module._SOURCE_CODE_FILE = code_file.name

    # Create the XNAT connection and return it
    xnat = xnat_module.XNAT(server)
    xnat._source_code_file = code_file.name
    return xnat

