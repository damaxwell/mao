import mao
import re
import pandas

prereq_list_pre_ALEKS = {
  "STAT_F200X":["EAMA","SATM","AACM","COCA","APCA","APCB","ACOL","MATH_F151X", "MATH_F122X"],
  "MATH_F232X":[ "EAMA","SATM","AACM",["COCA","COTR"],"APCA","APCB", ["MATH_F151X","MATH_F152X"]],
  "MATH_F222X":[ "EAMA","SATM","AACM",["COCA","COTR"],"APCA","APCB", "MATH_F122X"],
  "MATH_F211":[ "EAMA", "SATM", "MATH_F122X", "MATH_F151X", "MATH_F194", "MATH_F194X"],
  "MATH_F253X":["MATH_F252X","APCB"],
  "MATH_F252X":["MATH_F251X","APCA","APCB"],
  "MATH_F251X":["EAMA","SATM","AACM",["COCA","COTR"],"APCA","APCB",["MATH_F151X","MATH_F152X"]],
  "MATH_F156X":[],
  "MATH_F122X":["EAMA","SATM","AACM","COCA","APCA","APCB","ACOL","APPL","DEVM_F105","DEVM_F106"],
  # This next one isn't quite right.  Concurrent enrollment with 107 is OK.
  "MATH_F152X": ["EAMA", "SATM", "AACM", "COCA", "DEVM_F106","DEVM_F105"],
  "MATH_F151X":["EAMA","SATM","AACM","COCA","APCA","APCB","ACOL","DEVM_F106","DEVM_F105"],
  "MATH_F113X":["EAMA","SATM","AAEA","COAL",["AELE","AINT"],"DEVM_F105","DEVM_F055"],
  "DEVM_F106":["EAMA","SATM","AAEA","COAL",["AELE","AINT"],"DEVM_F055","DEVM_F062"],
  "DEVM_F105":["EAMA","SATM","AAEA","COAL",["AELE","AINT"],"DEVM_F055","DEVM_F062"],
  "DEVM_F055":["EAMA","SATM","AAEA","COPA",["AELE","ANUM"],"DEVM_F054","DEVM_F052"],
  "DEVM_F054":["EAMA","SATM","AAAR","COPA","ANUM"]
}


prereq_list_post_ALEKS = { 
  "STAT_F200X":["APPL", "MATH_F151X", "MATH_F122X"],
  "MATH_F232X":["APPL", ["MATH_F151X","MATH_F152X"]],
  "MATH_F222X":["APPL", "MATH_F122X"],
  "MATH_F211": ["APPL", "MATH_F122X", "MATH_F151X", "MATH_F194", "MATH_F194X"],
  "MATH_F253X":["MATH_F252X","APCB"],
  "MATH_F252X":["MATH_F251X","APCA","APCB"],
  "MATH_F251X":["APPL","APCA","APCB",["MATH_F151X","MATH_F152X"], "MATH_F194", "MATH_F156X"],
  "MATH_F156X":["APPL"],
  "MATH_F122X":["APPL","DEVM_F105","DEVM_F106"],
  # This next one isn't quite right.  Concurrent enrollment with 107 is OK.
  "MATH_F152X": ["APPL","DEVM_F106","DEVM_F105"],
  "MATH_F151X":["APPL","APCA","APCB","DEVM_F106","DEVM_F105"],
  "MATH_F113X":["APPL","DEVM_F105","DEVM_F055"],
  "DEVM_F106":["APPL","DEVM_F055","DEVM_F062"],
  "DEVM_F105":["APPL","DEVM_F055","DEVM_F062"],
  "DEVM_F065":["APPL"],
  "DEVM_F055":["APPL","DEVM_F054","DEVM_F052"],
  "DEVM_F054":["APPL"]
}

