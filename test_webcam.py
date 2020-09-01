import unittest
from pprint import pprint
from unittest import TestCase

from webcam import decode_filename, Metadata, File, Group


class TestDecodeFilename(TestCase):
    def test_decode_filename(self):
        target = decode_filename('CAM1_123-20200825130031-89.jpg')
        self.assertEqual(3, len(target))
        group = target[0]
        date = target[1]
        index = target[2]
        self.assertEqual('123', group)
        self.assertEqual('2020-08-25 13-00-31', date.strftime('%Y-%m-%d %H-%M-%S'))
        self.assertEqual('89', index)


class TestWebcam(TestCase):

    def setUp(self) -> None:
        with open('test_files/ls.txt', 'r') as f:
            self.lines = [line.rstrip('\n') for line in f.readlines()]
        with open('test_files/ls_bug1.txt', 'r') as f:
            self.lines_bug1 = [line.rstrip('\n') for line in f.readlines()]

    def test_file_line_count(self):
        self.assertEqual(103, len(self.lines))

    def test_GroupList(self):
        target = Metadata(self.lines)
        self.assertEqual(['01', '02', '355', '402', '403'], target.groups.names)
        self.assertEqual(91, len(target.files))

    def test_GroupList_files(self):
        target = Metadata(reversed(self.lines))
        actual = target.groups['402'].files
        self.assertEqual(12, len(actual))
        self.assertEqual('CAM1_402-20200827012933-00.jpg', actual[0].name)
        self.assertEqual('CAM1_402-20200827012934-01.jpg', actual[3].name)
        self.assertEqual('CAM1_402-20200827012938-01.jpg', actual[-1].name)

    def test_Groups_index(self):
        target = Metadata(reversed(self.lines))
        self.assertEqual('402', target.days['2020-08-27'].groups[0].name)

    def test_days(self):
        target = Metadata(self.lines)
        self.assertEqual(3, len(target.days))
        self.assertEqual('2020-08-26', target.days[0].date_str)
        self.assertEqual('2020-08-27', target.days[1].date_str)
        self.assertEqual('2020-08-30', target.days[2].date_str)

    def test_days_names(self):
        target = Metadata(self.lines)
        self.assertEqual(['2020-08-26', '2020-08-27', '2020-08-30'], target.days.names)

    def test_days_string_dictionary(self):
        target = Metadata(self.lines)
        self.assertEqual('2020-08-27', target.days['2020-08-27'].date_str)

    def test_days_groups(self):
        target = Metadata(self.lines)
        groups = target.days['2020-08-27'].groups
        self.assertEqual(['402', '403'], groups.names)

    def test_group_time_str(self):
        target = Metadata(self.lines)
        self.assertEqual('01:29:33', target.groups['402'].time_str)

    def test_with_folder(self):
        target = Metadata.from_folder('test_files/flat_files')
        self.assertEqual(['174', '500', '804', '805'], target.groups.names)

    def test_days_names_with_folder(self):
        target = Metadata.from_folder('test_files/flat_files')
        self.assertEqual(['2020-08-25', '2020-08-27', '2020-08-30'], target.days.names)

    def test_days_names_bug1(self):
        target = Metadata(self.lines_bug1)
        actual = target.days.names
        expected = sorted(list(set(actual)))
        self.assertEqual(expected, actual)

    def test_files_by_name_should_match_group(self):
        target = Metadata(self.lines)
        file: File = target.files['CAM1_402-20200827012938-01.jpg']
        self.assertEqual('CAM1_402-20200827012938-01.jpg', file.name)

    def test_files_by_name__should_provide_group(self):
        target = Metadata(self.lines)
        file: File = target.files['CAM1_402-20200827012938-01.jpg']
        group: Group = file.group
        self.assertEqual('402', group.name)
        self.assertEqual(12, len(group.files))

    def test_summary_should_have_length_as_days(self):
        target = Metadata(self.lines)

        summary = target.summary
        self.assertEqual(list, type(summary))
        self.assertEqual(3, len(summary))

        expected_day0 = ['2020-08-26', [('13:55:49', 'CAM1_355-20200826135549-00.jpg')]]
        self.assertEqual(expected_day0, summary[0])

        expected_day1 = ['2020-08-27', [('01:29:33', 'CAM1_402-20200827012933-00.jpg'),
                                        ('02:00:00', 'CAM1_403-20200827020000-00.jpg')]]
        self.assertEqual(expected_day1, summary[1])

        expected_day2 = ['2020-08-30', [('17:15:49', 'CAM1_01-20200830171549-00.jpg'),
                                        ('17:16:35', 'CAM1_02-20200830171635-01.jpg')]]
        self.assertEqual(expected_day2, summary[2])
