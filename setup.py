from setuptools import setup, find_packages

setup(
    name='HARey',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pandas',
        'notebook',
    ],
    package_data={
        'HARey': ['datafiles/hip_redux.dat', 'datafiles/index.json', 'datafiles/names.csv', 'cardbacks/*.png', 'markers/*.svg'],
    },
    author='Giacomo Menegatti',
    description='A python package to create constellation in the style of HARey',
    long_description=open('README.md').read(),
    classifiers=['Programming Language :: Python :: 3'],
    python_requires='>=3.10',
)
