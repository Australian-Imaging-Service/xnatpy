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


def download_xnat_session_type(connection, projectid, session, outputdir):
    output_path = os.path.join('outputdir', connection.projects[projectid].experiments[session].label)
    connection.projects[projectid].experiments[session].download(output_path)


def main():
    parser = argparse.ArgumentParser(description='delete all data with a given session type')
    parser.add_argument('--xnathost', type=unicode, required=True, help='xnat host name')
    parser.add_argument('--project', type=unicode, required=True, help='Project id')
    parser.add_argument('--session', type=unicode, required=True, help='session')
    parser.add_argument('--output_dir', type=unicode, required=False,default=True, help='outputdir')
    args = parser.parse_args()

    print('xnat host: {}'.format(args.xnathost))
    print('project: {}'.format(args.project))
    print('session: {}'.format(args.session))
    print('output: {}'.format(args.output_dir))

    with xnat.connect(args.xnathost) as connection:
        download_xnat_session_type(connection, args.project, args.session, args.output_dir)


if __name__ == '__main__':
    main()
