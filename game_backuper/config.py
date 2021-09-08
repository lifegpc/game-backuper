from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except Exception:
    from yaml import SafeLoader
from os.path import join, relpath, isfile, isdir, isabs
from typing import List, Union
from game_backuper.file import listdirs
from collections import namedtuple
try:
    from functools import cached_property
except ImportError:
    cached_property = property


class BasicOption:
    _remove_old_files = None

    @cached_property
    def remove_old_files(self) -> bool:
        if self._remove_old_files is not None:
            return self._remove_old_files
        prog = getattr(self, "_prog", None)
        if prog is not None:
            if prog._remove_old_files is not None:
                return prog._remove_old_files
        cfg = getattr(self, "_cfg", None)
        if cfg is not None:
            if cfg._remove_old_files is not None:
                return cfg._remove_old_files
        return True

    def parse_all(self, data=None):
        self.parse_remove_old_files(data)

    def parse_remove_old_files(self, data=None):
        if data is None:
            data = getattr(self, 'data')
        if 'remove_old_files' in data:
            v = data['remove_old_files']
            if isinstance(v, bool):
                self._remove_old_files = v
            else:
                raise TypeError('remove_old_files option must be a boolean.')
            del v


def namedtuple_bo(typename, field_names):
    a = namedtuple(typename, field_names)
    return type(typename, (a, BasicOption), {})


ConfigNormalFile = namedtuple_bo('ConfigNormalFile', ['name', 'full_path'])
ConfigLeveldb = namedtuple_bo('ConfigLeveldb', ['name', 'full_path', 'domains'])  # noqa: E501
ConfigResult = Union[ConfigNormalFile, ConfigLeveldb]


class Program(BasicOption):
    def __init__(self, data: dict, cfg):
        self.data = data
        self._files = None
        self._cfg = cfg
        self.parse_all()

    @cached_property
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
    def files(self) -> List[ConfigResult]:
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
                if isabs(i):
                    raise ValueError('Absolute path must need a name.')
                bp = join(b, i)
                if isfile(bp):
                    r.append(ConfigNormalFile(i, bp))
                elif isdir(bp):
                    ll = listdirs(bp)
                    for ii in ll:
                        r.append(ConfigNormalFile(relpath(ii, b), ii))
            elif isinstance(i, dict):
                t = i['type']
                if t == 'path':
                    if isabs(i['path']):
                        if 'name' not in i or not isinstance(i['name'], str) or i['name'] == '':  # noqa: E501
                            raise ValueError('Absolute path must need a name.')
                        bp = i['path']
                        name = i['name']
                    else:
                        bp = join(b, i['path'])
                        name = i['path']
                        if 'name' in i and isinstance(i['name'], str):
                            if i['name'] != '':
                                name = i['name']
                    if isfile(bp):
                        tmp = ConfigNormalFile(name, bp)
                        tmp.parse_all(i)
                        r.append(tmp)
                    elif isdir(bp):
                        ll = listdirs(bp)
                        for ii in ll:
                            tmp = ConfigNormalFile(join(name, relpath(ii, bp)), ii)  # noqa: E501
                            tmp.parse_all(i)
                            r.append(tmp)
                elif t == 'leveldb':
                    if isabs(i['path']):
                        if 'name' not in i or not isinstance(i['name'], str) or i['name'] == '':  # noqa: E501
                            raise ValueError('Absolute path must need a name.')
                        p = i['path']
                        n = i['name']
                    else:
                        p = join(b, i['path'])
                        n = i['path']
                        if 'name' in i and isinstance(i['name'], str):
                            if i['name'] != '':
                                n = i['name']
                    dms = None
                    if 'domains' in i and isinstance(i['domains'], list):
                        dms = []
                        for ii in i['domains']:
                            if isinstance(ii, str) and len(ii) > 0:
                                dms.append(ii.encode())
                        if len(dms) == 0:
                            dms = None
                    tmp = ConfigLeveldb(n, p, dms)
                    tmp.parse_all(i)
                    r.append(tmp)
        for i in r:
            i._prog = self
        return r

    @cached_property
    def name(self) -> str:
        if 'name' in self.data:
            v = self.data['name']
            if isinstance(v, str) and len(v) > 0:
                return v


class Config(BasicOption):
    dest = ''
    progs = []
    progs_name = []

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
        self.parse_all(t)
        progs = t['programs']
        if not isinstance(progs, list):
            raise ValueError("programs should be list.")
        for prog in progs:
            p = Program(prog, self)
            if not p.check():
                raise ValueError('Config error: program information error')
            if p.name not in self.progs_name:
                self.progs_name.append(p.name)
                self.progs.append(p)
            else:
                raise ValueError(f'have same name "{p.name}" in programs.')
