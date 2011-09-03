# -*- coding: utf-8 -*-
import math
from Lfunctionutilities import pair2complex, splitcoeff, seriescoeff
from sage.all import *
import sage.libs.lcalc.lcalc_Lfunction as lc
import re
import pymongo
import bson
import utils
import logging

logger = utils.make_logger("LF")

def get_attr_or_method(thiswillbeexecuted, attr_or_method_name):
    """
        Given an object O and a string "text", this returns O.text() or O.text depending on
        whether text is an attribute or a method of O itself _or one of its superclasses_, which I will
        only know at running time. I think I need an eval for that.   POD
        
    """
    # I don't see a way around using eval for what I want to be able to do
    # Because of inheritance, which method should be called depends on self
    try:
        return eval("thiswillbeexecuted."+attr_or_method_name)
    except:
        return None

import logging
def my_find_update(the_coll, search_dict, update_dict):
    """ This performs a search using search_dict, and updates each find in  
    the_coll using update_dict. If there are none, update_dict is actually inserted.
    """
    x = the_coll.find(search_dict,limit=1)
    if x.count() == 0:
        the_coll.insert(update_dict)
    else:
        for x in the_coll.find(search_dict):
            x.update(update_dict)
            the_coll.save(x)
        
        
##================================================================================

def constructor_logger(object, args):
    logging.info(str(object.__class__)+str(args))
    object.inject_database(["original_mathematical_object()", "poles", "residues", "kappa_fe", 
        "lambda_fe", "mu_fe", "nu_fe"])
