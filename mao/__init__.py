from .common import *
from .lookup import *
from .prereqs import *
from .session import *

# For convenience, MAO allows a bit of flexibility in specifying a course identifier
# This function contains the needed processing.
#
# A number is taken to be either a DEVM or MATH course with that number
#
# The F, as in F302, is not required, nor is the trailing X for core classes.  
#
# A subject name can be included, e.g. "STAT 200" will match "STAT F200X"
#
# The return value is a string with the subject and proper course number joined
# with an underscore.
#
# course_id_for("200") -> "MATH_F200X"
# course_id_for("60")  -> "DEVM_F060"
#


## Translation between old-school names (pre-fall 2015)
## and their modern equivalents


grade_equivalents = { 
'A+':4.0, 'A':4.0, 'A-':3.7,
'B+':3.3, 'B':3.0, 'B-':2.7,
'C+':2.3, 'C':2.0, 'C-':1.7,
'D+':1.3, 'D':1.0, 'D-':0.7,
'F':0.0, 'W':-1.0, 'I':-2.0,
'AU':-3.0, 'NB':-4.0, 'DF':-4.0,
'NS':-4.0, 'A Z':4.0, 'B Z':3.0,
'C Z':2.0, 'D Z':1.0, 'F Z':-4.0,
'':-4.0, 'P':-4, 'OG':-5, 'I N':-4 }

dawn_of_time = 199801

def to_numerical_grades(x):
	return map( lambda z: grade_equivalents[z], x)

def is_passing_grade(grades):
	return map( lambda z: z>= 1.7, to_numerical_grades(grades) )

def is_failing_grade(grades):
	return map( lambda z: z < 1.7, to_numerical_grades(grades) )

def is_F_section(x):
        return map( lambda z: z[0:2] == 'F0', x)

def is_FE_section(x):
        return map( lambda z: z[0:2] == 'FE', x)

def is_our_section(x):
        return map( lambda z: (z[0:2] == 'F0' or z[0:2] == 'FE') , x)

def is_not_our_section(x):
        return map( lambda z: (z[0:2] != 'F0' and z[0:2] != 'FE') , x)

def is_UX_section(x):
        return map( lambda z: (z[0:2] == 'UX') , x)


# Determines if a prerequisite identifier is a course (i.e starts XXXX_F and
# is followed by a digit.
def is_course_name(c):
	if not isinstance(c,basestring):
		return False
	regex = "[A-Z]+_F[0-9]"
	return re.match(regex,c) != None




# def create_table_if_needed(db, tablename, schema):
# 	r = db.cursor().execute("SELECT table_name FROM user_tables WHERE table_name=UPPER('%s')" % tablename)
	
# 	if r.fetchone() is None:
# 		print "no table, buildig"
# 		cmd = "CREATE GLOBAL TEMPORARY TABLE %s %s" %(tablename,schema)
# 		db.cursor().execute(cmd)

# def build_grade_table(db):
# 	table_name = 'dms_grade_lookup'
# 	schema ='( grade VARCHAR2(8), numerical_grade FLOAT)'
# 	create_table_if_needed(db,table_name, schema)

# 	q="SELECT COUNT(*) FROM %s" % table_name
# 	n=db.cursor().execute(q).fetchone()[0]
# 	if n == 0:
# 		print "empty table"
# 		cursor = db.cursor()
# 		grade_lookup = [('A+',4.0),
# 						('A',4.0),
# 						('A-',3.7),
# 						('B+',3.3),
# 						('B',3.0),
# 						('B-',2.7),
# 						('C+',2.3),
# 						('C',2.0),
# 						('C-',1.7),
# 						('D+',1.3),
# 						('D',1.0),
# 						('D-',0.7),
# 						('F',0.),
# 						('W',-1.),
# 						('I',-2.),
# 						('AU',-3.),
# 						('NB',-4.),
# 						('DF',-4.),
# 						('NS',-4.),
# 						('A Z',4.),
# 						('B Z',3.),
# 						('C Z',2.),
# 						('D Z',1.),
# 						('F Z',-4.),
# 						('',-4.),
# 						('P',-4.),
# 						('OG',-5.)]
# 		for (letter,numerical) in grade_lookup:
# 			cursor.execute("INSERT INTO %s values ('%s',%g)" % (table_name,letter,numerical))
