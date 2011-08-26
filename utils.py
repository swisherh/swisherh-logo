# -*- encoding: utf-8 -*-
# this is the caching wrapper, use it like this:
# @app.route(....)
# @cached()
# def func(): ...
from flask import request, make_response
from functools import wraps
from werkzeug.contrib.cache import SimpleCache

from copy import copy
from werkzeug import cached_property
from flask import url_for

cache = SimpleCache()
def cached(timeout=15 * 60, key='cache::%s::%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % (request.path, request.args)
            rv = cache.get(cache_key)
            if rv is None:
                rv = f(*args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
            ret = make_response(rv)
            # this header basically says that any cache can store this infinitely long
            ret.headers['Cache-Control'] = 'max-age=360000, public'
            return ret
        return decorated_function
    return decorator

def make_logger(blueprint):
  import flask
  assert type(blueprint) == flask.Blueprint
  import logging
  l = logging.getLogger(blueprint.name)
  l.propagate = False
  l.setLevel(logging.DEBUG)
  formatter = logging.Formatter('%(levelname)s:%(name)s@%(asctime)s: %(message)s')
  ch = logging.StreamHandler()
  ch.setFormatter(formatter)
  l.addHandler(ch)
  return l

class MongoDBPagination(object):
    def __init__(self, query, per_page, page, endpoint, endpoint_params):
        self.query = query
        self.per_page = int(per_page)
        self.page = int(page)
        self.endpoint = endpoint
        self.endpoint_params = endpoint_params

    @cached_property
    def count(self):
        return self.query.count(True)

    @cached_property
    def entries(self):
        return self.query.skip(self.start).limit(self.per_page)

    has_previous = property(lambda x: x.page > 1)
    has_next = property(lambda x: x.page < x.pages)
    pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)
    start = property(lambda x: (x.page - 1) * x.per_page)
    end = property(lambda x: x.start + x.per_page - 1)

    @property
    def previous(self):
        kwds = copy(self.endpoint_params)
        kwds['page'] = self.page - 1
        return url_for(self.endpoint, **kwds)

    @property
    def next(self):
        kwds = copy(self.endpoint_params)
        kwds['page'] = self.page + 1
        return url_for(self.endpoint, **kwds)

class LazyMongoDBPagination(MongoDBPagination):
    @cached_property
    def has_next(self):
        return self.query.skip(self.start).limit(self.per_page+1).count(True) > self.per_page

    @property
    def count(self):
        raise NotImplementedError
    
    @property
    def pages(self):
        raise NotImplementedError


def orddict_to_strlist(v):
    """
    v -- dictionary with int keys
    """


### this was formerly in utilities.py
import tempfile
import random
import os, re, time

from base import app
from flask import url_for, make_response
import sage.all


def to_dict(args):
    d = {}
    for key in args:
        values = args[key]
        if isinstance(values, list):
            if values:
                d[key] = values[-1]
        elif values:
            d[key] = values
    return d


def pair2complex(pair):
    local = re.match(" *([^ ]+)[ \t]*([^ ]*)", pair)
    if local:
        rp = local.group(1)
        if local.group(2):
            ip = local.group(2)
        else:
            ip=0
    else:
        rp=0
        ip=0
    return [float(rp),float(ip)]


def splitcoeff(coeff):
    local = coeff.split("\n")
    answer = []
    for s in local:
        if s:
            answer.append(pair2complex(s))

    return answer

def pol_to_html(p):
   r"""
   Convert polynomial p to html.
   """
   s = str(p)
   s = re.sub("\^(\d*)","<sup>\\1</sup>",s)
   s = re.sub("\_(\d*)","<sub>\\1</sub>",s)
   s = re.sub("\*","",s)
   s = re.sub("x","<i>x</i>",s)
   return s


def web_latex(x):
    if isinstance(x, (str, unicode)):
        return x
    else:
        return "\( %s \)" % sage.all.latex(x)


class LinkedList(object):
    __slots__ = ('value', 'next', 'timestamp')
    def __init__(self, value, next):
        self.value = value
        self.next = next
        self.timestamp = time.time()
    def append(self, value):
        self.next = LinkedList(value, self)
        return self.next

class AjaxPool(object):

    def __init__(self, size=1e4, expiration=3600):
        self._size = size
        self._key_list = self._head = LinkedList(None, None)
        self._expiration = expiration
        self._all = {}
        
    def get(self, key, value=None): 
        return self._all.get(key, value)
        
    def __contains__(self, key):
        return key in self._all
        
    def __setitem__(self, key, value):
        self._key_list = self._key_list.append(key)
        self._all[key] = value
        
    def __getitem__(self, key):
        res = self._all[key]
        self.purge()
        return res
        
    def __delitem__(self, key):
        del self._all[key]
    
    def pop_key(self):
        head = self._head
        if head.next is None:
            return None
        else:
            key = head.value
            self._head = head.next
            return key
    
    def purge(self):
        if self._size:
            while len(self._all) > self._size:
                key = self.pop_key()
                if key in self._all:
                    del self._all[key]
        if self._expiration:
            oldest = time.time() - self._expiration
            while self._head.timestamp < oldest:
                key = self.pop_key()
                if key in self._all:
                    del self._all[key]
    

pending = AjaxPool()


def ajax_url(callback, *args, **kwds):
    if '_ajax_sticky' in kwds:
        _ajax_sticky = kwds.pop('_ajax_sticky')
    else:
        _ajax_sticky = False
    if not isinstance(args, tuple):
        args = args,
    nonce = hex(random.randint(0, 1<<128))
    pending[nonce] = callback, args, kwds, _ajax_sticky
    return url_for('ajax_result', id=nonce)

@app.route('/callback_ajax/<id>')
def ajax_result(id):
    if id in pending:
        f, args, kwds, _ajax_sticky = pending[id]
        if not _ajax_sticky:
            del pending[id]
        return f(*args, **kwds)
    else:
        return "<expired>"

def ajax_more(callback, *arg_list, **kwds):
    inline = kwds.get('inline', True)
    text = kwds.get('text', 'more')
    nonce = hex(random.randint(0, 1<<128))
    if inline:
        args = arg_list[0]
        arg_list = arg_list[1:]
        if isinstance(args, tuple):
            res = callback(*arg_list)
        elif isinstance(args, dict):
            res = callback(**args)
        else:
            res = callback(args)
        res = web_latex(res)
    else:
        res = ''
    if arg_list:
        url = ajax_url(ajax_more, callback, *arg_list, inline=True, text=text)
        return """<span id='%(nonce)s'>%(res)s <a onclick="$('#%(nonce)s').load('%(url)s', function() { MathJax.Hub.Queue(['Typeset',MathJax.Hub,'%(nonce)s']);}); return false;" href="#">%(text)s</a></span>""" % locals()
    else:
        return res

def image_src(G):
    return ajax_url(image_callback, G, _ajax_sticky=True)

def image_callback(G):
    
    P = G.plot()
    _, filename = tempfile.mkstemp('.png')
    P.save(filename)
    data = open(filename).read()
    os.unlink(filename)
    response = make_response(data)
    response.headers['Content-type'] = 'image/png'
    return response



def parse_range(arg, parse_singleton=int):
    # TODO: graceful errors
    if type(arg)==parse_singleton:
        return arg
    if ',' in arg:
        return {'$or': [parse_range(a) for a in arg.split(',')]}
    elif '-' in arg[1:]:
        ix = arg.index('-', 1)
        start, end = arg[:ix], arg[ix+1:]
        q = {}
        if start:
            q['$gte'] = parse_singleton(start)
        if end:
            q['$lte'] = parse_singleton(end)
        return q
    else:
        return parse_singleton(arg)


def coeff_to_poly(c):
    from sage.all import PolynomialRing, QQ
    return PolynomialRing(QQ, 'x')(c)

