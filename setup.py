from setuptools import setup, find_packages

setup(
    name='tmplt',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click', 'Jinja2', 'deepmerge'
    ],
    entry_points='''
        [console_scripts]
        tmplt=tmplt:cli
    '''
)
