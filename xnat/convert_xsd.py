# Copyright 2011-2015 Biomedical Imaging Group Rotterdam, Departments of
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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
import collections
import contextlib
import inspect
import keyword
import os
import re
from xml.etree import ElementTree

from . import core
from . import xnatbases
from .constants import SECONDARY_LOOKUP_FIELDS, FIELD_HINTS, CORE_REST_OBJECTS


FILE_HEADER = '''
# Copyright 2011-2015 Biomedical Imaging Group Rotterdam, Departments of
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

from __future__ import absolute_import
from __future__ import unicode_literals
import os
import tempfile  # Needed by generated code
from zipfile import ZipFile  # Needed by generated code

from xnat import search
from xnat.core import XNATObject, XNATNestedObject, XNATSubObject, XNATListing, XNATSimpleListing, XNATSubListing, caching
from xnat.utils import mixedproperty


SESSION = None


def current_session():
    return SESSION


# These mixins are to set the xnat_session automatically in all created classes
class XNATObjectMixin(XNATObject):
    @mixedproperty
    def xnat_session(self):
        return current_session()

    @classmethod
    def query(cls, *constraints):
        query = search.Query(cls._XSI_TYPE, cls.xnat_session)

        # Add in constraints immediatly
        if len(constraints) > 0:
            query = query.filter(*constraints)

        return query


class XNATNestedObjectMixin(XNATNestedObject):
    @mixedproperty
    def xnat_session(self):
        return current_session()


class XNATSubObjectMixin(XNATSubObject):
    @mixedproperty
    def xnat_session(self):
        return current_session()


class FileData(XNATObjectMixin):
    SECONDARY_LOOKUP_FIELD = "{file_secondary_lookup}"
    _XSI_TYPE = 'xnat:fileData'

    def __init__(self, uri, xnat_session, id_=None, datafields=None, name=None, parent=None, field_name=None):
        super(FileData, self).__init__(uri=uri,
                                   xnat_session=xnat_session,
                                   id_=id_,
                                   datafields=datafields,
                                   parent=parent,
                                   field_name=field_name)
        if name is not None:
            self._name = name

    @property
    def name(self):
        return self._name

    def delete(self):
        self.xnat_session.delete(self.uri)

    def download(self, path, verbose=True):
        self.xnat_session.download(self.uri, path, verbose=verbose)

    def download_stream(self, target_stream, verbose=False):
        self.xnat_session.download_stream(self.uri, target_stream, verbose=verbose)

    @property
    @caching
    def size(self):
        response = self.xnat_session.head(self.uri)
        return response.headers['Content-Length']


# Empty class lookup to place all new lookup values
XNAT_CLASS_LOOKUP = {{
    "xnat:fileData": FileData,
}}


# The following code represents the data structure of the XNAT server
# It is automatically generated using
{schemas}


'''

# TODO: Add more fields to FileData from [Name, Size, URI, cat_ID, collection, file_content, file_format, tile_tags]?
# TODO: Add display identifiers support (DONE?)
# <xs:annotation>
# <xs:appinfo>
# <xdat:element displayIdentifiers="label"/>
# </xs:appinfo>
# <xs:documentation>An individual person involved in experimental research</xs:documentation>
# </xs:annotation>
# <xs:sequence>
# TODO: Add XPATHs for setting SubObjects (SEMI-DONE)
# TODO: Make Listings without key and with numeric index possible (inProgress)
# TODO: Fix scan parameters https://groups.google.com/forum/#!topic/xnat_discussion/GBZoamC2ZmY
# TODO: Check the nesting weirdness in petScanDataParametersFramesFrames (DONE?)
# TODO: Figure out the object/subobject/semi-subobject mess.
# TODO: Move all system function to use a __ prefix


class BaseClassRepresentation(object):
    def __init__(self, parser, name, parent=None):
        self.parser = parser
        self.name = name
        self.parent = parent


class SimpleClassRepresentation(BaseClassRepresentation):
    def __init__(self, keyname, type_, **kwargs):
        super(SimpleClassRepresentation, self).__init__(**kwargs)
        self.keyname = keyname
        self.type = type_


class SubObjectClassRepresentation(BaseClassRepresentation):
    def __init__(self, xsi_type, field_name, **kwargs):
        super(SubObjectClassRepresentation, self).__init__(**kwargs)
        self._xsi_type = xsi_type
        self.attributes = collections.OrderedDict()
        self.field_name = field_name
        self._display_identifier = None


