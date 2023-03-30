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

from xnat.core import XNATListing
from xnat.mixin import ProjectData, SubjectData, ExperimentData

# Mark this entire module as functional tests requiring docker
pytestmark = [pytest.mark.docker_test, pytest.mark.functional_test]


def test_list_projects(xnat4tests_connection):
    projects = xnat4tests_connection.projects
    assert isinstance(projects, XNATListing)
    assert len(xnat4tests_connection.projects) == 1

    project = projects[0]
    assert isinstance(project, ProjectData)
    assert projects[0].id == 'dummydicomproject'
    assert projects['dummydicomproject'] is project


def test_list_subjects(xnat4tests_connection):
    project = xnat4tests_connection.projects[0]
    subjects = project.subjects
    assert isinstance(subjects, XNATListing)
    assert len(subjects) == 1

    subject = subjects[0]
    assert subject is subjects[0]
    assert isinstance(subject, SubjectData)
    assert subject.label == 'dummydicomsubject'
    assert subjects[subject.id] is subject
    assert subjects[subject.label] is subject


def test_list_experiments(xnat4tests_connection):
    project = xnat4tests_connection.projects[0]
    experiments = project.experiments
    assert isinstance(experiments, XNATListing)
    assert len(experiments) == 1

    experiment = experiments[0]
    assert experiment is experiments[0]
    assert isinstance(experiment, ExperimentData)
    assert experiment.label == 'dummydicomsession'
    assert experiments[experiment.id] is experiment
    assert experiments[experiment.label] is experiment
