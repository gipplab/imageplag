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