class ClassRepresentation(BaseClassRepresentation):
    # Override strings for certain properties
    SUBSTITUTIONS = {
    #        "fields": "    @property\n    def fields(self):\n        return self._fields",
            }

    # Fields for lookup besides the id

    def __init__(self, xsi_type, field_name=None, sub_object=True, **kwargs):
        super(ClassRepresentation, self).__init__(**kwargs)
        self._xsi_type = xsi_type
        self._base_class = None
        self.attributes = collections.OrderedDict()
        self.field_name = field_name
        self.abstract = False
        self._display_identifier = None
        self._sub_object = sub_object

        self.parser.xsi_to_cls_mapping[self.xsi_type] = self

    def __repr__(self):
        return '<ClassRepresentation {}({})>'.format(self.name, self.base_class)

    def __str__(self):
        base = self.get_base_template()
        if base is not None:
            base_source = inspect.getsource(base)
            base_source = re.sub(r'class {}\(XNATBaseObject\):'.format(self.python_name), 'class {}({}):'.format(self.python_name, self.python_baseclass), base_source)
            header = base_source.strip() + '\n\n    # END HEADER\n'
        else:
            header = '# No base template found for {}\n'.format(self.python_name)
            header += "class {name}({base}):\n".format(name=self.python_name, base=self.python_baseclass)

        header += "    # Abstract: {}\n".format(self.abstract)

        if self.display_identifier is not None:
            header += "    _DISPLAY_IDENTIFIER = '{}'\n".format(self.display_identifier)

        if 'fields' in self.attributes:
            header += "    _HAS_FIELDS = True\n"

        if self.parent is not None:
            header += "    _PARENT_CLASS = {}\n".format(self.python_parentclass)
            header += "    _FIELD_NAME = '{}'\n".format(self.field_name)
        elif self.xsi_type in FIELD_HINTS:
            header += "    _CONTAINED_IN = '{}'\n".format(FIELD_HINTS[self.xsi_type])

        header += "    _XSI_TYPE = '{}'\n".format(self.xsi_type)
        header += "    _IS_SUB_OBJECT = {}\n\n".format(self._sub_object)

        header += "    @classmethod\n" \
                  "    def __register(cls, target):\n" \
                  "        target['{}'] = cls\n\n".format(self.xsi_type_registration)

        if self.xsi_type in SECONDARY_LOOKUP_FIELDS:
            header += self.init

        if self.display_identifier is not None:
            header += ("    @property\n"
                       "    def display_identifier(self):\n"
                       "        return self.{}\n\n".format(self.display_identifier))

        #print('--- CLASS {} ---'.format(self.name))
        properties = '\n\n'.join(self.print_property(p) for p in self.attributes.values() if not self.hasattr(p.clean_name))
        return '{}{}'.format(header, properties)

    @property
    def display_identifier(self):
        if self.xsi_type in SECONDARY_LOOKUP_FIELDS:
            return SECONDARY_LOOKUP_FIELDS[self.xsi_type]
        else:
            return self._display_identifier

    @display_identifier.setter
    def display_identifier(self, value):
        self._display_identifier = value

    @property
    def base_class(self):
        if self._base_class is None:
            if not self._sub_object:
                if self.xsi_type in CORE_REST_OBJECTS:
                    return 'XNATObjectMixin'
                else:
                    return 'XNATNestedObjectMixin'
            else:
                return 'XNATSubObjectMixin'
        else:
            return self._base_class

    @base_class.setter
    def base_class(self, value):
        if self._base_class is None:
            self._base_class = value
        else:
            raise ValueError('Trying to reset base class again from {} to {}'.format(self._base_class, value))

    def root_base_class(self):
        base = self.base_class

        while not base.startswith('XNAT'):
            cls = self.parser.class_list[base]
            base = cls.base_class

        return base

    @property
    def xsi_type(self):
        xsi_type_name, xsi_type_extension = self._xsi_type
        if xsi_type_name in self.parser.cls_to_xsi_mapping:
            result = self.parser.cls_to_xsi_mapping[xsi_type_name] + xsi_type_extension
        else:
            result = 'xnat:' + xsi_type_name

        return result

    @property
    def xsi_type_registration(self):
        xsi_type_name, xsi_type_extension = self._xsi_type
        if xsi_type_name in self.parser.cls_to_xsi_mapping:
            result = self.parser.cls_to_xsi_mapping[xsi_type_name] + xsi_type_extension
        elif xsi_type_extension == '':
            result = 'xnat:' + xsi_type_name
        else:
            result = 'xnatpy:' + self.name

        return result

    def hasattr(self, name):
        base = self.get_base_template()

        if base is not None:
            return hasattr(base, name)
        else:
            base = self.parser.class_list.get(self.base_class)
            if base is not None:
                return base.hasattr(name)
            else:
                base = self.get_super_class()
                return hasattr(base, name)

    def getattr(self, name):
        base = self.get_base_template()

        if base is not None:
            return getattr(base, name)
        else:
            base = self.parser.class_list.get(self.base_class)
            if base is not None:
                return base.getattr(name)
            else:
                base = self.get_super_class()
                return getattr(base, name)

    @staticmethod
    def _pythonize_name(name):
        parts = name.split('_')
        parts = [x[0].upper() + x[1:] for x in parts]
        return ''.join(parts)

    @property
    def python_name(self):
        return self._pythonize_name(self.name)

    @property
    def python_baseclass(self):
        return self._pythonize_name(self.base_class)

    @property
    def python_parentclass(self):
        return self._pythonize_name(self.parent)

    def get_base_template(self):
        if hasattr(xnatbases, self.python_name):
            return getattr(xnatbases, self.python_name)

    def get_super_class(self):
        if hasattr(core, self.python_baseclass):
            return getattr(core, self.python_baseclass)

    def print_property(self, prop):
        if prop.name in self.SUBSTITUTIONS:
            return self.SUBSTITUTIONS[prop.name]
        else:
            data = str(prop)
            if prop.name == SECONDARY_LOOKUP_FIELDS.get(self.name, '!None'):
                head, tail = data.split('\n', 1)
                data = '{}\n    @caching\n{}'.format(head, tail)
            return data

    @property
    def init(self):
        return \
