#!/usr/bin/env python

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


import argparse
from time import sleep
import threading
from pathlib import Path
import abc

import json
import xnat
from xnat.exceptions import XNATLoginFailedError


class FileObject:
    def __init__(self, project, subject, experiment, scan, resource, filename, count, location):
        self.count = count
        self._location = location
        self._data = {
            'project': project,
            'subject': subject,
            'experiment': experiment,
            'scan': scan,
            'resource': resource,
            'filename': filename,
        }

    def __hash__(self):
        return hash((
            self._data['project'],
            self._data['subject'],
            self._data['experiment'],
            self._data['scan'],
            self._data['resource'],
            self._data['filename'],
        ))

    def __eq__(self, other):
        return self._data == other._data

    def __str__(self):
        value_list = [
            str(self._data['project']),
            str(self._data['subject']),
            str(self._data['experiment']),
            str(self._data['scan']),
            str(self._data['resource']),
            str(self._data['filename']),
        ]
        return '\t'.join(value_list)


class BaseScraper:
    def __init__(self, name):
        self._name = name
        self._work_list = []
        self.files = set()
        self._progress = 0

    def start(self):
        self._generate_worklist()
        self._check_running = True
        self._check_thread = threading.Thread(target=self._scrape, name=self._name)
        self._check_thread.daemon = True
        self._check_thread.start()

    def is_running(self):
        return self._check_thread.is_alive()

    def progress(self):
        return (self._progress/len(self._work_list))

    @abc.abstractmethod
    def _generate_worklist(self):
        raise NotImplementedError("Please Implement this method")

    @abc.abstractmethod
    def _scrape(self):
        raise NotImplementedError("Please Implement this method")


class XNATFileScraper(BaseScraper):
    def __init__(self, host):
        super().__init__('XNATFileScraper')
        self.host = host
        self.xnat_host = xnat.connect(host)
        self.missing_data = []

    def _generate_worklist(self):
        self._xnat_progress = 0
        self._work_list = self.xnat_host.projects
        print(f"XNAT contains {len(self._work_list)} projects: {' '.join(self._work_list)}")

    def _scrape(self):
        print(f"Start XNAT check on {self.xnat_host.uri}")
        for project in self._work_list:
            xnat_project = self.xnat_host.projects[project]
            for subject_id, xnat_subject in xnat_project.subjects.items():
                parent_info = {
                    'project': project,
                }
                self._check_xnat_subject(dict(parent_info), xnat_subject)

            self._progress += 1

    def _check_xnat_resource(self, parent_info, xnat_resource):
        parent_info['resource'] = xnat_resource.label
        if xnat_resource.file_count != len(xnat_resource.files):
            xnat_file_info = FileObject(
                parent_info.get('project'),
                parent_info.get('subject'),
                parent_info.get('experiment'),
                parent_info.get('scan'),
                parent_info.get('resource'),
                None,
                xnat_resource.file_count - len(xnat_resource.files),
                'xnat'
            )
            self.files.add(xnat_file_info)
        for file_id, xnat_file in xnat_resource.files.items():
            xnat_file_info = FileObject(
                parent_info.get('project'),
                parent_info.get('subject'),
                parent_info.get('experiment'),
                parent_info.get('scan'),
                parent_info.get('resource'),
                xnat_file.path,
                1,
                'xnat'
            )
            self.files.add(xnat_file_info)

    def _check_xnat_experiment(self, parent_info, xnat_experiment):
        parent_info['experiment'] = xnat_experiment.label
        for resource_id, xnat_resource in xnat_experiment.resources.items():
            result = self._check_xnat_resource(dict(parent_info), xnat_resource)
        for scan_id, xnat_scan in xnat_experiment.scans.items():
            self._check_xnat_scan(dict(parent_info), xnat_scan)

    def _check_xnat_scan(self, parent_info, xnat_scan):
        parent_info['scan'] = xnat_scan.id
        for resource_id, xnat_resource in xnat_scan.resources.items():
            result = self._check_xnat_resource(dict(parent_info), xnat_resource)

    def _check_xnat_subject(self, parent_info, xnat_subject):
        for experiment_id, xnat_experiment in xnat_subject.experiments.items():
            result = self._check_xnat_experiment(dict(parent_info), xnat_experiment)
        # Pass subject only to resource data not needed for FileSystem comparison.
        # No subject info available for experiments on Filesystem
        parent_info['subject'] = xnat_subject.label
        for resource_id, xnat_resource in xnat_subject.resources.items():
            result = self._check_xnat_resource(dict(parent_info), xnat_resource)


