# -*- coding: utf-8 -*-
#*****************************************************************************
#  Copyright (C) 2010 Fredrik Strömberg <fredrik314@gmail.com>,
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    General Public License for more details.
#
#  The full text of the GPL is available at:
#
#                  http://www.gnu.org/licenses/
#*****************************************************************************
r"""
Utilities file for elliptic (holomorhic) modular forms.

AUTHOR: Fredrik Strömberg


"""
import random
from flask import  jsonify
from utils import *
from modular_forms.elliptic_modular_forms import EMF,emf, emf_logger
logger = emf_logger
from sage.all import dimension_new_cusp_forms,vector,dimension_modular_forms,dimension_cusp_forms,is_odd

def ajax_more2(callback, *arg_list, **kwds):
    r"""
    Like ajax_more but accepts increase in two directions.
    Call with
    ajax_more2(function,{'arg1':[x1,x2,...,],'arg2':[y1,y2,...]},'text1','text2')
    where function takes two named argument 'arg1' and 'arg2'
    """
    inline = kwds.get('inline', True)
    text = kwds.get('text', 'more')
    emf_logger.debug("inline={0}".format(inline))
    emf_logger.debug("text={0}".format(text))
    text0 = text[0]
    text1 = text[1]
    emf_logger.debug("arglist={0}".format(arg_list))
    nonce = hex(random.randint(0, 1<<128))
    if inline:
        args = arg_list[0]
        emf_logger.debug("args={0}".format(args))
        key1,key2=args.keys()
        l1=args[key1]
        l2=args[key2]
        emf_logger.debug("key1={0}".format(key1))
        emf_logger.debug("key2={0}".format(key2))
        emf_logger.debug("l1={0}".format(l1))
        emf_logger.debug("l2={0}".format(l2))
        args={key1:l1[0],key2:l2[0]}
        l11=l1[1:]; l21=l2[1:]
        #arg_list = arg_list[1:]
        arg_list1 = {key1:l1,key2:l21}
        arg_list2 = {key1:l11,key2:l2}
        #emf_logger.debug("arglist1={0}".format(arg_list))
        if isinstance(args, tuple):
            res = callback(*arg_list)
        elif isinstance(args, dict):
            res = callback(**args)
        else:
            res = callback(args)
            res = web_latex(res)
    else:
        res = ''
    emf_logger.debug("arg_list1={0}".format(arg_list1))
    emf_logger.debug("arg_list2={0}".format(arg_list2))
    arg_list1=(arg_list1,)
    arg_list2=(arg_list2,)
    if arg_list1 or arg_list2:
        url1 = ajax_url(ajax_more2, callback, *arg_list1, inline=True, text=text)
        url2 = ajax_url(ajax_more2, callback, *arg_list2, inline=True, text=text)
        emf_logger.debug("arg_list1={0}".format(url1))
        emf_logger.debug("arg_list2={0}".format(url2))
        s0 = """<span id='%(nonce)s'>%(res)s """  % locals()
        s1 = """[<a onclick="$('#%(nonce)s').load('%(url1)s', function() { MathJax.Hub.Queue(['Typeset',MathJax.Hub,'%(nonce)s']);}); return false;" href="#">%(text0)s</a>""" % locals()
        t = """| <a onclick="$('#%(nonce)s').load('%(url2)s', function() { MathJax.Hub.Queue(['Typeset',MathJax.Hub,'%(nonce)s']);}); return false;" href="#">%(text1)s</a>]</span>""" % locals()
        return (s0+s1+t)
    else:
        return res

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


def ajax_once(callback,*arglist,**kwds):
    r"""
    """
    
    text = kwds.get('text', 'more')
    emf_logger.debug("text={0}".format(text))
    emf_logger.debug("arglist={0}".format(arglist))
    emf_logger.debug("kwds={0}".format(kwds))
    #emf_logger.debug("req={0}".format(request.args
    nonce = hex(random.randint(0, 1<<128))
    res = callback()
    url = ajax_url(ajax_once,arglist,kwds,inline=True)
    s0 = """<span id='%(nonce)s'>%(res)s """  % locals()
    #	s1 = """[<a onclick="$('#%(nonce)s').load('%(url)s', {'level':22,'weight':4},function() { MathJax.Hub.Queue(['Typeset',MathJax.Hub,'%(nonce)s']);}); return false;" href="#">%(text)s</a>""" % locals()
    s1 = """[<a onclick="$('#%(nonce)s').load('%(url)s', {a:1},function() { MathJax.Hub.Queue(['Typeset',MathJax.Hub,'%(nonce)s']);}); return false;" href="#">%(text)s</a>""" % locals()
    return s0+s1


