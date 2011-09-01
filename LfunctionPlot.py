from pymongo import Connection
import logging
import math
import datetime
from flask import url_for, make_response
import base
from classical_modular_forms.backend.web_modforms import *
#import runningWindow



## ============================================
## Returns the id for the L-function of given group, level, sign and
## spectral parameters. (Used for Maass forms and works for GL(n) and GSp(4).)
## This id is used in the database as '_id' of the L-function document.
## NOTE: SHOULD CHANGE THIS TO INCLUDE THE SIGN IN THE ID
## ============================================
def createLid(group, objectName, level, sign, parameters):
    ans = group + objectName + '_' + str(level) + '_' + str(sign)
    if group == 'GSp4':
        knownParameters = 2
    else:
        knownParameters = 1
    for index, item in enumerate(parameters):
        if index<len(parameters)-knownParameters:
            ans += '_'
            toAdd = str(item)
            ans += toAdd
    return ans

## ============================================
## Returns all the html including links to the svg-files for Maass forms
## of given degree (gives output for degree 3 and 4). Data is fetched from
## the database.
## ============================================
def getAllMaassGraphHtml(degree):
    conn = base.getDBConnection()
    db = conn.Lfunction
    collection = db.LemurellMaassHighDegree
    groups = collection.group(['group'],{ 'degree': degree },
                              {'csum': 0},
                              'function(obj,prev) { prev.csum += 1; }')

    ans = ""
    for docGroup in groups:
        g = docGroup['group']
##        logging.debug(g)
        ans += getGroupHtml(g)
        levels = collection.group(['level'],{ 'degree': degree ,'group': g },
                              {'csum': 0},
                              'function(obj,prev) { prev.csum += 1; }')
##        logging.debug(levels)
        for docLevel in levels:
            l = math.trunc(docLevel['level'])
            logging.info(l)
            signs = collection.group(['sign'],{ 'degree': degree ,'group': g
                                                ,'level': l},
                              {'csum': 0},
                              'function(obj,prev) { prev.csum += 1; }')
            for docSign in signs:
                s = docSign['sign']
                logging.info('sign: ' + s)
                ans += getOneGraphHtml(g,l,s)
                    
    return(ans)

## ============================================
## Returns the header and information about the Gamma-factors for the
## group with name group (in html and MathJax)
## ============================================
def getGroupHtml(group):
    if group == 'GSp4':
        ans = "<h3>Maass cusp forms for GSp(4)</h3>\n"
        ans += "<div>These satisfy a functional equation with \\(\\Gamma\\)-factors\n"
        ans += "\\begin{equation}"
        ans += "\\Gamma_R(s + i \\mu_1)"
        ans += "\\Gamma_R(s + i \\mu_2)"
        ans += "\\Gamma_R(s - i \\mu_1)"
        ans += "\\Gamma_R(s - i \\mu_2)"
        ans += "\\end{equation}\n"
        ans += "with \\(0 \\le \\mu_2 \\le \\mu_1\\).</div>\n"

    elif group == 'GL4':
        ans = "<h3>Maass cusp forms for GL(4)</h3>\n"
        ans += "<div>These satisfy a functional equation with \\(\\Gamma\\)-factors\n"
        ans += "\\begin{equation}"
        ans += "\\Gamma_R(s + i \\mu_1)"
        ans += "\\Gamma_R(s + i \\mu_2)"
        ans += "\\Gamma_R(s - i \\mu_3)"
        ans += "\\Gamma_R(s - i \\mu_4)"
        ans += "\\end{equation}\n"
        ans += "where \\(\\mu_1 + \\mu_2 = \\mu_3 + \\mu_4\\).</div>\n"

    elif group == 'GL3':
        ans = "<h3>Maass cusp forms for GL(3)</h3>\n"
        ans += "<div>These satisfy a functional equation with \\(\\Gamma\\)-factors\n"
        ans += "\\begin{equation}"
        ans += "\\Gamma_R(s + i \\mu_1)"
        ans += "\\Gamma_R(s + i \\mu_2)"
        ans += "\\Gamma_R(s - i \\mu_3)"
        ans += "\\end{equation}\n"
        ans += "where \\(\\mu_1 + \\mu_2 = \\mu_3\\).</div>\n"

    else:
        ans = ""
        
    return(ans)

