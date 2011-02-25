# -*- coding: utf-8 -*-
import re

from pymongo import ASCENDING
import base
from base import app
from flask import Flask, session, g, render_template, url_for, request, redirect, make_response


from utilities import ajax_more, image_src, web_latex, to_dict, parse_range
import sage.all 
from sage.all import ZZ, EllipticCurve, latex
q = ZZ['x'].gen()

#########################
#   Utility functions
#########################

cremona_label_regex = re.compile(r'(\d+)([a-z])+(\d*)')

def format_ainvs(ainvs):
    """
    The a-invariants are stored as a list of strings because mongodb doesn't
    have big-ints, and all strings are stored as unicode. However, printing 
    a list of unicodes looks like [u'0', u'1', ...]
    """
    return [int(a) for a in ainvs]

def xintegral_point(s):
    return [int(a) for a in eval(s) if a not in ['[',',',']']]    

#########################
#    Top level
#########################

@app.route("/EC")
def EC_redirect():
    return redirect(url_for("rational_elliptic_curves", **request.args))

@app.route("/EllipticCurve")
def EC_toplevel():
    return redirect(url_for("rational_elliptic_curves", **request.args))

#########################
#  Search/navigate
#########################

@app.route("/EllipticCurve/Q")
def rational_elliptic_curves():
    if len(request.args) != 0:
        return elliptic_curve_search(**request.args)
    conductor_list_endpoints = [1,100,1000,5000] + range(10000,130001,10000)
    conductor_list = ["%s-%s" % (start,end-1) for start, end in zip(conductor_list_endpoints[:-1], conductor_list_endpoints[1:])]
    info = {
        'rank_list': range(6),
        'torsion_list': [1,2,3,4,5,6,7,8,9,10,12,16], 
        'conductor_list': conductor_list,
    }
    credit = 'John Cremona'
    t = 'Elliptic curves over the rationals'
    return render_template("elliptic_curve/elliptic_curve_Q.html", info = info, credit=credit, title = t)

@app.route("/EllipticCurve/Q/<int:conductor>")
def by_conductor(conductor):
    return elliptic_curve_search(conductor=conductor, **request.args)

def elliptic_curve_search(**args):
    info = to_dict(args)
    query = {}
    if 'jump' in args:
        label = info.get('label', '')
        m = cremona_label_regex.match(label)
        if m:
            N, iso, number = cremona_label_regex.match(label).groups()
            if number:
                return render_curve_webpage(label=label)
            else:
                return iso_class(int(N), iso)
        else:
            query['label'] = label
    for field in ['conductor', 'torsion', 'rank']:
        if info.get(field):
            query[field] = parse_range(info[field])
    if info.get('iso'):
        query['iso'] = parse_range(info['iso'], str)
    if 'optimal' in info:
        query['number'] = 1
    info['query'] = query
    res = (base.getDBConnection().ellcurves.curves.find(query)
        .sort([('conductor', ASCENDING), ('iso', ASCENDING), ('number', ASCENDING)])
        .limit(500)) # TOOD: pages
    info['curves'] = res
    info['format_ainvs'] = format_ainvs
    credit = 'John Cremona'
    t = 'Elliptic curves over \(\mathbb{Q}\)'
    return render_template("elliptic_curve/elliptic_curve_search.html", info = info, credit=credit, title = t)
    

##########################
#  Specific curve pages
##########################

@app.route("/EllipticCurve/Q/<int:conductor>/<iso_class>")
def render_isogeny_class(conductor, iso_class):
    info = {}
    credit = 'John Cremona'
    label = "%s%s" % (conductor, iso_class)
    C = base.getDBConnection()
    data = C.ellcurves.curves.find_one({'label': label + "1"})
    if data is None:
        return "No such curves"
    label = "%s%s" % (conductor, iso_class)
    ainvs = [int(a) for a in data['ainvs']]
    E = EllipticCurve(ainvs)
    discriminant=E.discriminant()
    info = {'label': label}
    info['optimal_ainvs'] = ainvs
    info['f'] = ajax_more(E.q_eigenform, 10, 20, 50, 100, 250)
    G = E.isogeny_graph(); n = G.num_verts()
    G.relabel(range(1,n+1)) # proper cremona labels...
    info['graph_img'] = image_src(G.plot(edge_labels=True))
    curves = C.ellcurves.curves.find({'conductor': conductor, 'iso': iso_class}).sort('number')
    info['curves'] = list(curves)
    info['format_ainvs'] = format_ainvs
    info['download_qexp_url'] = url_for('download_qexp', limit=100, ainvs=','.join([str(a) for a in ainvs]))
    return render_template("elliptic_curve/iso_class.html", info = info, credit=credit)

@app.route("/EllipticCurve/Q/<label>")
def by_cremona_label(label):
    N, iso, number = cremona_label_regex.match(label).groups()
    if number:
        return render_curve_webpage(str(label))
    else:
        return render_isogeny_class(int(N), iso)

