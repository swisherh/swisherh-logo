#
# Markus Fraczek <marekf@gmx.net>
#
# TODO: 
# + show only 50 eigenvalues/coefficient pro page 
# + improve search 
#    - show additional information in search results (group,weight,character)
#    - restrict search when items are selected
# + extend database to include more informations (Artkin-Lenher Eigenvalues)
# + implement checks on homepage of maass wave form
# + provide API (class) for users (like L-functions guys) of database 
#
#


from mwf_utils import *

import flask
from flask import render_template, url_for, request, redirect, make_response,send_file
import bson
from sets import Set
import pymongo

mwf = flask.Module(__name__,'mwf')


@mwf.route("/",methods=['GET','POST'])

def render_maass_waveforms():
    info = get_args_mwf()
    #level = args.get("level", None)
    #weight = args.get("weight", None)
    #character = args.get("character", None)
    #MaassID = args.get("id", None)	
    #DBname = args.get("db", None)
    ##Search = args.get("search", None)
    #SearchAll = args.get("search_all", None)
    #eigenvalue = args.get("eigenvalue", None)
    print "INFO=",info
    info["credit"] = ""
    info["learnmore"]= []
    info["learnmore"].append(["Wiki","http://wiki.l-functions.org/ModularForms/MaassForms"])
    # If we have a fixed ID and Database we show that single Maass form
        
    if info['MaassID'] and info['DBname']:
        return render_one_maass_waveform_wp(info)

    level = info['level']; weight=info['weight']; character=info['character']
    eigenvalue=info['eigenvalue']
    if level and weight and character and eigenvalue:
        return redirect(url_for('mwf.render_maass_waveform_space',level=level,weight=weight,character=character,eigenvalue=eigenvalue))
    #info['cur_character'] = character
        
    if level and weight and character:
        return redirect(url_for('mwf.render_maass_waveform_space',level=level,weight=weight,character=character,eigenvalue=eigenvalue))

    if level:
        return redirect(url_for('mwf.render_maass_waveforms_for_one_group',level=level,weight=weight,character=character,eigenvalue=eigenvalue))

    info['cur_character'] = character
    #info["info1"] = MakeTitle(level,weight,character)	
    if level:
        info['maass_weight'] = getallweights(int(level))
        info['cur_level'] = level
        
    if level and weight:
        info['cur_weight'] = weight
        info['maass_character'] = getallcharacters(int(level),float(weight))
	
    if level and weight and character:
        info['cur_character'] = character
        
    if eigenvalue:
        index  = 0
        info["maass_eigenvalue"] = []			
        info["search_for_ev"] = eigenvalue
        
        [Sym,EVFS] = searchforEV(eigenvalue,"FS")
        
        if EVFS:
            info["maass_eigenvalue"].append([GetNameOfPerson("FS"),"FS",Sym,EVFS])	
            info["credit"] += GetNameOfPerson("FS")
            
            [Sym,EVHT] = searchforEV(eigenvalue,"HT")
            if EVHT:
                info["maass_eigenvalue"].append([GetNameOfPerson("HT"),"HT",Sym,EVHT])
                info["credit"] += " "+GetNameOfPerson("HT")
		
                #		if level and weight and character:
                #			Res = searchonLWC(eigenvalue,level,weight,character)
                #		elif level and weight:
                #			Res = searchonLW(eigenvalue,level,weight)
            #		elif level:
            #			Res = searchonL(eigenvalue,level)
            #		else:
            #			Res = searchon(eigenvalue)
            #               ("Name",DBname,Symetries,Eigenvalues)
            #		info["maass_eigenvalue"] 
                    


    elif level and weight and character:
        index = 0
        info["maass_eigenvalue"] = []
        [Sym,EVFS] = getEigenvaluesFS(int(level),float(weight),int(character),index)
        if EVFS:
            info["maass_eigenvalue"].append([GetNameOfPerson("FS"),"FS",Sym,EVFS])	
            info["credit"] += GetNameOfPerson("FS")
            [Sym2,EVHT] = getEigenvaluesHT(int(level),float(weight),int(character),index)
            if EVHT:
                info["maass_eigenvalue"].append([GetNameOfPerson("HT"),"HT",Sym2,EVHT])
                info["credit"] += " and "+ GetNameOfPerson("HT")
                
                info['maass_group'] = getallgroupsLevel()
    title='Browse Maass waveforms'
    
    info['list_of_levels']=get_all_levels()
    info['max_level']=max(info['list_of_levels'])
    #print_table_of_levels()
    return render_template("mwf/mwf_browse.html", info=info,title=title)


