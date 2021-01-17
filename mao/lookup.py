#TODO: fix removal of dropped students?

import mao
from mao import Course
import re

def course_selector_sql( subject_field, course_field, course_name ):
	if course_name is None:
		return ""
		
	if isinstance(course_name,list):
		courses = []
		for c in course_name:
			if not isinstance(c,Course):
				c = Course(c)
			courses.extend( [ d for d in c.synonyms ] )
	else:
		if not isinstance(course_name, mao.Course):
			course_name = mao.Course(course_name)
		courses = course_name.synonyms
	return "(%s)" % " or ".join([c.sql_selector(subject_field, course_field) for c in courses])

def combine_restrictions(a,b):
	quals = []
	if a != "":
		quals.append(a)
	if b != "":
		quals.append(b)
	selector = " and ".join(quals)
	if selector != "":
		selector += " and "
	return selector

def course_attempts(db, courses, terms):
	q = course_attempts_sql(courses, terms)
	return mao.query(db,q)

def course_attempts_sql(courses, terms):

	courses = course_selector_sql("ssbsect_subj_code","ssbsect_crse_numb",courses)
	terms = terms.sql_selector("ssbsect_term_code")

	course_term_selector = combine_restrictions(courses,terms)

	q="""
	SELECT 
	sfrstcr_pidm as pidm, 
	spriden_id as id,
	spriden_last_name as last_name,
	spriden_first_name as first_name,
	ssbsect_term_code as term_code,
	ssbsect_subj_code as subject, 
	ssbsect_crse_numb as course_number,
	ssbsect_seq_numb as section,
	ssbsect_crn as crn,
	ssbsect_camp_code as camp_code, 
	sirasgn_pidm as instructor
	FROM sirasgn, spriden, ssbsect, sfrstcr
	WHERE
	%s

	-- match term_code/crn for list of sections vs student credits
	ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn

	-- -- Ensure that waitlisted, dropped or auditing students do not appear.
	-- -- (keep enrolled or withdrawn students instead)

	and sfrstcr_rsts_code in ('AC','AD','AL','AU','FW','RE','RI','RW','WA','WD','WR','WT','WX')

	--- tack on the student identification
	and spriden_pidm = sfrstcr_pidm
	and spriden_change_ind is Null

	--- tack on instructor information if available 
	and ssbsect_term_code=sirasgn_term_code(+)
	and ssbsect_crn=sirasgn_crn(+) 
	and sirasgn_primary_ind='Y' --- There can be more than one entry in sirasgn for a given course!

	""" % course_term_selector

	return q

def course_attempts_and_grades_sql(courses, terms):

	courses = course_selector_sql("ssbsect_subj_code","ssbsect_crse_numb",courses)
	terms = terms.sql_selector("ssbsect_term_code")

	course_term_selector = combine_restrictions(courses,terms)

	q="""SELECT A.*, B.final_grade
	FROM (
	SELECT 
	sfrstcr_pidm as pidm, 
	spriden_id as id,
	spriden_last_name as last_name,
	spriden_first_name as first_name,
	ssbsect_term_code as term_code,
	ssbsect_subj_code as subject, 
	ssbsect_crse_numb as course_number,
	ssbsect_seq_numb as section,
	ssbsect_crn as crn, 
	sirasgn_pidm as instructor
	FROM sirasgn, spriden, ssbsect, sfrstcr
	WHERE
	%s

	-- match term_code/crn for list of sections vs student credits
	ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn

	-- -- Ensure that waitlisted, dropped or auditing students do not appear.
	-- -- (keep enrolled or withdrawn students instead)

	and sfrstcr_rsts_code in ('AC','AD','AL','AU','FW','RE','RI','RW','WA','WD','WR','WT','WX')

	--- tack on the student identification
	and spriden_pidm = sfrstcr_pidm
	and spriden_change_ind is Null

	--- tack on instructor information if available 
	and ssbsect_term_code=sirasgn_term_code(+)
	and ssbsect_crn=sirasgn_crn(+) 
	and sirasgn_primary_ind='Y' --- There can be more than one entry in sirasgn for a given course!
	) A

	LEFT JOIN (
	SELECT
	shrtckn_pidm as pidm,
	shrtckn_term_code as term_code,
	shrtckn_crn as crn,
	shrtckg_grde_code_final as final_grade
	FROM shrtckg, shrtckn
	WHERE
	-- match the pidm/term_code/sequence number in shrtckg to shrtckn
	shrtckg_pidm=shrtckn_pidm
	and shrtckg_tckn_seq_no=shrtckn_seq_no
	and shrtckg_term_code=shrtckn_term_code
	-- make sure we get the latest grade
	and shrtckg_activity_date = (SELECT
						  max(shrtckg_activity_date)
	                      from shrtckg
	                      where (shrtckg_pidm=shrtckn_pidm
							and shrtckg_tckn_seq_no=shrtckn_seq_no
							and shrtckg_term_code=shrtckn_term_code))	
	) B
	ON 	
	-- match the pidm/term_code/crn in sfrstcr to shrtckn
	A.pidm=B.pidm
	and A.term_code=B.term_code
	and A.crn=B.crn
	""" % course_term_selector

	return q

