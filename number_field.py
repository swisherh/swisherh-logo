import re
import pymongo

from base import app, db, C
from flask import Flask, session, g, render_template, url_for, request, redirect

from utilities import ajax_more, image_src, web_latex, to_dict, parse_range
import sage.all
from sage.all import ZZ, QQ, PolynomialRing, NumberField, latex, AbelianGroup

@app.route("/NF")
def NF_redirect():
    return redirect(url_for("number_field_render_webpage", **request.args))

# function copied from classical_modular_form.py
def set_sidebar(l):
	res=list()
#	print "l=",l
	for ll in l:
		if(len(ll)>1):
			content=list()
			for n in range(1,len(ll)):
				content.append(ll[n])
			res.append([ll[0],content])
#	print "res=",res
	return res


@app.route("/NumberField/GaloisGroups")
def render_groups_page():
    info = {}
    info['credit'] = 'the PARI group'	
    return render_template("number_field/galois_groups.html", groups=groups, info=info)

@app.route("/NumberField")
def number_field_render_webpage():
    args = request.args
    if len(args) == 0:      
        discriminant_list_endpoints = [100**k for k in range(6)]
        discriminant_list = ["%s-%s" % (start,end-1) for start, end in zip(discriminant_list_endpoints[:-1], discriminant_list_endpoints[1:])]
        info = {
        'degree_list': [1,2,3,4,5,6,7],
        'signature_list': [[1,1],[2,0],[0,1],[3,0],[1,1],[4,0],[2,1],[0,2],[5,0],[3,1],[1,2],[6,0],[4,1],[2,2],[0,3],[7,0],[5,1],[3,2],[1,3]],
        'class_number_list': [1,2,3,4,5,6,7,8,9,10,'11-1000000'],
        'discriminant_list': discriminant_list
    }
        info['credit'] = 'the PARI group'	

        explain=['Further information']
        explain.append(('Unique labels for number fields (not yet implemented)','/'))
	explain.append(('Unique labels for Galois groups',url_for("render_groups_page")))
        explain.append(('Discriminant ranges (not yet implemented)','/'))
        info['sidebar']=set_sidebar([explain])

        return render_template("number_field/number_field_all.html", info = info)
    else:
        return number_field_search(**args)

def coeff_to_poly(c):
    return PolynomialRing(QQ, 'x')(c)

def coeff_to_nf(c):
    return NumberField(coeff_to_poly(c), 'a')

def sig2sign(sig):
    return [1,-1][sig[1]%2]

group_names = {}
group_names[(1, 1, 1, 1)] = ('S1','S1')
group_names[(2, 2, -1, 1)] = ('S2','S2')
group_names[(3, 6, -1, 1)] = ('S3','S3')
group_names[(3, 3, 1, 2)] = ('A3','A3')
group_names[(4, 8, -1, 1)] = ('D(4)','D4')
group_names[(4, 4, -1, 1)] = ('C(4) = 4','C4')
group_names[(4, 4, 1, 1)] = ('E(4) = 2[x]2','V4')
group_names[(4, 24, -1, 1)] = ('S4','S4')
group_names[(4, 12, 1, 1)] = ('A4','A4')
group_names[(5, 120, -1, 1)] = ('S5','S5')
group_names[(5, 10, 1, 1)] = ('D(5) = 5:2','D5')
group_names[(5, 60, 1, 1)] = ('A5','A5')
group_names[(5, 20, -1, 1)] = ('F(5) = 5:4','F5')
group_names[(5, 5, 1, 1)] = ('C(5) = 5','C5')
group_names[(6, 18, -1, 1)] = ('F_18(6) = [3^2]2 = 3 wr 2','?')
group_names[(6, 48, -1, 1)] = ('2S_4(6) = [2^3]S(3) = 2 wr S(3)','?')
group_names[(6, 72, -1, 1)] = ('F_36(6):2 = [S(3)^2]2 = S(3) wr 2','?')
group_names[(6, 6, -1, 2)] = ('D_6(6) = [3]2','?')
group_names[(6, 12, -1, 1)] = ('D(6) = S(3)[x]2','D6')
group_names[(6, 720, -1, 1)] = ('S6','S6')
group_names[(6, 6, -1, 1)] = ('C(6) = 6 = 3[x]2','C6')
group_names[(6, 24, -1, 1)] = ('S_4(6c) = 1/2[2^3]S(3)','?')
group_names[(6, 24, -1, 2)] = ('2A_4(6) = [2^3]3 = 2 wr 3','?')
group_names[(6, 24, 1, 1)] = ('S_4(6d) = [2^2]S(3)','?')
group_names[(6, 12, 1, 1)] = ('A_4(6) = [2^2]3','?')
group_names[(6, 36, -1, 1)] = ('F_18(6):2 = [1/2.S(3)^2]2','?')
group_names[(6, 360, 1, 1)] = ('A6','A6')
group_names[(6, 60, 1, 1)] = ('L(6) = PSL(2,5) = A_5(6)','?')
# 2 more degree 6 fields exist, not yet in the database
group_names[(7, 5040, -1, 1)] = ('S7','S7')
group_names[(7, 14, -1, 1)] = ('D(7) = 7:2','D7')
group_names[(7, 7, 1, 1)] = ('C(7) = 7','C7')
group_names[(7, 2520, 1, 1)] = ('A7','A7')
# 3 more degree 7 fields exist, not yet in the database

