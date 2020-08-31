import itertools
from itertools import groupby
import os
import datetime
from pprint import pprint
from typing import List


def decode_filename(filename: str):
    # 'CAM1_220-20200825130031-00.jpg'
    parts = filename.replace('-', '_').split('_')
    if len(parts) < 3:
        return None, None
    group = parts[1]
    date = datetime.datetime.strptime(parts[2], '%Y%m%d%H%M%S')
    return (group, date)


class File:
    def __init__(self, name):
        self.name = name
        self.group_name, self.date = decode_filename(name)
        if self.name is None or self.group_name is None:
            return
        self.date_str = datetime.datetime.strftime(self.date, '%Y-%m-%d')


class Group:
    def __init__(self, name, files: List[File]):
        self.name = name
        self.files = files
        self.date_str = self.files[0].date_str


class Day:
    def __init__(self, date_str, group_list: List[Group]):
        self.date_str = date_str

    def __lt__(self, other):
        return self.date_str < other.date_str


class Days:
    def __init__(self, groups: List[Group]):
        by_date_str = groupby(groups, lambda group: group.date_str)
        self.list = [Day(date_str, list(group_list)) for date_str, group_list in by_date_str]
        self.list.sort()
        self.by_date_str = {d.date_str: d for d in self.list}
        # self.list = [Day(date_str) for date_str in sorted(list(self.day_dict.keys()))]

    def __len__(self):
        return len(self.list)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.by_date_str[item]

        return self.list[item]


class GroupList:
    def __init__(self, file_list):
        self.files: List[File] = [f for f in [File(name) for name in sorted(file_list)] if f.group_name is not None]
        by_name = groupby(self.files, lambda f: f.group_name)
        self.groups: List[Group] = [Group(name, list(files)) for name, files in by_name]
        self.names = [group.name for group in self.groups]
        self.groups_by_name = {group.name: group for group in self.groups}
        self.days = Days(self.groups)

    def __getitem__(self, item):
        return self.groups_by_name[item]
