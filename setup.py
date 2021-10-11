from setuptools import setup
from xscreenfilter import VERSION

setup(
    name='xscreenfilter',
    version=VERSION,
    description='Python',
    url='https://github.com/caph1993/xscreenfilter',
    author='Carlos Pinzón',
    author_email='caph1993@gmail.com',
    license='MIT',
    packages=[
        'xscreenfilter',
    ],
    install_requires=[
        'xlib',
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