## ============================================
## Returns the header, some information and the url for the svg-file for
## the L-functions of the Maass forms for given group, level and
## sign (of the functional equation) (in html and MathJax)
## ============================================
def getOneGraphHtml(group, level, sign):
    ans = ("<h4>Maass cusp forms of level " + str(level) + " and sign " 
          + str(sign) + "</h4>\n")
    ans += "<div>The dots in the plot correspond to \\((\\mu_1,\\mu_2)\\) "
    ans += "in the \\(\\Gamma\\)-factors. These have been found by a computer "
    ans += "search. Click on any of the dots to get detailed information about "
    ans += "the L-function.</div>\n<br />"
    graphInfo = getGraphInfo(group, level, sign)
    ans += ("<embed src='" + graphInfo['src'] + "' width='" + str(graphInfo['width']) + 
           "' height='" + str(graphInfo['height']) +
            "' type='image/svg+xml' " +
            "pluginspage='http://www.adobe.com/svg/viewer/install/'/>\n")
    ans += "<br/>\n"
        
    return(ans)
    
## ============================================
## Returns the url and width and height of the svg-file for
## the L-functions of the Maass forms for given group, level and
## sign (of the functional equation).
## ============================================
def getGraphInfo(group, level, sign):
    (width,height) = getWidthAndHeight(group, level, sign)
##    url = url_for('browseGraph',group=group, level=level, sign=sign)
    url = ('/browseGraph?group=' + group + '&level=' + str(level)
           + '&sign=' + sign)
    url =url.replace('+', '%2B')  ## + is a special character in urls
    ans = {'src': url}
    ans['width']= width
    ans['height']= height

    return(ans)

## ============================================
## Returns the url and width and height of the svg-file for
## the L-functions of holomorphic cusp form.
## ============================================
def getGraphInfoHolo(Nmin, Nmax, kmin, kmax):
#    (width,height) = getWidthAndHeight(group, level, sign)
    xfactor = 90
    yfactor = 30
    extraSpace = 30

    (width,height) = (extraSpace + xfactor*(Nmax), extraSpace + yfactor*(kmax))
##    url = url_for('browseGraph',group=group, level=level, sign=sign)
    url = ('/browseGraphHolo?Nmin=' + str(Nmin) + '&Nmax=' + str(Nmax)
           + '&kmin=' + str(kmin) + '&kmax=' + str(kmax))
#    url =url.replace('+', '%2B')  ## + is a special character in urls
    ans = {'src': url}
    ans['width']= width
    ans['height']= height

    return(ans)


## ============================================
## Returns the width and height of the svg-file for
## the L-functions of the Maass forms for given group, level and
## sign (of the functional equation).
## ============================================
def getWidthAndHeight(group, level, sign):
    conn = base.getDBConnection()
    db = conn.Lfunction
    collection = db.LemurellMaassHighDegree
    LfunctionList = collection.find({'group':group, 'level': level, 'sign': sign}
                                    , {'_id':True})
    index1 = 2
    index2 = 3

    xfactor = 20
    yfactor = 20
    extraSpace = 40

    xMax = 0
    yMax = 0
    for l in LfunctionList:
        splitId = l['_id'].split("_")
        if float(splitId[index1])>xMax:
            xMax = float(splitId[index1])
        if float(splitId[index2])>yMax:
            yMax = float(splitId[index2])

    xMax = math.ceil(xMax)
    yMax = math.ceil(yMax)
    width = int(xfactor *xMax + extraSpace)
    height = int(yfactor *yMax + extraSpace)

    return( (width, height) )


