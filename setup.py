from setuptools import setup, find_packages

setup(
    name='GitSync',
    version='0.1.6',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'toml',
        'requests',
    ],
    entry_points='''
        [console_scripts]
        gitsync=GitSync.cli:main
    ''',
)