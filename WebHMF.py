import math
import logging

class WebHMF:
    """Class for presenting a Hilbert modular form on a web page

    """
     
    def __init__(self, dict):
        self.type = dict['type']
        self.coefficient_period = 0
        self.poles = []
        self.residues = []
        self.kappa_fe = []
        self.lambda_fe =[]
        self.mu_fe = []
        self.nu_fe = []
        self.langlands = True
        
        if self.type=='lcalcurl':
            import urllib
            self.url = dict['url']
            self.contents = urllib.urlopen(self.url).read()
            self.parseLcalcfile()

        elif self.type=='lcalcfile':
            self.contents = dict['filecontents']
            self.parseLcalcfile()

        elif self.type=='modularform':
            self.level = dict['level']
            self.weight = dict['weight']
            logging.info('My level is ' + self.level + ' and my weight is + ' self.weight)
             
        else:
            raise KeyError 

        """
        self.coefficient_type: 1 = integer, 2 = double, 3 = complex
        self.ceofficient_period:  0 = non-periodic
        self.sageLfunction = lc.Lfunction_C(self.title, self.coefficient_type, self.dirichlet_coefficients, self.ceofficient_period, self.Q_fe, self.sign , self.kappa_fe, self.lambda_fe ,self.poles, self.residues)
        """


    def parseLcalcfile(self):
        lines = self.contents.split('\n',6)
        self.coefficient_type = int(lines[0])
        self.quasidegree = int(lines[4])
        lines = self.contents.split('\n',8+2*self.quasidegree)
        self.Q_fe = float(lines[5+2*self.quasidegree])
        self.sign = pair2complex(lines[6+2*self.quasidegree])

        for i in range(self.quasidegree):
            localdegree = float(lines[5+2*i])
            self.kappa_fe.append(localdegree)
            locallambda = pair2complex(lines[6+2*i])
            self.lambda_fe.append(locallambda)
            if math.fabs(localdegree-0.5)<0.00001:
                self.mu_fe.append(2*locallambda)
            elif math.fabs(localdegree-1)<0.00001:
                self.nu_fe.append(locallambda)
            else:
                self.nu_fe.append(locallambda)
                self.langlands = False

        """ Do poles here later
        """
        
        self.degree = round(2*sum(self.kappa_fe))
        self.level = round(math.pi**self.degree * 4**len(self.nu_fe) * self.Q_fe**2 )

        self.dirichlet_coefficients = splitcoeff(lines[-1])
        
	originalfile = re.match(".*/([^/]+)$", self.url)
        originalfile = originalfile.group(1)
#        self.title = "An L-function generated by an Lcalc file: "
        self.title = "An L-function generated by an Lcalc file: "+originalfile
        self.credit = "David Farmer, Sally Koutsoliotas and Stefan Lemurell"
        

    def lfuncDStex(self,fmt):
        numperline=5
        numcoeffs=10
        ans=""
        if fmt=="analytic":
	    ans="\\begin{align}\n"
	    ans=ans+latex(self.dirichlet_coefficients[0])+"\\mathstrut&"
	    for n in range(1,numcoeffs):
	        ans=ans+seriescoeff(self.dirichlet_coefficients[n],n+1,"dirichlet",0.000000001)
	        if(n % numperline ==0):
		    ans=ans+"\\cr\n"
		    ans=ans+"&"
	    ans=ans+"\\cdots\n\\end{align}"
        return(ans)
                           
        
#===========================

    def lfuncFEtex(self,fmt):
        ans=""
        if fmt=="lang":
            ans="\\begin{align}\n\\Lambda(s)=&"
            ans=ans+latex(self.level)+"^{-\\frac{s}{2}}"
            for mu in self.mu_fe:
               ans=ans+"\Gamma_R(s+"+latex(mu)+")"
            for nu in self.nu_fe:
               ans=ans+"\Gamma_C(s+"+latex(nu)+")"
            ans=ans+"\\cdot L(s)\\cr\n"
            ans=ans+"=\\mathstrut & "+latex(self.sign)+\
"\\overline{\\Lambda(1-\\overline{s})}\n\\end{align}\n"
	return(ans)

def latex(thetext):
    return str(thetext)

def seriescoeff(coeff, index, seriestype, truncation):
    rp=real_part(coeff)
    ip=imag_part(coeff)
# below we use float(abs()) instead of abs() to avoid a sage bug
    if (float(abs(rp))>truncation) & (float(abs(ip))>truncation):
        return("+(" + latex(coeff) +")" + seriesvar(index, seriestype))
    elif (float(abs(rp))<truncation) & (float(abs(ip))<truncation):
        return("")
# if we get this far, either pure real or pure imaginary
    if rp>truncation: 
        if float(abs(rp-1))<truncation:
            return("+" + seriesvar(index,seriestype))
        else:
            return("+" + latex(rp) + seriesvar(index, seriestype))
    elif float(abs(rp+1))<truncation:
        return("-" + seriesvar(index, seriestype))
    elif ip>truncation:
        if float(abs(ip-1))<truncation:
            return("+" + seriesvar(index,seriestype))
        else:
            return("+" + latex(ip) + seriesvar(index, seriestype))
    elif float(abs(ip+1))<truncation:
        return("-" + seriesvar(index, seriestype))
    else:
        return(latex(coeff) + seriesvar(index, seriestype))
    
#---------

def seriesvar(index,seriestype):
    if seriestype=="dirichlet":
        return(" \\ " + str(index)+"^{-s}")
    else:
        return("\\, " + "q^{"+str(index)+"}")

def real_part(pair):
    return pair[0]

def imag_part(pair):
    return pair[1]
