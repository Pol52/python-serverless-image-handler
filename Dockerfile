FROM amazonlinux

RUN yum install yum-utils epel-release -y
RUN yum-config-manager --enable epel
RUN yum update -y
RUN yum install zip wget git bzip2-devel libffi-devel libpng-devel libcurl-devel gcc python-devel libjpeg-devel tar nano openssl-devel -y
RUN yum install -y make
RUN cd /opt \
    && wget https://www.python.org/ftp/python/3.8.7/Python-3.8.7.tgz \
    && tar xzf Python-3.8.7.tgz \
    && cd Python-3.8.7 \
    && ./configure --enable-optimizations \
    && make altinstall\
    && rm /opt/Python-3.8.7.tgz
RUN pip3.8 install setuptools
RUN pip3.8 install virtualenv


ENTRYPOINT "bash"
