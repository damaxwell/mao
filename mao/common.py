import re, sys
import cx_Oracle
import pandas.io.sql as psql

def open_database():

    user_name = None

    if sys.platform == 'darwin':
        from . import mac_keychain
        creds = mac_keychain.get_credentials('rptp.alaska.edu')
        if creds is not None:
            (user_name, passwd) = creds


    if user_name is None:
        sys.stderr.write("Username: ")
        sys.stderr.flush()
        user_name = sys.stdin.readline().strip()
        if user_name is None:
            raise EOFError
        passwd=getpass.getpass()

    tns=cx_Oracle.makedsn('rptp.alaska.edu',1541,service_name='rptp.alaska.edu')
    db = cx_Oracle.connect(user_name,passwd,tns)

    return db

def query(db, qstring):
        return psql.read_sql(qstring, db)


"""
  A course is described by a combination of two strings:

  * A *subject* (e.g. MATH/DEVM/CHEM, etc)

  * A *course number*, which is not a number, but typically
    has additional character decorations (e.g. F251X, F412).

  It can be convenient to represent a course via a single string,
  a *course name*, which is a contatination of the subject
  and course number with an underscore, e.g. 'MATH_F251X'.
  The course name does not exist as a concept in Banner or RPTP
  but is useful for post-processing.

  Several math classes have two course numbers associated
  with them.  Prior to Fall 2015 one set of numbers was used,
  and after harmonization a different set of numbers has been used.
  We refer to these two numbering schemes as *archaic* or *modern*,
  which are *synonyms* of each other.  A `Course` maintains a distinction
  between these two numbers (i.e. a single `Course` represents
  only one of 'MATH_F251X' or 'MATH_F200X' but allows for conversion
  between these two names via `archaic_name` and `modern_name`, as
  well as a list of all equivalent `synonyms`.)
"""
class Course:

    """Attempts to construct a `Course` from partial
    information that could desribe a course.

    Given one argument, `course`:

      If `course` is a number, it is assumed to be the course
      number.

      If `course` is a string, we attempt to extract a subject
      and course number from it, either by interpeting 
      `course` as a course name (i.e subject and number joined
      by an underscore) or as an optional subject and required
      number joined by a space.

    Given two arguments they are taken to be `subject` and `number`.

    If the subject has not been specified directly, it
    is inferred to be MATH/DEVM based on the course number.

    Subjects are always converted to upper case.

    A single keyword argument `normalize` is accepted.  If `normalize`
    is `True` (default) then an attempt is made to convert the
    course number into a cannonical version, adding the prefix `F`
    and adding an `X` if the course number is in the list of known
    MATH/STAT core classes.
"""
    def __init__(self, *args, **kwargs):

        normalize = kwargs.pop('normalize', True)

        self._subject = None
        self._number = None

        if len(args) == 2:
            self._subject = str(args[0])
            course = args[1]
            if isinstance(course,float):
                course = int(course)
            self._number = str(course)
        else:
            if len(args) != 1:
                raise ValueError("Wrong number of arguments")

            course = args[0]
            if type(course) == type(self):
                self._subject = course._subject
                self._number = course._number
                return

            if isinstance(course,int) or isinstance(course,float):
                self._number = str(int(course))
            else:
                course = str(course)
                course_regex = "([a-z|A-Z]+)[ ,_]+?([A-Z]?[0-9]+[a-z|A-Z]*)"
                match = re.match(course_regex, course)
                if match is not None:                    
                    self._subject = match.groups()[0]
                    self._number = match.groups()[1]
                else:
                    course_regex = "([A-Z]?[0-9]+[a-z|A-Z]*)"
                    match = re.match(course_regex, course)
                    if match is not None:                    
                        self._number = match.groups()[0]
                    else:
                        raise ValueError( "Cannot construct a course from '%s'" % course )

        # If we haven't yet determined a subject, it's MATH or DEVM.
        # Decide which based on the number.
        if self._subject == None:

                number_regex = "[A-Z]?([0-9]+)[a-z|A-Z]*"
                match = re.match(number_regex, self._number)
                course_number_int = int(match.groups()[0])

                if course_number_int >= 107 or course_number_int == 103:
                    self._subject = "MATH"
                else:
                    self._subject = "DEVM"

        self._subject = self.subject.upper()

        if normalize:
            course_number_regex="([A-Z]?)([0-9]+)[a-z|A-Z]*"
            match = re.match(course_number_regex, self._number)

            campus = match.groups()[0];
            if campus == "":
                campus = "F"
            course_number = int(match.groups()[1])

            self._number = "%s%03d" % (campus,course_number)

            # Only Fairbanks does the X thing
            if campus == "F":
                if self._subject == "MATH":
                    if self._number in core_math:
                        self._number = self._number + "X"
                if self._subject == "STAT":
                    if self._number in core_stat:
                        self._number = self._number + "X"

    @property
    def campus(self):
        course_number_regex="([A-Z]?)([0-9]+)[a-z|A-Z]*"
        match = re.match(course_number_regex, self._number)
        return match.groups()[0]

    """Returns the course name prior to renaming in 2015"""
    @property
    def archaic_version(self):
        new_course_name = course_name_translation_table.get(self.name,None)
        if new_course_name is None:
            return self
        return Course(new_course_name)

    """Returns the course name post renaming in 2015"""
    @property
    def modern_version(self):
        try:
            n = list(course_name_translation_table.values()).index(self.name)
            return Course(list(course_name_translation_table.keys())[n])
        except ValueError:
            return self

    """Returns the course name: SUBJ_NUMBER"""
    @property
    def name(self):
        return "%s_%s" % (self._subject,self._number)

    @property
    def synonyms(self):
        archaic = self.archaic_version
        modern = self.modern_version
        if archaic == modern:
            return [modern]
        return [archaic, modern]

    @property
    def subject( self ):
        return self._subject

    @property
    def number( self ):
        return self._number

    """ Returns a SQL clause suitable for filtering a course
    exactly equal to this one.

    Parameters
    ----------    
    subject_field_name: The SQL column name containing subjects
    course_field_name: The SQL column name containing course numbers
    """ 
    def sql_selector(self, subject_field_name, course_field_name, ):
        return "(%s='%s' AND %s='%s')" % \
        (subject_field_name,self.subject,course_field_name,self.number)

    """Compares this `Course` to another. Subjects and course numbers 
    must match identically"""
    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return (self._subject == other._subject) and (self._number == other._number)

    def __str__(self):
        return "%s_%s" % (self.subject,self.number)

    def __repr__(self):
        return self.name

