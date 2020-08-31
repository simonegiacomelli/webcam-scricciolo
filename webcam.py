import itertools
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
        # TODO rename self.date to self.datetime
        self.group_name, self.date, self.index = decode_filename(name)
        if self.name is None or self.group_name is None:
            return
        self.date_str = datetime.datetime.strftime(self.date, '%Y-%m-%d')

    def __lt__(self, other):
        return self.name < other.name

class Group:
    def __init__(self, name, files: List[File]):
        self.name = name
        self.files = sorted(files)
        self.date_str = self.files[0].date_str

    def __lt__(self, other):
        return (self.date_str, self.name) < (other.date_str, other.name)


class Day:
    def __init__(self, date_str, group_list: List[Group]):
        self.date_str = date_str
        self.groups = Groups(group_list)

    def __lt__(self, other):
        return self.date_str < other.date_str


class Groups:
    def __init__(self, groups: List[Group]):
        self.groups = groups
        self.names = [group.name for group in self.groups]
        self.groups_by_name = {group.name: group for group in self.groups}

    def __getitem__(self, item):
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


class Metadata:
    def __init__(self, file_list):
        self.files: List[File] = sorted([f for f in [File(name) for name in file_list] if f.group_name is not None])
        by_name = groupby(self.files, lambda f: f.group_name)
        self.groups: Groups = Groups([Group(name, list(files)) for name, files in by_name])
        self.days = Days(self.groups)

    @classmethod
    def from_folder(cls, file) -> 'Metadata':
        return Metadata(os.listdir(file))