@mwf.route("/<int:level>/<weight>/<character>/")
def render_maass_waveform_space(level,weight,character):
    title="Space of Maass waveforms"
    info=dict()
    return render_template("mwf/mwf_browse.html", info=info,title=title)


@mwf.route("/<int:level>/")
def render_maass_waveforms_for_one_group(level):
    DB = ConnectDB()
    res  = dict()
    info=dict()
    for collection_name in DB.collection_names():
        res[collection_name] = list()
        C = pymongo.collection.Collection(DB,collection_name)
        L = C.find({'Level':level,'Weight':0.0})
        for F in L:
            try:
                id = F['_id']
                R  =  F['Eigenvalue']
                k =   F['Weight']
                res[collection_name].append((R,k,id))
            except:
                pass
        res[collection_name].sort()
    # now we have all maass waveforms for this group
    
    s="<table><tr>"
    for name in res.keys():
        if(len(res[name])==0):
            continue
        s+="<td>"
        s+="<table><thead>"
        s+=" <tr><td>Collection:"+name
        s+="     </td></tr></thead>"
        s+="<tbody>"
        for (R,k,id) in res[name]:
            url = url_for('mwf.render_one_maass_waveform',objectid=str(id),db=name)
            s+="<tr><td><a href=\"%s\">%s</a></td></tr>" %(url,R)
        s+="</tbody>"
        s+="</table>"
        s+="</td>"
    s+="</tr></table>"
    #print "S=",s
    info['table_of_eigenvalues']=s
    title="Maass waveforms for \(\Gamma_{0}("+str(level)+")\)"
    bread=[('Maass waveforms',url_for('render_maass_waveforms'))]
    return render_template("mwf/mwf_one_group.html", info=info,title=title)


@mwf.route("/<objectid>",methods=['GET','POST'])
def render_one_maass_waveform(objectid):
    info = get_args_mwf()
    info['MaassID']=objectid
    return render_one_maass_waveform_wp(info)
    


def render_one_maass_waveform_wp(info):
    r"""
    Render the webpage of one Maass waveform.
    """
    #if not info.has_key('MaassID'):
    #    return redirect(url_for('mwf.render_maass_waveforms'))
    info["check"]=[]
    #info["check"].append(["Hecke relation",url_for('not_yet_implemented')])
    #info["check"].append(["Ramanujan-Petersson conjecture",url_for('not_yet_implemented')])
    maass_id = info['MaassID']
    #dbname=info['db']
    info["friends"]= []
    info["friends"].append(["L-function","L/"+url_for('render_one_maass_waveform',objectid=maass_id)])
    info["downloads"]= []
    #info["downloads"].append(["Maass form data",url_for('not_yet_implemented')])
    
    bread=[('Maass waveforms',url_for('render_maass_waveforms'))]

    properties=[]
    data = get_maassform_by_id(maass_id)
    if not data.has_key('error'):
        [title,maass_info] =  set_info_for_maass_form(data)
        info["maass_data"] = maass_info
        numc=data['num_coeffs']
        largs = [{'maass_id':maass_id,'number':k} for k in range(10,numc,50)]
        info['coefficients']=ajax_more(make_table_of_coefficients,*largs,text='more')
        #info['list_spaces']=ajax_once(make_table_of_spaces_fixed_level,*largs,text='more',maass_id=maass_id)

        #
        #info["coefficients"]=table_of_coefficients(
        info["credit"] = GetNameOfPerson(data['dbname'])
        level = data['Level']
        R = data['Eigenvalue']
        title="Maass waveforms on \(\Gamma_{0}(%s)\) with R=%s" %(level,R)
    else:
        print "data=",data
        title="Could not find Maass this waveform in the database!"
        info['error']=data['error']

    bread=[('Maass waveforms',url_for('render_maass_waveforms'))]
    return render_template("mwf/mwf_one_maass_form.html", info=info,title=title,bread=bread,properties=properties)

    
    
    