def ajax_later(callback,*arglist,**kwds):
    r"""
    Try to make a function that gets called after displaying the page.
    """
    
    text = kwds.get('text', 'more')
    text = 'more'
    emf_logger.debug("text={0}".format(text))
    emf_logger.debug("arglist={0}".format(arglist))
    emf_logger.debug("kwds={0}".format(kwds))
    emf_logger.debug("callback={0}".format(callback))
    #emf_logger.debug("req={0}".format(request.args
    nonce = hex(random.randint(0, 1<<128))
    # do not call the first time around
    if kwds.has_key("do_now"):
        if kwds['do_now']==1:
            do_now=0
        else:
            do_now=1
    else:
        do_now=0
    if not do_now:
        url = ajax_url(ajax_later,callback,*arglist,inline=True,do_now=do_now,_ajax_sticky=True)
        emf_logger.debug("ajax_url={0}".format(url))
        s0 = """<span id='%(nonce)s'></span>"""  % locals()
        s1 = """<a class='later' href=# id='%(nonce)s' onclick='this_fun()'>%(text)s</a>""" % locals()
        s2= """<script>
        function this_fun(){
        $.getJSON('%(url)s',{do_now:1},
        function(data) {
        $(\"span#%(nonce)s\").text(data.result);
        });
        return true;
        };
        </script>
        
        """ % locals()
        emf_logger.debug("s0+s1={0}".format(s2+s0))
        return s2+s0+s1
    else:
        res = callback(do_now=do_now)
        return jsonify(result=res)


emf_dbname = 'modularforms'

def connect_db():
    import base
    return base.getDBConnection()[emf_dbname]
def connect_mf_db():
    return 

from modular_forms.backend import  ModularFormDisplay


class ClassicalMFDisplay(ModularFormDisplay):

    def __init__(self,dbname=''):
        ModularFormDisplay.__init__(self,dbname)
        
    
    def set_table(self,skip=[0,0],limit=[(2,12),(1,30)],keys=['Weight','Level'],character=0,dimension_fun=dimension_new_cusp_forms,title='Dimension of newforms'):
        r"""
        Table of Holomorphic modular forms spaces.
        Skip tells you how many chunks of data you want to skip (from the geginning) and limit tells you how large each chunk is.
        INPUT:
        - dimension_fun should be a function which gives you the desired dimensions, as functions of level N and weight k
        - character = 0 for trivial character and 1 for Kronecker symbol.
          set to 'all' for all characters.
        """
        self._keys=keys
        self._skip=skip
        self._limit=limit
        self._metadata=[]
        self._title=''
        self._cols=[]
        self.table={}
        self._character = character
        logger.debug("skip= {0}".format(self._skip))
        logger.debug("limit= {0}".format(self._limit))
        il  = self._keys.index('Level')
        iwt = self._keys.index('Weight')
        level_len = self._limit[il][1]-self._limit[il][0]+1
        level_ll=self._skip[il]*level_len+self._limit[il][0];   level_ul=self._skip[il]*level_len+self._limit[il][1]
        wt_len = self._limit[iwt][1]-self._limit[iwt][0]+1
        wt_ll=self._skip[iwt]*wt_len+self._limit[iwt][0]; wt_ul=self._skip[iwt]*wt_len+self._limit[iwt][1]
        if level_ll<1: level_l=1
        self._table={}
        self._table['rows']=[]
        #self._table['col_heads']=range(wt_ll,wt_ul+1)
        #self._table['row_heads']=range(level_ll,level_ul+1)
        logger.debug("wt_range: {0} -- {1}".format(wt_ll,wt_ul))
        logger.debug("level_range: {0} -- {1}".format(level_ll,level_ul))
        if character in [0,1]:
            for N in range(level_ll,level_ul+1):
                if not N in self._table['row_heads']:
                    self._table['row_heads'].append(N)
                row=[]
                for k in range(wt_ll,wt_ul+1):
                    if character == 0 and is_odd(k):
                        continue
                    try:
                        if character==0:
                            d = dimension_fun(N,k)
                        elif character==1:
                            x = kronecker_character_upside_down(N)
                            d = dimension_fun(x,k)
                    except Exception as ex:
                        emf_logger.critical("Exception: {0}. \n Could not compute the dimension with function {0}".format(ex,dimension_fun))
                    url = url_for('emf.render_elliptic_modular_form_browsing',level=N,weight=k)
                    if not k in self._table['col_heads']:
                        self._table['col_heads'].append(k)
                    row.append({'N':N,'k':k,'url':url,'dim':d})
                self._table['rows'].append(row)
        elif character=='all':
            # make table with all characters.
            for N in range(level_ll,level_ul+1):
                if not N in self._table['row_heads']:
                    self._table['row_heads'].append(N)
                row=[]
                D = DirichletGroup(N)
                for k in range(wt_ll,wt_ul+1):
                    tbl=[]
                    for x in D:
                        if x.is_even() and is_odd(k):
                            continue
                        if x.is_odd() and is_even(k):
                            continue
                        try:
                            d = dimension_fun(x,k)
                        except Exception as ex:
                            emf_logger.critical("Exception: {0} \n Could not compute the dimension with function {0}".format(ex,dimension_fun))
                        url = url_for('emf.render_elliptic_modular_form_browsing',level=N,weight=k)
                        if not k in self._table['col_heads']:
                            self._table['col_heads'].append(k)
                        tbl.append({'N':N,'k':k,'chi':D.list().index(x),'url':url,'dim':d})
                    row.append(tbl)
                self._table['rows'].append(row)            

