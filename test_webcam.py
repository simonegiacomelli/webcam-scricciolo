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

    def setUp(self) -> None:
        with open('test_files/ls.txt', 'r') as f:
            self.lines = [line.rstrip('\n') for line in f.readlines()]

    def test_file_line_count(self):
        self.assertEqual(103, len(self.lines))

    def test_GroupList(self):
        target = GroupList(self.lines)
        self.assertEqual(['01', '02', '355', '402', '403'], target.names)
        self.assertEqual(91, len(target.files))

    def test_GroupList_files(self):
        target = GroupList(reversed(self.lines))
        actual = target['402'].files
        self.assertEqual(12, len(actual))
        self.assertEqual('CAM1_402-20200827012933-00.jpg', actual[0].name)
        self.assertEqual('CAM1_402-20200827012934-01.jpg', actual[3].name)
        self.assertEqual('CAM1_402-20200827012938-01.jpg', actual[-1].name)
