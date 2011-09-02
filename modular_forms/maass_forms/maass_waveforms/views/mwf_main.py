r"""

AUTHORS:

 Markus Fraczek <marekf@gmx.net> (2010)
 Fredrik Stroemberg (2011-)



 TODO: 
 + show only 50 eigenvalues/coefficient pro page 
 + improve search 
    - show additional information in search results (group,weght,character)
    - restrict search when items are selected
 + extend database to include more informations (Artkin-Lenhe Eigenvalues)
 + implement checks on homepage of maass wave form
 + provide API (class) for users (like L-functions guys) of database 


"""

import flask
from flask import render_template, url_for, request, redirect, make_response,send_file
import bson
from sets import Set
import pymongo
from sage.all import is_odd,is_even
#mwf = flask.Blueprint('mwf', __name__, template_folder="templates",static_folder="static")
import utils
from  modular_forms.maass_forms.maass_waveforms import MWF,mwf_logger, mwf
from modular_forms.maass_forms.maass_waveforms.backend.mwf_utils import *
from mwf_upload_data import *
logger = mwf_logger

# this is a blueprint specific default for the tempate system.
# it identifies the body tag of the html website with class="wmf"
@mwf.context_processor
def body_class():
  return { 'body_class' : MWF }

@mwf.route("/",methods=['GET','POST'])

def render_maass_waveforms():
    info = get_args_mwf()
    print "INFO=",info
    info["credit"] = ""
    info["learnmore"]= []
    info["learnmore"].append(["Wiki","http://wiki.l-functions.org/ModularForms/MaassForms"])
    # if we submit a search we search the database:
    mwf_logger.debug("args=%s"%request.args)
    mwf_logger.debug("method=%s"%request.method)
    mwf_logger.debug("req.form=%s"%request.form)
    mwf_logger.debug("info=%s"%info)
    if info['search']:
        search = get_search_parameters(info)
        return render_search_results_wp(info,search)
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
        mwf_logger.debug("info(level)=%s"%info)
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
    title='Maass waveforms'
    
    info['list_of_levels']=get_all_levels()
    info['max_level']=max(info['list_of_levels'])
    mwf_logger.debug("info3=%s"%info)
    #print_table_of_levels()
    return render_template("mwf_browse.html", info=info,title=title)
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
    title='Maass waveforms'
    
    info['list_of_levels']=get_all_levels()
    info['max_level']=max(info['list_of_levels'])
    mwf_logger.debug("info3=%s"%info)
    #print_table_of_levels()
    return render_template("mwf_browse.html", info=info,title=title)


@mwf.route("/<int:level>/<weight>/<character>/")
def render_maass_waveform_space(level,weight,character):
    title="Space of Maass waveforms"
    info=dict()
    return render_template("mwf_browse.html", info=info,title=title)


@mwf.route("/<int:level>/")
def render_maass_waveforms_for_one_group(level):
    DB = ConnectDB()
    res  = dict()
    info=dict()
    mwf_logger.debug("collections {0}".format(DB.collection_names()))
    for collection_name in DB.collection_names():
        res[collection_name] = list()
        C = pymongo.collection.Collection(DB,collection_name)
        mwf_logger.debug("Collection {0}".format(C))
        L = C.find({'Level':level,'Weight':0.0})
        for F in L:
            mwf_logger.debug("F: {0}".format(F))
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
        s+="<td valign='top'>"
        s+="<table><thead>"
        s+=" <tr><td valign='top'>Collection:"+name
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
    bread=[('Maass waveforms',url_for('.render_maass_waveforms'))]
    return render_template("mwf_one_group.html", info=info,title=title)


@mwf.route("/<objectid>",methods=['GET','POST'])
def render_one_maass_waveform(objectid):
    if objectid=='upload' or objectid=='Upload':
        title="Upload Maass waveforms"
        bread=[('Maass waveforms',url_for('render_maass_waveforms'))]
        if request.method <> "GET":
            info = get_args_upload()
            #file = request.files['file']
            print "INFO=",info
            info['allowed_entries']=allowed_entries
            remote_addr = request.remote_addr
            print "remote addr:",remote_addr
            check_data(info)
            print "check_data:"
            return render_template("mwf/mwf_upload_confirm.html", info=info,title=title,bread=bread)
        else:
            info = get_args_mwf()
            info['allowed_entries']=allowed_entries
            return render_template("mwf/mwf_upload.html", info=info,title=title,bread=bread)
        #return upload_maass_waveforms(info)
    else:
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
    info["friends"].append(["L-function","L/"+url_for('.render_one_maass_waveform',objectid=maass_id)])
    info["downloads"]= []
    #info["downloads"].append(["Maass form data",url_for('not_yet_implemented')])
    bread=[('Maass waveforms',url_for('.render_maass_waveforms'))]
    properties=[]
    data = get_maassform_by_id(maass_id)
    if not data.has_key('error'):
        [title,maass_info] =  set_info_for_maass_form(data)
        info["maass_data"] = maass_info
        #rint "data=",info["maass_data"]
        numc=data['num_coeffs']
        largs = [{'maass_id':maass_id,'number':k} for k in range(10,numc,50)]
        mwf_logger.error("numc={0}".format(numc))
        mwf_logger.error("largs={0}".format(largs))
        if(numc>0):
            info['coefficients']=ajax_once(make_table_of_coefficients,largs,text='more')
        else:
            info["maass_data"].append(['Coefficients',''])
            
            s='No coefficients in the database for this form!'
            info['coefficients']=s
        #info['list_spaces']=ajax_once(make_table_of_spaces_fixed_level,*largs,text='more',maass_id=maass_id)
        #info["coefficients"]=table_of_coefficients(
        info["credit"] = GetNameOfPerson(data['dbname'])
        level = data['Level']
        R = data['Eigenvalue']
        title="Maass waveforms on \(\Gamma_{0}(%s)\) with R=%s" %(level,R)
        ## We see if there is a plot file associated to this waveform
        if data.has_key('plot'):
            mwf_logger.error("file={0}".format(data['plot']))
    else:
        print "data=",data
        title="Could not find Maass this waveform in the database!"
        info['error']=data['error']


    bread=[('Maass waveforms',url_for('.render_maass_waveforms'))]
    return render_template("mwf_one_maass_form.html", info=info,title=title,bread=bread,properties=properties)

    

    


