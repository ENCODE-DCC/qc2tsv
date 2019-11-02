import setuptools
import qc2tsv

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='qc2tsv',
    version=qc2tsv.__version__,
    scripts=['bin/qc2tsv'],
    python_requires='>3.4.1',
    author='Jin Lee',
    author_email='leepc12@gmail.com',
    description='Converts multiple QC JSONs to a spread sheet (TSV/CSV)',
    long_description='https://github.com/ENCODE-DCC/qc2tsv',
    long_description_content_type='text/markdown',
    url='https://github.com/ENCODE-DCC/qc2tsv',
    packages=setuptools.find_packages(exclude=['examples', 'docs']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
    ],
    install_requires=['caper>=0.5.4', 'pandas>=0.20.0']
)