class FileSystemFileScraper(BaseScraper):
    def __init__(self, base_dir):
        super().__init__('FileSystemFileScraper')
        self.xnat_base_dir = Path(base_dir)

    def _generate_worklist(self):
        self._fs_progress = 0
        self._work_list = [x for x in self.xnat_base_dir.iterdir() if x.is_dir()]
        projects = [str(x) for x in self._work_list]
        print(f"FS contains {len(self._work_list)} projects: {' '.join(projects)}")

    def _scrape(self):
        print(f"Start filesystem check on {self.xnat_base_dir}")
        for project in self._work_list:
            # Check experiment data
            experiments = [x for x in (project / 'arc001').iterdir() if x.is_dir()]
            for experiment in experiments:
                parent_info = {
                    'project': project.name
                }
                self._fs_experiment_check(dict(parent_info), experiment)

            # Check subject specific data(resources)
            if (project / 'subjects').exists():
                subjects = [x for x in (project / 'subjects').iterdir() if x.is_dir()]
                for subject in subjects:
                    parent_info = {
                        'project': project.name
                    }
                    self._fs_subject_check(dict(parent_info), subject)

            self._progress += 1

    def _fs_resource_check(self, parent_info, resource):
        parent_info['resource'] = resource.name
        files = [x for x in resource.iterdir() if x.is_file()]
        for file in files:
            if file.name.endswith('catalog.xml'):
                continue
            xnat_file_info = FileObject(
                parent_info.get('project'),
                parent_info.get('subject'),
                parent_info.get('experiment'),
                parent_info.get('scan'),
                parent_info.get('resource'),
                str(file.name),
                1,
                'filesystem'
            )
            self.files.add(xnat_file_info)

    def _fs_subject_check(self, parent_info, subject):
        parent_info['subject'] = subject.name
        resources = [x for x in subject.iterdir() if x.is_dir()]
        for resource in resources:
            self._fs_resource_check(dict(parent_info), resource)

    def _fs_experiment_check(self, parent_info, experiment):
        parent_info['experiment'] = experiment.name

        resources_dir = experiment / 'RESOURCES'
        if resources_dir.is_dir():
            resources = [x for x in (experiment / 'RESOURCES').iterdir() if x.is_dir()]
            for resource in resources:
                self._fs_resource_check(dict(parent_info), resource)

        scans_dir = experiment / 'SCANS'
        if scans_dir.is_dir():
            scans = [x for x in (experiment / 'SCANS').iterdir() if x.is_dir()]
            for scan in scans:
                self._fs_scan_check(dict(parent_info), scan)

    def _fs_scan_check(self, parent_info, scan):
        parent_info['scan'] = scan.name
        resources = [x for x in scan.iterdir() if x.is_dir()]
        for resource in resources:
            self._fs_resource_check(dict(parent_info), resource)


class XNATIntegrityCheck:
    def __init__(self, host, xnat_base_dir):
        self._xnat_file_scraper = XNATFileScraper(host)
        self._filesystem_scraper = FileSystemFileScraper(xnat_base_dir)

    def start(self):
        self._xnat_file_scraper.start()
        self._filesystem_scraper.start()

    def is_running(self):
        return self._xnat_file_scraper.is_running() or self._filesystem_scraper.is_running()

    def progress(self):
        return (self._xnat_file_scraper.progress(), self._filesystem_scraper.progress())

    def write_report(self, filename):
        print(f'Files scanned on XNAT: {len(self._xnat_file_scraper.files)}')
        print(f'Files scanned on FS: {len(self._filesystem_scraper.files)}')

        missing_on_fs = self._xnat_file_scraper.files.difference(self._filesystem_scraper.files)
        missing_on_fs_count = sum(missing.count for missing in missing_on_fs)
        print(f'Files missing on FS: {missing_on_fs_count}')

        missing_on_xnat = self._filesystem_scraper.files.difference(self._xnat_file_scraper.files)
        missing_on_xnat_count = sum(missing.count for missing in missing_on_xnat)
        print(f'Files missing on XNAT: {missing_on_fs_count}')

        with open(filename, 'w') as fo:
            fo.write(f"Missing on XNAT:\n")
            for file in missing_on_xnat:
                fo.write(f"{file}\n")
            fo.write(f'Missing on Filesystem:\n')
            for file in missing_on_fs:
                fo.write(f"{file}\n")


def main():
    parser = argparse.ArgumentParser(description='Xnat data integrity check')
    parser.add_argument('--host', type=str, required=True, help='XNAT url')
    parser.add_argument('--xnat-home-dir', type=str, required=True, help='path to xnat home dir')
    parser.add_argument('--report', type=str, required=True, help='path to xnat home dir')
    args = parser.parse_args()

    xnat_integrity_checker = XNATIntegrityCheck(args.host, args.xnat_home_dir)
    xnat_integrity_checker.start()
    print('progress\t FS\tXNAT')
    while xnat_integrity_checker.is_running():
        xnat_progress, fs_progress = xnat_integrity_checker.progress()
        print(f'\t\t{fs_progress*100}\t{xnat_progress*100}', end='\r')
        sleep(1)
    fs_progress, xnat_progress = xnat_integrity_checker.progress()
    print(f'\t\t{fs_progress*100}\t{xnat_progress*100}')
    print("--- REPORT ---")
    xnat_integrity_checker.write_report(args.report)
    print('--- DONE ---')


if __name__ == "__main__":
    main()
