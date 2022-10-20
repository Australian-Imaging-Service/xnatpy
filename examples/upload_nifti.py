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
from pathlib import Path

import xnat


def upload_files(session, project, subject, experiment, experiment_type, scan, scan_description, resource, data):
    if experiment_type not in ['CT', 'MR']:
        print(f"[ERROR] experiment type {experiment_type} not supported use 'MR' or 'CT'")
        return

    xnat_project = session.projects[project]
    # If subject does not exist create subject
    if subject in xnat_project.subjects:
        xnat_subject = xnat_project.subjects[subject]
    else:
        xnat_subject = session.classes.SubjectData(parent=xnat_project, label=subject)

    # if experiment does not create new experiment
    if experiment in xnat_subject.experiments:
        xnat_experiment = xnat_subject.experiments[experiment]
    else:
        if experiment_type == 'CT':
            xnat_experiment = session.classes.CtSessionData(parent=xnat_subject, label=experiment)
        elif experiment_type == 'MR':
            xnat_experiment = session.classes.MrSessionData(parent=xnat_subject, label=experiment)
        else:
            print(f"[ERROR] experiment type {experiment_type} not supported use 'MR' or 'CT'")
            return

    # if scan does not exist create new Scan
    if scan in xnat_experiment.scans:
        xnat_scan = xnat_experiment.scans[scan]
    else:
        if experiment_type == 'CT':
            xnat_scan = session.classes.CtScanData(parent=xnat_experiment, id=scan, type=scan, series_description=scan_description, label=scan)
        elif experiment_type == 'MR':
            xnat_scan = session.classes.MrScanData(parent=xnat_experiment, id=scan, type=scan, series_description=scan_description, label=scan)
        else:
            print(f"[ERROR] scan type {experiment_type} not supported use 'MR' or 'CT'")
            return

    # If resource exists create new resource
    if resource in xnat_scan.resources:
        xnat_resource = xnat_scan.resources[resource]
    else:
        xnat_resource = session.classes.ResourceCatalog(parent=xnat_scan, label=resource)
    for file_ in data:
        file_ = Path(file_)
        if file_.exists():
            xnat_resource.upload(str(file_), file_.name)
        else:
            print(f'[WARNING] Could not find file: {file_}')
    pass


def main():
    parser = argparse.ArgumentParser(description='upload Assesment to XNAT')
    parser.add_argument('--xnathost', required=True, help='xnat host name')
    parser.add_argument('--user', required=False, default="", help='xnat user name')
    parser.add_argument('--project', required=True, help='Project id')
    parser.add_argument('--subject', required=True, help='subject')
    parser.add_argument('--experiment', required=True, help='session')
    parser.add_argument('--experiment-type', required=False, help='session type (CT/MR)')
    parser.add_argument('--scan', required=True, help='scan id')
    parser.add_argument('--scan-description', required=False, help='scan description')
    parser.add_argument('--resource-name', required=True, help='resource name')
    parser.add_argument('--files', nargs='+', required=True, help='list of files')
    args = parser.parse_args()

    print('xnat host: {}'.format(args.xnathost))
    print('project: {}'.format(args.project))
    print('subject: {}'.format(args.subject))
    print('experiment: {}'.format(args.experiment))
    print('experiment-type: {}'.format(args.experiment_type))
    print('scan: {}'.format(args.scan))
    print('scan-description: {}'.format(args.scan_description))
    print('resource-name: {}'.format(args.resource_name))
    print('files:')

    for filename in args.files:
        print('     {}'.format(filename))

    with xnat.connect(args.xnathost, user=args.user) as session:
        upload_files(session, args.project, args.subject, args.experiment, args.experiment_type, args.scan, args.scan_description, args.resource_name, args.files)


if __name__ == '__main__':
    main()
