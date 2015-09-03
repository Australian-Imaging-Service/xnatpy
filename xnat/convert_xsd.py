import contextlib
import inspect
import keyword
import re

import isodate

import xnatbases


class ClassRepresentation(object):
    # Override strings for certain properties
    SUBSTITUTIONS = {
            "projects": "    @property\n    @caching\n    def projects(self):\n        return XNATListing(self.uri + '/projects', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:projectData')",
            "subjects": "    @property\n    @caching\n    def subjects(self):\n        return XNATListing(self.uri + '/subjects', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:subjectData')",
            "experiments": "    @property\n    @caching\n    def experiments(self):\n        return XNATListing(self.uri + '/experiments', xnat=self.xnat, secondary_lookup_field='label')",
            "assessors": "    @property\n    @caching\n    def assessors(self):\n        return XNATListing(self.uri + '/assessors', xnat=self.xnat, secondary_lookup_field='label')",
            "reconstructions": "    @property\n    @caching\n    def reconstructions(self):\n        return XNATListing(self.uri + '/reconstructions', xnat=self.xnat, secondary_lookup_field='label')",
            "fields": "    @property\n    def fields(self):\n        return self._fields",
            "scans": "    @property\n    @caching\n    def scans(self):\n        return XNATListing(self.uri + '/scans', xnat=self.xnat, secondary_lookup_field='series_description')",
            "resources": "    @property\n    @caching\n    def resources(self):\n        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resource')",
            "files": "    @property\n    @caching\n    def files(self):\n        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')",
            "download": "    def download(self, path):\n        self.xnat.download_zip(self.uri + '/files', path)",
            # From here the specific override
            ("subjectData", "experiments"): "    @property\n    @caching\n    def experiments(self):\n        # HACK because self.uri + '/subjects' does not work\n        uri = '/data/archive/projects/{}/subjects/{}/experiments'.format(self.project, self.id)\n        return XNATListing(uri, xnat=self.xnat, secondary_lookup_field='label')",
            ("imageSessionData", "download"): "    def download(self, path):\n        self.xnat.download_zip(self.uri + '/scans/ALL/files', path)",

            # Fullids here
            ("projectData", "fulluri"): "    @property\n    def fulluri(self):\n        return '{}/projects/{}'.format(self.xnat.fulluri, self.id)",
            ("subjectData", "fulluri"): "    @property\n    def fulluri(self):\n        return '{}/projects/{}/subjects/{}'.format(self.xnat.fulluri, self.project, self.id)",
            ("experimentData", "fulluri"): "    @property\n    def fulluri(self):\n        return '{}/projects/{}/subjects/{}/experiments/{}'.format(self.xnat.fulluri, self.project, self.subject_id, self.id)",
            }

    # Properties that have to be generated for a class
    ADDITIONS = {
            'projectData': ('subjects', 'experiments', 'fulluri'),
            'subjectData': ('experiments', 'fulluri'),
            'experimentData': ('download', 'fulluri'),
            'imageSessionData': ('download',),
            'imageScanData': ('resources', 'files', 'download'),
            'abstractResource': ('files', 'download'),
            }

    # Properties that are not generated
    BLACKLIST = ('id', 'uri')

    # Fields for lookup besides the id
    SECONDARY_LOOKUP_FIELDS = {
            "projectData": "name",
            "subjectData": "label",
            "experimentData": "label",
            "imageScanData": "series_description",
            "abstractResource": "label"
            }

    def __init__(self, parser, name):
        self.parser = parser
        self.name = name
        self.baseclass = 'XNATObject'
        self.properties = {}

    def __repr__(self):
        return '<Class {}({})>'.format(self.name, self.baseclass)

    def __str__(self):
        print('Base template class for {} is {}'.format(self.python_name, self.get_base_template()))
        base = self.get_base_template()
        if base is not None:
            base_source = inspect.getsource(base)
            header = base_source.strip() + '\n\n'
        else:
            header = '# No base template found for {}\n'.format(self.python_name)
            header += "class {name}({base}):\n".format(name=self.python_name, base=self.python_baseclass)

        if 'fields' in self.properties:
            header += "    _HAS_FIELDS = True\n"
        header += "    _XSI_TYPE = 'xnat:{}'\n\n".format(self.name)

        if self.name in self.SECONDARY_LOOKUP_FIELDS:
            header += self.init

        properties = [self.properties[k] for k in sorted(self.properties.keys())]

        properties = '\n\n'.join(self.print_property(p) for p in properties if not hasattr(base, p.clean_name))
        return '{}{}'.format(header, properties)

    @property
    def python_name(self):
        return self.name[0].upper() + self.name[1:]

    @property
    def python_baseclass(self):
        return self.baseclass[0].upper() + self.baseclass[1:]

    def get_base_template(self):
        if hasattr(xnatbases, self.python_name):
            return getattr(xnatbases, self.python_name)

    def print_property(self, prop):
        if (self.name, prop.name) in self.SUBSTITUTIONS:
            return self.SUBSTITUTIONS[self.name, prop.name]
        elif prop.name in self.SUBSTITUTIONS:
            return self.SUBSTITUTIONS[prop.name]
        else:
            data = str(prop)
            if prop.name == self.SECONDARY_LOOKUP_FIELDS.get(self.name, '!None'):
                head, tail = data.split('\n', 1)
                data = '{}\n    @caching\n{}'.format(head, tail)
            return data

    @property
    def init(self):
        if self.name in self.SECONDARY_LOOKUP_FIELDS:
            return "    def __init__(self, uri, xnat, id_=None, datafields=None, {lookup}=None):\n        super({name}, self).__init__(uri, xnat, id_=id_, datafields=datafields)\n        if {lookup} is not None:\n            self._cache['{lookup}'] = {lookup}\n\n".format(name=self.python_name, lookup=self.SECONDARY_LOOKUP_FIELDS[self.name])
        else:
            return ""