# Convert archaic course names into modern equivalents
course_name_translation_table = {
    "DEVM_F054" : "DEVM_F050",
    "DEVM_F055" : "DEVM_F060",
    "DEVM_F055D" : "DEVM_F094D",
    "DEVM_F055E" : "DEVM_F094E",
    "DEVM_F055F" : "DEVM_F094F",
    "DEVM_F105N" : "DEVM_F106",
    "DEVM_F105G" : "DEVM_F194G",
    "DEVM_F105H" : "DEVM_F194H",
    "DEVM_F105J" : "DEVM_F194J",
    "MATH_F113X":"MATH_F103X",
    "MATH_F151X":"MATH_F107X",
    "MATH_F152X":"MATH_F108",
    "MATH_F122X":"MATH_F161X",
    "MATH_F251X":"MATH_F200X",
    "MATH_F252X":"MATH_F201X",
    "MATH_F253X":"MATH_F202X",
    "MATH_F211":"MATH_F205",
    "MATH_F212":"MATH_F206",
    "MATH_F265":"MATH_F215",
    "MATH_F222X":"MATH_F262X",
    "MATH_F232X":"MATH_F272X",
    "MATH_F156X":"MATH_F194X" }

# List of clases that are core (and hence should terminate in X)
core_math = [ # archaic course names
              "F200", "F201", "F202", "F107", "F103", "F161", "F262", "F272", "F194",
              # modern course names....
              "F113", "F114", "F151", "F152", "F122", "F222", "F230", "F232", "F156", "F251", "F252", "F253" ]
core_stat = [ "F200" ]

dawn_of_time = 199801

semester_text_value = { 1:"Spring", 2:"Summer", 3:"Fall"}

