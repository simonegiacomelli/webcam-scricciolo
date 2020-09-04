import datetime
import glob
import json
from itertools import groupby
from typing import List, Callable, TypeVar, Generic


def decode_filename(filename: str):
    no_match = None, None, None
    # '20200830/02/CAM1_02-20200830171635-01.jpg'
    parts = filename.replace('-', '_').replace('.', '_').split('_')
    if len(parts) < 4:
        return None, None, None
    group = parts[1]
    date = datetime.datetime.strptime(parts[2], '%Y%m%d%H%M%S')
    index = parts[3]
    return group, date, index


class File:
    def __init__(self, name):
        self.name = name
        self.group_name, self.datetime, self.index = decode_filename(name)
        if self.name is None or self.group_name is None:
            return
        self.date_str = datetime.datetime.strftime(self.datetime, '%Y-%m-%d')
        self.time_str = datetime.datetime.strftime(self.datetime, '%H:%M:%S')
        self.group: Group = None

    def __lt__(self, other):
        return self.name < other.name


class Group:
    def __init__(self, name, files: List[File]):
        self.name = name
        self.files: List[File] = sorted(files)
        self.date_str = self.files[0].date_str
        self.time_str = self.files[0].time_str
        for f in files:
            f.group = self

    def __lt__(self, other):
        return (self.date_str, self.name) < (other.date_str, other.name)


class Day:
    def __init__(self, date_str, group_list: List[Group]):
        self.date_str = date_str
        self.groups = Groups(group_list)

    def __lt__(self, other):
        return self.date_str < other.date_str

    def __repr__(self):
        return self.date_str + ' ' + str([g.time_str for g in self.groups.groups])


class Groups:
    def __init__(self, groups: List[Group]):
        self.groups = groups
        self.names = sorted([group.name for group in self.groups])
        self.groups_by_name = {group.name: group for group in self.groups}

    def __getitem__(self, item) -> Group:
        if isinstance(item, int):
            return self.groups[item]
        return self.groups_by_name[item]


class Days:
    def __init__(self, groups: Groups):
        by_date_str = groupby(sorted(groups.groups), lambda group: group.date_str)
        self.list = [Day(date_str, list(group_list)) for date_str, group_list in by_date_str]
        self.list.sort()
        self.names = [d.date_str for d in self.list]
        self.by_date_str = {d.date_str: d for d in self.list}
        # self.list = [Day(date_str) for date_str in sorted(list(self.day_dict.keys()))]

    def __len__(self):
        return len(self.list)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.by_date_str[item]

        return self.list[item]


class Files(list):
    def __init__(self, files: List[File]):
        super().__init__(files)
        self.by_name = {f.name: f for f in files}

    def __getitem__(self, item) -> File:
        if isinstance(item, str):
            return self.by_name[item]
        return super().__getitem__(item)


class Metadata:
    def __init__(self, file_list):
        self.files: Files = Files(sorted([f for f in [File(name) for name in file_list] if f.group_name is not None]))
        by_group_name = groupby(self.files, lambda f: f.group_name)
        self.groups: Groups = Groups([Group(name, list(files)) for name, files in by_group_name])
        self.days = Days(self.groups)

    @classmethod
    def from_folder(cls, file) -> 'Metadata':
        glob_list = [f[len(file) + 1:] for f in glob.glob(file + "/**", recursive=True) if f.endswith('.jpg')]
        return Metadata(glob_list)


T = TypeVar('T')


class RefreshableCache(Generic[T]):
    def __init__(self, provider: Callable[[], T]):
        self.provider = provider
        self._value: T = None

    @property
    def value(self) -> T:
        if self._value is None:
            self.refresh()
        return self._value

    def refresh(self):
        self._value = self.provider()


class WebApi:
    def __init__(self, refreshable_metadata: RefreshableCache[Metadata]):
        self.refreshable_metadata = refreshable_metadata

    @property
    def metadata(self):
        return self.refreshable_metadata.value

    def API_days(self):
        return tuple({'name': n} for n in self.metadata.days.names)

    def API_summary(self):
        # [ day_1, day_2, ..., day_n]
        # day_i = ('2020-08-31',[ group_1, group_2, ..., group_n] )
        # group_i = ( '17:15:49', 'CAM1_01-20200830171549-00.jpg' )
        return [[d.date_str, [(g.time_str, g.files[0].name) for g in d.groups]] for d in self.metadata.days]

    def API_group_summary(self, filename):
        files = self.metadata.files[filename].group.files
        return [f.name for f in files]

    def API_metadata_refresh(self):
        self.refreshable_metadata.refresh()
        return {'result': 'ok'}


if __name__ == '__main__':
    md = Metadata.from_folder('/Users/simonegiacomelli/Documents/webcam/pi/webcam/capture')

    print(json.dumps(md.summary, indent=2))
