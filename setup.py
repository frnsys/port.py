from setuptools import setup, find_packages

setup(
    name='port',
    version='0.0.9',
    description='lightweight static blog',
    url='https://github.com/ftzeng/port',
    author='Francis Tseng (@frnsys)',
    license='MIT',

    zip_safe=True,
    package_data={'': ['port/themes']},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'click',
        'flask',
        'py-gfm',
        'pyrss2gen',
        'python-dateutil',
        'pyyaml',
    ],
    entry_points='''
        [console_scripts]
        port=port.cli:cli
    ''',
)