import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='recollection',
    version='0.9.3',
    author='Mike Malinowski',
    author_email='mike@twisted.space',
    description='A python package exposing the memento design pattern',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mikemalinowski/recollection',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'six',
    ],
    keywords="recollect recollection memento mementos",
)
