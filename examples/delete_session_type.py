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


def delete_xnat_session_type(connection, projectid, session_to_be_removed, dryrun)
    for subject in connection.projects[projectid].subjects:
        experiments = connection.projects[projectid].subjects[subject].experiments
        for experiment in experiments:
            xsiType = connection.projects[projectid].subjects[subject].experiments[experiment].xsi_type
            if xsiType == session_to_be_removed:
                if dryrun:
                    print('{},{},{}'.format(subject, experiment, xsiType))
                    print('Remove session: {}'.format(session.projects[projectid].subjects[subject].experiments[experiment]))
                else:
                    connection.projects[projectid].subjects[subject].experiments[experiment].delete(remove_files=True)


def main():
    parser = argparse.ArgumentParser(description='delete all data with a given session type')
    parser.add_argument('--xnathost', type=unicode, required=True, help='xnat host name')
    parser.add_argument('--project', type=unicode, required=True, help='Project id')
    parser.add_argument('--sessiontype', type=unicode, required=True, help='session')
    parser.add_argument('--dryrun', type=unicode, required=False,default=True, help='session')
    args = parser.parse_args()

    print('xnat host: {}'.format(args.xnathost))
    print('project: {}'.format(args.project))
    print('session: {}'.format(args.session))
    print('dryrun: {}'.format(args.dryrun))

    with xnat.connect(args.xnathost) as connection:
        delete_xnat_session_type(connection, args.project, args.session, args.dryrun)


if __name__ == '__main__':
    main()