## ============================================
## Returns the contents (as a string) of the svg-file for
## the L-functions of the Maass forms for given group, level and
## sign (of the functional equation).
## ============================================
def paintSvgFile(group, level, sign):
    conn = base.getDBConnection()
    db = conn.Lfunction
    collection = db.LemurellMaassHighDegree
    LfunctionList = collection.find({'group':group, 'level': level, 'sign': sign}
                                    , {'_id':True})
    index1 = 2
    index2 = 3

    xfactor = 20
    yfactor = 20
    extraSpace = 20
    ticlength = 4
    radius = 3

    ans = "<svg  xmlns='http://www.w3.org/2000/svg'"
    ans += " xmlns:xlink='http://www.w3.org/1999/xlink'>\n"

    paralist = []
    xMax = 0
    yMax = 0
    for l in LfunctionList:
        splitId = l['_id'].split("_")
        paralist.append((splitId[index1],splitId[index2],l['_id']))
        if float(splitId[index1])>xMax:
            xMax = float(splitId[index1])
        if float(splitId[index2])>yMax:
            yMax = float(splitId[index2])

    xMax = int(math.ceil(xMax))
    yMax = int(math.ceil(yMax))
    width = xfactor *xMax + extraSpace
    height = yfactor *yMax + extraSpace

    ans += paintCS(width, height, xMax, yMax, xfactor, yfactor, ticlength)

    for (x,y,lid) in paralist:
        linkurl = "/L/ModularForm/" + group + "/Q/maass?source=db&amp;id=" + lid
        ans += "<a xlink:href='" + linkurl + "' target='_top'>\n"
        ans += "<circle cx='" + str(float(x)*xfactor)[0:7]
        ans += "' cy='" +  str(height- float(y)*yfactor)[0:7]
        ans += "' r='" + str(radius)
        ans += "' style='fill:rgb(0,204,0)'>"
        ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
        ans += "</circle></a>\n"

    ans += "</svg>"
    
    return(ans)

## ============================================
## Returns the svg-code for a simple coordinate system.
## width = width of the system
## height = height of the system
## xMax = maximum in first (x) coordinate
## yMax = maximum in second (y) coordinate
## xfactor = the number of pixels per unit in x
## yfactor = the number of pixels per unit in y
## ticlength = the length of the tickmarks
## ============================================
def paintCS(width, height, xMax, yMax, xfactor, yfactor,ticlength):
    xmlText = ("<line x1='0' y1='" + str(height) + "' x2='" +
               str(width) + "' y2='" + str(height) +
               "' style='stroke:rgb(0,0,0);'/>\n")
    xmlText = xmlText + ("<line x1='0' y1='" + str(height) +
                         "' x2='0' y2='0' style='stroke:rgb(0,0,0);'/>\n")
    for i in range( 1,  xMax + 1):
        xmlText = xmlText + ("<line x1='" + str(i*xfactor) + "' y1='" +
                             str(height - ticlength) + "' x2='" +
                             str(i*xfactor) + "' y2='" + str(height) +
                             "' style='stroke:rgb(0,0,0);'/>\n")

    for i in range( 5,  xMax + 1, 5):
        xmlText = xmlText + ("<text x='" + str(i*xfactor - 6) + "' y='" +
                             str(height - 2 * ticlength) +
                             "' style='fill:rgb(102,102,102);font-size:11px;'>"
                             + str(i) + "</text>\n")
        
        xmlText = xmlText + ("<line y1='0' x1='" + str(i*xfactor) +
                         "' y2='" + str(height) + "' x2='" +
                         str(i*xfactor) +
                         "' style='stroke:rgb(204,204,204);stroke-dasharray:3,3;'/>\n")

    for i in range( 1,  yMax + 1):
        xmlText = xmlText + ("<line x1='0' y1='" +
                             str(height - i*yfactor) + "' x2='" +
                             str(ticlength) + "' y2='" +
                             str(height - i*yfactor) +
                             "' style='stroke:rgb(0,0,0);'/>\n")

    for i in range( 5,  yMax + 1, 5):
        xmlText = xmlText + ("<text x='5' y='" +
                             str(height - i*yfactor + 3) +
                             "' style='fill:rgb(102,102,102);font-size:11px;'>" +
                             str(i) + "</text>\n")

        xmlText = xmlText + ("<line x1='0' y1='" +
                         str(height - i*yfactor) + "' x2='" + str(width) +
                         "' y2='" + str(height - i*yfactor) +
                         "' style='stroke:rgb(204,204,204);stroke-dasharray:3,3;'/>\n")

    return(xmlText)

