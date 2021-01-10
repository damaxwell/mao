from mao import Course

def test_create():
	calcI = Course(251)
	assert calcI.name == "MATH_F251X"

	calcII = Course("math",252)
	assert calcII.name == "MATH_F252X"

	acalcII = Course("math","A252")
	assert acalcII.name == "MATH_A252"

	stat200 = Course("STAT",200)
	assert stat200.name == "STAT_F200X"

def test_archaic_name():
	calcI = Course(251)
	assert calcI.name == "MATH_F251X"
	assert calcI.archaic_version.name == "MATH_F200X"
	
	acalcI = Course("MATH", "A251")
	assert acalcI.name == "MATH_A251"
	assert acalcI.archaic_version.name == "MATH_A251"

def test_modern_name():
	calcI = Course(200)
	assert calcI.name == "MATH_F200X"
	assert calcI.modern_version.name == "MATH_F251X"
	
	acalcI = Course("MATH", "A200")
	assert acalcI.name == "MATH_A200"
	assert acalcI.modern_version.name == "MATH_A200"

def test_synonyms():
	calcI = Course(251)
	synonyms = calcI.synonyms
	print(synonyms)
	assert len(synonyms) == 2
	assert Course(200) in synonyms
	assert Course(251) in synonyms

def test_sql_selector():
	calcI = Course(251)
	assert calcI.sql_selector("SUBJ","NUMBER") == "(SUBJ='MATH' AND NUMBER='F251X')"

def test_campus():
	calcI = Course(251)
	assert calcI.campus == "F"

	calcI = Course("MATH","A251")
	assert calcI.campus == "A"
