from mao import Term, TermRange, TermSet

def test_create():
	basic = Term(201301);

	assert( basic == Term(2013,1))
	assert( basic == Term("201301"))
	assert( basic != Term(2013,2))
	assert( basic != Term(2014,1))


def test_sql():
	term = Term(201301);
	assert term.sql_selector("MyField") == "(MyField = '201301')"

def test_props():
	term = Term(201301);
	assert term.year == 2013
	assert term.semester == 1
	assert term.semester_text == "Spring"
	assert term.banner_value == '201301'

def test_arithmentic():
	term = Term(201301);
	assert term+1 == Term(201302)
	assert term-1 == Term(201203)
	assert term+2 == Term(201303)
	assert term+3 == Term(201401)

def test_term_range():

	start = Term(201301)
	end = Term(201802)

	terms = TermRange(start,end)
	assert terms.sql_selector("TERM") == "(TERM >= '201301' AND TERM <= '201802')"

	assert terms.contains(201503)
	assert not terms.contains(202001)

def test_term_set():

	terms = TermSet(201301,201303)
	assert terms.sql_selector("TERM") == "((TERM = '201301') OR (TERM = '201303'))"
