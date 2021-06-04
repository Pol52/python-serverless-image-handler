# coding: utf-8
from setuptools import setup


tests_require = [
    'mock==4.0.3',
    'pytest==6.2.4'
]

setup(
    name='image_handler',
    version='3.2',
    description='Python3.8 version of AWS Serverless Image Handler',
    author='Ian Hartz',
    license='ASL',
    zip_safe=False,
    test_suite='tests',
    packages=['image_handler'],
    package_dir={'image_handler': '.'},
    include_package_data=True,
    package_data={
        '': ['*.conf'],
    },
    install_requires=[
        'botocore',
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
        #'thumbor_rekognition==0.1.1', #TODO: fix thumbor_rekognition boto3 dependencies before enabling
        #'tc_aws @ git+https://github.com/amanagr/aws.git@thumbor-7#egg=tc_aws', # manually build from submodule until stable community release
        'opencv-python-headless==4.5.2.52'
    ],
    extras_require={
        'tests': tests_require,
    },
    classifiers=[
        'Programming Language :: Python :: 3.8',
    ],
)