class Lfunction:
    """Class representing a general L-function
    It can be called with a dictionary of these forms:
    
    dict = { 'Ltype': 'lcalcurl', 'url': ... }  url is any url for an lcalcfile
    dict = { 'Ltype': 'lcalcfile', 'filecontens': ... }  filecontens is the
           contents of an lcalcfile
    
    """
    
    def __init__(self, **args):
        constructor_logger(self,args)
        # Initialize some default values
        self.coefficient_period = 0
        self.poles = []
        self.residues = []
        self.kappa_fe = []
        self.lambda_fe =[]
        self.mu_fe = []
        self.nu_fe = []
        self.selfdual = False
        self.langlands = True
        self.texname = "L(s)"  # default name.  will be set later, for most L-functions
        self.texnamecompleteds = "\\Lambda(s)"  # default name.  will be set later, for most L-functions
        self.texnamecompleted1ms = "\\overline{\\Lambda(1-\\overline{s})}"  # default name.  will be set later, for most L-functions
        self.primitive = True # should be changed later
        self.citation = ''
        self.credit = ''

        # Initialize from an lcalcfile if it's not a subclass
        if 'Ltype' in args.keys():
            self._Ltype = args.pop("Ltype")
            # Put the args into the object dictionary
            self.__dict__.update(args)
        
            # Get the lcalcfile from the web
            if self.Ltype=='lcalcurl':
                if 'url' in args.keys():
                    try:
                        import urllib
                        self.filecontents = urllib.urlopen(self.url).read()
                    except:
                        raise Exception("Wasn't able to read the file at the url")
                else:
                    raise Exception("You forgot to supply an url.")           

            # Parse the Lcalcfile
            self.parseLcalcfile()

            # Check if self dual
            self.checkselfdual()
  
            if self.selfdual:
                self.texnamecompleted1ms = "\\Lambda(1-s)"

            try:
                self.originalfile = re.match(".*/([^/]+)$", self.url)
                self.originalfile = self.originalfile.group(1)
                self.title = "An L-function generated by an Lcalc file: "+self.originalfile

            except:
                self.originalfile = ''
                self.title = "An L-function generated by an Lcalc file."

            self.generateSageLfunction()

    def Ltype(self):
        return self._Ltype

    def parseLcalcfile(self, filecontents):
        """ Extracts informtion from the lcalcfile
        """
        
        lines = filecontents.split('\n',6)
        self.coefficient_type = int(lines[0])
        self.quasidegree = int(lines[4])
        lines = self.lcalcfile.split('\n',8+2*self.quasidegree)
        self.Q_fe = float(lines[5+2*self.quasidegree])
        self.sign = pair2complex(lines[6+2*self.quasidegree])

        self.kappa_fe = []
        self.lambda_fe = []
        self.mu_fe = []
        self.nu_fe = []

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
        
        self.degree = int(round(2*sum(self.kappa_fe)))

        self.level = int(round(math.pi**float(self.degree) * 4**len(self.nu_fe) * self.Q_fe**2 ))
        # note:  math.pi was not compatible with the sage type of degree

        self.dirichlet_coefficients = splitcoeff(lines[-1])
        

    def checkselfdual(self):
        """ Checks whether coefficients are real to determine
            whether L-function is selfdual
        """

        self.selfdual = True
        for n in range(1,min(8,len(self.dirichlet_coefficients))):
            if abs(imag_part(self.dirichlet_coefficients[n]/self.dirichlet_coefficients[0])) > 0.00001:
                self.selfdual = False

    def generateSageLfunction(self):
        """ Generate a SageLfunction to do computations
        """
        self.sageLfunction = lc.Lfunction_C(self.title, self.coefficient_type,
                                            self.dirichlet_coefficients,
                                            self.coefficient_period,
                                            self.Q_fe, self.sign ,
                                            self.kappa_fe, self.lambda_fe ,
                                            self.poles, self.residues)

    def createLcalcfile(self):
        thefile="";
        if self.selfdual:
            thefile += "2\n"  # 2 means real coefficients
        else:
            thefile += "3\n"  # 3 means complex coefficients

        thefile += "0\n"  # 0 means unknown type

        thefile += str(len(self.dirichlet_coefficients)) + "\n"  

        thefile += "0\n"  # assume the coefficients are not periodic
        
        thefile += str(self.quasidegree) + "\n"  # number of actual Gamma functions

        for n in range(0,self.quasidegree):
            thefile = thefile + str(self.kappa_fe[n]) + "\n"
            thefile = thefile + str(real_part(self.lambda_fe[n])) + " " + str(imag_part(self.lambda_fe[n])) + "\n"
        
        thefile += str(real_part(self.Q_fe)) +  "\n"

        thefile += str(real_part(self.sign)) + " " + str(imag_part(self.sign)) + "\n"

        thefile += str(len(self.poles)) + "\n"  # counts number of poles

        for n in range(0,len(self.poles)):
            thefile += str(real_part(self.poles[n])) + " " + str(imag_part(self.poles[n])) + "\n" #pole location
            thefile += str(real_part(self.residues[n])) + " " + str(imag_part(self.residues[n])) + "\n" #residue at pole

        for n in range(0,len(self.dirichlet_coefficients)):
            thefile += str(real_part(self.dirichlet_coefficients[n]))   # add real part of Dirichlet coefficient
            if not self.selfdual:  # if not selfdual
                thefile += " " + str(imag_part(self.dirichlet_coefficients[n]))   # add imaginary part of Dirichlet coefficient
            thefile += "\n" 
        
        return(thefile)

    #==================================================
    # other useful methods
    #==================================================
    
    def original_mathematical_object(self):
        raise Error("not all L-function have a mathematical object tag defined atm")
        
    def initial_zeroes(self, numzeroes=0):
        pass

    def critical_value(self):
        pass
        
    def value_at_1(self):
        pass
        
    def conductor(self, advocate):
        # Advocate could be IK, CFKRS or B
        pass
        
    #============== Injects into the database of all the L-functions
    #==============
            
    def inject_database(self, relevant_info, time_limit = None):
        #   relevant_methods are text strings 
        #    desired_database_fields = [Lfunction.original_mathematical_object, Lfunction.level]
        #    also zeroes, degree, conductor, type, real_coeff, rational_coeff, algebraic_coeff, critical_value, value_at_1, sign
        #    ok_methods = [Lfunction.math_id, Lfunction.level]
        #   
        # Is used to inject the data in relevant_fields
        
        logging.info("Trying to inject")
        import base
        db = base.getDBConnection().Lfunctions
        Lfunctions = db.full_collection
        update_dict = dict([(method_name,get_attr_or_method(self,method_name)) for method_name in relevant_info])
        
        logging.info("injecting " + str(update_dict))
        search_dict = {"original_mathematical_object()": get_attr_or_method(self, "original_mathematical_object()")}
        
        my_find_update(Lfunctions, search_dict, update_dict)
        

##================================================================================