def basic_course_attempts_sql(courses,terms):

	courses = course_selector_sql("ssbsect_subj_code","ssbsect_crse_numb",courses)
	terms = terms.sql_selector("ssbsect_term_code")
	course_term_selector = combine_restrictions(courses,terms)

	q = """
	SELECT
	sfrstcr_pidm as pidm, 
	spriden_id as id,
	ssbsect_term_code as term_code,
	ssbsect_subj_code as subject, 
	ssbsect_crse_numb as course_number,
	ssbsect_seq_numb as section
	FROM spriden, ssbsect, sfrstcr
	WHERE
	-- Restrict courses and terms
	%s



	-- match term_code/crn for list of sections vs student credits
	ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn

	-- -- Ensure that waitlisted, dropped or auditing students do not appear.
	-- -- (keep enrolled or withdrawn students instead)
	--- sfrstcr_rsts_code in ('AC','AD','AL','AU','FW','RE','RI','RW','WA','WD','WR','WT','WX')


	--- tack on the student identification
	and spriden_pidm = sfrstcr_pidm
	and spriden_change_ind is Null

	""" % course_term_selector
	return q

def withdrawals_sql(courses,terms):

	courses = course_selector_sql("ssbsect_subj_code","ssbsect_crse_numb",courses)
	terms = terms.sql_selector("ssbsect_term_code")
	course_term_selector = combine_restrictions(courses,terms)

	q = """
	SELECT
	sfrstcr_pidm as pidm, 
	spriden_id as id,
	ssbsect_term_code as term_code,
	ssbsect_subj_code as subject, 
	ssbsect_crse_numb as course_number,
	ssbsect_seq_numb as section
	FROM spriden, ssbsect, sfrstcr
	WHERE
	-- Restrict courses and terms
	%s



	-- match term_code/crn for list of sections vs student credits
	ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn

	-- -- Ensure that waitlisted, dropped or auditing students do not appear.
	-- -- (keep enrolled or withdrawn students instead)
	and sfrstcr_rsts_code like 'W%%'


	--- tack on the student identification
	and spriden_pidm = sfrstcr_pidm
	and spriden_change_ind is Null

	""" % course_term_selector
	return q

def basic_course_attempts_and_grades_sql(courses,terms):

	courses = course_selector_sql("ssbsect_subj_code","ssbsect_crse_numb",courses)
	terms = terms.sql_selector("ssbsect_term_code")
	course_term_selector = combine_restrictions(courses,terms)

	q = """
	SELECT
	sfrstcr_pidm as pidm, 
	spriden_id as id,
	ssbsect_term_code as term_code,
	ssbsect_subj_code as subject, 
	ssbsect_crse_numb as course_number,
	ssbsect_seq_numb as section,
	shrtckg_grde_code_final as final_grade
	FROM shrtckg, shrtckn, spriden, ssbsect, sfrstcr
	WHERE
	-- Restrict courses and terms
	%s



	-- match term_code/crn for list of sections vs student credits
	ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn

	-- -- Ensure that waitlisted, dropped or auditing students do not appear.
	-- -- (keep enrolled or withdrawn students instead)
	--- sfrstcr_rsts_code in ('AC','AD','AL','AU','FW','RE','RI','RW','WA','WD','WR','WT','WX')	

	--- tack on the student identification
	and spriden_pidm = sfrstcr_pidm
	and spriden_change_ind is Null

	-- tack on grade information:
	-- match the pidm/term_code/crn in sfrstcr to shrtckn
	and shrtckn_pidm=sfrstcr_pidm
	and shrtckn_term_code=sfrstcr_term_code
	and shrtckn_crn=sfrstcr_crn
	-- -- match the pidm/term_code/sequence number in shrtckg to shrtckn
	and shrtckg_pidm=shrtckn_pidm
	and shrtckg_tckn_seq_no=shrtckn_seq_no
	and shrtckg_term_code=shrtckn_term_code
	-- make sure we get the latest grade
	and shrtckg_activity_date = (SELECT
						  max(shrtckg_activity_date)
	                      from shrtckg
	                      where (shrtckg_pidm=shrtckn_pidm
							and shrtckg_tckn_seq_no=shrtckn_seq_no
							and shrtckg_term_code=shrtckn_term_code))

	""" % course_term_selector
	return q


