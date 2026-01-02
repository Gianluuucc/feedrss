import sys
import os

# Aggiungi la cartella corrente e 'libs' al path per trovare le librerie
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

from wsgiref.handlers import CGIHandler
from app import app

class ProxyFix(object):
   def __init__(self, app):
       self.app = app
   def __call__(self, environ, start_response):
       script_name = environ.get('SCRIPT_NAME', '')
       if script_name:
           environ['SCRIPT_NAME'] = script_name
           path_info = environ.get('PATH_INFO', '')
           if path_info.startswith(script_name):
               environ['PATH_INFO'] = path_info[len(script_name):]
       return self.app(environ, start_response)

if __name__ == '__main__':
    app.wsgi_app = ProxyFix(app.wsgi_app)
    CGIHandler().run(app)