"""    def __init__(self, uri=None, xnat_session=None, id_=None, datafields=None, parent=None, {lookup}=None, **kwargs):
        super({name}, self).__init__(uri=uri, xnat_session=xnat_session, id_=id_, datafields=datafields, parent=parent, {lookup}={lookup}, **kwargs)
        if {lookup} is not None:
            self._cache['{lookup}'] = {lookup}

""".format(name=self.python_name, lookup=SECONDARY_LOOKUP_FIELDS[self.xsi_type])


class Attribute(object):
    __metaclass__ = ABCMeta

    def __init__(self, parser, name, type_=None, restrictions=None, docstring=None, element_class=None, parent_class=None):
        self.docstring = docstring
        self.parser = parser
        self.name = name
        self.type_ = type_
        self.element_class = element_class
        self.parent_class = parent_class

        if restrictions is not None:
            self.restrictions = restrictions
        else:
            self.restrictions = {}

    def __repr__(self):
        parent = self.parent_class.name if self.parent_class else None
        element = self.element_class.name if self.element_class else None

        return '<{} {} (parent: {}, element: {})>'.format(type(self).__name__,
                                                          self.name,
                                                          parent,
                                                          element)

    @abstractmethod
    def __str__(self):
        """String version"""

    @property
    def clean_name(self):
        name = re.sub('[^0-9a-zA-Z]+', '_', self.name)

        if keyword.iskeyword(name):
            name += '_'
        return name.lower()

    def restrictions_code(self):
        if len(self.restrictions) > 0:
            data = '\n        # Restrictions for value'
            if 'min' in self.restrictions:
                data += "\n        if value < {min}:\n            raise ValueError('{name} has to be greater than or equal to {min}')\n".format(name=self.name, min=self.restrictions['min'])
            if 'max' in self.restrictions:
                data += "\n        if value > {max}:\n            raise ValueError('{name} has to be smaller than or equal to {max}')\n".format(name=self.name, max=self.restrictions['max'])
            if 'maxlength' in self.restrictions:
                data += "\n        if len(value) > {maxlength}:\n            raise ValueError('length {name} has to be smaller than or equal to {maxlength}')\n".format(name=self.name, maxlength=self.restrictions['maxlength'])
            if 'minlength' in self.restrictions:
                data += "\n        if len(value) < {minlength}:\n            raise ValueError('length {name} has to be larger than or equal to {minlength}')\n".format(name=self.name, minlength=self.restrictions['minlength'])
            if 'enum' in self.restrictions:
                data += "\n        if value not in [{enum}]:\n            raise ValueError('{name} has to be one of: {enum}')\n".format(name=self.name, enum=', '.join('"{}"'.format(x.replace("'", "\\'")) for x in self.restrictions['enum']))

            return data
        else:
            return ''


