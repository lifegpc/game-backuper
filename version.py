import sys
from os.path import exists, dirname, abspath, join
from subprocess import Popen, DEVNULL, PIPE


def check_git():
    p = Popen(['git', '--help'], stdout=DEVNULL, stderr=DEVNULL)
    p.wait()
    return True if p.poll() == 0 else False


def get_git_desc():
    p = Popen(['git', 'describe', '--tags', '--long', '--dirty'], stdout=PIPE,
              stderr=DEVNULL)
    p.wait()
    if p.poll() == 0:
        return p.stdout.read()


def normalize(s: str):
    li = s.split("-")
    nv = li[0].split('.')
    nv = [int(i) for i in nv if i.isnumeric()]
    if len(li) == 1:
        nv = [str(i) for i in nv]
        return '.'.join(nv)
    if li[1].isnumeric():
        if len(nv) >= 4:
            nv[-1] += int(li[1])
        else:
            while len(nv) <= 2:
                nv += [0]
            nv += [int(li[1])]
    nv = [str(i) for i in nv]
    return '.'.join(nv)


default_version = "1.0.0"
use_git = True
if '--no-git-version' in sys.argv:
    use_git = False
    sys.argv.remove("--no-git-version")
d = abspath(join(dirname(abspath(__file__)), ".git"))
if not exists(d):
    use_git = False
if use_git and not check_git():
    use_git = False
if use_git:
    d = get_git_desc()
    if d is None:
        use_git = False
        version = default_version
        dversion = version
    else:
        d = d.decode().splitlines(False)[0]
        dversion = d[1:]
        version = normalize(dversion)
else:
    version = default_version
    dversion = version
