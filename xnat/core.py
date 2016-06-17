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
from collections import MutableMapping, Mapping, namedtuple
import fnmatch
import re
import textwrap

from . import exceptions
from . import search
from .datatypes import convert_from, convert_to
import six


def caching(func):
    """
    This decorator caches the value in self._cache to avoid data to be
    retrieved multiple times. This works for properties or functions without
    arguments.
    """
    name = func.__name__

    def wrapper(self):
        # We use self._cache here, in the decorator _cache will be a member of
        #  the objects, so nothing to worry about
        # pylint: disable=protected-access
        if not self.caching or name not in self._cache:
            # Compute the value if not cached
            self._cache[name] = func(self)

        return self._cache[name]

    docstring = func.__doc__ if func.__doc__ is not None else ''
    wrapper.__doc__ = textwrap.dedent(docstring) + '\nCached using the caching decorator'
    return wrapper


class VariableMap(MutableMapping):
    def __init__(self, parent, field):
        self._cache = {}
        self.caching = True
        self.parent = parent
        self._field = field

    def __repr__(self):
        return "<VariableMap {}>".format(dict(self))

    @property
    @caching
    def data(self):
        try:
            variables = next(x for x in self.parent.fulldata['children'] if x['field'] == self.field)
            variables_map = {x['data_fields']['name']: x['data_fields']['field'] for x in variables['items'] if 'field' in x['data_fields']}
        except StopIteration:
            variables_map = {}

        return variables_map

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        query = {'xsiType': self.parent.xsi_type,
                 '{parent_type_}/{field}[@xsi_type={type}]/{key}'.format(parent_type_=self.parent.xsi_type,
                                                                         field=self.field,
                                                                         type=self.xsi_type,
                                                                         key=key): value}
        self.xnat.put(self.parent.fulluri, query=query)

        # Remove cache and make sure the reload the data
        if 'data' in self._cache:
            self.clearcache()

    def __delitem__(self, key):
        print('[WARNING] Deleting of variables is currently not supported!')

    def __iter__(self):
        for key in self.data.keys():
            yield key

    def __len__(self):
        return len(self.data)

    @property
    def field(self):
        return self._field

    @property
    def xnat(self):
        return self.parent.xnat_session

    def clearcache(self):
        self._cache.clear()
        self.parent.clearcache()


class CustomVariableMap(VariableMap):
    def __setitem__(self, key, value):
        query = {'xsiType': self.parent.xsi_type,
                 '{type_}/fields/field[name={key}]/field'.format(type_=self.parent.xsi_type,
                                                                 key=key): value}
        self.xnat.put(self.parent.fulluri, query=query)

        # Remove cache and make sure the reload the data
        if 'data' in self._cache:
            self.clearcache()


