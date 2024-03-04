import os, sys, mao, datetime, yaml
import pandas.io.sql as psql
from sqlalchemy import create_engine


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
        import getpass
        passwd=getpass.getpass()

    host = 'rptp.alaska.edu'
    port = 1521
    service_name='rptp.alaska.edu'
  
    engine = create_engine(f'oracle+oracledb://{user_name}:{passwd}@{host}:{port}/?service_name={service_name}')

    return engine


class Session:

    def __init__(self,argv=None,save_record=True,recording_file=None):
        if argv == None:
            argv = sys.argv
        self._argv = argv

        self._db = mao.open_database()
        self._queries = []

        if recording_file is None:
            now = datetime.datetime.now() # current date and time
            time = now.strftime("%Y-%m-%d:%H:%M:%S")
            file_base = os.path.basename(sys.argv[0])

            target_dir = "mao_queries"
            if not os.path.isdir(target_dir):
                if os.path.exists(target_dir):
                    raise "Unable to save mao queries into directory %s; is an existing file" % target_dir
                os.mkdir(target_dir)

            recording_file = os.path.join(target_dir,file_base+"_"+time+".yml")


        self._recording_file = recording_file


    def query(self, qstring, description=None):
        if description is None:
            description = "NO DESCRIPTION"
        self._queries.append({'description':description, 'sql':clean_str(qstring)})
        return psql.read_sql(qstring, self._db)

    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_value, traceback):
        with open(self._recording_file,"w") as f:
            contents = {'argv':self._argv}
            contents['queries'] = self._queries

            yaml.add_representer(str, str_presenter)
            yaml.dump(contents,f)

        return False


