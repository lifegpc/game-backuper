from yaml import load
try:
    from yaml import CSafeLoader as SafeLoader
except Exception:
    from yaml import SafeLoader
from os.path import join, relpath, isfile, isdir, isabs, abspath
from typing import List, Union
from game_backuper.file import listdirs
from collections import namedtuple
try:
    from functools import cached_property
except ImportError:
    cached_property = property
from game_backuper.regexp import Regex, wildcards_to_regex
from game_backuper.compress import CompressConfig


class BasicOption:
    '''Basic options which is included in config, program and files.'''
    _remove_old_files = None
    _enable_pcre2 = None
    _encrypt_files = None
    _compress_config = None

    @property
    def compress_config(self) -> CompressConfig:
        if self._compress_config is not None:
            return self._compress_config
        prog = getattr(self, "_prog", None)
        if prog is not None:
            if prog._compress_config is not None:
                return prog._compress_config
        cfg = getattr(self, "_cfg", None)
        if cfg is not None:
            if cfg._compress_config is not None:
                return cfg._compress_config
        return None

    @cached_property
    def enable_pcre2(self) -> bool:
        if self._enable_pcre2 is not None:
            return self._enable_pcre2
        prog = getattr(self, "_prog", None)
        if prog is not None:
            if prog._enable_pcre2 is not None:
                return prog._enable_pcre2
        cfg = getattr(self, "_cfg", None)
        if cfg is not None:
            if cfg._enable_pcre2 is not None:
                return cfg._enable_pcre2
        return False

    @cached_property
    def encrypt_files(self) -> bool:
        if self._encrypt_files is not None:
            return self._encrypt_files
        prog = getattr(self, "_prog", None)
        if prog is not None:
            if prog._encrypt_files is not None:
                return prog._encrypt_files
        cfg = getattr(self, "_cfg", None)
        if cfg is not None:
            if cfg._encrypt_files is not None:
                return cfg._encrypt_files
        return False

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
        self.parse_compress_config(data)
        self.parse_remove_old_files(data)
        self.parse_enable_pcre2(data)
        self.parse_encrypt_files(data)

    def parse_compress_config(self, data=None):
        if data is None:
            data = getattr(self, 'data')
        if 'compress_method' in data:
            v = data['compress_method']
            if isinstance(v, str):
                self._compress_config = CompressConfig(v, data.get("compress_level"))  # noqa: E501
            elif v is not None:
                raise TypeError('compress_method option should be str or None.')  # noqa: E501

    def parse_enable_pcre2(self, data=None):
        if data is None:
            data = getattr(self, 'data')
        if 'enable_pcre2' in data:
            v = data['enable_pcre2']
            if isinstance(v, bool):
                self._enable_pcre2 = v
            else:
                raise TypeError('enable_pcre2 option must be a boolean.')
            del v

    def parse_encrypt_files(self, data=None):
        if data is None:
            data = getattr(self, 'data')
        if 'encrypt_files' in data:
            v = data['encrypt_files']
            if isinstance(v, bool):
                self._encrypt_files = v
            else:
                raise TypeError('encrypt_files option must be a boolean.')
            del v

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


class NFBasicOption:
    """Basic options which is included in config, program."""
    _ignore_hidden_files = None

    def __init__(self, cfg=None, prog=None):
        self._cfg = cfg
        self._prog = prog

    @cached_property
    def ignore_hidden_files(self) -> bool:
        if self._ignore_hidden_files is not None:
            return self._ignore_hidden_files
        prog = getattr(self, "_prog", None)
        if prog is not None:
            if prog._ignore_hidden_files is not None:
                return prog._ignore_hidden_files
        cfg = getattr(self, "_cfg", None)
        if cfg is not None:
            if cfg._ignore_hidden_files is not None:
                return cfg._ignore_hidden_files
        return True

    def parse_all_nf(self, data=None):
        self.parse_ignore_hidden_files(data)

    def parse_ignore_hidden_files(self, data=None):
        if data is None:
            data = getattr(self, 'data')
        if 'ignore_hidden_files' in data:
            v = data['ignore_hidden_files']
            if isinstance(v, bool):
                self._ignore_hidden_files = v
            else:
                raise TypeError('ignore_hidden_files option must be a bool.')
            del v


