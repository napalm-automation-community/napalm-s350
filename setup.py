"""setup.py file."""

import uuid

from setuptools import setup, find_packages

__author__ = 'Jasper Lievisse Adriaanse <j@jasper.la>'

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-s350",
    version="0.1.2",
    packages=find_packages(),
    author="Jasper Lievisse Adriaanse",
    author_email="j@jasper.la",
    description="Network Automation and Programmability Abstraction Layer with Multivendor support",
    classifiers=[
        'Topic :: Utilities',
         'Programming Language :: Python',
         'Programming Language :: Python :: 3',
         'Programming Language :: Python :: 3.6',
         'Programming Language :: Python :: 3.7',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    url="https://github.com/jasperla/napalm-s350",
    include_package_data=True,
    install_requires=reqs,
)