## ============================================
## Returns the svg-code for a simple coordinate system.
## width = width of the system
## height = height of the system
## xMax = maximum in first (x) coordinate
## yMax = maximum in second (y) coordinate
## xfactor = the number of pixels per unit in x
## yfactor = the number of pixels per unit in y
## ticlength = the length of the tickmarks
## ============================================
def paintCSHolo(width, height, xMax, yMax, xfactor, yfactor,ticlength):
    xmlText = ("<line x1='0' y1='" + str(height) + "' x2='" +
               str(width) + "' y2='" + str(height) +
               "' style='stroke:rgb(0,0,0);'/>\n")
    xmlText = xmlText + ("<line x1='0' y1='" + str(height) +
                         "' x2='0' y2='0' style='stroke:rgb(0,0,0);'/>\n")
    for i in range( 1,  xMax + 1):
        xmlText = xmlText + ("<line x1='" + str(i*xfactor) + "' y1='" +
                             str(height - ticlength) + "' x2='" +
                             str(i*xfactor) + "' y2='" + str(height) +
                             "' style='stroke:rgb(0,0,0);'/>\n")

    for i in range( 1,  xMax + 1, 1):
        digitoffset = 6
        if i < 10:
           digitoffset = 3
        xmlText = xmlText + ("<text x='" + str(i*xfactor - digitoffset) + "' y='" +
                             str(height - 2 * ticlength) +
                             "' style='fill:rgb(102,102,102);font-size:11px;'>"
                             + str(i) + "</text>\n")

        xmlText = xmlText + ("<line y1='0' x1='" + str(i*xfactor) +
                         "' y2='" + str(height) + "' x2='" +
                         str(i*xfactor) +
                         "' style='stroke:rgb(204,204,204);stroke-dasharray:3,3;'/>\n")

    for i in range( 1,  yMax + 1):
        xmlText = xmlText + ("<line x1='0' y1='" +
                             str(height - i*yfactor) + "' x2='" +
                             str(ticlength) + "' y2='" +
                             str(height - i*yfactor) +
                             "' style='stroke:rgb(0,0,0);'/>\n")

    for i in range( 2,  yMax + 1, 2):
        xmlText = xmlText + ("<text x='5' y='" +
                             str(height - i*yfactor + 3) +
                             "' style='fill:rgb(102,102,102);font-size:11px;'>" +
                             str(i) + "</text>\n")

        if i%4==0 :  #  put dahes every four units
           xmlText = xmlText + ("<line x1='0' y1='" +
                         str(height - i*yfactor) + "' x2='" + str(width) +
                         "' y2='" + str(height - i*yfactor) +
                         "' style='stroke:rgb(204,204,204);stroke-dasharray:3,3;'/>\n")

    return(xmlText)


## ============================================
## Returns the contents (as a string) of the svg-file for
## the L-functions of holomorphic cusp forms.
## ============================================
def paintSvgHolo(Nmin,Nmax,kmin,kmax):
    xfactor = 90
    yfactor = 30
    extraSpace = 20
    ticlength = 4
    radius = 3.3
    xdotspacing = 0.11  # horizontal spacing of dots
    ydotspacing = 0.28  # vertical spacing of dots
    colourplus = "rgb(0,0,255)"
    colourminus = "rgb(204,0,0)"
    maxdots = 5  # max number of dots to display

    ans = "<svg  xmlns='http://www.w3.org/2000/svg'"
    ans += " xmlns:xlink='http://www.w3.org/1999/xlink'>\n"

    xMax = int(Nmax)
    yMax = int(kmax)
    width = xfactor *xMax + extraSpace
    height = yfactor *yMax + extraSpace

    ans += paintCSHolo(width, height, xMax, yMax, xfactor, yfactor, ticlength)

    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
#loop over levels and weights
    for x in range(int(Nmin), int(Nmax) + 1):  # x is the level
        logging.info("level = %s" % x)
        for y in range(int(kmin), int(kmax) + 1, 2):  # y is the weight 
           logging.info("  weight = %s"%y)
           lid = "(" + str(x) + "," + str(y) + ")"
           linkurl = "/L/ModularForm/" + "GL2/Q/holomorphic?weight=" + str(y) +"&amp;level=" + str(x) + "&amp;character=0"
           WS = WebModFormSpace(y,x)
           numlabels = len(WS.galois_decomposition())  # one label per Galois orbit
           thelabels = alphabet[0:numlabels]    # list of labels for the Galois orbits for weight y, level x
           countplus = 0   # count how many Galois orbits have sign Plus (+ 1)
           countminus = 0   # count how many Galois orbits have sign Minus (- 1)
           ybaseplus = y  # baseline y-coord for plus cases
           ybaseminus = y  # baseline y-coord for minus cases
           numpluslabels=0
           numminuslabels=0
           for label in thelabels:  # looping over Galois orbit
               linkurl = "/L/ModularForm/" + "GL2/Q/holomorphic?weight=" + str(y) +"&amp;level=" + str(x) + "&amp;character=0"
               linkurl += "&amp;label=" + label
               MF = WebNewForm(y,x,0,label)   # one of the Galois orbits for weight y, level x
               numberwithlabel = MF.degree()  # number of forms in the Galois orbit
               if x == 1: # For level 1, the sign is always plus
                  signfe = 1
               else:
                  frickeeigenvalue = MF.atkin_lehner_eigenvalues()[x] # gives Fricke eigenvalue
                  signfe = frickeeigenvalue * (-1)**float(y/2)  # sign of functional equation
               xbase = x - signfe * (xdotspacing/2.0) 

               if signfe > 0:  # go to right in BLUE if plus
                  ybase = ybaseplus
                  ybaseplus += ydotspacing
                  thiscolour = colourplus
                  numpluslabels += 1
               else:  # go to the left in RED of minus
                  ybase = ybaseminus
                  ybaseminus += ydotspacing
                  thiscolour = colourminus
                  numminuslabels += 1

               if numberwithlabel > maxdots:  # if more than maxdots in orbit, use number as symbol
                   xbase += 1.5 * signfe * xdotspacing
                   if signfe < 0:   # move over more to position numbers on minus side.
                      xbase += signfe * xdotspacing
                   ybase += -0.5 * ydotspacing
                   if (signfe > 0 and numpluslabels>1) or (signfe < 0 and numminuslabels>1):
                       ybase += ydotspacing
                   ans += "<a xlink:href='" + url_for('not_yet_implemented') + "' target='_top'>\n"