class Lfunction_EC(Lfunction):
    """Class representing an elliptic curve L-function
    It can be called with a dictionary of these forms:
    
    dict = { 'label': ... }  label is the Cremona label of the elliptic curve
    dict = { 'label': ... , 'numcoeff': ...  }  numcoeff is the number of
           coefficients to use when computing
    """
    
    def __init__(self, **args):
        #Check for compulsory arguments
        if not 'label' in args.keys():
            raise Exception("You have to supply a label for an elliptic curve L-function")
        
        # Initialize default values
        self.numcoeff = 20 # set default to 20 coefficients

        # Put the arguments into the object dictionary
        self.__dict__.update(args)
        self.numcoeff = int(self.numcoeff)


        # Create the elliptic curve
        self.E = EllipticCurve(str(self.label))

        # Extract the L-function information from the elliptic curve
        self.quasidegree = 1
        self.level = self.E.conductor()
        self.Q_fe = float(sqrt(self.level)/(2*math.pi))
        self.sign = self.E.lseries().dokchitser().eps
        self.kappa_fe = [1]
        self.lambda_fe = [0.5]
        self.mu_fe = []
        self.nu_fe = [0.5]
        self.langlands = True
        self.degree = 2
        
        self.dirichlet_coefficients = self.E.anlist(self.numcoeff)[1:]  #remove a0

        # Renormalize the coefficients
        for n in range(0,len(self.dirichlet_coefficients)-1):
           an = self.dirichlet_coefficients[n]
           self.dirichlet_coefficients[n]=float(an)/float(sqrt(n+1))
       
        self.poles = []
        self.residues = []
        self.coefficient_period = 0
        self.selfdual = True
        self.primitive = True
        self.coefficient_type = 2
        self.texname = "L(s,E)"
        self.texnamecompleteds = "\\Lambda(s,E)"
        self.texnamecompleted1ms = "\\Lambda(1-s,E)"
        self.title = "L-function $L(s,E)$ for the Elliptic Curve over Q with label "+ self.E.label()

        self.properties = [('Degree ','%s' % self.degree)]
        self.properties.append(('Level', '%s' % self.level))
        self.credit = 'Sage'
        self.citation = ''
        
        self.generateSageLfunction()

        logging.info("I am now proud to have ", str(self.__dict__))
        constructor_logger(self,args)

    def Ltype(self):
        return "ellipticcurve"
        
    def ground_field(self):
        return "Q"
        # At the moment
    
    def original_mathematical_object(self):
        return [self.Ltype(), self.ground_field(), self.label]
        
            
##================================================================================

class Lfunction_EMF(Lfunction):
    """Class representing an elliptic modular form L-function

    Compulsory parameters: weight
                           level

    Possible parameters: character
                         label
                         number
    
    """
    
    def __init__(self, **args):

        #Check for compulsory arguments
        if not ('weight' in args.keys() and 'level' in args.keys()):
            raise KeyError, "You have to supply weight and level for an elliptic modular form L-function"
        
        # Initialize default values
        self.character = 0  # Trivial character is default
        self.label=''       # No label, is OK If space is one-dimensional
        self.number = 1     # Default choice of embedding of the coefficients

        # Put the arguments into the object dictionary
        self.__dict__.update(args)
        self.weight = int(self.weight)
        self.level = int(self.level)
        self.character = int(self.character)
        self.number = int(self.number)

        # Create the modular form
        self.MF = WebNewForm(self.weight, self.level, self.character, self.label)

        # Extract the L-function information from the elliptic modular form
        self.automorphyexp = float(self.weight-1)/float(2)
        self.Q_fe = float(sqrt(self.level)/(2*math.pi))
                            
        if self.level == 1:  # For level 1, the sign is always plus
            self.sign = 1
        else:  # for level not 1, calculate sign from Fricke involution and weight
            self.sign = self.MF.atkin_lehner_eigenvalues()[self.level] * (-1)**(float(self.weight/2))
                            
        self.kappa_fe = [1]
        self.lambda_fe = [self.automorphyexp]
        self.mu_fe = []
        self.nu_fe = [self.automorphyexp]
        self.selfdual = True
        self.langlands = True
        self.primitive = True
        self.degree = 2
        self.poles = []
        self.residues = []
        self.numcoeff = 30 #just testing  NB: Need to learn how to use more coefficients
        self.dirichlet_coefficients = []
                            
        # Appending list of Dirichlet coefficients
        GaloisDegree = self.MF.degree()  #number of forms in the Galois orbit
        if GaloisDegree == 1:
           self.dirichlet_coefficients = self.MF.q_expansion_embeddings(self.numcoeff) #when coeffs are rational, q_expansion_embedding() is the list of Fourier coefficients
        else:
           for n in range(0,self.numcoeff):
              logger.info("n=%s  self.number = %s" % (n, self.number))
              self.dirichlet_coefficients.append(self.MF.q_expansion_embeddings(self.numcoeff)[n][self.number])
        for n in range(0,len(self.dirichlet_coefficients)):
            an = self.dirichlet_coefficients[n]
            self.dirichlet_coefficients[n]=float(an)/float((n+1)**self.automorphyexp)