cut_score_default = {
  "STAT_F200X": {'APPL':55, 'EAMA':23, 'SATM':530, 'COCA':50, 'AACM':50, 'APCA':3, 'APCB':3, 'ACOL':41, 'MATH_F151X':"C-",'MATH_F122X':"C-"},
  "MATH_F232X": {'EAMA':28, 'SATM':610, 'COCA':56, 'COTR':46, 'AACM':90, 'APCA':3, 'APCB':3,'APPL':78, 'MATH_F151X':"C-", 'MATH_F152X':"C-"},
  "MATH_F222X":  {'APPL':70, 'EAMA':28, 'SATM':610, 'COCA':56, 'COTR':46, 'AACM':90, 'APCA':3, 'APCB':3, 'MATH_F122X':"C-"},
  "MATH_F211":  {'APPL':70, 'EAMA':26, 'SATM':590, 'MATH_F151X':"C-", 'MATH_F122X':"C-", 'MATH_F194':"C-", 'MATH_F156X':"C-"},
  "MATH_F253X": { 'MATH_F252X':"C-", 'APCB':3},
  "MATH_F252X": { 'MATH_F251X':"C-", 'APCA':3, 'APCB':3},
  "MATH_F251X": {'APPL':78, 'EAMA':28, 'SATM':610, 'COCA':56, 'COTR':46, 'AACM':90, 'APCA':3, 'APCB':3, 'MATH_F151X':"C-", 'MATH_F152X':"C-", 'MATH_F194':"C-", 'MATH_F156X':"C-"},
  "MATH_F156X": {'APPL':65},
  "MATH_F122X": {'APPL':55, 'EAMA':23, 'SATM':530, 'COCA':50, 'AACM':50, 'APCA':3, 'APCB':3, 'ACOL':41, 'APPL':55, 'DEVM_F105':"C-",'DEVM_F106':"C-"},
  "MATH_F152X":  {'APPL':65,  'EAMA':23, 'SATM':530, 'COCA':50, 'AACM':60, 'APCA':3, 'APCB':3, 'ACOL':41, 'DEVM_F105':"B-", 'DEVM_F106':"B-"},
  "MATH_F151X": {'APPL':55, 'EAMA':23, 'SATM':530, 'COCA':50, 'AACM':50, 'APCA':3, 'APCB':3, 'ACOL':41, 'DEVM_F105':"B-", 'DEVM_F106':"B-"},
  "MATH_F113X": {'APPL':30, 'EAMA':20, 'SATM':470, 'COAL':50, 'AAEA':70, 'AELE':37, 'AINT':23,'DEVM_F105':"C-",'DEVM_F055':"C-",'DEVM_F062':"C-"},
  "DEVM_F105":  {'APPL':30, 'EAMA':20, 'SATM':470, 'COAL':50, 'AAEA':70, 'AELE':37, 'AINT':23,'DEVM_F055':"C-",'DEVM_F062':"C-"},
  "DEVM_F106":  {'APPL':30, 'EAMA':20, 'SATM':470, 'COAL':50, 'AAEA':70, 'AELE':37, 'AINT':23,'DEVM_F055':"C-",'DEVM_F062':"C-"},
  "DEVM_F065":  {'APPL':15, 'EAMA':17, 'SATM':410, 'COPA':50, 'AAEA':48, 'AELE':23, 'ANUM':37,'DEVM_F054':"C-",'DEVM_F052':"C-" },
  "DEVM_F055":  {'APPL':15, 'EAMA':17, 'SATM':410, 'COPA':50, 'AAEA':48, 'AELE':23, 'ANUM':37,'DEVM_F054':"C-",'DEVM_F052':"C-" },
  "DEVM_F054":  {'APPL':1,  'EAMA':1, 'SATM':200,  'COPA':25, 'AAAR':34, 'ANUM':33}
}

# Build list of grades meeting a threshold.  Note that
# transfer credit grades have a " T" suffix so we include those, too.
grades = ["A+", "A", "A-", "B", "B+", "B-"]
tgrades = [x+" T" for x in grades]
Bminus_or_better = set( grades + tgrades )
grades = ["A+", "A", "A-", "B", "B+", "B-", "C+", "C", "C-"]
tgrades = [x+" T" for x in grades]
Cminus_or_better = set( grades + tgrades )
grade_cutoffs = { "C-":Cminus_or_better, "B-":Bminus_or_better}

letter_to_number = {
  "A+":4.3,
  "A":4.0,
  "A-":3.7,
  "B+":3.3,
  "B":3.0,
  "B-":2.7,
  "C+":2.3,
  "C":2.0,
  "C-":1.7,
  "D+":1.3,
  "D":1.0,
  "D-":0.7,
  "F":0.0,
  "A+ T":4.3,
  "A T":4.0,
  "A- T":3.7,
  "B+ T":3.3,
  "B T ":3.0,
  "B- T":2.7,
  "C+T ":2.3,
  "C T ":2.0,
  "C- T ":1.7,
  "D+ T":1.3,
  "D T":1.0,
  "D- T":0.7,
  "F T":0.0,
}

# Determines if a string looks like a course name (i.e starts XXXX_F and
# is followed by a digit.
def is_course_name(c):
    if not isinstance(c,basestring):
        return False
    regex = "[A-Z]+_F[0-9]"
    return re.match(regex,c) != None