groups = [{'label':list(g),'gap_name':group_names[g][0],'human_name':group_names[g][1]} for g in group_names.keys()]

def complete_group_code(c):
    for g in group_names.keys():
        if c in group_names[g]:
            return list(g)[1:]+[group_names[g][0]]
    try:
        c = parse_list(c)
        return c[1:]+[group_names[tuple(c)][0]]
    except KeyError:
        return 0
 
def render_field_webpage(args):
    data = None
    if 'label' in args:
        label = str(args['label'])
        data = C.numberfields.fields.find_one({'label': label})
    if data is None:
        return "No such field"    
    info = {}
    info['credit'] = 'the PARI group'	
    try:
        info['count'] = args['count']
    except KeyError:
        info['count'] = 10
    K = coeff_to_nf(data['coefficients'])
    D = data['discriminant']
    h = data['class_number']
    data['galois_group'] = str(data['galois_group'][3])
    data['class_group'] = str(AbelianGroup(data['class_group']))
    sig = data['signature']
    unit_rank = sig[0]+sig[1]-1
    if unit_rank==0:
        reg = 1
    else:
        reg = K.regulator()
    info.update(data)
    info.update({
        'label': label,
        'polynomial': web_latex(K.defining_polynomial()),
        'integral_basis': web_latex(K.integral_basis()),
        'regulator': web_latex(reg)
        })
    info['downloads_visible'] = True
    info['downloads'] = [('worksheet', '/')]
    info['friends'] = [('L-function', '/')]
    info['learnmore'] = [('Number Fields', '/')]
    return render_template("number_field/number_field.html", info = info)

def format_coeffs(coeffs):
    """
    The a-invariants are stored as a list of strings because mongodb doesn't
    have big-ints, and all strings are stored as unicode. However, printing 
    a list of unicodes looks like [u'0', u'1', ...]
    """
    return web_latex(coeff_to_poly(coeffs))


@app.route("/NumberField")
def number_fields():
    if len(request.args) != 0:
        return number_field_search(**request.args)
    info['credit'] = 'the PARI group'
    info['learnmore'] = [('Galois groups', '/')]
    return render_template("number_field/number_field_all.html", info = info)
    

@app.route("/NumberField/<label>")
def by_label(label):
    return render_field_webpage({'label' : label})

def parse_list(L):
    return eval(str(L))