#FIX: These coefficients are wrong; too large and a1 is not 1
                            
        self.coefficient_period = 0
        self.coefficient_type = 2
        self.quasidegree = 1
        
        self.checkselfdual()

        self.texname = "L(s,f)"
        self.texnamecompleteds = "\\Lambda(s,f)"
        if self.selfdual:
            self.texnamecompleted1ms = "\\Lambda(1-s,f)"
        else:
            self.texnamecompleted1ms = "\\Lambda(1-s,\\overline{f})"
        self.title = "L-function of a holomorphic cusp form: $L(s,f)$, "+ "where $f$ is a holomorphic cusp form with weight "+str(self.weight)+", level "+str(self.level)+", and character "+str(self.character)

        self.citation = ''
        self.credit = ''
       
        self.generateSageLfunction()
        constructor_logger(self,args)


    def Ltype(self):
        return "ellipticmodularform"


##================================================================================

class RiemannZeta(Lfunction):
    """Class representing the Riemann zeta fucntion

    Possible parameters: numcoeff  (the number of coefficients when computing)

    """
    
    def __init__(self, **args):
        constructor_logger(self,args)

        # Initialize default values
        self.numcoeff = 30 # set default to 30 coefficients

        # Put the arguments into the object dictionary
        self.__dict__.update(args)
        self.numcoeff = int(self.numcoeff)

        self.coefficient_type = 1
        self.quasidegree = 1
        self.Q_fe = float(1/sqrt(math.pi))
        self.sign = 1
        self.kappa_fe = [0.5]
        self.lambda_fe = [0]
        self.mu_fe = [0]
        self.nu_fe = []
        self.langlands = True
        self.degree = 1
        self.level = 1
        self.dirichlet_coefficients = []
        for n in range(self.numcoeff):
            self.dirichlet_coefficients.append(1)
        self.poles = [0,1]
        self.residues = [-1,1]
        self.coefficient_period = 0
        self.selfdual = True
        self.texname = "\\zeta(s)"
        self.texnamecompleteds = "\\xi(s)"
        self.texnamecompleted1ms = "\\xi(1-s)"
        self.credit = 'Sage'
        self.primitive = True
        self.citation = ''
        self.title = "Riemann Zeta-function: $\\zeta(s)$"
        
        self.generateSageLfunction()
    
    def Ltype(self):
        return "riemann"

    def original_mathematical_object(self):
        return ["riemann"]

##================================================================================