class XNATObject(six.with_metaclass(search.XNATMeta, object)):
    _HAS_FIELDS = False
    _XSI_TYPE = 'xnat:baseObject'

    def __init__(self, uri=None, xnat_session=None, id_=None, datafields=None, parent=None, fieldname=None):
        if (uri is None or xnat_session is None) and parent is None:
            raise exceptions.XNATValueError('Either the uri and xnat session have to be given, or the parent object')

        # Set the xnat session
        self._cache = {}
        self._caching = None

        if uri is None and parent is not None:
            self._xnat_session = parent.xnat_session
            if isinstance(parent, XNATListing):
                put_uri = parent.uri
            else:
                listing_field = {'xsi:projectData': 'projects',
                                 'xsi:subjectData': 'subjects',
                                 }
                put_uri = '{}/{}'.format(parent.uri, listing_field)
            put_uri = parent.uri
            self._uri = parent.uri + id_
            self._parent = None
        else:
            self._xnat_session = xnat_session
            self._uri = uri
            self._parent = parent

        self._fieldname = fieldname

        if self._HAS_FIELDS:
            self._fields = CustomVariableMap(self, field='fields/field')
        else:
            self._fields = None

        if id_ is not None:
            self._cache['id'] = id_

        if datafields is not None:
            self._cache['data'] = datafields

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.id)

    @property
    def parent(self):
        return self._parent

    @property
    def fieldname(self):
        return self._fieldname

    def get(self, name, type_=None):
        value = self.data.get(name)
        if type_ is not None and value is not None:
            if isinstance(type_, str):
                value = convert_to(value, type_)
            else:
                value = type_(value)
        return value
    
    _TYPE_HINTS = {
            'demographics': 'xnat:demographicData',
            'investigator': 'xnat:investigatorData',
            'metadata': 'xnat:subjectMetadata',
            'pi': 'xnat:investigatorData',
            'studyprotocol': 'xnat:studyProtocol',
            'validation': 'xnat:validationData',
            'baseimage': 'xnat:abstractResource',
            }

    def get_object(self, fieldname, type_=None):
        if type_ is None:
            try:
                data = next(x for x in self.fulldata['children'] if x['field'] == fieldname)['items'][0]
                type_ = data['meta']['xsi:type']
            except StopIteration:
                type_ = self._TYPE_HINTS.get(fieldname)
            if type_ is None:
                raise exceptions.XNATValueError('Cannot determine type of field {}!'.format(fieldname))
        return self.xnat_session.create_object(self.uri, type_=type_, parent=self, fieldname=fieldname)

    @property
    def fulluri(self):
        return self.uri

    def set(self, name, value, type_=None):
        if type_ is not None:
            if isinstance(type_, str):
                # Make sure we have a valid string here that is properly casted
                value = convert_from(value, type_)
            else:
                value = type_(value)

        if self.parent is None:
            query = {'xsiType': self.xsi_type,
                    '{xsitype}/{name}'.format(xsitype=self.xsi_type, name=name): value}
            self.xnat_session.put(self.fulluri, query=query)
            self.clearcache()
        else:
            query = {'xsiType': self.parent.xsi_type,
                     '{parent_type}/{fieldname}[@xsi:type={xsitype}]/{name}'.format(parent_type=self.parent.xsi_type,
                                                                                    fieldname=self.fieldname,
                                                                                    xsitype=self.xsi_type,
                                                                                    name=name): value}
            self.xnat_session.put(self.parent.fulluri, query=query)
            self.parent.clearcache()

    @property
    def xsi_type(self):
        return self._XSI_TYPE

    @property
    @caching
    def id(self):
        if 'ID' in self.data:
            return self.data['ID']
        elif self.parent is not None:
            return '{}/{}'.format(self.parent.id, self.fieldname)
        else:
            return '#NOID#'

    @property
    @caching
    def fulldata(self):
        return self.xnat_session.get_json(self.uri)['items'][0]

    @property
    def data(self):
        if self.parent is None:
            return self.fulldata['data_fields']
        else:
            try:
                data = next(x for x in self.parent.fulldata['children'] if x['field'] == self.fieldname)['items'][0]['data_fields']
            except StopIteration:
                data = {}
            return data

    @property
    def xnat_session(self):
        return self._xnat_session

    @property
    def uri(self):
        return self._uri

    def clearcache(self):
        self._cache.clear()

    # This needs to be at the end of the class because it shadows the caching
    # decorator for the remainder of the scope.
    @property
    def caching(self):
        if self._caching is not None:
            return self._caching
        else:
            return self.xnat_session.caching

    @caching.setter
    def caching(self, value):
        self._caching = value

    @caching.deleter
    def caching(self):
        self._caching = None

    def delete(self, remove_files=True):
        """
        Remove the item from XNATSession
        """
        query = {}

        if remove_files:
            query['removeFiles'] = 'true'

        self.xnat_session.delete(self.fulluri, query=query)
        # Make sure there is no cache, this will cause 404 erros on subsequent use
        # of this object, indicating that is has been in fact removed
        self.clearcache()

    @classmethod
    def query(self, session):
        return search.Query(self._XSI_TYPE, session)


class XNATSubObject(XNATObject):
    @property
    def xsi_type(self):
        return self.parent.xsi_type

    @property
    def data(self):
        prefix = '{}/'.format(self.fieldname)

        result = self.parent.data
        result = {k[len(prefix):]: v for k, v in result.items() if k.startswith(prefix)}

        return result

    def set(self, name, value, type_=None):
        name = '{}/{}'.format(self.fieldname, name)
        self.parent.set(name, value, type_)

    #def get(self, name, type_=None):
    #    return self.parent.get('{}/{}'.format(self.id, name))