class AttributePrototype(object):
    def __init__(self, cls, data=None, parent=None):
        self.cls = cls

        if data is None:
            self.data = collections.defaultdict(collections.OrderedDict)
        elif not isinstance(data, collections.defaultdict):
            self.data = collections.defaultdict(collections.OrderedDict)
            self.data.update(data)
        else:
            self.data = data

        self.data['parent_class'] = parent

    def create(self, parser):
        if 'element_class' in self.data:
            element_class = self.data['element_class']

            if element_class is not None and len(element_class.attributes) == 1:
                element_property = element_class.attributes.values()[0]

                if isinstance(element_property, AttributePrototype):
                    element_property = element_property.create(parser)

                # Reset parent to current parent
                element_property.parent_class = self.data["parent_class"]

                if isinstance(element_property, PropertyListingRepresentation):
                    print("+--> Found element class: [{}]".format(element_class.name))
                    print("+--> Found element property: [{}] {}".format(type(element_property).__name__,
                                                                        element_property.name))
                    element_property.field_name = '{}/{}'.format(self.data["name"], element_property.name)
                    element_property.name = self.data["name"]
                    return element_property
        elif isinstance(self.data['type_'], str) and self.data['type_'].startswith('xs:') and self.cls is PropertySubObjectRepresentation:
            self.cls = PropertyRepresentation
        elif self.data['type_'] is None:
            self.data['type_'] = 'xs:string'
            self.cls = PropertyRepresentation

        return self.cls(parser=parser, **self.data)

    def __repr__(self):
        return "<AttributePrototype [{}] {}>".format(self.cls.__name__, self.data)


class ConstantRepresentation(Attribute):
    def __init__(self, parser, name, value=None):
        super(ConstantRepresentation, self).__init__(parser, name)

        self.value = value

    def __str__(self):
        return "    {s.clean_name} = {s.value}".format(s=self)

    def __repr__(self):
        return '<ConstantRepresentation {}({})>'.format(self.name, self.value)

    @property
    def clean_name(self):
        name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
        name = '_{}'.format(name.upper())

        return name


class PropertyRepresentation(Attribute):
    def __repr__(self):
        return '<PropertyRepresentation {}({})>'.format(self.name, self.type_)

    def __str__(self):
        docstring = '\n        """ {} """'.format(self.docstring) if self.docstring is not None else ''
        return \
    """    @mixedproperty
    def {clean_name}(cls):{docstring}
        # 0 Automatically generated Property, type: {type_}
        return search.SearchField(cls, "{name}")

    @{clean_name}.getter
    def {clean_name}(self):
        # Generate automatically, type: {type_}
        return self.get("{name}", type_="{type_}")

    @{clean_name}.setter
    def {clean_name}(self, value):{docstring}{restrictions}
        # Automatically generated Property, type: {type_}
        self.set("{name}", value, type_="{type_}")""".format(clean_name=self.clean_name,
                                                             docstring=docstring,
                                                             name=self.name,
                                                             type_=self.type_,
                                                             restrictions=self.restrictions_code())


class PropertySubObjectRepresentation(Attribute):
    def __repr__(self):
        return '<PropertySubObjectRepresentation {}({})>'.format(self.name, self.type_)

    def __str__(self):
        docstring = '\n        """ {} """'.format(self.docstring) if self.docstring is not None else ''
        if self.type_ is None:
            xsi_type = self.element_class.xsi_type_registration
            xsi_type_arg = ', "{}"'.format(xsi_type)
        else:
            xsi_type = '{}'.format(core.TYPE_HINTS.get(self.name, self.type_))
            xsi_type_arg = ''

        return \
            """    @mixedproperty
    def {clean_name}(cls):{docstring}
        # 1 Automatically generated Property, type: {type_}
        return XNAT_CLASS_LOOKUP["{xsi_type}"]

    @{clean_name}.getter
    @caching
    def {clean_name}(self):
        # Generated automatically, type: {type_}
        return self.get_object("{name}"{xsi_type_arg})""".format(clean_name=self.clean_name,
                                                                 docstring=docstring,
                                                                 name=self.name,
                                                                 type_=self.type_,
                                                                 xsi_type=xsi_type,
                                                                 xsi_type_arg=xsi_type_arg)


