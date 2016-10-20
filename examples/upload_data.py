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


import xnat
import argparse
import os
import time


def upload_data(session, project, subject, experiment, assessment, resource, data):
    xnat_project = session.projects[project]
    # Will Create subject of none with label exists
    xnat_subject = session.classes.SubjectData(parent=xnat_project, label=subject)
    # Will Create experiment of none with label exists
    xnat_experiment = session.classes.MrSessionData(parent=xnat_subject, label=experiment)
    # Will Create QcAssessment of none with label exists
    xnat_assessment = session.classes.QcAssessmentData(parent=xnat_experiment, label=assessment)
    # Will Create new Resource of none with label exists
    resource = session.classes.ResourceCatalog(parent=xnat_assessment, label=resource)
    for file in data:
        resource.upload(file, os.path.basename(file))
    pass


def main():
    parser = argparse.ArgumentParser(description='upload Assesment to XNAT')
    parser.add_argument('--xnathost', type=unicode, required=True, help='xnat host name')
    parser.add_argument('--project', type=unicode, required=True, help='Project id')
    parser.add_argument('--subject', type=unicode, required=True, help='subject')
    parser.add_argument('--session', type=unicode, required=True, help='session')
    parser.add_argument('--assessment', type=unicode, required=False, default='assessment', help='assessment label')
    parser.add_argument('--resource', type=unicode, required=False, default='resource_' + time.strftime("%Y%m%d-%H%M%S"), help='resource label')
    parser.add_argument('--data', type=unicode, nargs='+', required=True, help='list of files')
    args = parser.parse_args()

    print('xnat host: {}'.format(args.xnathost))
    print('project: {}'.format(args.project))
    print('subject: {}'.format(args.subject))
    print('session: {}'.format(args.session))
    print('assessment: {}'.format(args.assessment))
    print('resource: {}'.format(args.resource))
    print('data:')

    for filename in args.data:
        print('     {}'.format(filename))

    with xnat.connect(args.xnathost) as session:
        upload_data(session, args.project, args.subject, args.session, args.assessment, args.resource, args.data)


if __name__ == '__main__':
    main()
