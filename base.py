# -*- encoding: utf-8 -*-

import sys
import logging
from time import sleep
from flask import Flask, session, g, render_template, url_for, request, redirect
from pymongo import Connection
from pymongo.cursor import Cursor                                                             
from pymongo.errors import AutoReconnect  
from pymongo.connection import Connection
from sage.all import *
from functools import wraps
from werkzeug.contrib.cache import SimpleCache

# global db connection instance
_C = None

readonly_dbs = [ 'HTPicard', 'Lfunction', 'Lfunctions', 'MaassWaveForm',
        'ellcurves', 'hmfs', 'modularforms', 'modularforms_2010',
        'mwf_dbname', 'numberfields', 'quadratic_twists', 'test', 'test_pdehaye']

readwrite_dbs = ['userdb', 'upload', 'knowledge']

readonly_username = 'lmfdb'
readonly_password = 'readonly'

readwrite_username = 'lmfdb_website'

AUTO_RECONNECT_MAX = 10
AUTO_RECONNECT_DELAY = 1
AUTO_RECONNECT_ATTEMPTS = 0

def _db_reconnect(func):
  """
  Wrapper to automatically reconnect when mongodb throws a AutoReconnect exception.

  See 
    * http://stackoverflow.com/questions/5287621/occasional-connectionerror-cannot-connect-to-the-database-to-mongo
    * http://paste.pocoo.org/show/224441/
  and similar workarounds
  """
  def retry(*args, **kwargs):
    global AUTO_RECONNECT_ATTEMPTS
    while True:
      try:
        return func(*args, **kwargs)
      except AutoReconnect, e:
        AUTO_RECONNECT_ATTEMPTS += 1
        if AUTO_RECONNECT_ATTEMPTS > AUTO_RECONNECT_MAX:
           AUTO_RECONNECT_ATTEMPTS = 0
           import flask
           flask.flash("AutoReconnect failed to reconnect", "error")
           raise
        logging.warning('AutoReconnect #%d - %s raised [%s]' % (AUTO_RECONNECT_ATTEMPTS, func.__name__, e))
        sleep(AUTO_RECONNECT_DELAY)
  return retry

Cursor._Cursor__send_message = _db_reconnect(Cursor._Cursor__send_message)
Connection._send_message = _db_reconnect(Connection._send_message)
Connection._send_message_with_response = _db_reconnect(Connection._send_message_with_response)

 
def _init(dbport, readwrite_password):
    global _C
    logging.info("establishing db connection at port %s ..." % dbport)
    _C = Connection(port=dbport)
    return _C
    for db in readonly_dbs:
        _C[db].authenticate(readonly_username, readonly_password)
        logging.info("authenticated readonly on database %s" % db)
    if readwrite_password == '':
        for db in readwrite_dbs:
            _C[db].authenticate(readonly_username, readonly_password)
            logging.info("authenticated readonly on database %s" % db)
    else:
        for db in readwrite_dbs:
            _C[db].authenticate(readwrite_username, readwrite_password)
            logging.info("authenticated readwrite on database %s" % db)

def getDBConnection():
  return _C

app = Flask(__name__)

# the following context processor inserts
#  * empty info={} dict variable
#  * body_class = ''
#  * bread = [...] for the default bread crumb hierarch
#  * title = 'test string'
@app.context_processor
def ctx_proc_userdata():
  # insert an empty info={} as default
  # set the body class to some default, blueprints should
  # overwrite it with their name, using @<blueprint_object>.context_processor
  # see http://flask.pocoo.org/docs/api/?highlight=context_processor#flask.Blueprint.context_processor
  vars = { 'info' : {}, 'body_class' : '' }

  # insert the default bread crumb hierarchy
  # overwrite this variable when you want to customize it
  vars['bread'] = None #[ ('Bread', '.'), ('Crumb', '.'), ('Hierarchy', '.')]
  
  # default title
  vars['title'] = r'Title variable "title" has not been set. This is a test: \( \LaTeX \) and \( \frac{1}{1+x+x^2} \) and more ...'
  return vars


# datetime format in jinja templates
# you can now pass in a datetime.datetime python object and via
# {{ <datetimeobject>|fmtdatetime }} you can format it right inside the template
# if you want to do more than just the default, use it for example this way:
# {{ <datetimeobject>|fmtdatetime('%H:%M:%S') }}
@app.template_filter("fmtdatetime")
def fmtdatetime(value, format='%Y-%m-%d %H:%M:%S'):
    return value.strftime(format)

@app.template_filter('obfuscate_email')
def obfuscate_email(email):
    """
    obfuscating the email
    TODO: doesn't work yet
    """
    return u"%s…@…%s" % (email[:2],email[-2:])

@app.template_filter('urlencode')
def urlencode(kwargs):
  import urllib
  return urllib.urlencode(kwargs)

### for testing.py ###
import unittest
class LmfdbTest(unittest.TestCase):
  def setUp(self):
    app.config['TESTING'] = True
    self.app = app
    self.tc = app.test_client()
    import website
    self.C = getDBConnection()