class PropertyRepresentation(object):
    def __init__(self, parser, name, type_=None):
        self.parser = parser
        self.name = name
        self.restrictions = {}
        self.type_ = type_
        self.docstring = None

    def __repr__(self):
        return '<Property {}({})>'.format(self.name, self.type_)

    def __str__(self):
        docstring = '\n        """{}"""'.format(self.docstring) if self.docstring is not None else ''
        if self.type_ is None or not self.type_.startswith('xnat:'):
            return \
        """    @property
    def {clean_name}(self):{docstring}
        # Generate automatically, type: {type}
        return self.get("{name}", type_="{type}")
    
    @ {clean_name}.setter
    def {clean_name}(self, value):{docstring}{restrictions}
        # Generate automatically, type: {type}
        self.set("{name}", value, type_="{type}")""".format(clean_name=self.clean_name, docstring=docstring, name=self.name, type=self.type_, restrictions=self.restrictions_code())
        else:
            return \
        """    @property
    @caching
    def {clean_name}(self):{docstring}
        # Generated automatically, type: {type_}
        return self.get_object("{name}")""".format(clean_name=self.clean_name,
                                                   docstring=docstring,
                                                   name = self.name,
                                                   type_=self.type_)

    @property
    def clean_name(self):
        name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
        if keyword.iskeyword(name):
            name = name + '_'
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
            if 'enum' in self.restrictions:
                data += "\n        if value not in [{enum}]:\n            raise ValueError('{name} has to be one of: {enum}')\n".format(name=self.name, enum=', '.join('"{}"'.format(x) for x in self.restrictions['enum']))

            return data
        else:
            return ''

    @staticmethod
    def to_date(value):
        return isodate.parse_date(value)

    @staticmethod
    def to_time(value):
        return isodate.parse_time(value)

    @staticmethod
    def to_datetime(value):
        return isodate.parse_datetime(value)

    @staticmethod
    def to_timedelta(value):
        return isodate.parse_duration(value).tdelta

    @staticmethod
    def to_bool(value):
        return value in ["true", "1"]
        
    TYPE_MAP = {
            'xs:anyURI': str,
            'xs:string': str,
            'xs:boolean': to_bool,
            'xs:integer': int,
            'xs:long': int,
            'xs:float': float,
            'xs:double': float,
            'xs:dateTime': to_datetime,
            'xs:time': to_time,
            'xs:date': to_date,
            'xs:duration': to_timedelta,
            }

    TYPE_CODE_MAP = {
            'xs:anyURI': 'str',
            'xs:string': 'str',
            'xs:boolean': 'bool',
            'xs:integer': 'int',
            'xs:long': 'int',
            'xs:float': 'float',
            'xs:double': 'float',
            'xs:dateTime': 'datetime',
            'xs:time': 'time',
            'xs:date': 'date',
            'xs:duration': 'timedelta',
            }


