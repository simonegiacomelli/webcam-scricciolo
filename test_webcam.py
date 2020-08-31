import unittest
from pprint import pprint
from unittest import TestCase

from webcam import decode_filename, GroupList


class TestDecodeFilename(TestCase):
    def test_decode_filename(self):
        target = decode_filename('CAM1_123-20200825130031-00.jpg')
        self.assertEqual(2, len(target))
        group = target[0]
        date = target[1]
        self.assertEqual('123', group)
        self.assertEqual('2020-08-25 13-00-31', date.strftime('%Y-%m-%d %H-%M-%S'))


class TestWebcam(TestCase):

    def test_file_line_count(self):
        with open('test_files/ls.txt', 'r') as f:
            lines = f.readlines()
        self.assertEqual(103, len(lines))

    def test_GroupList(self):
        with open('test_files/ls.txt', 'r') as f:
            lines = f.readlines()
        target = GroupList(lines)
        self.assertEqual(['01', '02', '355', '402', '403'], target.names)
        self.assertEqual(91, len(target.files))

    def test_GroupList_files(self):
        with open('test_files/ls.txt', 'r') as f:
            lines = [line.rstrip('\n') for line in f.readlines()]
        target = GroupList(reversed(lines))
        actual = target['402'].files
        self.assertEqual(12, len(actual))
        self.assertEqual('CAM1_402-20200827012933-00.jpg', actual[0].name)
        self.assertEqual('CAM1_402-20200827012934-01.jpg', actual[3].name)
        self.assertEqual('CAM1_402-20200827012938-01.jpg', actual[-1].name)