# Same as course_attempts, but we are able to
# return a column indicating the semester of first attempt
# for the course (in either archaic or modern form).
def single_course_first_attempts(db, course, terms):
	q = single_course_first_attempts_sql(course, terms)
	return mao.query(db,q)

def single_course_first_attempts_sql(course, terms):

	# Make sure we are only looking at one course
	if ~isinstance(course,Course):
		course = Course(course)
	courses = course_selector_sql("ssbsect_subj_code", "ssbsect_crse_numb",course)

	all_attempts_sql = basic_course_attempts_sql(course,terms)

	q="""SELECT C.*, first_attempt.first_term_code FROM
	( %s ) C
	JOIN
	( SELECT 	
	sfrstcr_pidm as pidm,
	MIN(ssbsect_term_code) as first_term_code 
	FROM ssbsect, sfrstcr
	WHERE
	-- Restrict courses
	%s
	-- match term_code/crn for list of sections vs student credits
	and ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn
	GROUP BY sfrstcr_pidm
	) first_attempt
	ON C.pidm = first_attempt.pidm
""" % (all_attempts_sql,courses)

	return q


def attempts_with_prereq_course(db,course_name, prereq_course_name, terms):
	q = attempts_with_prereq_course_sql(course_name, prereq_course_name, terms)

	table = mao.query(db,q)

	return table


def attempts_with_prereq_course_sql(course_name, prereq_course_name, terms):

	this_course = basic_course_attempts_sql(course_name,terms)
	prereq_course = basic_course_attempts_and_grades_sql(prereq_course_name, 
		mao.TermRange(start=None,end=None))

	q="""SELECT a.*, b.term_code as prereq_term_code, b.subject as prereq_subject, b.course_number as prereq_course_number, b.final_grade as prereq_score, b.section as prereq_section 
	FROM ( %s ) a
	JOIN ( %s ) b
	ON a.pidm = b.pidm
	WHERE a.term_code > b.term_code
""" % (this_course, prereq_course)

	return q


def attempts_with_prereq_xfer_course(db, course_name, prereq_course_name, terms):
	q = attempts_with_prereq_xfer_course_sql(course_name, prereq_course_name, terms)
	table = mao.query(db,q)

	return table

def attempts_with_prereq_xfer_course_sql(course_name, prereq_course_name, terms):

	class_sql = basic_course_attempts_sql(course_name,terms)

	xfer_courses = course_selector_sql("shrtrce_subj_code","shrtrce_crse_numb",prereq_course_name)

	q="""SELECT a.*, b.term_code as prereq_term_code, b.subj_code as prereq_subj_code, b.course_number as prereq_course_number, b.final_grade as prereq_score FROM 
	(%s) a
	JOIN ( SELECT 
	shrtrce_pidm as pidm, 
	shrtrce_term_code_eff as term_code,
	shrtrce_subj_code as subj_code, 
	shrtrce_crse_numb as course_number,
	shrtrce_grde_code as final_grade
	FROM shrtrce
	WHERE
	-- List of courses
	%s
	)  b
	ON a.pidm = b.pidm
	--- Use >= since the term_code is the semester the transfer was approved.
	WHERE a.term_code >= b.term_code
""" % (class_sql,xfer_courses)

	return q

def attempts_with_prereq_tests(db,course_name, prereqs, terms):
	q = attempts_with_prereq_tests_sql(course_name, prereqs, terms)
	return mao.query(db,q)

	return df

