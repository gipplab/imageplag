FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        wget \
        libatlas-base-dev \
        libboost-all-dev \
        libgflags-dev \
        libgoogle-glog-dev \
        libhdf5-serial-dev \
        libleveldb-dev \
        liblmdb-dev \
        libopencv-dev \
        libprotobuf-dev \
        libsnappy-dev \
        tesseract-ocr \
        poppler-utils \
        protobuf-compiler \
        python-dev \
        python-numpy \
        python-pip \
        python-setuptools \
        python-scipy \
        python-virtualenv \
    && rm -rf /var/lib/apt/lists/*

#Might not need a virtual environment inside an isolated Docker container
#RUN python -m virtualenv --python=/usr/bin/python /opt/venv
#COPY . /

#Install dependencies:
COPY requirements.txt .
RUN pip install -r requirements.txt

ENV CAFFE_ROOT=/opt/caffe
WORKDIR $CAFFE_ROOT

# FIXME: use ARG instead of ENV once DockerHub supports this
# https://github.com/docker/hub-feedback/issues/460
ENV CLONE_TAG=1.0

RUN git clone -b ${CLONE_TAG} --depth 1 https://github.com/BVLC/caffe.git . && \
#    pip install --upgrade pip && \
    cd python && for req in $(cat requirements.txt) pydot; do pip install $req; done && cd .. && \
    mkdir build && cd build && \
    cmake -DCPU_ONLY=1 .. && \
    make -j"$(nproc)"

# Set python environment variables (after the installation of python)
ENV PYCAFFE_ROOT $CAFFE_ROOT/python
ENV PYTHONPATH $PYCAFFE_ROOT:$PYTHONPATH
ENV PATH $CAFFE_ROOT/build/tools:$PYCAFFE_ROOT:$PATH
RUN echo "$CAFFE_ROOT/build/lib" >> /etc/ld.so.conf.d/caffe.conf && ldconfig

# Copy ImagePlag program
COPY API /API

# Execute gunicorn with our ImagePlag application
WORKDIR "/API"
CMD gunicorn -b localhost:5000 app

#RUN ../bin/gunicorn --pythonpath "/opt/venv/caffe/python" -b 0.0.0.0:5000 app


