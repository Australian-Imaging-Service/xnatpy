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
import tempfile
from zipfile import ZipFile

from .core import caching, XNATBaseObject, XNATListing


class ProjectData(XNATBaseObject):
    SECONDARY_LOOKUP_FIELD = 'name'

    @property
    def fulluri(self):
        return '{}/projects/{}'.format(self.xnat_session.fulluri, self.id)

    @property
    @caching
    def subjects(self):
        return XNATListing(self.uri + '/subjects',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='subjects',
                           secondary_lookup_field='label',
                           xsi_type='xnat:subjectData')

    @property
    @caching
    def experiments(self):
        return XNATListing(self.uri + '/experiments',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='experiments',
                           secondary_lookup_field='label')

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='files',
                           secondary_lookup_field='path',
                           xsi_type='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='resources',
                           secondary_lookup_field='label',
                           xsi_type='xnat:resourceCatalog')

    def download_dir(self, target_dir, verbose=True):
        project_dir = os.path.join(target_dir, self.name)
        if not os.path.isdir(project_dir):
            os.mkdir(project_dir)

        for subject in self.subjects.values():
            subject.download_dir(project_dir, verbose=verbose)

        if verbose:
            self.logger.info('Downloaded subject to {}'.format(project_dir))


class SubjectData(XNATBaseObject):
    SECONDARY_LOOKUP_FIELD = 'label'

    @property
    def fulluri(self):
        return '{}/projects/{}/subjects/{}'.format(self.xnat_session.fulluri, self.project, self.id)

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='files',
                           secondary_lookup_field='path',
                           xsi_type='xnat:fileData')

    def download_dir(self, target_dir, verbose=True):
        subject_dir = os.path.join(target_dir, self.label)
        if not os.path.isdir(subject_dir):
            os.mkdir(subject_dir)

        for experiment in self.experiments.values():
            experiment.download_dir(subject_dir, verbose=verbose)

        if verbose:
            self.logger.info('Downloaded subject to {}'.format(subject_dir))


class ExperimentData(XNATBaseObject):
    SECONDARY_LOOKUP_FIELD = 'label'


class SubjectAssessorData(XNATBaseObject):
    @property
    def fulluri(self):
        return '/data/archive/projects/{}/subjects/{}/experiments/{}'.format(self.project, self.subject_id, self.id)

    @property
    def subject(self):
        return self.xnat_session.subjects[self.subject_id]


class ImageSessionData(XNATBaseObject):
    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='files',
                           secondary_lookup_field='path',
                           xsi_type='xnat:fileData')

    def create_assessor(self, label, type_='xnat:mrAssessorData'):
        uri = '{}/assessors/{label}?xsiType={type}&label={label}&req_format=qs'.format(self.fulluri,
                                                                                       type=type_,
                                                                                       label=label)
        self.xnat_session.put(uri, accepted_status=(200, 201))
        self.clearcache()  # The resources changed, so we have to clear the cache
        return self.xnat_session.create_object('{}/assessors/{}'.format(self.fulluri, label), type_=type_)

    def download(self, path, verbose=True):
        self.xnat_session.download_zip(self.uri + '/scans/ALL/files', path, verbose=verbose)

    def download_dir(self, target_dir, verbose=True):
        with tempfile.TemporaryFile() as temp_path:
            self.xnat_session.download_stream(self.uri + '/scans/ALL/files', temp_path, format='zip', verbose=verbose)

            with ZipFile(temp_path) as zip_file:
                zip_file.extractall(target_dir)

        if verbose:
            self.logger.info('\nDownloaded image session to {}'.format(target_dir))


class DerivedData(XNATBaseObject):
    @property
    def fulluri(self):
        return '/data/experiments/{}/assessors/{}'.format(self.image_session_id, self.id)

    @property
    @caching
    def files(self):
        return XNATListing(self.fulluri + '/files',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='files',
                           secondary_lookup_field='path',
                           xsi_type='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.fulluri + '/resources',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='resources',
                           secondary_lookup_field='label',
                           xsi_type='xnat:resourceCatalog')

    def create_resource(self, label, format=None):
        uri = '{}/resources/{}'.format(self.fulluri, label)
        self.xnat_session.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache
        return self.xnat_session.create_object(uri, type_='xnat:resourceCatalog')

    def download(self, path, verbose=True):
        self.xnat_session.download_zip(self.uri + '/files', path, verbose=verbose)


class ImageScanData(XNATBaseObject):
    SECONDARY_LOOKUP_FIELD = 'type'

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='files',
                           secondary_lookup_field='path',
                           xsi_type='xnat:fileData')

    @property
    @caching
    def resources(self):
        return XNATListing(self.uri + '/resources',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='resources',
                           secondary_lookup_field='label',
                           xsi_type='xnat:resourceCatalog')

    def create_resource(self, label, format=None):
        uri = '{}/resources/{}'.format(self.uri, label)
        self.xnat_session.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache
        return self.xnat_session.create_object(uri, type_='xnat:resourceCatalog')

    def download(self, path, verbose=True):
        self.xnat_session.download_zip(self.uri + '/files', path, verbose=verbose)

    def download_dir(self, target_dir, verbose=True):
        with tempfile.TemporaryFile() as temp_path:
            self.xnat_session.download_stream(self.uri + '/files', temp_path, format='zip', verbose=verbose)

            with ZipFile(temp_path) as zip_file:
                zip_file.extractall(target_dir)

        if verbose:
            self.logger.info('Downloaded image scan data to {}'.format(target_dir))


class AbstractResource(XNATBaseObject):
    SECONDARY_LOOKUP_FIELD = 'label'

    @property
    @caching
    def fulldata(self):
        # FIXME: ugly hack because direct query fails
        uri, label = self.uri.rsplit('/', 1)
        data = self.xnat_session.get_json(uri)['ResultSet']['Result']

        try:
            data = next(x for x in data if x['label'] == label)
        except StopIteration:
            raise ValueError('Cannot find full data!')

        data['ID'] = data['xnat_abstractresource_id']  # Make sure the ID is present
        return data

    @property
    def data(self):
        return self.fulldata

    @property
    def file_size(self):
        file_size = self.data['file_size']
        if file_size.strip() == '':
            return 0
        else:
            return int(file_size)

    @property
    def file_count(self):
        file_count = self.data['file_count']
        if file_count.strip() == '':
            return 0
        else:
            return int(file_count)

    @property
    @caching
    def files(self):
        return XNATListing(self.uri + '/files',
                           xnat_session=self.xnat_session,
                           parent=self,
                           field_name='files',
                           secondary_lookup_field='path',
                           xsi_type='xnat:fileData')

    def download(self, path, verbose=True):
        self.xnat_session.download_zip(self.uri + '/files', path, verbose=verbose)

    def download_dir(self, target_dir, verbose=True):
        with tempfile.TemporaryFile() as temp_path:
            self.xnat_session.download_stream(self.uri + '/files', temp_path, format='zip', verbose=verbose)

            with ZipFile(temp_path) as zip_file:
                zip_file.extractall(target_dir)

        if verbose:
            self.logger.info('Downloaded resource data to {}'.format(target_dir))

    def upload(self, data, remotepath, overwrite=False):
        uri = '{}/files/{}'.format(self.uri, remotepath.lstrip('/'))
        self.xnat_session.upload(uri, data, overwrite=overwrite)
        self.files.clearcache()
