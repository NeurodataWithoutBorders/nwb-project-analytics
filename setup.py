# -*- coding: utf-8 -*
import sys

from setuptools import setup, find_packages

# Some Python installations don't add the current directory to path.
if '' not in sys.path:
    sys.path.insert(0, '')

import versioneer

with open('README.rst', 'r') as fp:
    readme = fp.read()

pkgs = find_packages('src', exclude=['data'])
print('found these packages:', pkgs)


reqs = [
    'numpy',
    'pandas',
    'ruamel.yaml',
    'GitPython',
    'PyGithub',
    'setuptools',
    'matplotlib',
    'tqdm',
    'requests',
    'hdmf-docutils',
    'cloc',
    'dandi'
]
print(reqs)

setup_args = {
    'name': 'nwb_project_analytics',
    'version': versioneer.get_version(),
    'cmdclass': versioneer.get_cmdclass(),
    'description': 'A package with functionality for monitoring the NWB project',
    'long_description': readme,
    'long_description_content_type': 'text/x-rst; charset=UTF-8',
    'author': 'Oliver Ruebel',
    'author_email': 'oruebel@lbl.gov',
    'url': 'https://github.com/NeurodataWithoutBorders/nwb-project-analytics',
    'license': "BSD",
    'install_requires': reqs,
    'packages': pkgs,
    'package_dir': {'': 'src'},
    'package_data': {},
    'python_requires': '>=3.7',
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: Unix",
        "Topic :: Scientific/Engineering :: Medical Science Apps."
    ],
    'keywords': 'python '
                'cross-platform '
                'open-data '
                'data-format '
                'open-source '
                'open-science '
                'reproducible-research ',
    'zip_safe': False,
    'entry_points': {}
}

if __name__ == '__main__':
    setup(**setup_args)