#                  ans += "<a xlink:href='" + linkurl + "&amp;number=" + str(number) + "' target='_top'>\n"
#   url_for("not_yet_implemented")
                   ans += ("<text x='" + str(float(xbase)*xfactor)[0:7] + "' y='" +
                             str(height- float(ybase)*yfactor)[0:7] +
                             "' style='fill:" + thiscolour + ";font-size:14px;font-weight:bold;'>"
                             + str(numberwithlabel) + "</text>\n")
                   ans += "</a>\n"
                   if signfe < 0:
                      ybaseminus +=  1.5 * ydotspacing
                   else:
                      ybaseplus +=  1.5 * ydotspacing
               else:  # otherwise, use one dot per form in orbit, connected with a line 
                 if numberwithlabel > 1:  # join dots if there are at least two
# add lines first and then dots to prevent line from hiding link
                   firstcenterx = xbase + signfe * xdotspacing
                   firstcentery = ybase 
                   lastcenterx = xbase + (numberwithlabel * signfe * xdotspacing)
                   lastcentery = ybase
                   ans += "<line x1='%s'" %  str(float(firstcenterx)*xfactor)[0:7]
                   ans += "y1='%s'" % str(float(height - firstcentery*yfactor))[0:7]
                   ans += "x2='%s'" % str(float(lastcenterx)*xfactor)[0:7]
                   ans += "y2='%s'" % str(float(height - lastcentery*yfactor))[0:7]
                   ans += "style='stroke:%s;stroke-width:2.4'/>" % thiscolour 
                 for number in range(0,numberwithlabel):
                   xbase += signfe * xdotspacing
                   ans += "<a xlink:href='" + linkurl + "&amp;number=" + str(number) + "' target='_top'>\n"
                   ans += "<circle cx='" + str(float(xbase)*xfactor)[0:7]
                   ans += "' cy='" +  str(height- float(ybase)*yfactor)[0:7]
                   ans += "' r='" + str(radius)
                   ans += "' style='fill:"+ thiscolour +"'>"
                   ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                   ans += "</circle></a>\n"

    ans += "</svg>"

    logging.info(ans)
 
    return ans

## ============================================
## Returns the header, some information and the url for the svg-file for
## the L-functions of holomorphic cusp forms.
## ============================================
def getOneGraphHtmlHolo(Nmin, Nmax, kmin, kmax):
    ans = "<div>These L-functions have a functional equation of the form \n<br/>"
    ans += "\\begin{equation}\n \\Lambda(s) := N^{s/2} \\Gamma_C"
    ans += "\\left(s + \\frac{k-1}{2} \\right) L(s) "
    ans += "=\\pm \\Lambda(1-s)\n\\end{equation}\n<br/>"
    ans += "If \\(L(s) = \sum a_n n^{-s} \) then \(a_n n^{\frac{k-1}{2}} \) "
    ans += "is an algebraic integer. <p/> </div>\n"
    ans += "<div>This plot shows \((N,k)\) for such L-functions. "
    ans += "The color indicates the sign of the functional equation.  "
    ans += "The horizontal grouping indicates the degree of the field containing "
    ans += "the arithmetically normalized coefficients.\n<br/><br/></div>\n"
    graphInfo = getGraphInfoHolo(Nmin, Nmax, kmin, kmax)