"""
def write_eigenvalues(search,EVs,index):
	for i in search:
		link=url_for('render_maass_form',id=str(i['_id']))
		EVs.append([i['Eigenvalue'],index,i['Symmetry'], link])
		index=index+1
	return index

def render_webpage(args):
	info = dict(args)
	maassID = args.get("id", None)#[0]
	eigenvalue = args.get("eigenvalue", None)
#	multicheck = args.get("multicheck", None)
	
	import base
	C = base.getDBConnection()
	DB = C.MaassWaveForm
	Collection = DB.HT
	Collection.ensure_index("Eigenvalue")
#	if show == 'all':
#		return render_template("maass_form.html", info=info)
#	else:
	EVs=[]
	index = 0
	info["credit"] = "Holger Then"
        info["info1"] = "Maass cusp forms for \(PSL(2,Z)\)"
        info["info2"] = "list of  \(r\)"
#, Eigenvalue \(\\lambda= \\frac{1}{4}+ r^2\)"

	info["info3"] = "Maass form"
	info["info4"] = "\(\\quad f(z)=const\\sum_{ n \\not= 0}a_n\\sqrt{y}K_{ir}(2\\pi|n|y)e^{2\\pi inx}\)"
	info["info5"] = "Eigenvalue"
#	info["info6"] = "\( \\quad \\lambda=r^2 + \\frac{1}{4} \\ , \\quad r= \\ \) {{ info.eigenvalue  }}  "
#	info["info7"] = "Coefficients"
#	info["info8"] = "\\quad normalization \(a_1=1\)"
#	info["info9"] = "\\quad symmetry \(a_{-1}=\\%c1\)"
#	info["info10"]= "\\quad multiplicity \(a_{mp}=a_{m}a_{p}-a_{m/p}\)\\quad where \(a_{m/p}=0\) if \(p\\not|m\)"
#	info["info11"]= "\\quad prime coefficients \(a_2= \\%.5f \\quad a_3= \\%.5f \\quad a_5= \\%.5f \\quad a_7= \\%.5f \\quad \\ldots\)"

	info["learnmore"]= []
	info["learnmore"].append(["Wiki","http://wiki.l-functions.org/ModularForms/MaassForms"])
	info["learnmore"].append(["Literature","http://arxiv.org/abs/math-ph/0305047"])

	if maassID:
		try: 
			OBJ = bson.objectid.ObjectId(maassID)
		except bson.errors.InvalidId:
			return render_template("maass_form.html", info=info)
		data=Collection.find_one({'_id':bson.objectid.ObjectId(maassID)})
		info["info1"] += ", r="+str(data['Eigenvalue'])
		info["info2"] = str(data['Symmetry'])+' r='+str(data['Eigenvalue'])
		info["link"] = url_for('render_maass_form')
		info["info6"] = "\( \\quad \\lambda= \\frac{1}{4} + r^2 \\ , \\quad r= "+str(data['Eigenvalue'])+"\)"
		info["info7"] = "Symmetry"
		info["info8"] = str(data['Symmetry'])
		ANs = []
		id = 0
		for a in data['Coefficient']:
			ANs.append([id,a])
			id = id +1
		info["an"]= ANs
		info["check"]=[]
		info["check"].append(["Hecke relation",url_for('render_maass_form', multicheck=maassID)])
		info["check"].append(["Ramanujan-Petersson conjecture",url_for('render_maass_form', RPconj=maassID)])
		info["friends"]= []
		info["friends"].append(["L-function",url_for('render_maass_form', Lfunction=maassID)])
#		info["learnmore"]= []
#		info["learnmore"].append(["Wiki","http://wiki.l-functions.org/ModularForms/MaassForms"])
#		info["learnmore"].append(["Literature","http://arxiv.org/abs/math-ph/0305047"])
		info["downloads"]= []
		info["downloads"].append(["Maass form data",url_for('render_maass_form', download=maassID)])
		return render_template("maass_form2.html", info=info)
	else:	
		offset = maassID = args.get("id", 0)
		EVs = []
		index = 0
		if eigenvalue:
			try:
				ev = float(eigenvalue)
			except ValueError:
				return render_template("maass_form.html", info=info)
			search1 = Collection.find({"Eigenvalue" : {"$gte" : ev}},{'Eigenvalue':1,'Symmetry':1},sort=[('Eigenvalue',1)],limit=2)
			search2 = Collection.find({"Eigenvalue" : {"$lte" : ev}},{'Eigenvalue':1,'Symmetry':1},sort=[('Eigenvalue',-1)],limit=2)
			index=write_eigenvalues(reversed(list(search2)),EVs,index)
			write_eigenvalues(search1,EVs,index)
			info["info2"] += " search for: "+eigenvalue
		else:
			searchres=Collection.find({},{'Eigenvalue':1,'Symmetry':1},sort=[('Eigenvalue',1)])
			write_eigenvalues(searchres,EVs,index)
		info["ev"] = EVs
		
		return render_template("maass_form.html", info=info)

#find_one({'_id':bson.objectid.ObjectId('fsdfds')})
"""
