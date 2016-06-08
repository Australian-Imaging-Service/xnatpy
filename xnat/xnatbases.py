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
import os
import tempfile
from zipfile import ZipFile

from .xnatcore import caching, XNATObject, XNATListing


class ProjectData(XNATObject):
    @property
    def fulluri(self):
        return '{}/projects/{}'.format(self.xnat.fulluri, self.id)

    @property
    @caching
    def subjects(self):
        return XNATListing(self.uri + '/subjects', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:subjectData')

    @property
    @caching
    def experiments(self):
        return XNATListing(self.uri + '/experiments', xnat=self.xnat, secondary_lookup_field='label')

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceCatalog')

    def download_dir(self, target_dir, verbose=True):
        project_dir = os.path.join(target_dir, self.name)
        if not os.path.isdir(project_dir):
            os.mkdir(project_dir)

        for subject in self.subjects.values():
            subject.download_dir(project_dir, verbose=verbose)

        if verbose:
            print('Downloaded subject to {}'.format(project_dir))


class SubjectData(XNATObject):
    @property
    def fulluri(self):
        return '{}/projects/{}/subjects/{}'.format(self.xnat.fulluri, self.project, self.id)

    @property
    @caching
    def experiments(self):
        # HACK because self.uri + '/experiments' does not work
        uri = '{}/experiments'.format(self.fulluri, self.id)
        return XNATListing(uri, xnat=self.xnat, secondary_lookup_field='label')

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceCatalog')

    def download_dir(self, target_dir, verbose=True):
        subject_dir = os.path.join(target_dir, self.label)
        if not os.path.isdir(subject_dir):
            os.mkdir(subject_dir)

        for experiment in self.experiments.values():
            experiment.download_dir(subject_dir, verbose=verbose)

        if verbose:
            print('Downloaded subject to {}'.format(subject_dir))


class ImageSessionData(XNATObject):
    @property
    def fulluri(self):
        return '/data/archive/projects/{}/subjects/{}/experiments/{}'.format(self.project, self.subject_id, self.id)

    @property
    @caching
    def scans(self):
        return XNATListing(self.uri + '/scans', xnat=self.xnat, secondary_lookup_field='type')

    @property
    @caching
    def assessors(self):
        return XNATListing(self.uri + '/assessors', xnat=self.xnat, secondary_lookup_field='label')

    @property
    @caching
    def reconstructions(self):
        return XNATListing(self.uri + '/reconstructions', xnat=self.xnat, secondary_lookup_field='label')

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceCatalog')

    def create_assessor(self, label, type_='xnat:mrAssessorData'):
        uri = '{}/assessors/{label}?xsiType={type}&label={label}&req_format=qs'.format(self.fulluri,
                                                                                       type=type_,
                                                                                       label=label)
        self.xnat.put(uri, accepted_status=(200, 201))
        self.clearcache()  # The resources changed, so we have to clear the cache
        return self.xnat.create_object('{}/assessors/{}'.format(self.fulluri, label), type_=type_)

    def download(self, path):
        self.xnat.download_zip(self.uri + '/scans/ALL/files', path)

    def download_dir(self, target_dir, verbose=True):
        with tempfile.TemporaryFile() as temp_path:
            self.xnat.download_stream(self.uri + '/scans/ALL/files', temp_path, format='zip', verbose=verbose)

            with ZipFile(temp_path) as zip_file:
                zip_file.extractall(target_dir)

        if verbose:
            print('Downloaded image session to {}'.format(target_dir))


class DerivedData(XNATObject):
    @property
    def fulluri(self):
        return '/data/experiments/{}/assessors/{}'.format(self.imagesession_id, self.id)

    @property
    @caching
    def files(self):
        return XNATListing(self.fulluri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.fulluri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceCatalog')

    def create_resource(self, label, format=None):
        uri = '{}/resources/{}'.format(self.fulluri, label)
        self.xnat.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache
        return self.xnat.create_object(uri, type_='xnat:resourceCatalog')

    def download(self, path):
        self.xnat.download_zip(self.uri + '/files', path)


class ImageScanData(XNATObject):
    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources', xnat=self.xnat, secondary_lookup_field='label', xsiType='xnat:resourceCatalog')

    def create_resource(self, label, format=None):
        uri = '{}/resources/{}'.format(self.uri, label)
        self.xnat.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache
        return self.xnat.create_object(uri, type_='xnat:resourceCatalog')

    def download(self, path):
        self.xnat.download_zip(self.uri + '/files', path)


class AbstractResource(XNATObject):
    @property
    @caching
    def fulldata(self):
        # FIXME: ugly hack because direct query fails
        uri, label = self.uri.rsplit('/', 1)
        data = self.xnat.get_json(uri)['ResultSet']['Result']
        try:
            return next(x for x in data if x['label'] == label)
        except StopIteration:
            raise ValueError('Cannot find full data!')

    @property
    def data(self):
        return self.fulldata

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files', xnat=self.xnat, secondary_lookup_field='name', xsiType='xnat:fileData')

    def download(self, path):
        self.xnat.download_zip(self.uri + '/files', path)

    def upload(self, data, remotepath):
        uri = '{}/files/{}'.format(self.uri, remotepath)
        self.xnat.upload(uri, data)


class File(XNATObject):
    def __init__(self, uri, xnat, id_=None, datafields=None, name=None):
        super(File, self).__init__(uri, xnat, id_=id_, datafields=datafields)
        if name is not None:
            self._cache['name'] = name

    @property
    @caching
    def name(self):
        return self.data['name']

    @property
    def xsi_type(self):
        return 'xnat:fileData'  # FIXME: is this correct?

    def download(self, path):
        self.xnat.download(self.uri, path)