def number_field_search(**args):
    info = to_dict(args)
    if 'natural' in info:
        return render_field_webpage({'label' : info['natural']})
    query = {}
    for field in ['degree', 'signature', 'discriminant', 'class_number', 'class_group', 'galois_group']:
        if info.get(field):
            if field in ['class_group', 'signature']:
                query[field] = parse_list(info[field])
            else:
                if field == 'galois_group':
                    query[field] = complete_group_code(info[field])
                else:
                    query[field] = parse_range(info[field])
    if info.get('ur_primes'):
        ur_primes = [int(a) for a in str(info['ur_primes']).split(',')]
    else:
        ur_primes = []

    if info.get('count'):        
        try:
            count = int(info['count'])
        except:
            count = 10
    else:
        count = 10

    info['query'] = dict(query)
    if 'lucky' in args:
        one = C.numberfields.fields.find_one(query)
        if one:
            label = one['label']
            return render_field_webpage({'label': label})

    if 'discriminant' in query:
        res = C.numberfields.fields.find(query).sort([('degree',pymongo.ASCENDING),('signature',pymongo.DESCENDING),('discriminant',pymongo.ASCENDING)]) # TODO: pages
    else:
        # find matches with negative discriminant:
        neg_query = dict(query)
        neg_query['discriminant'] = {'$lt':0}
        res_neg = C.numberfields.fields.find(neg_query).sort([('degree',pymongo.ASCENDING),('discriminant',pymongo.DESCENDING)])
        # TODO: pages

        # find matches with positive discriminant:
        pos_query = dict(query)
        pos_query['discriminant'] = {'$gt':0}
        res_pos = C.numberfields.fields.find(pos_query).sort([('degree',pymongo.ASCENDING),('discriminant',pymongo.ASCENDING)])
        # TODO: pages

        res = merge_sort(iter(res_neg),iter(res_pos))

    if ur_primes:
        res = filter_ur_primes(res, ur_primes)

    res = iter_limit(res,count)
        
    info['fields'] = res
    info['format_coeffs'] = format_coeffs
    return render_template("number_field/number_field_search.html", info = info)


def iter_limit(it,lim):
    count = 0
    while count<lim:
        yield it.next()
        count += 1
    return

                   
def merge_sort(it1,it2):
    try:
        a = it1.next()
    except StopIteration:
        b = it2.next()
        while True:
            yield b
            b = it2.next()
        return
    
    try:
        b = it2.next()
    except StopIteration:
        a = it1.next()
        while True:
            yield a
            a = it1.next()
        return
                
    while True:
        if abs(a['discriminant'])<abs(b['discriminant']):
            yield a
            try:
                a = it1.next()
            except StopIteration:
                b = it2.next()
                while True:
                    yield b
                    b = it2.next()
                return
        else:
            yield b
            try:
                b = it2.next()
            except StopIteration:
                a = it1.next()
                while True:
                    yield a
                    a = it1.next()
                return
    return

def support_is_disjoint(D,plist):
    D = ZZ(D)
    for p in plist:
        if ZZ(p).divides(D):
            return False
    return True

def filter_ur_primes(it, ur_primes):
    a = it.next()
    D = a['discriminant']
    while True:
        if support_is_disjoint(D,ur_primes):
            yield a
        a = it.next()
        D = a['discriminant']
    return
    
# obsolete old function:                    
def old_merge(it1,it2,lim):
    count=0
    try:
        a = it1.next()
    except StopIteration:
        for b in it2:
            if count==lim:
                return
            yield b
            count += 1
        return
    try:
        b = it2.next()
    except StopIteration:
        for a in it1:
            if count==lim:
                return
            yield a
            count += 1
        return

    while count<lim:
        if abs(a['discriminant'])<abs(b['discriminant']):
            yield a
            count += 1
            try:
                a = it1.next()
            except StopIteration:
                for b in it2:
                    if count==lim:
                        return
                    yield b
                    count += 1
                return
        else:
            yield b
            count += 1
            try:
                b = it2.next()
            except StopIteration:
                for a in it1:
                    if count==lim:
                        return
                    yield a
                    count += 1
                return
