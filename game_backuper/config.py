from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except Exception:
    from yaml import SafeLoader
from os.path import join, relpath
from typing import List
from game_backuper.file import listdirs


class Program:
    def __init__(self, data: dict):
        self.data = data
        self._files = None

    @property
    def base(self) -> str:
        if 'base' in self.data:
            v = self.data['base']
            if isinstance(v, str) and len(v) > 0:
                return v

    def check(self) -> bool:
        if self.name is None or self.base is None:
            return False
        self.files
        return True

    def clear_cache(self):
        self._files = None

    @property
    def files(self) -> List[str]:
        ke = 'files'
        if ke not in self.data or not isinstance(self.data[ke], list):
            raise ValueError('Files is needed and should be a list.')
        if self._files is not None:
            return self._files.copy()
        r = []
        self._files = r.copy()
        for i in self.data[ke]:
            b = self.base
            if isinstance(i, str):
                r.append((i, join(b, i)))
            elif isinstance(i, dict):
                t = i['type']
                if t == 'path':
                    bp = join(b, i['path'])
                    ll = listdirs(bp)
                    for ii in ll:
                        r.append((relpath(ii, b), ii))
        return r

    @property
    def name(self) -> str:
        if 'name' in self.data:
            v = self.data['name']
            if isinstance(v, str) and len(v) > 0:
                return v


class Config:
    dest = ''
    progs = []

    def __init__(self, fn: str):
        with open(fn, 'r', encoding='UTF-8') as f:
            t = load(f.read(), SafeLoader)
        if t is None:
            raise ValueError('Can not load config file.')
        if not isinstance(t, dict):
            raise ValueError('Config file error.')
        if 'dest' not in t or not isinstance(t['dest'], str):
            raise ValueError("Config file don't have dest or dest is not str.")
        self.dest = t['dest']
        if 'programs' not in t:
            raise ValueError("No programs found.")
        progs = t['programs']
        if not isinstance(progs, list):
            raise ValueError("programs should be list.")
        for prog in progs:
            p = Program(prog)
            if not p.check():
                raise ValueError('Config error: program information error')
            self.progs.append(p)
