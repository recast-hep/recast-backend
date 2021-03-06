FROM cern/cc7-base
RUN yum install -y gcc gcc-c++ python-devel libffi-devel openssl openssl-devel unzip nano autoconf automake libtool openssh-server openssh-clients
RUN curl https://bootstrap.pypa.io/get-pip.py | python -
ADD . /recast_backend
WORKDIR /recast_backend
RUN pip install . --process-dependency-links
