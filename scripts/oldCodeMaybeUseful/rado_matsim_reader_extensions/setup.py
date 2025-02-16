from setuptools import setup, find_packages

setup(
    name='rado_matsim_reader_extensions',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'xopen',
        "xml.etree.ElementTree",
        # "matsim.utils"
        # add other dependencies here
    ],
)

