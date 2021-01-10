import os, sys, mao, datetime, yaml

def session(argv=None,save_record=True,recording_file=None):
    return Session(argv=None,save_record=True,recording_file=None)

"""Presenter for savign multiline strings in YAML as multiline strings if possible."""
def str_presenter(dumper, data):
    try:
        dlen = len(data.splitlines())
        if (dlen > 1):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    except TypeError as ex:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

"""Removes trailing whitespace at lineends and converts tabs to spaces in a 
string to allow the string to be saved in multiline format in YAML"""
def clean_str(q):
    q = q.replace("\t","    ")
    lines = []
    for l in q.splitlines():
        lines.append(l.rstrip())
    return "\n".join(lines)


class Session:

    def __init__(self,argv=None,save_record=True,recording_file=None):
        if argv == None:
            argv = sys.argv
        self._argv = argv

        # self._db = mao.open_database()
        self._queries = []

        if recording_file is None:
            now = datetime.datetime.now() # current date and time
            time = now.strftime("%Y-%m-%d:%H:%M:%S")
            file_base = os.path.basename(sys.argv[0])
            recording_file = file_base+"_"+time+".yml"

        self._recording_file = recording_file

    def query(self, qstring, description=None):
        if description is None:
            description = "NO DESCRIPTION"
        self._queries.append({'description':description, 'sql':clean_str(qstring)})

    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_value, traceback):
        with open(self._recording_file,"w") as f:
            contents = {'argv':self._argv}
            contents['queries'] = self._queries

            yaml.add_representer(str, str_presenter)
            yaml.dump(contents,f)

        return False