def render_search_results_wp(info,search):
    # res contains a lst of Maass waveforms
    print "info=",info
    print "Search:",search
    res =  search_for_eigenvalues(search)
    print "res=",res
    s="<table><tr>"
    if search.has_key('more'):
        info['more']=search['more']
        if info['more']:
            info['rec_start']=search['rec_start']+search['limit']
            info['limit']=search['limit']
    for name in res.keys():
        if len(res[name])==0 or name=='weights':
            continue
        s+="<td valign=\"top\">"
        s+="<table class=\"ntdata\"><thead>"
        s+=" <tr><td>Collection:"+name
        s+="     </td></tr>"
        s+="<tr><td>R</td><td>Level</td>\n"
        if len(res['weights'])>1:
            s+="<td>Weight</td>\n"
            s+="<td>Character</td>\n"
        s+"</tr></thead>"
        s+="<tbody>"
        i=0
        for rec in res[name]:
            print "rec=",rec
            R=my_get(rec,'Eigenvalue',None)
            N=my_get(rec,'Level','',str)
            k=my_get(rec,'Weight','',str)
            ch=my_get(rec,'character','',str)
            id=rec['_id']
            if is_odd(i):
                cl="odd"
            else:
                cl="even"
            i+=1
            url = url_for('mwf.render_one_maass_waveform',objectid=str(id),db=name)
            if len(res['weights'])>1:
                s+="<tr class=\"%s\"><td><a href=\"%s\">%s</a></td><td align=\"center\">%s</td><td>%s</td><td>%s</td></tr>\n" %(cl,url,R,N,k,ch)
            else:
                s+="<tr class=\"%s\"><td><a href=\"%s\">%s</a></td><td align=\"center\">%s</td></tr>\n" %(cl,url,R,N)
        s+="</tbody>"
        s+="</table>"
        s+="</td>"
    s+="</tr></table>"
    #print "S=",s
    info['table_of_eigenvalues']=s
    title="Search Results"
    bread=[('Maass waveforms',url_for('.render_maass_waveforms'))]
    return render_template("mwf_display_search_result.html", info=info,title=title,search=search,bread=bread)




"""
def write_eigenvalues(search,EVs,index):
        for i in search:
                link=url_for('.render_maass_form',id=str(i['_id']))
                EVs.append([i['Eigenvalue'],index,i['Symmetry'], link])
                index=index+1
        return index

def render_webpage(args):
        info = dict(args)
        maassID = args.get("id", None)#[0]
        eigenvalue = args.get("eigenvalue", None)
#       multicheck = args.get("multicheck", None)
        
        import base
        C = base.getDBConnection()
        DB = C.MaassWaveForm
        Collection = DB.HT
        Collection.ensure_index("Eigenvalue")
#       if show == 'all':
#               return render_template("maass_form.html", info=info)
#       else:
        EVs=[]
        index = 0
        info["credit"] = "Holger Then"
        info["info1"] = "Maass cusp forms for \(PSL(2,Z)\)"
        info["info2"] = "list of  \(r\)"
#, Eigenvalue \(\\lambda= \\frac{1}{4}+ r^2\)"

        info["info3"] = "Maass form"
        info["info4"] = "\(\\quad f(z)=const\\sum_{ n \\not= 0}a_n\\sqrt{y}K_{ir}(2\\pi|n|y)e^{2\\pi inx}\)"
        info["info5"] = "Eigenvalue"
#       info["info6"] = "\( \\quad \\lambda=r^2 + \\frac{1}{4} \\ , \\quad r= \\ \) {{ info.eigenvalue  }}  "
#       info["info7"] = "Coefficients"
#       info["info8"] = "\\quad normalization \(a_1=1\)"
#       info["info9"] = "\\quad symmetry \(a_{-1}=\\%c1\)"
#       info["info10"]= "\\quad multiplicity \(a_{mp}=a_{m}a_{p}-a_{m/p}\)\\quad where \(a_{m/p}=0\) if \(p\\not|m\)"
#       info["info11"]= "\\quad prime coefficients \(a_2= \\%.5f \\quad a_3= \\%.5f \\quad a_5= \\%.5f \\quad a_7= \\%.5f \\quad \\ldots\)"

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
                info["link"] = url_for('.render_maass_form')
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
                info["check"].append(["Hecke relation",url_for('.render_maass_form', multicheck=maassID)])
                info["check"].append(["Ramanujan-Petersson conjecture",url_for('.render_maass_form', RPconj=maassID)])
                info["friends"]= []
                info["friends"].append(["L-function",url_for('.render_maass_form', Lfunction=maassID)])
#               info["learnmore"]= []
#               info["learnmore"].append(["Wiki","http://wiki.l-functions.org/ModularForms/MaassForms"])
#               info["learnmore"].append(["Literature","http://arxiv.org/abs/math-ph/0305047"])
                info["downloads"]= []
                info["downloads"].append(["Maass form data",url_for('.render_maass_form', download=maassID)])
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
