# coding: utf-8
from setuptools import setup


tests_require = [
    'mock==4.0.3',
    'pytest==6.2.4'
]

setup(
    name='image_handler_py3',
    version='3.0py3',
    description='Python3.8 version of AWS Serverless Image Handler',
    author='Ian Hartz',
    license='ASL',
    zip_safe=False,
    test_suite='tests',
    packages=['image_handler_py3'],
    package_dir={'image_handler_py3': '.'},
    include_package_data=True,
    package_data={
        '': ['*.conf'],
    },
    install_requires=[
        'botocore==1.20.84',
        # SO-SIH-159 - 07/18/2018 - Version and dependencies fix
        # Locking botocore, pycurl version and moving dependencies from requirements
        'tornado==6.1',
        'pycurl==7.43.0.6',
        'tornado_botocore==1.5.0',
        'requests_unixsocket==0.2.0',
        'thumbor==7.0.0a5',
        'thumbor-plugins==0.2.4',
        # SO-SIH-155 - 07/18/2018 - Rekognition integration
        # Adding Rekognition
        #'thumbor_rekognition==0.1.1',
        #'tc_aws @ git+https://github.com/amanagr/aws.git@thumbor-7#egg=tc_aws',
        'opencv-python==4.5.2.52',
        'boto3==1.17.84',
        's3transfer==0.4.2'
    ],
    extras_require={
        'tests': tests_require,
    },
    classifiers=[
        'Programming Language :: Python :: 3.8',
    ],
)