@app.route("/EllipticCurve/Q/<int:conductor>/<iso_class>/<int:number>")
def by_curve(conductor, iso_class, number):
    return render_curve_webpage(label="%s%s%s" % (conductor, iso_class, number))

def render_curve_webpage(label):
    C = base.getDBConnection()
    data = C.ellcurves.curves.find_one({'label': label})
    if data is None:
        return "No such curve"    
    info = {}
    ainvs = [int(a) for a in data['ainvs']]
    E = EllipticCurve(ainvs)
    N = ZZ(data['conductor'])
    iso_class = data['iso']
    rank = data['rank']
    j_invariant=E.j_invariant()
    discriminant=E.discriminant()
    xintpoints=[E.lift_x(x) for x in xintegral_point(data['x-coordinates_of_integral_points'])]
    info.update(data)
    info.update({
        'conductor': N,
        'disc_factor': latex(discriminant.factor()),
        'j_invar_factor':latex(j_invariant.factor()),
        'label': label,
        'equation': web_latex(E),
        'f': ajax_more(E.q_eigenform, 10, 20, 50, 100, 250),
        'generators': (', '.join(web_latex(g) for g in data['gens'])) if 'gens' in data else '',

        'lder'  : "L%s(1)" % ("'"*rank),

        'p_adic_primes': [p for p in sage.all.prime_range(5,100) if E.is_ordinary(p) and not p.divides(N)],
        'ainvs': format_ainvs(data['ainvs']),
        'tamagawa_numbers': r' \cdot '.join(str(sage.all.factor(c)) for c in E.tamagawa_numbers()),
        'cond_factor':latex(N.factor()),
        'xintegral_points':','.join(str(i_p) for i_p in xintpoints)
            })
    info['downloads_visible'] = True
    info['downloads'] = [('worksheet', url_for("not_yet_implemented"))]
    info['friends'] = [('Isogeny class', "/EllipticCurve/Q/%s/%s" % (N, iso_class)),
                       ('modular form', url_for("not_yet_implemented")),
                       ('L-function', "/L/EllipticCurve/Q/%s" % label)]
    info['learnmore'] = [('Elliptic Curves', url_for("not_yet_implemented"))]
    info['plot'] = image_src(E.plot())
    info['iso_class'] = data['iso']

    info['download_qexp_url'] = url_for('download_qexp', limit=100, ainvs=','.join([str(a) for a in ainvs]))
    G = E.torsion_subgroup().gens()
    
    if len(G) == 0:
        tor_struct = '0'
        tor_group='0'
    else:
        tor_struct = ' \\times '.join(['C_{%s}'%a.order() for a in G]) + ' \\cong '
        tor_struct += ' \\times '.join(['\\langle %s \\rangle'%a for a in G])
        tor_group=' \\times '.join(['C_{%s}'%a.order() for a in G])
    info['tor_structure'] = tor_struct
    properties = [ '<h2>Torsion Structure</h2>', '\(%s\)<br/><br/>' % tor_group, '<h2>Rank</h2>','\(%s\)<br/><br/>' % rank, 
    '<h2> Discriminant</h2>','\(%s\)<br/><br/>' % discriminant,'<h2>Conductor</h2>','\(%s\)<br/><br/>' % N,
    '<h2>j-invariant</h2>','\(%s\)<br/><br/>' % j_invariant ]
    #properties.extend([ "prop %s = %s<br/>" % (_,_*1923) for _ in range(12) ])
    credit = 'John Cremona'
    t = "Ell Curve %s" % info['label']
    return render_template("elliptic_curve/elliptic_curve.html", info=info, properties=properties, credit=credit, title = t)

@app.route("/EllipticCurve/Q/padic_data")
def padic_data():
    info = {}
    label = request.args['label']
    p = int(request.args['p'])
    info['p'] = p
    N, iso, number = cremona_label_regex.match(label).groups()
    print N, iso, number
    if request.args['rank'] == '0':
        info['reg'] = 1
    elif number == '1':
        C = base.getDBConnection()
        data = C.ellcurves.padic_db.find_one({'label': N + iso, 'p': p})
        info['data'] = data
        if data is None:
            info['reg'] = 'no data'
        else:
            reg = sage.all.Qp(p, data['prec'])(int(data['unit'])) * sage.all.Integer(p)**int(data['val'])
            reg = reg.add_bigoh(min(data['prec'], data['prec'] + data['val']))
            info['reg'] = web_latex(reg)
    else:
        info['reg'] = "no data"
    return render_template("elliptic_curve/elliptic_curve_padic.html", info = info)

@app.route("/EllipticCurve/Q/download_qexp")
def download_qexp():
    ainvs = request.args.get('ainvs')
    E = EllipticCurve([int(a) for a in ainvs.split(',')])
    response = make_response('\n'.join(str(an) for an in E.anlist(int(request.args.get('limit', 100)), python_ints=True)))
    response.headers['Content-type'] = 'text/plain'
    return response
