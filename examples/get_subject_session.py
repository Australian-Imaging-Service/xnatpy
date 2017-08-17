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
import re


def get_sessions(session, project, subject):
    xnat_project = session.projects[project]
    xnat_subject = xnat_project.subjects[subject]
    sessions = [x.label for x in xnat_subject.experiments.values()]
    return sessions


def filter_sessions(session,regex):
    for label in xnat_sessions:
        regex = re.compile(regex)
        found = regex.match(label)
        if found:
            return label

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--xnathost', type=unicode, required=True, help='xnat host name')
    parser.add_argument('--project', type=unicode, required=True, help='Project id')
    parser.add_argument('--subject', type=unicode, required=True, help='subject')
    parser.add_argument('--session', type=unicode, required=True, help='session regex')
    args = parser.parse_args()

    with xnat.connect(args.xnathost) as session:
        xnat_sessions = get_sessions(session, args.project, args.subject)

    session_label = filter_sessions(xnat_sessions,args.session)
    print('{}'.format(session_label))
