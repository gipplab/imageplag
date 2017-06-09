======
README
======


Description
-----------

| ImagePlag is a plagiarism detection system to find image similarities. It is
| capable of storing hashes of images in a SQLite Database and check them
| against a given PDF or single images.
|
| Extended documentation located at docs/_build/html/index.html


Installation
------------

| Image Plag is intended to be used with and tested on Linux
| (Ubuntu 14.04.5 LTS).
|
| From command line run at this folder:
| $ pip install --user .
| (at least do not use sudo)
|
| Make sure that ~/.local/bin is in Path:
| $ export PATH=$PATH:~/.local/bin (temporary)
| OR
| add ~/.local/bin to /etc/environment, then reboot (permanent)
|
| Please note that for the ocr, tesseract must be installed. It will be utilized
| by pytesser.
|
| To use the PDF Module, poppler-utils and ImageMagick have to be installed.
| They will be called from the command line.
|
| GPU support is available for NVIDIA GPU.
|
| Some dependencies might need to be installed manually.


Additional Installation
-----------------------

| Additionally to the requirements from imageplagdeploy the package 'falcon' is necessary.


Upgrade
-------

| From commmand line run at this folder:
| $ pip install --user --upgrade .

=====
Usage
=====

| After installation, start the API with
|
| $ cd <path to app.py>
| $ service nginx start
| $ gunicorn -b localhost:5000 app
|
|
| Make sure to use Python 2.7, e.g.:
|
| $ python /usr/lib/python2.7/dist-packages/gunicorn/app/wsgiapp.py -b localhost:5000 app


====
API
====

| GET /images, response: 200 JSON
| GET /images/{name}, response: 200 raw image
| POST /images, params: name, body: raw image, response: 201 string


Author
------

| Christopher Gondek (gondek.christopher THAT-SIGN gmail.com)