#    ans += ("<embed src='" + graphInfo['src'] + "' width='" + str(graphInfo['width']) +
    ans += ("<embed src='/static/images/browseGraphHolo_22_14_3a.svg' width='" + str(graphInfo['width']) +
           "' height='" + str(graphInfo['height']) +
            "' type='image/svg+xml' " +
            "pluginspage='http://www.adobe.com/svg/viewer/install/'/>\n")
    ans += "<br/>\n"

    return(ans)
   


## ============================================
## Returns the url and width and height of the svg-file for
## Dirichlet L-functions.
## ============================================
def getGraphInfoChar(min_cond, max_cond, min_order, max_order):
#    (width,height) = getWidthAndHeight(group, level, sign)
    xfactor = 70
    yfactor = 30
    extraSpace = 30
    (width,height) = (2*extraSpace + xfactor*(max_order), 2*extraSpace + yfactor*(max_cond))
##    url = url_for('browseGraph',group=group, level=level, sign=sign)
    url = ('/browseGraphChar?min_cond=' + str(min_cond) + '&max_cond=' + str(max_cond) + '&min_order=' + str(min_order) + '&max_order=' + str(max_order))
#    url =url.replace('+', '%2B')  ## + is a special character in urls
    ans = {'src': url}
    ans['width']= width
    ans['height']= height
    return ans


## ============================================
## Returns the svg-code for a simple coordinate system.
## width = width of the system
## height = height of the system
## xMax = maximum in first (x) coordinate
## yMax = maximum in second (y) coordinate
## xfactor = the number of pixels per unit in x
## yfactor = the number of pixels per unit in y
## ticlength = the length of the tickmarks
## ============================================
def paintCSChar(width, height, xMax, yMax, xfactor, yfactor,ticlength):
    xmlText = ("<line x1='0' y1='" + str(height) + "' x2='" +
               str(width) + "' y2='" + str(height) +
               "' style='stroke:rgb(0,0,0);'/>\n")
    xmlText = xmlText + ("<line x1='0' y1='" + str(height) +
                         "' x2='0' y2='0' style='stroke:rgb(0,0,0);'/>\n")
    for i in range( 1,  xMax + 1):
        xmlText = xmlText + ("<line x1='" + str(i*xfactor) + "' y1='" +
                             str(height - ticlength) + "' x2='" +
                             str(i*xfactor) + "' y2='" + str(height) +
                             "' style='stroke:rgb(0,0,0);'/>\n")

    for i in range( 1,  xMax + 1, 1):
        digitoffset = 6
        if i < 10:
           digitoffset = 3
        xmlText = xmlText + ("<text x='" + str(i*xfactor - digitoffset) + "' y='" +
                             str(height - 2 * ticlength) +
                             "' style='fill:rgb(102,102,102);font-size:11px;'>"
                             + str(i) + "</text>\n")

        xmlText = xmlText + ("<line y1='0' x1='" + str(i*xfactor) +
                         "' y2='" + str(height) + "' x2='" +
                         str(i*xfactor) +
                         "' style='stroke:rgb(204,204,204);stroke-dasharray:3,3;'/>\n")

    for i in range( 1,  yMax + 1):
        xmlText = xmlText + ("<line x1='0' y1='" +
                             str(height - i*yfactor) + "' x2='" +
                             str(ticlength) + "' y2='" +
                             str(height - i*yfactor) +
                             "' style='stroke:rgb(0,0,0);'/>\n")

    for i in range( 2,  yMax + 1, 2):
        xmlText = xmlText + ("<text x='5' y='" +
                             str(height - i*yfactor + 3) +
                             "' style='fill:rgb(102,102,102);font-size:11px;'>" +
                             str(i) + "</text>\n")

        if i%4==0 :  #  put dahes every four units
           xmlText = xmlText + ("<line x1='0' y1='" +
                         str(height - i*yfactor) + "' x2='" + str(width) +
                         "' y2='" + str(height - i*yfactor) +
                         "' style='stroke:rgb(204,204,204);stroke-dasharray:3,3;'/>\n")

    return xmlText