class Lfunction_Dirichlet(Lfunction):
    """Class representing the L-function of a Dirichlet character

    Compulsory parameters: charactermodulus
                           characternumber

    Possible parameters: numcoeff  (the number of coefficients when computing)
    
    """
    
    def __init__(self, **args):

        #Check for compulsory arguments
        if not ('charactermodulus' in args.keys() and 'characternumber' in args.keys()):
            raise KeyError, "You have to supply charactermodulus and characternumber for the L-function of a Dirichlet character"
        
        # Initialize default values
        self.numcoeff = 30    # set default to 30 coefficients

        # Put the arguments into the object dictionary
        self.__dict__.update(args)
        self.charactermodulus = int(self.charactermodulus)
        self.characternumber = int(self.characternumber)
        self.numcoeff = int(self.numcoeff)

        # Create the Dirichlet character
        chi = DirichletGroup(self.charactermodulus)[self.characternumber]

        # Extract the L-function information from the Dirichlet character
        # Warning: will give nonsense if character is not primitive
        aa = int((1-chi(-1))/2)   # usually denoted \frak a
        self.quasidegree = 1
        self.Q_fe = float(sqrt(self.charactermodulus)/sqrt(math.pi))
        self.sign = 1/(I**aa * float(sqrt(self.charactermodulus))/(chi.gauss_sum_numerical()))
        self.kappa_fe = [0.5]
        self.lambda_fe = [0.5*aa]
        self.mu_fe = [aa]
        self.nu_fe = []
        self.langlands = True
        self.primitive = True
        self.degree = 1
        self.level = self.charactermodulus

        self.dirichlet_coefficients = []
        for n in range(1,self.numcoeff):
            self.dirichlet_coefficients.append(chi(n).n())
                            
        self.poles = []
        self.residues = []
        self.coefficient_period = self.charactermodulus

        # Determine if the character is real (i.e., if the L-function is selfdual)
        chivals=chi.values_on_gens()
        self.selfdual = True
        for v in chivals:
            if abs(imag_part(v)) > 0.0001:
                self.selfdual = False
  
        if self.selfdual:
            self.coefficient_type = 1
        else:
            self.coefficient_type = 2

        self.texname = "L(s,\\chi)"
        self.texnamecompleteds = "\\Lambda(s,\\chi)"
                            
        if self.selfdual:
            self.texnamecompleted1ms = "\\Lambda(1-s,\\chi)"
        else:
            self.texnamecompleted1ms = "\\Lambda(1-s,\\overline{\\chi})"

        self.credit = 'Sage'
        self.citation = ''
        self.title = "Dirichlet L-function: $L(s,\\chi)$"
        self.title = (self.title+", where $\\chi$ is the character modulo "+
                          str(self.charactermodulus) + ", number " +
                          str(self.characternumber))
        
        self.generateSageLfunction()
        constructor_logger(self,args)

    def Ltype(self):
        return "dirichlet"

    def original_mathematical_object(self):
        return [self.Ltype(), self.charactermodulus, self.characternumber]


##================================================================================

class Lfunction_Maass(Lfunction):
    """Class representing the L-function of a Maass form 

    Compulsory parameters: dbid

    Possible parameters: dbName  (the name of the database for the Maass form)
                         dbColl  (the name of the collection for the Maass form)
    
    """
    
    def __init__(self, **args):
        constructor_logger(self,args)

        #Check for compulsory arguments
        if not 'dbid' in args.keys():
            raise KeyError, "You have to supply dbid for the L-function of a Maass form"
        
        # Initialize default values
        self.dbName = 'MaassWaveForm'    # Set default database
        self.dbColl = 'HT'               # Set default collection    

        # Put the arguments into the object dictionary
        self.__dict__.update(args)

        # Fetch the information from the database
        import base
        connection = base.getDBConnection()
        db = pymongo.database.Database(connection, self.dbName)
        collection = pymongo.collection.Collection(db, self.dbColl)
        dbEntry = collection.find_one({'_id': self.dbid})

        if self.dbName == 'Lfunction':  # Data from Lemurell
            
            # Extract the L-function information from the database entry
            self.__dict__.update(dbEntry)

            self.coefficient_period = 0
            self.poles = []
            self.residues = []

            # Extract the L-function information from the lcalfile in the database
            self.parseLcalcfile(self.lcalcfile)  

        else: # GL2 data from Then or Stromberg

            self.group = 'GL2'
            
            # Extract the L-function information from the database entry
            self.symmetry = dbEntry['Symmetry']
            self.eigenvalue = float(dbEntry['Eigenvalue'])
            self.norm = dbEntry['Norm']
            self.dirichlet_coefficients = dbEntry['Coefficient']
            
            if 'Level' in dbEntry.keys():
                self.level = int(dbEntry['Level'])
            else:
                self.level = 1
            self.charactermodulus = self.level
            
            if 'Weight' in dbEntry.keys():
                self.weight = int(dbEntry['Weight'])
            else:
                self.weight = 0
                
            if 'Character' in dbEntry.keys():
                self.characternumber = int(dbEntry['Character'])
                
            if self.level > 1:
                self.fricke = dbEntry['Fricke']  #no fricke for level 1


            # Set properties of the L-function
            self.coefficient_type = 2
            self.selfdual = True
            self.primitive = True
            self.quasidegree = 2
            self.Q_fe = float(sqrt(self.level))/float(math.pi)
            
            if self.symmetry =="odd":
                aa=1
            else:
                aa=0
                
            if aa==0:
                self.sign = 1
            else:
                self.sign = -1
                
            if self.level > 1:
                self.sign = self.fricke * self.sign
                
            self.kappa_fe = [0.5,0.5]
            self.lambda_fe = [0.5*aa + self.eigenvalue*I, 0,5*aa - self.eigenvalue*I]
            self.mu_fe = [aa + 2*self.eigenvalue*I, aa -2*self.eigenvalue*I]
            self.nu_fe = []
            self.langlands = True
            self.degree = 2
            self.poles = []
            self.residues = []
            self.coefficient_period = 0

            self.checkselfdual()
            
            self.texname = "L(s,f)"
            self.texnamecompleteds = "\\Lambda(s,f)"
            
            if self.selfdual:
                self.texnamecompleted1ms = "\\Lambda(1-s,f)"
            else:
                self.texnamecompleted1ms = "\\Lambda(1-s,\\overline{f})"
                
            self.title = "$L(s,f)$, where $f$ is a Maass cusp form with level "+str(self.level)+", and eigenvalue "+str(self.eigenvalue)
            self.citation = ''
            self.credit = ''
        
        self.generateSageLfunction()

    def Ltype(self):
        return "maass"
