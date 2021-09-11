try:
    from game_backuper._pcre2 import PCRE2, Option as PCRE2Option, MatchOption
    have_pcre2 = True
except ImportError:
    have_pcre2 = False
from enum import IntFlag
from re import I as REI, compile as re_comp


class RegexFlag(IntFlag):
    I = 1  # noqa: E741
    IGNORECASE = 1


class Regex:
    def __init__(self, r: str, flags: RegexFlag = 0, use_pcre2: bool = False):
        if have_pcre2 and use_pcre2:
            opt = 0
            if flags & RegexFlag.I:
                opt = opt | PCRE2Option.PCRE2_CASELESS
            self._re = PCRE2(r)
            self._use_pcre2 = True
        else:
            if use_pcre2:
                from sys import stderr
                stderr.write("Can not load pcre2.\n")
            self._use_pcre2 = False
            opt = 0
            if flags & RegexFlag.I:
                opt = opt | REI
            self._re = re_comp(r)

    def match(self, s: str, startpos: int = 0):
        if self._use_pcre2:
            return self._re.match(s, MatchOption.PCRE2_ANCHORED, startpos)
        else:
            return self._re.match(s, startpos)

    def match_only(self, s: str, startpos: int = 0) -> bool:
        if self._use_pcre2:
            return self._re.match(s, MatchOption.PCRE2_ANCHORED, startpos, True)  # noqa: E501
        else:
            return False if self._re.match(s, startpos) is None else True


def wildcards_to_regex(s: str, **k):
    for i in ['\\', '$', '(', ')', '+', '.', '[', '^', '{', '|']:
        s = s.replace(i, f"\\{i}")
    s = s.replace("*", ".*")
    s = s.replace("?", ".")
    return Regex(s, **k)
