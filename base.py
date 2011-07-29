# -*- encoding: utf-8 -*-

import sys
from flask import Flask, session, g, render_template, url_for, request, redirect
from pymongo import Connection
from sage.all import *
from functools import wraps
from werkzeug.contrib.cache import SimpleCache

_C = None
 
def _init(dbport):
 global _C
 _C = Connection(port=dbport)

def getDBConnection():
  return _C

app = Flask(__name__)

# secret key, necessary for sessions, and sessions are
# in turn necessary for users to login
app.secret_key = '9af"]ßÄ!_°$2ha€42~µ…010'

from login import login_manager
login_manager.setup_app(app)

