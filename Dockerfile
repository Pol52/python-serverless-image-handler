FROM amazonlinux

RUN yum install yum-utils epel-release -y
RUN yum-config-manager --enable epel
RUN yum update -y
RUN yum install zip wget git libpng-devel libcurl-devel gcc python-devel libjpeg-devel tar nano openssl-devel -y
RUN yum install -y python2-pip
RUN yum install -y make
RUN pip install setuptools==39.0.1
RUN pip install virtualenv==15.2.0

ENTRYPOINT "bash"