## =============================================
## helper function that organizes the Dirichlet characters
## by order.  It returns a dict of characters where each entry
## is a list of pairs. In particular char_dict[(N, order)] = [(ii,parity)]
## where N is the conductor of the character with index ii in Sage's 
## ordering, and is even if parity is 0 and 1 otherwise.
## =============================================


def reindex_characters(min_mod, max_mod):
    from sage.sets.set import Set
    char_dict = {}
    for N in range(min_mod, max_mod + 1):
        GG = list(DirichletGroup(N))
        G = []
        for g in GG:
            if g.is_primitive():
                G.append(g)
        for ii in range(len(G)):
            chi = G[ii]
            chib = chi.bar()
            ord = chi.order()
            parity = 1 # even
            if chi.is_odd():
                parity = -1
            if ord < 13:
                if chi == chib: #chi is real
                    try:
                        char_dict[(ord, N)].append((ii, parity))
                    except KeyError:
                        char_dict[(ord, N)] = []
                        char_dict[(ord, N)].append((ii, parity))
                else: #chi is complex 
                    jj = G.index(chib)
                    try:
                        char_dict[(ord, N, "i")].append((ii,jj,parity))
                    except KeyError:
                        char_dict[(ord, N, "i")] = []
                        char_dict[(ord, N, "i")].append((ii,jj,parity))
            else:
                if chi == chib: #chi is real
                    try:
                        char_dict[(13, N)].append((ii, parity))
                    except KeyError:
                        char_dict[(13, N)] = []
                        char_dict[(13, N)].append((ii, parity))
                else: #chi is complex 
                    jj = G.index(chib)
                    try:
                        char_dict[(13, N, "i")].append((ii,jj,parity))
                    except KeyError:
                        char_dict[(13, N, "i")] = []
                        char_dict[(13, N, "i")].append((ii,jj,parity))
    cd = {} 
    for k in char_dict:
        if len(k) == 2:
            cd[k] = char_dict[k]

    for k in char_dict:
        if len(k) == 3:
            ll = char_dict[k]
            for a,b,c in ll:
                ll.remove((b,a,c))
            try:
                cd[(k[0],k[1])].extend(ll) 
            except KeyError:
                cd[(k[0],k[1])] = ll                         
    return cd

'''
def reindex_characters(min_cond, max_cond):
    from sage.modular.dirichlet import DirichletGroup
    char_dict = {}
    for N in range(min_cond, max_cond + 1):
        DGN = DirichletGroup(N)
        for ii in range(len(DGN)):
            chi = DGN[ii]
            ord = chi.order()
            parity = 1 # even
            if chi.is_odd():
                parity = -1 #odd
            if ord < 7:
                try:
                    char_dict[(ord,N)].append((ii,parity))
                except KeyError:
                    char_dict[(ord,N)] = []
                    char_dict[(ord,N)].append((ii,parity))
            else:
                try:
                    char_dict[(7,N)].append((ii,parity))
                except KeyError:
                    char_dict[(7,N)] = []
                    char_dict[(7,N)].append((ii,parity))
    return char_dict
'''


## ============================================
## Returns the contents (as a string) of the svg-file for
## the Dirichlet L-functions.
## ============================================

