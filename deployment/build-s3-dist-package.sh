#!/bin/bash

# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#sudo yum-config-manager --enable epel
#sudo yum update -y
#sudo yum install git libpng-devel libcurl-devel gcc python3.8-devel libjpeg-devel -y
# pip3.8 install --upgrade pip3.8==9.0.3
# alias sudo='sudo env PATH=$PATH'
# pip3.8 install --upgrade setuptools==39.0.1
# pip3.8 install --upgrade virtualenv==15.2.0
# This script should be run from the repo's deployment directory
# cd deployment
# ./build-s3-dist.sh source-bucket-base-name
# source-bucket-base-name should be the base name for the S3 bucket location where the template will source the Lambda code from.
# The template will append '-[region_name]' to this bucket name.
# For example: ./build-s3-dist.sh solutions
# The template will then expect the source code to be located in the solutions-[region_name] bucket

# Check to see if input has been provided:
if [ -z "$1" ]; then
    echo "Please provide the base source bucket name where the lambda code will eventually reside.\nFor example: ./build-s3-dist.sh solutions"
    exit 1
fi

# Build source
echo "Starting to build distribution"
echo "export deployment_dir=`pwd`"
export deployment_dir=`pwd`

# Building image handler zip
echo "Building Image Handler package ZIP file"
cd $deployment_dir/dist
pwd
echo "virtualenv --no-site-packages env"
virtualenv --no-site-packages env
echo "source env/bin/activate"
source env/bin/activate
echo "which python3.8 pip3.8 virtualenv, version"
which python3.8 && python3.8 --version
which pip3.8 && pip3.8 --version
which virtualenv && virtualenv --version

# SO-SIH-159 - 07/25/2018 - Pycurl ssl backend
# Configuring compile time ssl backend
# https://stackoverflow.com/questions/21096436/ssl-backend-error-when-using-openssl
export PYCURL_SSL_LIBRARY=nss

cd $VIRTUAL_ENV
rm -rf lib/python3.8/site-packages/image_handler

cd ../../..
pwd
echo "pip3.8 install source/image-handler/. --target=$VIRTUAL_ENV/lib/python3.8/site-packages/"
pip3.8 install source/image-handler/. --target=$VIRTUAL_ENV/lib/python3.8/site-packages/

cd $VIRTUAL_ENV

#building mozjpeg
cd $VIRTUAL_ENV
pwd
# SO-SIH-170 - 08/15/2018 - mozjpeg path
# mozjpeg executable becomes cjpeg, rectifying path
cd $VIRTUAL_ENV
cd $VIRTUAL_ENV/lib/python3.8/site-packages
pwd
echo "zip -q -r9 $VIRTUAL_ENV/../serverless-image-handler.zip *"
zip -q -r9 $VIRTUAL_ENV/../serverless-image-handler.zip *
cd $VIRTUAL_ENV
pwd
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip pngquant"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip pngquant
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip jpegtran"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip jpegtran
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip optipng"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip optipng
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip pngcrush"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip pngcrush
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip gifsicle"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip gifsicle
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip mozjpeg/cjpeg"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip cjpeg
echo "zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip imgmin"
zip -q -g $VIRTUAL_ENV/../serverless-image-handler.zip imgmin
cd $VIRTUAL_ENV/bin
pwd
echo "zip -r -q -g $VIRTUAL_ENV/../serverless-image-handler.zip lib"
zip -r -q -g $VIRTUAL_ENV/../serverless-image-handler.zip lib
cd $VIRTUAL_ENV
pwd
cd ..
zip -q -d serverless-image-handler.zip pip*
zip -q -d serverless-image-handler.zip easy*
echo "Clean up build material"
# rm -rf $VIRTUAL_ENV
echo "Completed building distribution"
