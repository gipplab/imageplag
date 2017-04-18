=====
Requirements
=====

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


=====
API
=====

| GET /images, response: 200 JSON
| GET /images/{name}, response: 200 raw image
| POST /images, params: (name, analyse{'true'|'false'}, store{'true'|'false'}, body: raw image, response: 201 string


