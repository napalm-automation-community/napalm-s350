"""setup.py file."""

from setuptools import setup, find_packages

__author__ = "Jasper Lievisse Adriaanse <j@jasper.la>"

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

with open("README.md", "r") as fs:
    long_description = fs.read()

setup(
    name="napalm-s350",
    version="0.4.1.1",
    packages=find_packages(exclude=("test*",)),
    author="Jasper Lievisse Adriaanse, Petr Klíma, Daniel Bacher",
    author_email="j@jasper.la, qaxi@seznam.cz, mail@phill93.de",
    description="NAPALM driver for Cisco SMB switches (SF3xx, SF5xx, SG3xx, SG5xx)",
    license="Apache 2.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    url="https://github.com/napalm-automation-community/napalm-s350",
    include_package_data=True,
    install_requires=reqs,
)