class PropertyListingRepresentation(Attribute):
    def __init__(self, display_identifier=None, field_name=None, **kwargs):
        super(PropertyListingRepresentation, self).__init__(**kwargs)
        self.display_identifier = display_identifier
        self.field_name = field_name

    def __repr__(self):
        return '<PropertyListingRepresentation {}({})>'.format(self.name, self.type_)

    def __str__(self):
        print('SELF data: {}'.format(vars(self)))

        # Figure out the baseclass of the elements
        if self.element_class is not None:
            xsi_type = self.element_class.xsi_type_registration
            root_base = self.element_class.root_base_class()
        elif self.type_ is not None:
            xsi_type = self.type_
            root_base = self.parser.xsi_to_cls_mapping.get(self.type_)
            if root_base is not None:
                root_base = root_base.root_base_class()
            else:
                root_base = 'XNATSimpleType'
        else:
            raise ValueError('This should never happen!')

        # Get the class of the listing to use
        LISTING_CLASSES = {
            'XNATObjectMixin': 'XNATListing',
            'XNATSubObjectMixin': 'XNATSubListing',
            'XNATSimpleType': 'XNATSimpleListing',
        }

        listing_class = LISTING_CLASSES.get(root_base, 'XNATSubListing')

        # TODO: Clean up this mess
        if self.element_class is not None:
            ec = "'{e.name}'  '{e.python_name}'  '{e.xsi_type_registration}'".format(e=self.element_class)
        else:
            ec = "None"

        if self.type_ is not None:
            print('Found type: {}'.format(self.type_))
            if self.type_ in self.parser.xsi_to_cls_mapping:
                cls = self.parser.xsi_to_cls_mapping[self.type_].name
            else:
                cls = self.type_.split(':')[1]
            print('Found class name: {}'.format(cls))

            if cls in ['string', 'float', 'int']:
                print('Found string TYPE {}'.format(self.clean_name))
                secondary_lookup = "N/A"
            else:
                cls = self.parser.class_list[cls]
                secondary_lookup = cls.display_identifier
                print('Secondary lookup: {}'.format(secondary_lookup))
        else:
            secondary_lookup = self.display_identifier

        if secondary_lookup is not None:
            secondary_lookup = "'{}'".format(secondary_lookup)

        return """    @property
    @caching
    def {clean_name}(self):
        # Automatically generated PropertyListing, type: {type_}
        # Element class: '{e}'
        # Secondary lookup: '{sl}'
        # Root base: '{rb}'
        return {cls}(uri=self.fulluri + '/{name}',
                     parent=self,
                     field_name='{field_name}',
                     secondary_lookup_field={sl},
                     xsi_type='{type_}')""".format(clean_name=self.clean_name,
                                                   cls=listing_class,
                                                   name=self.name,
                                                   field_name=self.field_name or self.name,
                                                   e=ec,
                                                   sl=secondary_lookup,
                                                   rb=root_base,
                                                   type_=xsi_type)


