======
README
======

ImagePlag is a plagiarism detection system to find image similarities. It is
capable of storing hashes of images in a SQLite Database and check them
against a given PDF or single images.

Extended documentation located at docs/_build/html/index.html


Installation
============

Image Plag is intended to be used with and tested on Linux
(Ubuntu 14.04.5 LTS).

From command line run at this folder:
$ pip install --user .
(at least do not use sudo)

Make sure that ~/.local/bin is in Path:
$ export PATH=$PATH:~/.local/bin (temporary)
OR
add ~/.local/bin to /etc/environment, then reboot (permanent)

Please note that for the ocr, tesseract must be installed. It will be utilized
by pytesser.

To use the PDF Module, poppler-utils and ImageMagick have to be installed.
They will be called from the command line.

GPU support is available for NVIDIA GPU.

Some dependencies might need to be installed manually.


Example Installation
--------------------

This example is based on a clean server environment and the use of python-virtualenv.


Ubuntu 16.04.1 LTS

1. Install system requirements

| sudo apt install python-pip
| sudo apt install python-virtualenv
| sudo apt install tesseract-ocr
| sudo apt install poppler-utils

2. Set up a virtualenv

a. Create virtual environment:  virtualenv 'imageplag/'
b. activate the virtual environment and install python dependencies

| source imageplag/bin/activate
| pip install backports.tempfile
| pip install pillow
| pip install imagehash
| pip install opencv-python
| pip install protobuf
| pip install pytesseract
| pip install falcon
| pip install gunicorn

3. Install caffe

Installing caffe can be quite hard, here is the general approach I took. Caffe can't
be installed in the virtualenv and should be installed as a system dependency. The path
is later also used for the usage of ImagePlag.

1. Get caffe and read the installation guide
1a. http://caffe.berkeleyvision.org/installation.html
1b. https://github.com/BVLC/caffe

Our goal is to later on run 'make pycaffe'.

2. Compile caffe locally
2a. activate the virtual environment
2b. chango the main directory and install all requirements of caffe
for req in $(cat requirements.txt); do pip install $req; done

3. Makefile.config changes
3a. uncomment CPU_ONLY := 1
3b. There was a renaming problem for hdf5, change the INCLUDE_DIRS to:
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial
3c. In 'Makefile' also rename 'hdf5' to 'hdf5_serial'
3d. run all make commands

I had several issue compiling everything, here are some I had resolve:

- https://github.com/BVLC/caffe/issues/2690
- https://gist.github.com/wangruohui/679b05fcd1466bb0937f
- https://github.com/BVLC/caffe/issues/559
- https://groups.google.com/forum/#!topic/caffe-users/3NHh06RhWd4

4. finally set the python path
4a. export PYTHONPATH=/home/vincent/IdeaProjects/caffe/caffe/python:

5. Extract additional data packages

separate packages extracted to '/image_plag/API'
- DNN_bar_no_bar
- DNN_chart_no_chart
- DNN_pure_no_pure

=====
Usage
=====

Usage with virtualenv
---------------------

Use the gunicorn installation in the virtualenv. Additionally the pythonpath should be set to
include the caffe installation. Finally change to the API folder in the imageplag
installation, e.g.: '/imageplag/API'.

$ cd API
$ ../bin/gunicorn --pythonpath "/opt/imageplag/caffe/python" -b localhost:5000 app

Usage without virtualenv
------------------------

$ cd <path to app.py>
$ service nginx start
$ gunicorn -b localhost:5000 app

Make sure to use Python 2.7, e.g.:

$ python /usr/lib/python2.7/dist-packages/gunicorn/app/wsgiapp.py -b localhost:5000 app


====
API
====

| GET /images, response: 200 JSON
| GET /images/{name}, response: 200 raw image
| POST /images, params: id, body: raw image, response: 201 string


Author
------

Christopher Gondek (gondek.christopher THAT-SIGN gmail.com)

Contributers
------------

Vincent Stange (vinc.sohn THAT-SIGN gmail.com)