class SchemaParser(object):
    def __init__(self):
        self.class_list = {}
        self.unknown_tags = set()
        self.new_class_stack = [None]
        self.new_property_stack = [None]

    def __iter__(self):
        visited = set(['XNATObject'])
        tries = 0
        while len(visited) < len(self.class_list) and tries < 50:
            for key, value in self.class_list.items():
                if key in visited:
                    continue

                base = value.baseclass
                if not base.startswith('xs:') and base not in visited:
                    continue

                visited.add(key)
                yield value

            tries += 1

        if len(visited) < len(self.class_list):
            print('Visited: {}, expected: {}'.format(len(visited), len(self.class_list)))
            print('Missed: {}'.format(set(self.class_list.keys()) - visited))

    @contextlib.contextmanager
    def descend(self, new_class=None, new_property=None):
        if new_class is not None:
            self.new_class_stack.append(new_class)
        if new_property is not None:
            self.new_property_stack.append(new_property)

        yield

        if new_class is not None:
            self.new_class_stack.pop()
        if new_property is not None:
            self.new_property_stack.pop()

    @property
    def current_class(self):
        return self.new_class_stack[-1]

    @property
    def current_property(self):
        return self.new_property_stack[-1]

    def parse(self, element):
        if element.tag in self.PARSERS:
            self.PARSERS[element.tag](self, element)
        else:
            self.parse_unknown(element)

    def parse_complex_type(self, element):
        name = element.get('name')

        new_class = ClassRepresentation(self, name)
        self.class_list[name] = new_class
        
        # Descend
        with self.descend(new_class=new_class):
            self.parse_children(element)

    def parse_children(self, element):
        for child in element.getchildren():
            self.parse(child)

    def parse_ignore(self, element):
        pass

    def parse_schema(self, element):
        self.parse_children(element)

    def parse_complex_content(self, element):
        self.parse_children(element)

    def parse_extension(self, element):
        old_base = self.current_class.baseclass 
        new_base = element.get('base')
        if new_base.startswith('xnat:'):
            new_base = new_base[5:]
        if old_base == 'XNATObject':
            self.current_class.baseclass = new_base
        else:
            raise ValueError('Trying to reset base class again from {} to {}'.format(old_base, new_base))

        self.parse_children(element)

    def parse_sequence(self, element):
        self.parse_children(element)

    def parse_simple_type(self, element):
        self.parse_children(element)

    def parse_simple_content(self, element):
        self.parse_children(element)

    def parse_attribute(self, element):
        name = element.get('name')
        type_ = element.get('type')

        if self.current_class is not None:
            new_property = PropertyRepresentation(self, name, type_)
            self.current_class.properties[name] = new_property

            with self.descend(new_property=new_property):
                self.parse_children(element)

    def parse_restriction(self, element):
        old_type = self.current_property.type_
        new_type = element.get('base')

        if old_type is not None:
            raise ValueError('Trying to override a type from a restriction!? (from {} to {})'.format(old_type, new_type))

        self.current_property.type_ = new_type

        self.parse_children(element)

    def parse_maxlength(self, element):
        self.current_property.restrictions['maxlength'] = element.get('value')

    def parse_min_inclusive(self, element):
        self.current_property.restrictions['min'] = element.get('value')

    def parse_max_inclusive(self, element):
        self.current_property.restrictions['max'] = element.get('value')

    def parse_annotation(self, element):
        self.parse_children(element)

    def parse_documentation(self, element):
        if self.current_property is not None:
            self.current_property.docstring = element.text

    def parse_choice(self, element):
        self.parse_children(element)

    def parse_enumeration(self, element):
        if 'enum' in self.current_property.restrictions:
            self.current_property.restrictions['enum'].append(element.get('value'))
        else:
            self.current_property.restrictions['enum'] = [element.get('value')]

    def parse_element(self, element):
        name = element.get('name')
        type_ = element.get('type')

        if self.current_class is not None:
            new_property = PropertyRepresentation(self, name, type_)
            self.current_class.properties[name] = new_property

            with self.descend(new_property=new_property):
                self.parse_children(element)

    def parse_unknown(self, element):
        self.unknown_tags.add(element.tag)

    PARSERS = {
            '{http://www.w3.org/2001/XMLSchema}complexType': parse_complex_type,
            '{http://www.w3.org/2001/XMLSchema}complexContent': parse_complex_content,
            '{http://www.w3.org/2001/XMLSchema}extension': parse_extension,
            '{http://www.w3.org/2001/XMLSchema}sequence': parse_sequence,
            '{http://www.w3.org/2001/XMLSchema}simpleType': parse_simple_type,
            '{http://www.w3.org/2001/XMLSchema}simpleContent': parse_simple_content,
            '{http://www.w3.org/2001/XMLSchema}attribute': parse_attribute,
            '{http://www.w3.org/2001/XMLSchema}restriction': parse_restriction,
            '{http://www.w3.org/2001/XMLSchema}minInclusive': parse_min_inclusive,
            '{http://www.w3.org/2001/XMLSchema}maxInclusive': parse_max_inclusive,
            '{http://www.w3.org/2001/XMLSchema}maxLength': parse_maxlength,
            '{http://www.w3.org/2001/XMLSchema}choice': parse_choice,
            '{http://www.w3.org/2001/XMLSchema}enumeration': parse_enumeration,
            '{http://www.w3.org/2001/XMLSchema}element': parse_element,
            '{http://www.w3.org/2001/XMLSchema}annotation': parse_annotation,
            '{http://www.w3.org/2001/XMLSchema}documentation': parse_documentation,
            '{http://www.w3.org/2001/XMLSchema}schema': parse_schema,
            '{http://www.w3.org/2001/XMLSchema}import': parse_ignore,
            }
if __name__ == '__main__':
    main()

