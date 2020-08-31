import itertools
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


class Group:
    def __init__(self, name, files: List[File]):
        self.name = name
        self.files = files


class GroupList:
    def __init__(self, file_list):
        self.files: List[File] = [f for f in [File(name) for name in sorted(file_list)] if f.group_name is not None]
        group_by = itertools.groupby(self.files, lambda f: f.group_name)
        self.groups = [Group(name, list(files)) for name, files in group_by]
        self.names = [group.name for group in self.groups]
        self.groups_by_name = {group.name: group for group in self.groups}

    def __getitem__(self, item):
        return self.groups_by_name[item]