def attempts_with_prereq_tests_sql(course_name, prereqs, terms):

	courses = course_selector_sql("ssbsect_subj_code","ssbsect_crse_numb",course_name)
	terms = terms.sql_selector("ssbsect_term_code")
	course_and_terms = combine_restrictions(courses,terms)

	test_codes = "("
	for (k,test) in enumerate(prereqs):
		if k!=0:
			test_codes += ","
		test_codes += "'%s'" % test
	test_codes += ")"

	q="""SELECT  	
	sfrstcr_pidm as pidm, 
	spriden_id as id,
	ssbsect_term_code as term_code,
	ssbsect_subj_code as subject, 
	ssbsect_crse_numb as course_number,
	ssbsect_seq_numb as section,
	sortest_tesc_code as test_code,
    sortest_test_score as test_score,
    sortest_test_date as test_date,
    SFRRSTS_END_DATE as registration_end_date

	FROM SFRRSTS, sortest, spriden, ssbsect, sfrstcr
	WHERE
	-- Restrict courses/terms
	%s

	-- match term_code/crn for list of sections vs student credits
	ssbsect_term_code=sfrstcr_term_code
	and ssbsect_crn=sfrstcr_crn

	and SFRRSTS_TERM_CODE = sfrstcr_term_code
	and SFRRSTS_PTRM_CODE = sfrstcr_ptrm_code

	-- Identitify the end of web registration for the course.  The
	-- prereq must have been taken before this date.
	and SFRRSTS_RSTS_CODE = 'RW'
	--- and sfrrsts_rsts_code in ('AC','AD','AL','AU','FW','RE','RI','RW','WA','WD','WR','WT','WX')
	and sortest_test_date <= SFRRSTS_END_DATE

	--- tack on the student identification
	and spriden_pidm = sfrstcr_pidm
	and spriden_change_ind is Null

	and sortest_pidm = sfrstcr_pidm
	and sortest_tesc_code in %s
""" % (course_and_terms,test_codes)

	return q

""" 
Given an SQL query that contains a PIDM column (`query_pidm`)
and a term code column (`query_term_code`) returns an SQL
query that generates the same table but adds on columns
for major 1 and major 2 for the student in effect at the
time of the original table's term code.
"""
def join_majors(query, query_pidm, query_term_code):
	q = """
	SELECT D.*, SGBSTDN_COLL_CODE_1 AS MAJOR_1_COLLEGE, SGBSTDN_DEGC_CODE_1 AS MAJOR_1_DEGREE, SGBSTDN_MAJR_CODE_1 AS MAJOR_1, SGBSTDN_COLL_CODE_2 as MAJOR_2_COLLEGE, SGBSTDN_DEGC_CODE_2 AS MAJOR_2_DEGREE, SGBSTDN_MAJR_CODE_2 AS MAJOR_2 FROM
		(SELECT C.*, MAJOR_TERM_CODE_EFF FROM
			(SELECT MQ1.PIDM,  MAX(SGBSTDN_TERM_CODE_EFF) AS MAJOR_TERM_CODE_EFF FROM ( %s ) MQ1
			JOIN SGBSTDN
			ON MQ1.%s = SGBSTDN.SGBSTDN_PIDM AND MQ1.%s >= SGBSTDN_TERM_CODE_EFF
			GROUP BY MQ1.PIDM ) B
		JOIN ( %s ) C
		ON B.PIDM = C.PIDM ) D
		JOIN SGBSTDN on 
	D.PIDM = SGBSTDN_PIDM AND MAJOR_TERM_CODE_EFF = SGBSTDN_TERM_CODE_EFF
	ORDER BY LAST_NAME
	""" % (query, query_pidm, query_term_code, query)
	return q

""" 
Given an SQL query that contains a PIDM column (`query_pidm`)
and a term code column (`query_term_code`) returns an SQL
query that generates the same table but adds on columns
for major 1 and major 2 for the student in effect at the
time of the original table's term code.
"""
def join_student_campus_code(query, query_pidm, query_term_code):
	q = """
	SELECT D.*, SGBSTDN_CAMP_CODE AS STUDENT_CAMP_CODE FROM
		(SELECT C.*, TERM_CODE_EFF FROM
			(SELECT MQ1.PIDM,  MAX(SGBSTDN_TERM_CODE_EFF) AS TERM_CODE_EFF FROM ( %s ) MQ1
			JOIN SGBSTDN
			ON MQ1.%s = SGBSTDN.SGBSTDN_PIDM AND MQ1.%s >= SGBSTDN_TERM_CODE_EFF
			GROUP BY MQ1.PIDM ) B
		JOIN ( %s ) C
		ON B.PIDM = C.PIDM ) D
		JOIN SGBSTDN on 
	D.PIDM = SGBSTDN_PIDM AND TERM_CODE_EFF = SGBSTDN_TERM_CODE_EFF
	ORDER BY LAST_NAME
	""" % (query, query_pidm, query_term_code, query)
	return q
