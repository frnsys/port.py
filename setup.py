from setuptools import setup, find_packages

setup(
    name='port',
    version='1.1.6',
    description='lightweight static blog',
    url='https://github.com/frnsys/port',
    author='Francis Tseng (@frnsys)',
    license='MIT',

    zip_safe=True,
    package_data={'': ['port/themes']},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'click==6.2',
        'watchdog==2.1.8',
        'pyrss2gen',
        'python-dateutil',
        'pyyaml',
        'nom'
    ],
    entry_points='''
        [console_scripts]
        port=port.cli:cli
    ''',
)