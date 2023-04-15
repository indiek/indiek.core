from setuptools import setup

setup(
    name='indiek-core',
    python_requires='>=3.8',
    version='0.1.0',
    description='core logic for indiek',
    long_description='',
    author='Adrian Ernesto Radillo',
    author_email='adrian.radillo@gmail.com',
    license='GNU Affero General Public License v3.0',
    packages=['indiek.core'],
    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'pytest-cov'
        ]
    }
)