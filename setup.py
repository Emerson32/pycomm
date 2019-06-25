from setuptools import setup, find_packages

setup(
    name='pycomm',
    version='1.0.0',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=[
        'Click',
        'prompt_toolkit',
        'PyInquirer',
        'pyfiglet',
    ],
    entry_points={
        'console_scripts': [
            'pycomm = pycomm.__main__:main'
        ]
    })
