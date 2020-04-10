import setuptools


with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='qc2tsv',
    version='0.1.3',
    scripts=['bin/qc2tsv'],
    python_requires='>=3.6',
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
    install_requires=['autouri>=0.1.2.1', 'pandas>=0.20.0', 'caper']
)
