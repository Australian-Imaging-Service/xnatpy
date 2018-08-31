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
from gzip import GzipFile
from zipfile import ZipFile
from tarfile import TarFile

from six import BytesIO

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
    def label(self):
        try:
            sharing = next(x for x in self.fulldata['children'] if x['field'] == 'sharing/share')
            share_info = next(x for x in sharing['items'] if x['data_fields']['project'] == self.project)
            return share_info['data_fields']['label']
        except (KeyError, StopIteration):
            return self.get('label', type_=str)

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

    def share(self, project, label=None):
        # Create the uri for sharing
        share_uri = '{}/projects/{}'.format(self.fulluri, project)

        # Add label if needed
        query = {}
        if label is not None:
            query['label'] = label

        self.xnat_session.put(share_uri, query=query)
        self.clearcache()


class ExperimentData(XNATBaseObject):
    SECONDARY_LOOKUP_FIELD = 'label'

    @property
    def label(self):
        try:
            sharing = next(x for x in self.fulldata['children'] if x['field'] == 'sharing/share')
            share_info = next(x for x in sharing['items'] if x['data_fields']['project'] == self.project)
            return share_info['data_fields']['label']
        except (KeyError, StopIteration):
            return self.get('label', type_=str)


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

    def create_assessor(self, label, type_):
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

    def share(self, project, label=None):
        # Create the uri for sharing
        share_uri = '{}/projects/{}'.format(self.fulluri , project)

        # Add label if needed
        query = {}
        if label is not None:
            query['label'] = label

        self.xnat_session.put(share_uri, query=query)
        self.clearcache()


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

    def create_resource(self, label, format=None, data_dir=None, method=None):
        uri = '{}/resources/{}'.format(self.fulluri, label)
        self.xnat_session.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache
        resource = self.xnat_session.create_object(uri, type_='xnat:resourceCatalog')

        if data_dir is not None:
            resource.upload_dir(data_dir, method=method)

        return resource

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

    def create_resource(self, label, format=None, data_dir=None, method='tgz_file'):
        uri = '{}/resources/{}'.format(self.uri, label)
        self.xnat_session.put(uri, format=format)
        self.clearcache()  # The resources changed, so we have to clear the cache
        resource = self.xnat_session.create_object(uri, type_='xnat:resourceCatalog')

        if data_dir is not None:
            resource.upload_dir(data_dir, method=method)

        return resource


    def download(self, path, verbose=True):
        self.xnat_session.download_zip(self.uri + '/files', path, verbose=verbose)

    def download_dir(self, target_dir, verbose=True):
        with tempfile.TemporaryFile() as temp_path:
            self.xnat_session.download_stream(self.uri + '/files', temp_path, format='zip', verbose=verbose)

            with ZipFile(temp_path) as zip_file:
                zip_file.extractall(target_dir)

        if verbose:
            self.logger.info('Downloaded image scan data to {}'.format(target_dir))

    def dicom_dump(self):
        """
        Retrieve a dicom dump as a JSON data structure

        :return: JSON object (dict) representation of DICOM header
        :rtype: dict
        """
        experiment = self.xnat_session.create_object('/data/experiments/{}'.format(self.image_session_id))

        uri = '/archive/projects/{}/experiments/{}/scans/{}'.format(
            experiment.project,
            self.image_session_id,
            self.id,
        )
        return self.xnat_session.services.dicom_dump(src=uri)


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

    def upload(self, data, remotepath, overwrite=False, extract=False):
        uri = '{}/files/{}'.format(self.uri, remotepath.lstrip('/'))
        query = {}
        if extract:
            query['extract'] = 'true'
        self.xnat_session.upload(uri, data, overwrite=overwrite, query=query)
        self.files.clearcache()

    def upload_dir(self, directory, overwrite=False, method='tgz_file'):
        """
        Upload a directory to an XNAT resource. This means that if you do
        resource.upload_dir(directory) that if there is a file directory/a.txt
        it will be uploaded to resource/files/a.txt

        The method has 5 options, default is tgz_file:

        1. ``per_file``: Scans the directory and uploads file by file
        2. ``tar_memory``: Create a tar archive in memory and upload it in one go
        3. ``tgz_memory``: Create a gzipped tar file in memory and upload that
        4. ``tar_file``: Create a temporary tar file and upload that
        4. ``tgz_file``: Create a temporary gzipped tar file and upload that

        The considerations are that sometimes you can fit things in memory so
        you can save disk IO by putting it in memory. The per file does not
        create additional archives, but has one request per file so might be
        slow when uploading many files.

        :param str directory: The directory to upload
        :param bool overwrite: Flag to force overwriting of files
        :param str method: The method to use
        """
        if not isinstance(directory, str):
            directory = str(directory)

        if method == 'per_file':
            for root, _, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    if os.path.getsize(file_path) == 0:
                        continue

                    target_path = os.path.relpath(file_path, directory)
                    self.upload(file_path, target_path, overwrite=overwrite)
        elif method == 'tar_memory':
            fh = BytesIO()
            tar_file = TarFile(name='upload.tar', mode='w', fileobj=fh)
            tar_file.add(directory, '')
            tar_file.close()
            fh.seek(0)
            self.upload(fh, 'upload.tar', overwrite=overwrite, extract=True)
        elif method == 'tgz_memory':
            fh = BytesIO()
            with GzipFile(filename='upload.tar.gz', mode='w', fileobj=fh) as gzip_file:
                with TarFile(name='upload.tar', mode='w', fileobj=gzip_file) as tar_file:
                    tar_file.add(directory, '')

            fh.seek(0)
            self.upload(fh, 'upload.tar.gz', overwrite=overwrite, extract=True)
            fh.close()
        elif method == 'tar_file':
            with tempfile.TemporaryFile('w+') as fh:
                tar_file = TarFile(name='upload.tar', mode='w', fileobj=fh)
                tar_file.add(directory, '')
                tar_file.close()
                fh.seek(0)
                self.upload(fh, 'upload.tar', overwrite=overwrite, extract=True)
        elif method == 'tgz_file':
            with tempfile.TemporaryFile('w+') as fh:
                with GzipFile(filename='upload.tar.gz', mode='w', fileobj=fh) as gzip_file:
                    with TarFile(name='upload.tar', mode='w', fileobj=gzip_file) as tar_file:
                        tar_file.add(directory, '')

                fh.seek(0)
                self.upload(fh, 'upload.tar.gz', overwrite=overwrite, extract=True)
        else:
            print('Selected invalid upload directory method!')
