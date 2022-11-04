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
import json
from collections.abc import Mapping
from .core import XNATBaseObject, caching

try:
    PYDICOM_LOADED = True
    import pydicom
except ImportError:
    PYDICOM_LOADED = False


class PluginConfiguration(XNATBaseObject):
    @property
    def id(self):
        """
        A unique ID for the plugin
        :return:
        """
        return self.data['id']

    @property
    def name(self):
        return self.data['name']

    @property
    def label(self):
        return self.name

    @property
    def version(self):
        return self.data['version']

    @property
    def plugin_class(self):
        return self.data['pluginClass']

    @property
    def log_file(self):
        return self.data['logConfigurationFile']

    @property
    def bean_name(self):
        return self.data['beanName']

    @property
    def xpath(self):
        return "xnatpy:pluginsSession"

    @property
    def fulldata(self):
        return self.xnat_session.get_json(self.uri)

    @property
    @caching
    def data(self):
        return self.fulldata

    def cli_str(self):
        return "Plugin {name}".format(name=self.label)


class Plugins(Mapping):
    def __init__(self, xnat_session):
        self._xnat_session = xnat_session
        self._cache = {}
        self._caching = True
        self._data = None

    def __repr__(self):
        return f"<Plugins: {self.data}>"

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self.data[item]

    def __iter__(self):
        return iter(self.data)

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

    @property
    def xnat_session(self):
        return self._xnat_session

    @property
    def data(self):
        """
        Get a list of all plugins

        :return: list of plugins
        :rtype: dict
        """
        if self._data is None:
            uri = '/xapi/plugins/'

            data = self.xnat_session.get_json(uri)
            plugin_names = list(data.keys())
            result = {}
            for plugin_name in plugin_names:
                uri = '/xapi/plugins/{}'.format(plugin_name)
                plugin_data = PluginConfiguration(uri, self.xnat_session)

                result[plugin_data.id] = plugin_data

            self._data = result

        return self._data