class SchemaParser(object):
    def __init__(self, debug=False):
        self.class_list = collections.OrderedDict()
        self.unknown_tags = set()
        self.new_class_stack = [None]
        self.new_property_stack = [None]
        self.property_prefixes = []
        self.debug = debug
        self.schemas = []
        self.cls_to_xsi_mapping = collections.OrderedDict()
        self.xsi_to_cls_mapping = collections.OrderedDict()

    def parse_schema_xmlstring(self, xml, schema_uri):
        root = ElementTree.fromstring(xml)

        # Register schema as being loaded
        self.schemas.append(schema_uri)

        # Parse xml schema
        self.parse(root, toplevel=True)

        if self.debug:
            print('[DEBUG] Found {} unknown tags: {}'.format(len(self.unknown_tags),
                                                             self.unknown_tags))

        return True

    def parse_schema_file(self, filepath):
        filepath = os.path.abspath(filepath)
        filepath = os.path.normpath(filepath)

        schema_uri = 'file://{}'.format(filepath)

        with open(filepath) as fin:
            data = fin.read()

        self.parse_schema_xmlstring(data, schema_uri=schema_uri)

    def parse_schema_uri(self, requests_session, schema_uri):
        print('[INFO] Retrieving schema from {}'.format(schema_uri))

        if self.debug:
            print('[DEBUG] GET SCHEMA {}'.format(schema_uri))
        resp = requests_session.get(schema_uri, headers={'Accept-Encoding': None})
        data = resp.text

        try:
            return self.parse_schema_xmlstring(data, schema_uri=schema_uri)
        except ElementTree.ParseError as exception:
            if 'action="/j_spring_security_check"' in data:
                print('[ERROR] You do not have access to this XNAT server, please check your credentials!')
            elif 'Status 403 - Your password has expired' in data:
                print('[ERROR] Your account has expired, please update your password via the website.')
            elif 'java.lang.IllegalStateException' in data:
                print('[ERROR] The server returned an error. You probably do not'
                      ' have access to this XNAT server, please check your credentials!')
            else:
                print('[ERROR] Could not parse schema from {}, not valid XML found'.format(schema_uri))

                if self.debug:
                    print('[DEBUG] XML schema request returned the following response: [{}] {}'.format(resp.status_code,
                                                                                                       data))
            return False

    @staticmethod
    def find_schema_uris(text):
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError:
            raise ValueError('Could not parse xml file')

        schemas_string = root.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', '')
        schemas = [x for x in schemas_string.split() if x.endswith('.xsd')]

        return schemas

    def __iter__(self):
        visited = {'XNATObjectMixin', 'XNATSubObjectMixin', 'XNATNestedObjectMixin'}
        nr_previsited = len(visited)
        tries = 0
        yielded_anything = True
        while len(visited) < len(self.class_list) and yielded_anything and tries < 250:
            yielded_anything = False
            for key, value in self.class_list.items():
                if key in visited:
                    continue

                base = value.base_class
                if not base.startswith('xs:') and base not in visited:
                    continue

                if value.parent is not None and value.parent not in visited:
                    continue

                visited.add(key)
                yielded_anything = True
                yield value

            tries += 1

        expected = len(self.class_list) + nr_previsited  # We started with two "visited" classes
        if self.debug:  # and len(visited) < len(self.class_list):
            print('[DEBUG] Visited: {}, expected: {}'.format(len(visited), expected))
            print('[DEBUG] Missed: {}'.format(set(self.class_list) - visited))
            print('[DEBUG] Spent {} iterations'.format(tries))

    @contextlib.contextmanager
    def descend(self, new_class=None, new_property=None, property_prefix=None):
        if new_class is not None:
            self.new_class_stack.append(new_class)
        if new_property is not None:
            self.new_property_stack.append(new_property)
        if property_prefix is not None:
            self.property_prefixes.append(property_prefix)

        yield

        if new_class is not None:
            self.new_class_stack.pop()
        if new_property is not None:
            self.new_property_stack.pop()
        if property_prefix is not None:
            self.property_prefixes.pop()

    @property
    def current_class(self):
        return self.new_class_stack[-1]

    @property
    def current_property(self):
        return self.new_property_stack[-1]

    def parse(self, element, toplevel=False):
        if toplevel:
            if element.tag != '{http://www.w3.org/2001/XMLSchema}schema':
                raise ValueError('File should contain a schema as root element!')

            for child in element.getchildren():
                if child.tag == '{http://www.w3.org/2001/XMLSchema}complexType':
                    self.parse(child)
                elif child.tag == '{http://www.w3.org/2001/XMLSchema}element':
                    name = child.get('name')
                    type_ = child.get('type')

                    if self.debug:
                        print('[DEBUG] Adding {} -> {} to XSI map'.format(name, type_))
                    self.cls_to_xsi_mapping[name] = type_
                else:
                    if self.debug:
                        print('[DEBUG] skipping non-class top-level tag {}'.format(child.tag))

        else:
            if element.tag in self.PARSERS:
                self.PARSERS[element.tag](self, element)
            else:
                self.parse_unknown(element)

    # TODO: We should check the following restrictions: http://www.w3schools.com/xml/schema_facets.asp

    def parse_all(self, element):
        self.parse_children(element)

    def parse_annotation(self, element):
        self.parse_children(element)

    def parse_attribute(self, element):
        name = element.get('name')
        type_ = element.get('type')

        if self.current_class is not None:
            if name is None:
                if self.debug:
                    print('[DEBUG] Encountered attribute without name')
                return
            new_property = AttributePrototype(PropertyRepresentation,
                                              {"name": name, "type_": type_},
                                              parent=self.current_class)

            self.current_class.attributes[name] = new_property

            with self.descend(new_property=new_property):
                self.parse_children(element)

    def parse_children(self, element):
        for child in element.getchildren():
            self.parse(child)

    def parse_choice(self, element):
        self.parse_children(element)

    def parse_complex_content(self, element):
        self.parse_children(element)

    def parse_complex_type(self, element):
        name = element.get('name')
        xsi_type = name, ''
        parent = None
        field_name = None
        sub_object = False

        if name is None:
            name = self.current_class.name + self.current_property.data['name'].capitalize()
            xsi_type = self.current_class._xsi_type[0], '{}/{}'.format(self.current_class._xsi_type[1],
                                                                       self.current_property.data['name'])
            parent = self.current_class.name
            field_name = self.current_property.data['name']
            sub_object = True

        new_class = ClassRepresentation(parser=self,
                                        name=name,
                                        xsi_type=xsi_type,
                                        parent=parent,
                                        field_name=field_name,
                                        sub_object=sub_object)

        if self.current_property is not None:
            self.current_property.data['element_class'] = new_class

        self.class_list[name] = new_class

        # Descend
        with self.descend(new_class=new_class):
            self.parse_children(element)

    def parse_documentation(self, element):
        if self.current_property is not None:
            self.current_property.data['docstring'] = element.text

    def parse_element(self, element):
        name = element.get('name')
        type_ = element.get('type')

        if name is None:
            abstract = element.get('abstract')
            if abstract is not None:
                self.current_class.abstract = abstract == "true"
            else:
                if self.debug:
                    print('[DEBUG] Encountered attribute without name')
            return

        if self.current_class is None:
            self.cls_to_xsi_mapping[name] = type_
        else:
            if element.get('maxOccurs') == 'unbounded':
                new_property = AttributePrototype(PropertyListingRepresentation,
                                                  {"name": name, "type_": type_},
                                                  parent=self.current_class)

            elif isinstance(type_, str) and type_.startswith('xs:'):
                new_property = AttributePrototype(PropertyRepresentation,
                                                  {"name": name, "type_": type_},
                                                  parent=self.current_class)
            else:
                new_property = AttributePrototype(PropertySubObjectRepresentation,
                                                  {"name": name, "type_": type_},
                                                  parent=self.current_class)

            self.current_class.attributes[name] = new_property

            with self.descend(new_property=new_property):
                self.parse_children(element)

    def parse_enumeration(self, element):
        if 'enum' in self.current_property.data['restrictions']:
            self.current_property.data['restrictions']['enum'].append(element.get('value'))
        else:
            self.current_property.data['restrictions']['enum'] = [element.get('value')]

    def parse_error(self, element):
        raise NotImplementedError('The parser for {} has not yet been implemented'.format(element.tag))

    def parse_extension(self, element):
        new_base = element.get('base')
        if new_base.startswith('xs:'):
            # Need to create a base object as we do not have this
            name = new_base[3:].capitalize()
            original_new_base = new_base
            if self.current_property is not None:
                new_base = self.current_property.data['name'].capitalize() + name
            else:
                new_base = self.current_class.python_name + name

            xsi_type = '', ''

            new_base_class = ClassRepresentation(parser=self,
                                                 name=new_base,
                                                 xsi_type=xsi_type)

            if self.current_property is not None:
                property_name = self.current_property.data['name']
            else:
                property_name = self.current_class.name.lower()

            new_property = AttributePrototype(PropertyRepresentation, {"name": property_name,
                                                                       "type_": original_new_base})
            new_base_class.attributes[name] = new_property
            self.class_list[new_base] = new_base_class
        elif ':' in new_base:
            new_base = new_base.split(':')[1]

        self.current_class.base_class = new_base
        self.parse_children(element)

    def parse_ignore(self, element):
        pass

    def parse_max_inclusive(self, element):
        self.current_property.data['restrictions']['max'] = element.get('value')

    def parse_max_length(self, element):
        self.current_property.data['restrictions']['maxlength'] = element.get('value')

    def parse_min_inclusive(self, element):
        self.current_property.data['restrictions']['min'] = element.get('value')

    def parse_min_length(self, element):
        self.current_property.data['restrictions']['minlength'] = element.get('value')

    def parse_restriction(self, element):
        old_type = self.current_property.data['type_']
        new_type = element.get('base')

        if old_type is not None:
            raise ValueError('Trying to override a type from a restriction!? (from {} to {})'.format(old_type, new_type))

        self.current_property.data['type_'] = new_type

        self.parse_children(element)

    def parse_schema(self, element):
        self.parse_children(element)

    def parse_sequence(self, element):
        self.parse_children(element)

    def parse_simple_content(self, element):
        self.parse_children(element)

    def parse_simple_type(self, element):
        self.parse_children(element)

    def parse_unknown(self, element):
        self.unknown_tags.add(element.tag)

    def parse_xdat_element(self, element):
        abstract = element.get("abstract")
        if abstract is not None:
            self.current_class.abstract = abstract == "true"

        display_identifier = element.get("displayIdentifiers")
        if display_identifier is not None:
            if self.current_property is None:
                self.current_class.display_identifier = display_identifier
            else:
                self.current_property.data['display_identifier'] = display_identifier

    def parse_sqlfield(self, element):
        print("CLASS: {}, PROP: {}, ELEMENT: {}".format(self.current_class.name, self.current_property.data["name"], element))

    PARSERS = {
        '{http://www.w3.org/2001/XMLSchema}all': parse_all,
        '{http://www.w3.org/2001/XMLSchema}annotation': parse_annotation,
        '{http://www.w3.org/2001/XMLSchema}appinfo': parse_children,
        '{http://www.w3.org/2001/XMLSchema}attribute': parse_attribute,
        '{http://www.w3.org/2001/XMLSchema}attributeGroup': parse_error,
        '{http://www.w3.org/2001/XMLSchema}choice': parse_choice,
        '{http://www.w3.org/2001/XMLSchema}complexContent': parse_complex_content,
        '{http://www.w3.org/2001/XMLSchema}complexType': parse_complex_type,
        '{http://www.w3.org/2001/XMLSchema}documentation': parse_documentation,
        '{http://www.w3.org/2001/XMLSchema}element': parse_element,
        '{http://www.w3.org/2001/XMLSchema}enumeration': parse_enumeration,
        '{http://www.w3.org/2001/XMLSchema}extension': parse_extension,
        '{http://www.w3.org/2001/XMLSchema}import': parse_ignore,
        '{http://www.w3.org/2001/XMLSchema}group': parse_error,
        '{http://www.w3.org/2001/XMLSchema}maxInclusive': parse_max_inclusive,
        '{http://www.w3.org/2001/XMLSchema}maxLength': parse_max_length,
        '{http://www.w3.org/2001/XMLSchema}minInclusive': parse_min_inclusive,
        '{http://www.w3.org/2001/XMLSchema}minLength': parse_min_length,
        '{http://www.w3.org/2001/XMLSchema}restriction': parse_restriction,
        '{http://www.w3.org/2001/XMLSchema}schema': parse_schema,
        '{http://www.w3.org/2001/XMLSchema}sequence': parse_sequence,
        '{http://www.w3.org/2001/XMLSchema}simpleContent': parse_simple_content,
        '{http://www.w3.org/2001/XMLSchema}simpleType': parse_simple_type,
        '{http://nrg.wustl.edu/xdat}element': parse_xdat_element,
        '{http://nrg.wustl.edu/xdat}field': parse_children,
        '{http://nrg.wustl.edu/xdat}sqlField': parse_sqlfield,
    }

    def write(self, code_file):
        # Build XSI to class mapping for using in writing out
        for cls in self.class_list.values():
            self.xsi_to_cls_mapping[cls.xsi_type] = cls

            # Make sure all attribute prototypes are expanded
            for key, value in cls.attributes.items():
                if isinstance(value, AttributePrototype):
                    cls.attributes[key] = value.create(self)

        schemas = '\n'.join('# - {}'.format(s) for s in self.schemas)
        code_file.write(FILE_HEADER.format(schemas=schemas,
                                           file_secondary_lookup=SECONDARY_LOOKUP_FIELDS['xnat:fileData']))

        code_file.write('\n\n\n'.join(str(c).strip() for c in self if c.name is not None))
