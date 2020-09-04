from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from serverweb import RefreshableCache
from webcam import decode_filename, Metadata, File, Group, WebApi


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


def file_lines(file):
    return [line for line in Path(file).read_text().splitlines()]


ls_txt_lines = file_lines('test_files/ls.txt')


class TestWebcam(TestCase):

    def test_file_line_count(self):
        self.assertEqual(103, len(ls_txt_lines))

    def test_GroupList(self):
        target = Metadata(ls_txt_lines)
        self.assertEqual(['01', '02', '355', '402', '403'], target.groups.names)
        self.assertEqual(91, len(target.files))

    def test_GroupList_files(self):
        target = Metadata(reversed(ls_txt_lines))
        actual = target.groups['402'].files
        self.assertEqual(12, len(actual))
        self.assertEqual('20200827/402/CAM1_402-20200827012933-00.jpg', actual[0].name)
        self.assertEqual('20200827/402/CAM1_402-20200827012934-01.jpg', actual[3].name)
        self.assertEqual('20200827/402/CAM1_402-20200827012938-01.jpg', actual[-1].name)

    def test_Groups_index(self):
        target = Metadata(reversed(ls_txt_lines))
        self.assertEqual('402', target.days['2020-08-27'].groups[0].name)

    def test_days(self):
        target = Metadata(ls_txt_lines)
        self.assertEqual(3, len(target.days))
        self.assertEqual('2020-08-26', target.days[0].date_str)
        self.assertEqual('2020-08-27', target.days[1].date_str)
        self.assertEqual('2020-08-30', target.days[2].date_str)

    def test_days_names(self):
        target = Metadata(ls_txt_lines)
        self.assertEqual(['2020-08-26', '2020-08-27', '2020-08-30'], target.days.names)

    def test_days_string_dictionary(self):
        target = Metadata(ls_txt_lines)
        self.assertEqual('2020-08-27', target.days['2020-08-27'].date_str)

    def test_days_groups(self):
        target = Metadata(ls_txt_lines)
        groups = target.days['2020-08-27'].groups
        self.assertEqual(['402', '403'], groups.names)

    def test_group_time_str(self):
        target = Metadata(ls_txt_lines)
        self.assertEqual('01:29:33', target.groups['402'].time_str)

    def test_with_folder(self):
        target = Metadata.from_folder('test_files/flat_files')
        self.assertEqual(['174', '500', '804', '805'], target.groups.names)

    def test_days_names_with_folder(self):
        target = Metadata.from_folder('test_files/flat_files')
        self.assertEqual(['2020-08-25', '2020-08-27', '2020-08-30'], target.days.names)

    def test_days_names_bug1(self):
        target = Metadata(file_lines('test_files/ls_bug1.txt'))
        actual = target.days.names
        expected = sorted(list(set(actual)))
        self.assertEqual(expected, actual)

    def test_files_by_name_should_match_group(self):
        target = Metadata(ls_txt_lines)
        file: File = target.files['20200827/402/CAM1_402-20200827012938-01.jpg']
        self.assertEqual('20200827/402/CAM1_402-20200827012938-01.jpg', file.name)

    def test_files_by_name__should_provide_group(self):
        target = Metadata(ls_txt_lines)
        file: File = target.files['20200827/402/CAM1_402-20200827012938-01.jpg']
        group: Group = file.group
        self.assertEqual('402', group.name)
        self.assertEqual(12, len(group.files))
        self.assertEqual('20200827/402/CAM1_402-20200827012938-01.jpg', group.files[-1].name)


class TestWebApi(TestCase):

    def setUp(self) -> None:
        self.refreshable_metadata = RefreshableCache(lambda: Metadata(ls_txt_lines))
        self.target = WebApi(self.refreshable_metadata)

    def test_API_days(self):
        self.assertEqual(({'name': '2020-08-26'}, {'name': '2020-08-27'}, {'name': '2020-08-30'}),
                         self.target.API_days())

    def test_API_summary(self):
        expected = [['2020-08-26', [('13:55:49', '20200826/355/CAM1_355-20200826135549-00.jpg')]],
                    ['2020-08-27',
                     [('01:29:33', '20200827/402/CAM1_402-20200827012933-00.jpg'),
                      ('02:00:00', '20200827/403/CAM1_403-20200827020000-00.jpg')]],
                    ['2020-08-30',
                     [('17:15:49', '20200830/01/CAM1_01-20200830171549-00.jpg'),
                      ('17:16:35', '20200830/02/CAM1_02-20200830171635-01.jpg')]]]
        self.assertEqual(expected, self.target.API_summary())

    def test_API_group_summary(self):
        gs = self.target.API_group_summary('20200827/403/CAM1_403-20200827020000-00.jpg')
        self.assertEqual(7, len(gs))
        self.assertEqual('20200827/403/CAM1_403-20200827020000-00.jpg', gs[0])
        self.assertEqual('20200827/403/CAM1_403-20200827020003-00.jpg', gs[-1])

    def test_API_metadata_refresh(self):
        mock = Mock()
        self.refreshable_metadata.refresh = mock
        result = self.target.API_metadata_refresh()
        self.assertEqual({'result': 'ok'}, result)
        mock.assert_called_once()


class TestRefreshableCache(TestCase):

    def setUp(self) -> None:
        self.counter = 0

    def inc_counter(self):
        self.counter += 1
        return self.counter

    def test_should_return_value_from_provider(self):
        target = RefreshableCache(lambda: 'foo')
        self.assertEqual('foo', target.value)

    def test_should_call_provider_only_once(self):
        target = RefreshableCache(self.inc_counter)

        self.assertEqual(1, target.value)
        self.assertEqual(1, target.value)

    def test_early_refresh__should_call_provider_once(self):
        target = RefreshableCache(self.inc_counter)
        target.refresh()
        self.assertEqual(1, target.value)
        self.assertEqual(1, self.counter)

    def test_provider_should_be_called_lazily(self):
        target = RefreshableCache(self.inc_counter)
        self.assertEqual(0, self.counter)
        tmp = target.value
        self.assertEqual(1, self.counter)