class XNATListing(Mapping):
    def __init__(self, uri, xnat_session, secondary_lookup_field, xsiType=None, filter=None):
        # Cache fields
        self._cache = {}
        self.caching = True

        # Important for communication
        self._xnat_session = xnat_session
        self._uri = uri
        self._xsiType = xsiType

        # List specific things
        self.secondary_lookup_field = secondary_lookup_field
        self._used_filters = filter or {}

    @property
    @caching
    def data_maps(self):
        xsi_type = ',xsiType' if self._xsiType is None else ''
        columns = 'ID,URI,{}{}'.format(self.secondary_lookup_field, xsi_type)
        query = dict(self.used_filters)
        query['columns'] = columns
        result = self.xnat_session.get_json(self.uri, query=query)['ResultSet']['Result']

        if not all('URI' in x for x in result):
            # HACK: This is a Resource, that misses the URI and ID field (let's fix that)
            for entry in result:
                if 'URI' not in entry:
                    entry['URI'] = '{}/{}'.format(self.uri, entry['label'])
                if 'ID' not in entry:
                    entry['ID'] = entry['xnat_abstractresource_id']

        elif not all('ID' in x for x in result):
            # HACK: This is a File and it misses an ID field and has Name (let's fix that)
            for entry in result:
                if 'ID' not in entry:
                    entry['ID'] = '{}/files/{}'.format(entry['cat_ID'], entry['Name'])
                    entry['name'] = entry['Name']

        # Post filter result if server side query did not work
        result = [x for x in result if all(fnmatch.fnmatch(x.get(k), v) for k, v in self.used_filters.items())]

        # Create object dictionaries
        id_map = {}
        key_map = {}
        for x in result:
            new_object = self.xnat_session.create_object(x['URI'],
                                                         type_=x.get('xsiType', self._xsiType),
                                                         id_=x['ID'],
                                                         **{self.secondary_lookup_field: x.get(self.secondary_lookup_field)})
            id_map[x['ID']] = new_object
            key_map[x.get(self.secondary_lookup_field)] = new_object

        return id_map, key_map

    @property
    def data(self):
        return self.data_maps[0]

    @property
    def key_map(self):
        return self.data_maps[1]

    def __repr__(self):
        content = ', '.join('({}, {}): {}'.format(k, getattr(v, self.secondary_lookup_field), v) for k, v in self.items())
        return '<XNATListing {}>'.format(content)

    def __getitem__(self, item):
        try:
            return self.data[item]
        except KeyError:
            try:
                return self.key_map[item]
            except StopIteration:
                raise KeyError('Could not find ID/label {} in collection!'.format(item))

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def tabulate(self, columns=None, filter=None):
        """
        Create a table (tuple of namedtuples) from this listing. It is possible
        to choose the columns and add a filter to the tabulation.

        :param tuple columns: names of the variables to use for columns
        :param dict filter: update filters to use (form of {'variable': 'filter*'}),
                             setting this option will try to merge the filters and
                             throw an error if that is not possible.
        :return: tabulated data
        :rtype: tuple
        :raises ValueError: if the new filters conflict with the object filters
        """
        if columns is None:
            columns = ('DEFAULT',)

        if filter is None:
            filter = self.used_filters
        else:
            filter = self.merge_filters(self.used_filters, filter)

        query = dict(filter)
        query['columns'] = ','.join(columns)

        result = self.xnat_session.get_json(self.uri, query=query)
        if len(result['ResultSet']['Result']) > 0:
            result_columns = list(result['ResultSet']['Result'][0].keys())

            # Retain requested order
            if columns != ('DEFAULT',):
                result_columns = [x for x in columns if x in result_columns]

            # Replace all non-alphanumeric characters with an underscore
            result_columns = {s: re.sub('[^0-9a-zA-Z]+', '_', s) for s in result_columns}
            rowtype = namedtuple('TableRow', list(result_columns.values()))

            # Replace all non-alphanumeric characters in each key of the keyword dictionary
            return tuple(rowtype(**{result_columns[k]: v for k, v in x.items()}) for x in result['ResultSet']['Result'])
        else:
            return ()

    @property
    def used_filters(self):
        return self._used_filters

    @staticmethod
    def merge_filters(old_filters, extra_filters):
        # First check for conflicting filters
        for key in extra_filters:
            if key in old_filters and old_filters[key] != extra_filters[key]:
                raise ValueError('Trying to redefine filter {key}={oldval} to {key}={newval}'.format(key=key,
                                                                                                     oldval=old_filters[key],
                                                                                                     newval=extra_filters[key]))

        new_filters = dict(old_filters)
        new_filters.update(extra_filters)

        return new_filters

    def filter(self, filters=None, **kwargs):
        """
        Create a new filtered listing based on this listing. There are two way
        of defining the new filters. Either by passing a dict as the first
        argument, or by adding filters as keyword arguments.

        For example::
          >>> listing.filter({'ID': 'A*'})
          >>> listing.filter(ID='A*')

        are equivalent.

        :param dict filters: a dictionary containing the filters
        :param str kwargs: keyword arguments containing the filters
        :return: new filtered XNATListing
        :rtype: XNATListing
        """
        if filters is None:
            filters = kwargs

        new_filters = self.merge_filters(self.used_filters, filters)
        return XNATListing(self.uri, self.xnat_session, self.secondary_lookup_field, self._xsiType, new_filters)

    @property
    def uri(self):
        return self._uri

    @property
    def xnat_session(self):
        return self._xnat_session
