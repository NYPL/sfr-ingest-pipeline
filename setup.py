from setuptools import setup, find_packages

def readme():
    with open('README.md') as rm:
        return rm.read()

setup(
    name='sfrCore',
    version='0.3.3',
    description='Core database model and utilities for the SFR project',
    url='https://github.com/nypl/sfr-core',
    author='Michael Benowitz',
    author_email='michaelbenowitz@nypl.org',
    license='MIT',
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        'psycopg2-binary',
        'sqlalchemy',
        'python-dateutil',
        'requests',
        'pycountry',
        'alembic'
    ],
    zip_safe=False
)
