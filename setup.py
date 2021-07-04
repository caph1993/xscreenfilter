from setuptools import setup
'''
sh sumbit.sh
    rm dist/*
    python3 setup.py check
    python3 setup.py sdist
    twine upload dist/*
    pip3 install --upgrade xscreenfilter
    pip3 install --upgrade xscreenfilter
'''

setup(
    name='xscreenfilter',
    version='0.1.3',
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