# pylint: disable=unsupported-membership-test, unsubscriptable-object
class BasicConfig:
    def __repr__(self) -> str:
        data = getattr(self, "data", None)
        return f"{self.__class__.__name__}<{data}>"

    @cached_property
    def name(self) -> str:
        data = getattr(self, "data", None)
        if isinstance(data, dict) and 'name' in data:
            v = data['name']
            if isinstance(v, str) and len(v) > 0:
                return v

    @cached_property
    def real_name(self) -> str:
        return self.name if self.name else self.path

    @cached_property
    def path(self) -> str:
        data = getattr(self, "data", None)
        if isinstance(data, dict) and 'path' in data:
            v = data['path']
            if isinstance(v, str) and len(v) > 0:
                return v
        raise ValueError('Path not found.')

    @cached_property
    def type(self) -> str:
        data = getattr(self, "data", None)
        if isinstance(data, dict) and 'type' in data:
            v = data['type']
            if isinstance(v, str) and len(v) > 0:
                return v
        raise ValueError('Type not found.')
# pylint: enable=unsupported-membership-test, unsubscriptable-object


def parse_ex_or_in_cludes(li: list, enable_pcre2) -> List[Union[str, Regex]]:
    r = []
    for i in li:
        if isinstance(i, str):
            r.append(i)
        elif isinstance(i, dict):
            t = i['type']
            if t == 'wildcards':
                r.append(wildcards_to_regex(i['rule'], use_pcre2=enable_pcre2))
            elif t == "regex":
                r.append(Regex(i['rule'], use_pcre2=enable_pcre2))
    return r


class ConfigPath(BasicOption, NFBasicOption, BasicConfig):
    def __init__(self, data, cfg, prog):
        NFBasicOption.__init__(self, cfg, prog)
        if isinstance(data, str):
            self.data = {"path": data, "type": "path"}
        elif isinstance(data, dict):
            self.data = data
        else:
            raise TypeError('Must be str or dict.')
        self.parse_all()
        self.parse_all_nf()

    @property
    def excludes(self) -> List[Union[str, Regex]]:
        t = getattr(self, "__excludes", None)
        if t is not None:
            return t
        del t
        if 'excludes' in self.data:
            if isinstance(self.data['excludes'], list):
                r = parse_ex_or_in_cludes(self.data["excludes"], self.enable_pcre2)  # noqa: E501
                self.__excludes = r
                return r

    @property
    def includes(self) -> List[Union[str, Regex]]:
        t = getattr(self, "__includes", None)
        if t is not None:
            return t
        del t
        if 'includes' in self.data:
            if isinstance(self.data['includes'], list):
                r = parse_ex_or_in_cludes(self.data["includes"], self.enable_pcre2)  # noqa: E501
                self.__includes = r
                return r

    def is_ex_or_in_clude(self, b: str, loc: str, exclude: bool) -> bool:
        e = self.excludes if exclude else self.includes
        if e is None:
            return False if exclude else True
        if isabs(loc):
            bl = abspath(loc)
            rl = relpath(loc, b)
        else:
            bl = abspath(join(b, loc))
            rl = relpath(join(b, loc), b)
        for i in e:
            if isinstance(i, str):
                if isabs(i):
                    if abspath(i) == bl:
                        return True
                else:
                    if relpath(join(b, i), b) == rl:
                        return True
            elif isinstance(i, Regex):
                if i.match_only(rl):
                    return True
                elif bl != loc and i.match_only(bl):
                    return True
        return False

    def is_exclude(self, b: str, loc: str) -> bool:
        return self.is_ex_or_in_clude(b, loc, True)

    def is_include(self, b: str, loc: str) -> bool:
        return self.is_ex_or_in_clude(b, loc, False)


class ConfigOLeveldb(BasicOption, NFBasicOption, BasicConfig):
    def __init__(self, data, cfg, prog):
        NFBasicOption.__init__(self, cfg, prog)
        if isinstance(data, dict):
            self.data = data
        else:
            raise TypeError('Must be dict.')
        self.parse_all()
        self.parse_all_nf()

    @cached_property
    def ignore_hidden_files(self):
        True

    @cached_property
    def domains(self) -> List[str]:
        if 'domains' in self.data:
            if isinstance(self.data['domains'], list):
                dms = []
                for i in self.data['domains']:
                    if isinstance(i, str) and len(i) > 0:
                        dms.append(i.encode())
                if len(dms) > 0:
                    return dms


