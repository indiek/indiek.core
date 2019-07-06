import setuptools
from indiek.core import __version__
from indiek.core import name as init_name

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = init_name,
    version = __version__,
    author= "Adrian Ernesto Radillo",
    author_email="adrian.radillo@gmail.com",
    description="Core functions for IndieK, a knowledge management app.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/indiek/indiek.core",
    packages=setuptools.find_namespace_packages(exclude=['docs', 'tests*', 'ignore']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    license = 'GNU Affero General Public License v3.0',
)
