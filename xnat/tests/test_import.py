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

import pytest


def test_import():
    from xnat import connect


@pytest.mark.functional_test
def test_connect():
    from xnat import connect
    with connect('https://central.xnat.org') as connection:
        print('Connected to XNAT central, running version {}'.format(connection.xnat_version))


@pytest.mark.functional_test
def test_list_projects():
    from xnat import connect
    with connect('https://central.xnat.org') as connection:
        print('Projects on XNAT central: {}'.format(connection.projects))
