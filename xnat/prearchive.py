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

import datetime
from pathlib import Path
import re
from typing import Any, List, Optional, Union, TYPE_CHECKING

import isodate
import requests

from .core import XNATBaseObject, caching
from .datatypes import to_date, to_time
from .utils import RequestsFileLike
from .type_hints import JSONType

if TYPE_CHECKING:
    from .session import BaseXNATSession

try:
    PYDICOM_LOADED = True
    import pydicom
except ImportError:
    PYDICOM_LOADED = False
    pydicom = None


class PrearchiveSession(XNATBaseObject):
    @property
    def id(self) -> str:
        """
        A unique ID for the session in the prearchive
        :return:
        """
        return '{}/{}/{}'.format(self.data['project'], self.data['timestamp'], self.data['name'])

    @property
    def xpath(self) -> str:
        return "xnatpy:prearchiveSession"

    @property
    def fulldata(self) -> JSONType:
        # There is a bug in 1.7.0-1.7.2 that misses a route in the REST API
        # this should be fixed from 1.7.3 onward
        if re.match(r'^1\.7\.[0-2]', self.xnat_session.xnat_version):
            # Find the xnat prearchive project uri
            project_uri = self.uri.rsplit('/', 2)[0]

            # We need to search for session with url field without the /data start
            target_uri = self.uri[5:] if self.uri.startswith('/data') else self.uri
            all_sessions = self.xnat_session.get_json(project_uri)
            for session in all_sessions['ResultSet']['Result']:
                if session['url'] == target_uri:
                    return session
            else:
                raise IndexError('Could not find specified prearchive session {}'.format(self.uri))
        else:
            return self.xnat_session.get_json(self.uri)['ResultSet']['Result'][0]

    @property
    @caching
    def data(self) -> JSONType:
        return self.fulldata

    @property
    def autoarchive(self):
        return self.data['autoarchive']

    @property
    def folder_name(self) -> str:
        return self.data['folderName']

    @property
    def lastmod(self) -> datetime.datetime:
        lastmod_string = self.data['lastmod']
        return datetime.datetime.strptime(lastmod_string, '%Y-%m-%d %H:%M:%S.%f')

    @property
    def name(self) -> str:
        return self.data['name']

    @property
    def label(self) -> str:
        return self.name

    @property
    def prevent_anon(self):
        return self.data['prevent_anon']

    @property
    def prevent_auto_commit(self):
        return self.data['prevent_auto_commit']

    @property
    def project(self) -> str:
        return self.data['project']

    @property
    def scan_date(self) -> Optional[datetime.date]:
        try:
            return to_date(self.data['scan_date'])
        except isodate.ISO8601Error:
            return None

    @property
    def scan_time(self) -> Optional[datetime.time]:
        try:
            return to_time(self.data['scan_time'])
        except isodate.ISO8601Error:
            return None

    @property
    def status(self) -> str:
        return self.data['status']

    @property
    def subject(self) -> str:
        return self.data['subject']

    @property
    def tag(self):
        return self.data['tag']

    @property
    def timestamp(self):
        return self.data['timestamp']

    @property
    def uploaded(self) -> Optional[datetime.datetime]:
        """
        Datetime when the session was uploaded
        """
        uploaded_string = self.data['uploaded']
        try:
            return datetime.datetime.strptime(uploaded_string, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            return None

    @property
    def scans(self) -> List['PrearchiveScan']:
        """
        List of scans in the prearchive session
        """
        data = self.xnat_session.get_json(self.uri + '/scans')
        # We need to prepend /data to our url (seems to be a bug?)

        return [PrearchiveScan('{}/scans/{}'.format(self.uri, x['ID']),
                               self.xnat_session,
                               id_=x['ID'],
                               datafields=x) for x in data['ResultSet']['Result']]

    def download(self,
                 path: Union[Path, str]):
        """
        Method to download the zip of the prearchive session

        :param str path: path to download to
        :return: path of the downloaded zip file
        :rtype: str
        """
        self.xnat_session.download_zip(self.uri, path)
        return path

    def archive(self,
                overwrite: str = None,
                quarantine: bool = None,
                trigger_pipelines: bool = None,
                project: str = None,
                subject: str = None,
                experiment: str = None):
        """
        Method to archive this prearchive session to the main archive

        :param overwrite: how the handle existing data (none, append, delete)
        :param quarantine: flag to indicate session should be quarantined
        :param trigger_pipelines: indicate that archiving should trigger pipelines
        :param project: the project in the archive to assign the session to
        :param subject: the subject in the archive to assign the session to
        :param experiment: the experiment in the archive to assign the session content to
        :return: the newly created experiment
        """
        query = {'src': self.uri}

        if overwrite is not None:
            if overwrite not in ['none', 'append', 'delete']:
                raise ValueError('Overwrite should be none, append or delete!')
            query['overwrite'] = overwrite

        if quarantine is not None:
            if isinstance(quarantine, bool):
                if quarantine:
                    query['quarantine'] = 'true'
                else:
                    query['quarantine'] = 'false'
            else:
                raise TypeError('Quarantine should be a boolean')

        if trigger_pipelines is not None:
            if isinstance(trigger_pipelines, bool):
                if trigger_pipelines:
                    query['triggerPipelines'] = 'true'
                else:
                    query['triggerPipelines'] = 'false'
            else:
                raise TypeError('trigger_pipelines should be a boolean')

        # Change the destination of the session
        # BEWARE the dest argument is completely ignored, but there is a work around:
        # HACK: See https://groups.google.com/forum/#!searchin/xnat_discussion/prearchive$20archive$20service/xnat_discussion/hwx3NOdfzCk/rQ6r2lRpZjwJ
        if project is not None:
            query['project'] = project

        if subject is not None:
            query['subject'] = subject

        if experiment is not None:
            query['session'] = experiment

        response = self.xnat_session.post('/data/services/archive', query=query)
        object_uri = response.text.strip()

        self.clearcache()  # Make object unavailable
        return self.xnat_session.create_object(object_uri)

    def delete(self,
               asynchronous: Optional[bool] = None) -> requests.Response:
        """
        Delete the session from the prearchive

        :param asynchronous: flag to delete asynchronously
        :return: requests response
        """
        query = {'src': self.uri}

        if asynchronous is not None:
            if isinstance(asynchronous, bool):
                if asynchronous:
                    query['async'] = 'true'
                else:
                    query['async'] = 'false'
            else:
                raise TypeError('async should be a boolean')

        response = self.xnat_session.post('/data/services/prearchive/delete', query=query)
        self.clearcache()
        return response

    def rebuild(self,
                asynchronous: Optional[bool] = None) -> requests.Response:
        """
        Rebuilt the session in the prearchive

        :param asynchronous: flag to rebuild asynchronously
        :return: requests response
        """
        query = {'src': self.uri}

        if asynchronous is not None:
            if isinstance(asynchronous, bool):
                if asynchronous:
                    query['async'] = 'true'
                else:
                    query['async'] = 'false'
            else:
                raise TypeError('async should be a boolean')

        response = self.xnat_session.post('/data/services/prearchive/rebuild', query=query)
        self.clearcache()
        return response

    def move(self,
             new_project: str,
             asynchronous: Optional[bool] = None) -> requests.Response:
        """
        Move the session to a different project in the prearchive

        :param new_project: the id of the project to move to
        :param asynchronous: flag to move asynchronously
        :return: requests response
        """
        query = {'src': self.uri,
                 'newProject': new_project}

        if asynchronous is not None:
            if isinstance(asynchronous, bool):
                if asynchronous:
                    query['async'] = 'true'
                else:
                    query['async'] = 'false'
            else:
                raise TypeError('async should be a boolean')

        response = self.xnat_session.post('/data/services/prearchive/move', query=query)
        self.clearcache()
        return response
    
    def cli_str(self) -> str:
        return "Prearchive session {name}".format(name=self.label)


class PrearchiveScan(XNATBaseObject):
    def __init__(self,
                 uri: str,
                 xnat_session: 'BaseXNATSession',
                 id_: str = None,
                 datafields: Any = None,
                 parent: PrearchiveSession = None,
                 fieldname: str = None):
        super(PrearchiveScan, self).__init__(uri=uri,
                                             xnat_session=xnat_session,
                                             id_=id_,
                                             datafields=datafields,
                                             parent=parent,
                                             fieldname=fieldname)

        self._fulldata = {'data_fields': datafields}

    @property
    def series_description(self) -> str:
        """
        The series description of the scan
        """
        return self.data['series_description']

    @property
    def files(self) -> List['PrearchiveFile']:
        """
        List of files contained in the scan
        """
        data = self.xnat_session.get_json(self.uri + '/resources/DICOM/files')

        return [PrearchiveFile(x['URI'],
                               self.xnat_session,
                               id_=x['Name'],
                               datafields=x) for x in data['ResultSet']['Result']]

    def download(self,
                 path: Union[Path, str]) -> Union[Path, str]:
        """
        Download the scan as a zip

        :param str path: the path to download to
        :return: the path of the downloaded file
        :rtype: str
        """
        self.xnat_session.download_zip(self.uri, path)
        return path

    @property
    def data(self):
        return self.fulldata['data_fields']

    @property
    def fulldata(self) -> Any:
        return self._fulldata

    @property
    def xpath(self) -> str:
        return "xnatpy:prearchiveScan"

    def dicom_dump(self, fields: Optional[List[str]] = None) -> JSONType:
        """
        Retrieve a dicom dump as a JSON data structure
        See the XAPI documentation for more detailed information: `DICOM Dump Service <https://wiki.xnat.org/display/XAPI/DICOM+Dump+Service+API>`_

        :param fields: Fields to filter for DICOM tags. It can either a tag name or tag number in the format GGGGEEEE (G = Group number, E = Element number)
        :return: JSON object (dict) representation of DICOM header
        """

        # Get the uri in the following format /prearchive/projects/${project}/${timestamp}/${session}
        # Get the uri and remove the first five characters: /data
        uri = self.uri[5:]
        return self.xnat_session.services.dicom_dump(src=uri, fields=fields)

    def read_dicom(self,
                   file: Optional['PrearchiveFile'] = None,
                   read_pixel_data: bool = False,
                   force: bool = False) -> pydicom.FileDataset:
        # Check https://gist.github.com/obskyr/b9d4b4223e7eaf4eedcd9defabb34f13 for partial loading?
        if not PYDICOM_LOADED:
            raise RuntimeError('Cannot read DICOM, missing required dependency: pydicom')

        if file is None:
            dicom_files = sorted(self.files, key=lambda x: x.name)
            file = dicom_files[0]
        else:
            if file not in self.files:
                raise ValueError('File {} not part of scan {} prearchive session'.format(file, self))

        with file.open() as dicom_fh:
            dicom_data = pydicom.dcmread(dicom_fh,
                                         stop_before_pixels=not read_pixel_data,
                                         force=force)

        return dicom_data


class PrearchiveFile(XNATBaseObject):
    def __init__(self,
                 uri: str,
                 xnat_session: 'BaseXNATSession',
                 id_: str = None,
                 datafields=None,
                 parent: PrearchiveScan = None,
                 fieldname: str = None):
        super(PrearchiveFile, self).__init__(uri=uri,
                                             xnat_session=xnat_session,
                                             id_=id_,
                                             datafields=datafields,
                                             parent=parent,
                                             fieldname=fieldname)

        self._fulldata = datafields

    def open(self):
        uri = self.xnat_session.url_for(self)
        request = self.xnat_session.interface.get(uri, stream=True)
        return RequestsFileLike(request)

    @property
    def data(self):
        return self.fulldata

    @property
    def fulldata(self):
        return self._fulldata

    @property
    def name(self):
        """
        The name of the file
        """
        return self.data['Name']

    @property
    def size(self):
        """
        The size of the file
        """
        return self.data['Size']

    @property
    def xpath(self):
        return "xnatpy:prearchiveFile"

    def download(self, path):
        """
        Download the file

        :param str path: the path to download to
        :return: the path of the downloaded file
        :rtype: str
        """
        self.xnat_session.download_zip(self.uri, path)
        return path


class Prearchive(object):
    def __init__(self,
                 xnat_session: 'BaseXNATSession'):
        self._xnat_session = xnat_session
        self._cache = {}
        self._caching = True

    @property
    def caching(self) -> bool:
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
    def xnat_session(self) -> 'BaseXNATSession':
        return self._xnat_session

    def sessions(self,
                 project: str = None) -> List[PrearchiveSession]:
        """
        Get the session in the prearchive, optionally filtered by project. This
        function is not cached and returns the results of a query at each call.

        :param project: the project to filter on
        :return: list of prearchive session found
        """
        if project is None:
            uri = '/data/prearchive/projects'
        else:
            uri = '/data/prearchive/projects/{}'.format(project)

        data = self.xnat_session.get_json(uri)
        # We need to prepend /data to our url (seems to be a bug?)

        result = []
        for session_data in data['ResultSet']['Result']:
            # You can't query receiving sessions via the REST API yet, so don't show them
            if session_data.get('status', 'unknown') == 'RECEIVING':
                continue

            uri = '/data{}'.format(session_data['url'])

            session = self._cache.get(uri, None)

            if session is None:
                session = PrearchiveSession(uri, self.xnat_session)
                self._cache[uri] = session

            result.append(session)

        return result

    def find(self,
             project: str = None,
             subject: str = None,
             session: str = None,
             status: str = None) -> List[PrearchiveSession]:
        """
        Find specific session(s) given the project/subject/session/status

        :param project:
        :param subject:
        :param session:
        :param status:
        :return: list of matching sessions
        """
        result = []
        sessions = self.sessions(project=project)

        for option in sessions:
            if subject is not None and option.subject != subject:
                continue

            if session is not None and option.label != session:
                continue

            if status is not None and option.status != status:
                continue

            result.append(option)

        return result
