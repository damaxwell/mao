from subprocess import check_output, STDOUT, CalledProcessError
from sys import platform
import re

# password: "XXXXX"
find_passwd = re.compile('password: "([^"]+)"').search
#     "acct"<blob>="miki.tebeka@gmail.com"
find_user = re.compile('"acct"<blob>="([^"]+)"').search


def find_key(fn, out):
    match = fn(out)
    return match and match.group(1)


def get_credentials(domain):

    if platform != 'darwin':
        raise SystemExit('error: mac_keychain.get_credentials() works only on OSX')

    cmd = [
        'security',
        'find-generic-password',
        '-g',
        '-s', domain,
    ]
    try:
        out = check_output(cmd, stderr=STDOUT).decode('utf-8')
    except CalledProcessError:
        return None

    user = find_key(find_user, out)
    if not user:
        return None

    passwd = find_key(find_passwd, out)
    if not passwd:
        return None

    return (user, passwd)