def paintSvgChar(min_cond,max_cond,min_order,max_order):
    xfactor = 70
    yfactor = 30
    extraSpace = 20
    ticlength = 4
    radius = 3
    xdotspacing = 0.10  # horizontal spacing of dots
    ydotspacing = 0.16  # vertical spacing of dots
    colourplus = "rgb(0,0,255)"
    colourminus = "rgb(204,0,0)"
    maxdots = 1  # max number of dots to display

    ans = "<svg  xmlns='http://www.w3.org/2000/svg'"
    ans += " xmlns:xlink='http://www.w3.org/1999/xlink'>\n"

    xMax = int(max_order)
    yMax = int(max_cond)
    width = xfactor *xMax + 3*extraSpace
    height = yfactor *yMax + 3*extraSpace

    ans += paintCSChar(width, height, xMax, yMax, xfactor, yfactor, ticlength)

    #loop over orders and conductors
    cd = reindex_characters(min_cond, max_cond)
    for (x,y) in cd:
        lid = "(" + str(x) + "," + str(y) + ")"
        linkurl = "/L/" + "Character/Dirichlet/" + str(y) 
        counteven = 0   # count how many characters are even
        countodd = 0   # count how many characters are odd
        xbaseplus = x - (xdotspacing/2.0)
        xbaseminus = x + (xdotspacing/2.0)
        for ii in range(len(cd[(x,y)])):
            current = cd[(x,y)][ii]
            if len(current) == 2:
                parity = current[1]
                if parity == 1:
                    xbaseplus += xdotspacing
                    thiscolour = colourplus
                    counteven += 1
                    ans += "<a xlink:href='" + linkurl + "/" + str(current[0]) + "' target='_top'>\n"
                    ans += "<circle cx='" + str(float(xbaseplus)*xfactor)[0:7]
                    ans += "' cy='" +  str(height-(y*yfactor))[0:7]
                    ans += "' r='" + str(radius)
                    ans += "' style='fill:"+ thiscolour +"'>"
                    ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                    ans += "</circle></a>\n"
    
                else:
                    xbaseminus -= xdotspacing
                    thiscolour = colourminus
                    countodd += 1
                    ans += "<a xlink:href='" + linkurl + "/" + str(current[0]) + "' target='_top'>\n"
                    ans += "<circle cx='" + str(float(xbaseminus)*xfactor)[0:7]
                    ans += "' cy='" +  str(height-(y*yfactor))[0:7]
                    ans += "' r='" + str(radius)
                    ans += "' style='fill:"+ thiscolour +"'>"
                    ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                    ans += "</circle></a>\n"
            if len(current) == 3:
                parity = cd[(x,y)][ii][2]
                if parity == 1:
                    xbaseplus += xdotspacing
                    thiscolour = colourplus
                    counteven += 1
                    ans += "<a xlink:href='" + linkurl + "/" + str(current[0]) + "' target='_top'>\n"
                    ans += "<circle cx='" + str(float(xbaseplus)*xfactor)[0:7]
                    ans += "' cy='" +  str(height-(y*yfactor))[0:7]
                    ans += "' r='" + str(radius)
                    ans += "' style='fill:"+ thiscolour +"'>"
                    ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                    ans += "</circle></a>\n"
                    ans += "<a xlink:href='" + linkurl + "/" + str(current[1]) + "' target='_top'>\n"
                    ans += "<circle cx='" + str(float(xbaseplus)*xfactor)[0:7]
                    ans += "' cy='" +  str(height-(y*yfactor)+ 2*radius)[0:7]
                    ans += "' r='" + str(radius)
                    ans += "' style='fill:"+ thiscolour +"'>"
                    ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                    ans += "</circle></a>\n"
                else:
                    xbaseminus -= xdotspacing
                    thiscolour = colourminus
                    countodd += 1
                    ans += "<a xlink:href='" + linkurl + "/" + str(cd[(x,y)][ii][0]) + "' target='_top'>\n"
                    ans += "<circle cx='" + str(float(xbaseminus)*xfactor)[0:7]
                    ans += "' cy='" +  str(height-(y*yfactor))[0:7]
                    ans += "' r='" + str(radius)
                    ans += "' style='fill:"+ thiscolour +"'>"
                    ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                    ans += "</circle></a>\n"
                    ans += "<a xlink:href='" + linkurl + "/" + str(cd[(x,y)][ii][1]) + "' target='_top'>\n"
                    ans += "<circle cx='%s'" % str(float(xbaseminus)*xfactor)[0:7]
                    ans += "cy='%s'" %  str(height-(y*yfactor)+ 2*radius)[0:7]
                    ans += "r='%s'" % radius
                    ans += "style='fill:%s'>" % thiscolour 
                    ans += "<title>" + str((x,y)).replace("u", "").replace("'", "") + "</title>"
                    ans += "</circle></a>\n"

    ans += "</svg>"


    return ans 



## ============================================
## Returns the header, some information and the url for the svg-file for
## the Dirichlet L-functions.
## ============================================
def getOneGraphHtmlChar(min_cond, max_cond, min_order, max_order):
    ans = "<div>These L-functions have a functional equation of the form ...</div>\n"
    graphInfo = getGraphInfoChar(min_cond, max_cond, min_order, max_order)
    logging.info("graphInfo %s" % graphInfo)
#    ans += ("<embed src='" + graphInfo['src'] + "' width='" + str(graphInfo['width']) +
    ans += ("<embed src='/static/images/browseGraphChar_1_35.svg' width='" + str(graphInfo['width']) +
           "' height='" + str(graphInfo['height']) +
            "' type='image/svg+xml' " +
            "pluginspage='http://www.adobe.com/svg/viewer/install/'/>\n")
    ans += "<br/>\n"

    return(ans)
