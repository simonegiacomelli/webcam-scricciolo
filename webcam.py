import itertools
import json
from itertools import groupby
import os
import datetime
from pprint import pprint
from typing import List


def decode_filename(filename: str):
    # 'CAM1_220-20200825130031-00.jpg'
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
        self.group = None

    def __lt__(self, other):
        return self.name < other.name

    def next(self) -> 'File':
        return None

    def prev(self) -> 'File':
        return None


class Group:
    def __init__(self, name, files: List[File]):
        self.name = name
        self.files = sorted(files)
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
        self.names = [group.name for group in self.groups]
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

    def __getitem__(self, item):
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
        return Metadata(os.listdir(file))

    @property
    def summary(self):
        # [ day_1, day_2, ..., day_n]
        # day_i = ('2020-08-31',[ group_1, group_2, ..., group_n] )
        # group_i = ( '17:15:49', 'CAM1_01-20200830171549-00.jpg' )
        return [[d.date_str, [(g.time_str, g.files[0].name) for g in d.groups]] for d in self.days]


if __name__ == '__main__':
    md = Metadata.from_folder('/Users/simonegiacomelli/Documents/webcam/pi/webcam/capture')

    print(json.dumps(md.summary,indent=2))