##================================================================================

class DedekindZeta(Lfunction):   # added by DK
    """Class representing the Dedekind zeta-fucntion

    Compulsory parameters: label
    
    """
    
    def __init__(self, **args):
        constructor_logger(self,args)

        #Check for compulsory arguments
        if not 'label' in args.keys():
            raise Exception("You have to supply a label for a Dedekind zeta function")
        
        # Initialize default values

        # Put the arguments into the object dictionary
        self.__dict__.update(args)

        # Fetch the polynomial of the field from the database
        import base
        connection = base.getDBConnection()
        db = connection.numberfields.fields
        poly_coeffs = db.find_one({'label':self.label})['coefficients']

        # Extract the L-function information from the polynomial
        R = QQ['x']; (x,) = R._first_ngens(1)
        self.polynomial = sum([poly_coeffs[i]*x**i for i in range(len(poly_coeffs))])
        self.NF = NumberField(self.polynomial, 'a')
        self.signature = self.NF.signature()
        self.sign = 1
        self.quasidegree = sum(self.signature)
        self.level = self.NF.discriminant().abs()
        self.degreeofN = self.NF.degree()

        self.Q_fe = float(sqrt(self.level)/(2**(self.signature[1]) * (math.pi)**(float(self.degreeofN)/2.0)))

        self.kappa_fe = self.signature[0]* [0.5] + self.signature[1] * [1]
        self.lambda_fe = self.quasidegree * [0]
        self.mu_fe = self.signature[0]*[0] # not in use?
        self.nu_fe = self.signature[1]*[0] # not in use?
        self.langlands = True
        self.degree = self.signature[0] + 2 * self.signature[1] # N = r1 +2r2
        self.dirichlet_coefficients = [Integer(x) for x in self.NF.zeta_coefficients(5000)]
        self.h=self.NF.class_number()
        self.R=self.NF.regulator()
        self.w=len(self.NF.roots_of_unity())
        self.h=self.NF.class_number()
        self.res=RR(2**self.signature[0]*self.h*self.R/self.w) #r1 = self.signature[0]

        self.poles = [1,0]
        self.residues = [self.res,-self.res]
        self.coefficient_period = 0
        self.selfdual = True
        self.primitive = True
        self.coefficient_type = 0
        self.texname = "\\zeta_K(s)"
        self.texnamecompleteds = "\\Lambda_K(s)"
        if self.selfdual:
            self.texnamecompleted1ms = "\\Lambda_K(1-s)"
        else:
            self.texnamecompleted1ms = "\\Lambda_K(1-s)"
        self.title = "Dedekind zeta-function: $\\zeta_K(s)$"
        self.title = self.title+", where $K$ is the "+ str(self.NF)
        self.credit = 'Sage'
        self.citation = ''
        
        self.generateSageLfunction()



