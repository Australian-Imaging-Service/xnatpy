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

import re
import keyword


class mixedproperty(object):
    """
    A special property-like class that can act as a property for a class as
    well as a property for an object. These properties can have different
    function so the behaviour changes depending on whether it is called on
    the class or and instance of the class.
    """
    def __init__(self, fcget, fget=None, fset=None, fdel=None, doc=None):
        # fcget is the get on the class e.g. Test.x
        # fget is the get on an instance Test().x
        # fset and fdel are the set and delete of the instance
        self.fcget = fcget
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

        # Copy docstring from fcget or fget if required
        if doc is None:
            if fcget is not None:
                doc = fcget.__doc__
            elif fget is not None:
                doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype):
        if obj is not None and self.fget is not None:
            # If the obj is None, it is called on the class
            # If the fget is not set, call the class version
            return self.fget(obj)
        else:
            return self.fcget(objtype)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    # These allow the updating of the property using the @x.getter, @x.setter
    # and @x.deleter decorators.
    def getter(self, fget):
        return type(self)(self.fcget, fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fcget, self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fcget, self.fget, self.fset, fdel, self.__doc__)


def pythonize_class_name(name):
    """
    Turns string into a valid PEP8 class name, meaning camel cased
    (e.g. someValue -> SomeValue)

    :param str name: the name to convert to a PEP8 valid version
    :return: the PEP8 valid class name
    :rtype: str
    """
    if ':' in name:
        name = name.split(':', 1)[-1]

    parts = re.split('[\-\_\W]+', name)
    parts = [x[0].upper() + x[1:] for x in parts]
    name = ''.join(parts)
    return name


def pythonize_attribute_name(name):
    """
    Turns string into a valid PEP8 class name, meaning lower case with
    underscores when needed (e.g. someValue -> some_value)

    :param str name: the name to convert to a PEP8 valid version
    :return: the PEP8 valid attribute name
    :rtype: str
    """
    name = re.sub('[^0-9a-zA-Z]+', '_', name)

    # Change CamelCaseString to camel_case_string
    # Note that addID would become add_id
    name = re.sub("[A-Z]+", lambda x: '_' + x.group(0).lower(), name)
    if name[0] == '_':
        name = name[1:]

    # Avoid multiple underscores (replace them by single underscore)
    name = re.sub("__+", '_', name)

    # Avoid overwriting keywords TODO: Do we want this, as a property it is not a huge problem?
    if keyword.iskeyword(name):
        name += '_'

    return name