""" 
Represents a term (a year/semester pair).

Banner represents terms by an integer YYYYSS
where SS encodes semester by Spring/Summer/Fall being 01/02/03.

"""
class Term:
    """ Creates a Term from either a single integer banner value 
    (possibly represented as a string) or from a pair year/semester 
    of integers.
    """
    def __init__(self,*args):
        if len(args) == 1:
            term = args[0]
            if isinstance(term,Term):
                self._term = term._term
                return
            if isinstance(term,str):
                term = int(term)
            if not isinstance(term,int):
                raise ValueError(term)
            self._term = term
        else:
            if len(args)!=2:
                raise ValueError(args)
            year = args[0]; semester = args[1]
            if not (isinstance(year,int) and isinstance(semester,int)):
                raise ValueError(args)
            self._term = 100*year + semester

    """Returns an SQL clause sutable for matching the
    given term_field_name with this Term"""
    def sql_selector(self, term_field_name):
        return "(%s = '%s')" % (term_field_name,self._term)

    @property
    def year(self):
        return self._term // 100

    @property
    def semester(self):
        return self._term % 100

    """Returns a name representing the semester (Spring/Summer/Fall)"""
    @property
    def semester_text(self):
        return semester_text_value[self.semester]

    @property
    def season(self):
        return self.semester

    """Returns a name representing the semester (Spring/Summer/Fall)"""
    @property
    def season_text(self):
        return self.semester_text

    def __str__(self):
        return "%s %d" % (self.semester_text,self.year)

    """Returns a string representation of the integer YYYYSS
    representing the term.  Banner stores semesters as strings"""
    @property
    def banner_value(self):
        return repr(self)

    def __repr__(self):
        return "%d" % self._term

    """Adds a number of terms to the current term.  There 
    are three terms in a year, so 

      201902 + 1 = 201903
      201902 + 2 = 202001
      201902 + 3 = 202003
    """
    def __add__(self,delta_terms):
        delta_year = delta_terms // 3
        delta_semester = delta_terms % 3
        new_semester = self.semester + delta_semester
        if new_semester < 1:
            delta_year = delta_year - 1
            new_semester = new_semester + 3
        if new_semester > 3:
            delta_year = delta_year + 1
            new_semester = new_semester - 3
        new_year = delta_year + self.year
        return Term(new_year, new_semester)

    def __sub__(self,terms):
        return self + (-terms)

    def __le__(self,other):
        return self._term <= other._term
    def __ge__(self,other):
        return self._term >= other._term
    def __lt__(self,other):
        return self._term < other._term
    def __gt__(self,other):
        return self._term > other._term
    def __eq__(self,other):
        return self._term == other._term


class TermRange:

    """ Represents a range of terms t_start <= t <= t_end

    Parameters
    ----------
    start: first term in the range
    end: last term in the range
    """
    def __init__(self, start, end):

        if end is not None and start is not None:
            if start > end:
                tmp = start
                start = end
                end = start
        if start is not None:
            start = Term(start)
        if end is not None:
            end = Term(end)

        self._start = start
        self._end = end

    """
    Determines if a term is contained in the range
    """
    def contains(self, term):
        term = Term(term)
        if self._start is not None:
            if self._start > term:
                return False
        if self._end is not None:
            if self._end < term:
                return False
        return True

    def __iter__(self):
        current = self._start
        if current is None:
            current = Term(dawn_of_time)

        if self._end is None:
            while True:
                yield current
                current = current + 1
        else:
            while current <= self._end:
                yield current
                current = current + 1



    """Returns an SQL clause sutable for matching the
    given term_field_name with the terms in this range"""
    def sql_selector(self, term_field_name):
        if self._start is None and self._end is None:
            return ""
        if self._start is None:
            return "(%s <= '%s')" %(term_field_name,repr(self._end))
        if self._end is None:
            return "(%s >= '%s')" %(term_field_name,repr(self._start))
        return "(%s >= '%s' AND %s <= '%s')" % \
        (term_field_name,repr(self._start),term_field_name,repr(self._end))

    def __eq__(self, other):
        if type(other) != type(self):
            return false
        return (self._start == other._start) and (self._end == other._end)

    def __str__(self):
        start = self._start
        end = self._end
        if start is None and end is None:
            return "All terms"
        if start is None:
            return "All terms up to %s" % Term(end)
        if end is None:
            return "All terms starting %s" % Term(start)
        return "Terms from %s to %s" % (Term(start),Term(end))

    def __repr__(self):
        return("TermRange(%s,%s)" % (repr(self._start),repr(self._end)))

"""Represents a collection of specific terms"""
class TermSet:
    """Constructs from a variable number of `Term`s or term-like objects"""
    def __init__(self,*args):
        self.terms = [Term(t) for t in args]

    """Returns an SQL clause sutable for matching the
    given term_field_name with the terms in this collection"""
    def sql_selector(self, term_field_name):
        return "(%s)" % " OR ".join([ "%s" % t.sql_selector(term_field_name) for t in self.terms])
