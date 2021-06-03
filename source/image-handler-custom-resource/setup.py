# coding: utf-8

from setuptools import setup, find_packages
# SO-SIH-156 - 07/16/2018 - Pip version upgrade
# Upgrading pip version, handling error


setup(
    name='image_handler_custom_resource_py3',
    version='1.0',
    description='AWS Serverless Image Handler CFN Custom Resource',
    author='AWS Solutions Builder',
    license='ASL',
    zip_safe=False,
    packages=['image_handler_custom_resource'],
    package_dir={'image_handler_custom_resource': '.'},
    include_package_data=False,
    install_requires=[
        'image_handler_custom_resource_py3>=1.0',
        'requests',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.8',
    ],
)
