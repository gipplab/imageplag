============
Requirements
============

Additionally to the requirements from imageplagdeploy the package 'falcon' is necessary.

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

=========
API Specs
=========

1. GET /images, response: 200 JSON
2. GET /images, params: (id) response: 200 JSON
3. GET /images/{id}, response: 200 raw image
4. POST /images, params: (id, store{'true'|'false'}), body: raw image, response: 201 string