def numerical_grade(grade):
  try:
    n=letter_to_number[grade]
  except:
    n=-1.0
  return n

def flatten_prereqs(prereq):
  courses = []
  tests = []
  if isinstance(prereq,list):
    for subprereq in prereq:
      (c2,t2) = flatten_prereqs(subprereq)
      courses.extend(c2)
      tests.extend(t2)
  else:
    if is_course_name(prereq):
      courses.append(prereq)
    else:
      if prereq == "APPL":
        tests.extend( [ "AX%d"%k for k in range (1,9) ] )
      else:
        tests.append(prereq)
  return (courses,tests)

# course_expiry -> number of terms back to look for prerequisite courses
# test_exipry -> a pd.DateOffset indicating a time period to look back 
#                for prereq tests
def attempts_with_prereqs( db, course, terms, prereq_list, cut_scores, course_expiry=None, test_expiry=None):
    data = rptp.lookup.course_attempts(db,course,terms)
    d2 = join_prereqs(db,data,course,terms,prereq_list,course_expiry,test_expiry)
    d3 =  build_prereq_matches( d2, course, prereq_list, cut_scores )
    for c in d3.columns:
      data[c] = d3[c]
    return data


def join_prereqs(db,data,course,terms,prereq_list,course_expiry=None,test_expiry=None):

  (prereq_courses,prereq_tests) = flatten_prereqs(prereq_list)

  for prereq_course in prereq_courses:
    if prereq_course == "MATH_F194":
      prereq_course = rptp.Course(prereq_course,normalize=False)
    data = join_prereq_course(db,data,course,terms,prereq_course,course_expiry)
    data = join_prereq_xfer_course(db,data,course,terms,prereq_course)
  data = join_prereq_tests(db,data,course,terms,prereq_tests,test_expiry)
  return data

def join_prereq_tests( db, data, course, terms, test_names, expiry_threshold=None ):

  data_prereq = rptp.lookup.attempts_with_prereq_tests(db, course, test_names, terms)

  for test in test_names:
    # Banner maintains different ALEKS attempts as different test scores.
    # We hide this here by merging all AX%d scores into one APPL test.
    if test == "AX1":
      print( "appending APPL" )
      # Build all the various alex test names
      alexes = [ "AX%d"%k for k in range (1,9) ]
      this_prereq = data_prereq[data_prereq["TEST_CODE"].map( lambda x: x in alexes)]
      test = "APPL"
    elif test in [ "AX%d"%k for k in range (2,9) ]:
      continue
    else:
      print( "appending %s" % test)
      this_prereq = data_prereq[data_prereq["TEST_CODE"] == test]

    # Pandas seems to have a bug related to conversion of datetimes
    # far from the present.  Banner has erroneous test dates (e.g. 2012->1012)
    # and this seems to cause pandas to throw exceptions on some operations.
    # So we sidestep this by converting test dates to Periods, which reflect
    # the whole day the test was taken, not an instant in time. 
    this_prereq.TEST_DATE = this_prereq.TEST_DATE.map(lambda x: pandas.Period(x,'D'))

    if expiry_threshold is not None:
      expiry = this_prereq["REGISTRATION_END_DATE"].map(lambda x: pandas.Period(x - expiry_threshold,'D'))
      valid_mask = this_prereq.TEST_DATE >= expiry
      this_prereq = this_prereq[valid_mask]

    keep = ["PIDM","TERM_CODE","SECTION","TEST_DATE","TEST_SCORE"]
    this_prereq = this_prereq[keep]

    # # Find the maximum grade per student
    idx = this_prereq.groupby("PIDM")["TEST_SCORE"].transform(max) == this_prereq["TEST_SCORE"]

    # (in the event of ties, take the first one)
    this_prereq = this_prereq[idx].groupby("PIDM").first()
    # That last operation silently turns PIDM into the index.
    # We undo that now.
    this_prereq.reset_index(level=0, inplace=True)
 
    keep[3] = "%s_DATE" % test
    keep[4] = test

    this_prereq.columns = keep

    data = data.merge( this_prereq, how='left')

  return data