def namedtuple_bo(typename, field_names):
    a = namedtuple(typename, field_names)
    return type(typename, (a, BasicOption), {})


ConfigNormalFile = namedtuple_bo('ConfigNormalFile', ['name', 'full_path'])
ConfigLeveldb = namedtuple_bo('ConfigLeveldb', ['name', 'full_path', 'domains'])  # noqa: E501
ConfigResult = Union[ConfigNormalFile, ConfigLeveldb]
ConfigOriginResult = Union[ConfigPath, ConfigOLeveldb]


class Program(BasicOption, NFBasicOption):
    def __init__(self, data: dict, cfg):
        self.data = data
        self._files = None
        self._cfg = cfg
        self.parse_all()
        self.parse_all_nf()

    @cached_property
    def all_configs(self) -> List[ConfigOriginResult]:
        r = []
        for i in self.data['files']:
            if isinstance(i, str):
                r.append(ConfigPath(i, self._cfg, self))
            elif isinstance(i, dict):
                t = i['type']
                if t == 'path':
                    r.append(ConfigPath(i, self._cfg, self))
                elif t == 'leveldb':
                    r.append(ConfigOLeveldb(i, self._cfg, self))
        return r

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
        for i in self.all_configs:
            b = self.base
            if isinstance(i, ConfigPath):
                if isabs(i.path):
                    bp = i.path
                else:
                    bp = join(b, i.path)
                name = i.real_name
                if isfile(bp):
                    tname = relpath(join(b, name), b)
                    tmp = ConfigNormalFile(tname, bp)
                    del tname
                    tmp.parse_all(i.data)
                    r.append(tmp)
                elif isdir(bp):
                    top = NFBasicOption(self._cfg, self)
                    top.parse_ignore_hidden_files(i.data)
                    ll = listdirs(bp, top.ignore_hidden_files)
                    del top
                    for ii in ll:
                        if i.is_exclude(bp, ii):
                            continue
                        if not i.is_include(bp, ii):
                            continue
                        tname = relpath(join(b, join(name, relpath(ii, bp))), b)  # noqa: E501
                        tmp = ConfigNormalFile(tname, ii)
                        del tname
                        tmp.parse_all(i.data)
                        r.append(tmp)
            elif isinstance(i, ConfigOLeveldb):
                if isabs(i.path):
                    p = i.path
                else:
                    p = join(b, i.path)
                name = i.real_name
                tname = relpath(join(b, name), b)
                tmp = ConfigLeveldb(tname, p, i.domains)
                del tname
                tmp.parse_all(i.data)
                r.append(tmp)
        for i in r:
            i._cfg = self._cfg
            i._prog = self
        return r

    def get_config(self, name: str) -> ConfigOriginResult:
        for i in self.data['files']:
            if isinstance(i, str):
                if not relpath(name, i).startswith('..'):
                    return ConfigPath(i, self._cfg, self)
            elif isinstance(i, dict):
                t = i['type']
                if t == 'path':
                    if isabs(i['path']):
                        n = i['name']
                    else:
                        n = i['path']
                        if 'name' in i and isinstance(i['name'], str):
                            if i['name'] != '':
                                n = i['name']
                    if not relpath(name, n).startswith('..'):
                        r = ConfigPath(i, self._cfg, self)
                        tmp = relpath(name, n)
                        if r.is_exclude(n, tmp):
                            continue
                        if not r.is_include(n, tmp):
                            continue
                        return r
                elif t == 'leveldb':
                    if relpath(i['name'], name) == '.':
                        return ConfigOLeveldb(i, self._cfg, self)

    @cached_property
    def name(self) -> str:
        if 'name' in self.data:
            v = self.data['name']
            if isinstance(v, str) and len(v) > 0:
                return v


class Config(BasicOption, NFBasicOption):
    dest = ''
    encrypt_db = False
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
        if 'encrypt_db' in t:
            if not isinstance(t['encrypt_db'], bool):
                raise ValueError('encrypt_db should be true or false.')
            self.encrypt_db = t['encrypt_db']
        else:
            self.encrypt_db = False
        if 'programs' not in t:
            raise ValueError("No programs found.")
        self.parse_all(t)
        self.parse_all_nf(t)
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
