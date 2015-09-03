import os
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

# Get the requirements
with open('requirements.txt', 'r') as fh:
    _requires = fh.read().splitlines()

# Get information about the version (polling mercurial if possible)
version = '0.1.0'
dirstate = './.hg/dirstate'
if os.path.isfile(dirstate):
    with open(dirstate, 'rb') as f_dirstate:
        hg_version = f_dirstate.read(20).encode('hex')
else:
    hg_version = None

branch = './.hg/branch'
if os.path.isfile(branch):
    with open(branch, 'r') as f_branch:
        hg_branch = f_branch.read().strip()
else:
    hg_branch = ''

if hg_version is not None:
    extra_version = '{}-{}-{}'.format(version, hg_branch, hg_version[0:6])
else:
    extra_version = '{}'.format(version)

# Write information to version.py
with open('./xnat/version.py', 'w') as f_version:
    f_version.write('version = "{}"\n'.format(version))
    f_version.write('extra_version = "{}"\n'.format(extra_version))
    f_version.write('hg_revision = "{}"\n'.format(hg_version))
    f_version.write('hg_branch = "{}"\n'.format(hg_branch))

setup(
    name='xnat',
    version='0.1.0',
    author='H.C. Achterberg',
    author_email='hakim.achterberg@gmail.com',
    packages=['xnat'],
    url='https://bitbucket.org/bigr_erasmusmc/xnat',
    license='LICENSE',
    description='A package that allows you to check MR sessions (a directory of dicoms) against a schema to validate it matches the expected MR experiment.',
    long_description=open('README').read(),
    install_requires=_requires
)