def join_prereq_course(db,data,course,terms,prereq_course,term_expiry_threshold=None):

  # Find all instances of previous attempts at `course` with
  # a prior attempt at `prereq_course`

  data_prereq = rptp.lookup.attempts_with_prereq_course(db, course, prereq_course, terms)

  # If a term expiry is requested, only keep prereq courses taken within the expiry
  # window.
  if term_expiry_threshold is not None:
    expiry = data_prereq["TERM_CODE"].map(
      lambda x: (rptp.Term(x)-term_expiry_threshold).banner_value )
    valid_mask = data_prereq["PREREQ_TERM_CODE"] >= expiry
    data_prereq=data_prereq[valid_mask]

  keep=["PIDM","TERM_CODE","SECTION","PREREQ_TERM_CODE","PREREQ_SCORE","PREREQ_SECTION"]
  data_prereq = data_prereq[keep]


  # # Append a numerical grade to make it easier to find maxima.
  data_prereq["PREREQ_SCORE_NUMERICAL"] = data_prereq["PREREQ_SCORE"].map(numerical_grade)

  # # Find the maximum grade per student
  idx = data_prereq.groupby("PIDM")["PREREQ_SCORE_NUMERICAL"].transform(max) == data_prereq["PREREQ_SCORE_NUMERICAL"]

  # (in the event of ties, take the first one)
  data_prereq = data_prereq[idx].groupby("PIDM").first()

  # That last operation silently turns PIDM into the index.
  # We undo that now.
  data_prereq.reset_index(level=0, inplace=True)

  # Remove the artifical numerical grade column
  data_prereq.drop('PREREQ_SCORE_NUMERICAL', axis=1, inplace=True)

  # Rename columns  
  p_course_name = rptp.Course(prereq_course).modern_name.name
  keep[3] = "%s_TERM_CODE" % p_course_name
  keep[4] = p_course_name
  keep[5] = "%s_SECTION" % p_course_name

  data_prereq.columns = keep

  return data.merge( data_prereq, how='left')

def join_prereq_xfer_course(db,data,course,terms,prereq_course):

  data_prereq = rptp.lookup.attempts_with_prereq_xfer_course(db, course, prereq_course,terms)

  keep = ["PIDM","TERM_CODE","PREREQ_TERM_CODE","PREREQ_SCORE"]
  if len(data_prereq)>0:
    data_prereq = data_prereq[keep]
  else:
    data_prereq  = pandas.DataFrame( columns = keep );

  # # Append a numerical grade to make it easier to find maxima.
  data_prereq["PREREQ_SCORE_NUMERICAL"] = data_prereq["PREREQ_SCORE"].map(numerical_grade)

  # # Find the maximum grade per student
  idx = data_prereq.groupby("PIDM")["PREREQ_SCORE_NUMERICAL"].transform(max) == data_prereq["PREREQ_SCORE_NUMERICAL"]

  # (in the event of more than one instance, take a random
  # one.
  data_prereq = data_prereq[idx].groupby("PIDM").first()

  # That last operation silently turns PIDM into the index.
  # We undo that now.
  data_prereq.reset_index(level=0, inplace=True)

  # Remove the artifical numerical grade column
  data_prereq.drop('PREREQ_SCORE_NUMERICAL', axis=1, inplace=True)
  
  # Helpfully rename columns
  p_course_name = rptp.Course(prereq_course).modern_name.name
  keep[2] = "XFER_%s_TERM_CODE" % p_course_name
  keep[3] = "XFER_%s" % p_course_name
  data_prereq.columns = keep

  # Do a left join of the prereq scores into 'data'
  return data.merge( data_prereq, how='left')

def build_prereq_matches( data, course_name, p_list, cut_scores ):
  has_prereq = {}

  for prereq in p_list:
    if isinstance(prereq,basestring):
        has_prereq[prereq] = prereq_matches(data, prereq, cut_scores)
    else:
      if len(prereq)==2:

        p0 = prereq[0]
        p1 = prereq[1]
        has_prereq[ "%s_%s" % (p0,p1)] = \
          prereq_matches(data,p0,cut_scores) & prereq_matches(data,p1,cut_scores)
      else:
        raise "Cannot handle prerequisite list of %d or more" % len(prereq)

  return pandas.DataFrame(has_prereq)

def grade_meets_cutoff(series, cutoff):
  allowable = grade_cutoffs[cutoff]
  return series.map(lambda x: x in allowable)

def prereq_matches(data,prereq,cut_score):
    if is_course_name(prereq):
        prereq = mao.Course(prereq,normalize=False).modern_name.name
        hp = grade_meets_cutoff(data[prereq], cut_score[prereq]) | \
             grade_meets_cutoff(data["XFER_%s" % prereq], cut_score[prereq]) 
    else:
        # Test scores are stored in banner as strings.  Convert now to
        # an integer.
        hp = data[prereq].map(int,na_action="ignore")>=cut_score[prereq]
    return hp
