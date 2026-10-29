import base64
import copy
import io
import stat
import unittest
import zipfile
from unittest.mock import patch
from tools.windows_archive import validate_windows_archive
from tools import catalog_admin as server
from tools import test_catalog_admin as fixtures


def archive(files):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w') as z:
        for name,data in files: z.writestr(name,data)
    output.seek(0)
    return output


class WindowsArchiveTests(unittest.TestCase):
    def test_windows_tool_is_inspected_without_extraction(self):
        validate_windows_archive(archive([('Editor/Editor.exe',b'MZ fixture'),('Editor/data/file.dat',b'data')]))

    def test_unsafe_paths_and_drive_letters_are_rejected(self):
        for name in ('../tool.exe','/tool.exe','C:/tool.exe','folder/../../tool.exe','C:\\tool.exe'):
            with self.assertRaises(ValueError): validate_windows_archive(archive([(name,b'MZ')]))

    def test_sources_or_empty_archives_are_not_windows_tools(self):
        for files in ([],[('README.txt',b'hello')],[('source.cs',b'code')]):
            with self.assertRaises(ValueError): validate_windows_archive(archive(files))

    def test_symlinks_and_expansion_bombs_are_rejected(self):
        link=zipfile.ZipInfo('link.exe'); link.external_attr=(stat.S_IFLNK|0o777)<<16
        with self.assertRaises(ValueError): validate_windows_archive(archive([(link,b'target')]))
        huge=zipfile.ZipInfo('tool.exe'); huge.file_size=3*1024*1024*1024
        with patch.object(zipfile.ZipFile,'infolist',return_value=[huge]):
            with self.assertRaises(ValueError): validate_windows_archive(archive([]))

    @patch.object(server,'github')
    def test_counts_are_separate_for_android_and_windows(self,github):
        github.return_value=[{'assets':[{'name':'game.apk','download_count':5},{'name':'editor.zip','download_count':7}]}]
        self.assertEqual(5,server.release_download_total('owner/app',{},('.apk',)))
        self.assertEqual(7,server.release_download_total('owner/app',{},('.zip',)))


class WindowsPublisherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): fixtures.PublisherTests.setUpClass.__func__(cls)
    def setUp(self): fixtures.PublisherTests.setUp(self)
    @patch.object(server,'github',return_value={'private':False,'owner':{'id':server.OWNER_ID}})
    def test_android_and_multiple_windows_entries_do_not_replace_each_other(self,github):
        root=copy.deepcopy(self.seed)
        def win(identifier,repo): return {'id':identifier,'platform':'Windows','packageName':'','visibility':'public','repository':repo,'certificateSha256':'','sha256':'a'*64,'versionCode':22,'releaseId':5,'icon':'hub_icon','downloadEnabled':False}
        root['apps'].append(win('windows-one','owner/one'))
        self.publisher.read=lambda:(copy.deepcopy(root),'sha')
        result=self.publisher.change(entry=win('windows-two','owner/two'))
        self.assertEqual(len(root['apps'])+1,len(result['apps']))
        self.assertTrue({'windows-one','windows-two'}.issubset({a['id'] for a in result['apps']}))

    @patch.object(server,'github',return_value={'private':False,'owner':{'id':server.OWNER_ID}})
    def test_windows_revision_preserves_the_owners_disabled_download(self,github):
        root=copy.deepcopy(self.seed)
        win={'id':'windows','platform':'Windows','packageName':'','visibility':'public','repository':'owner/tools','certificateSha256':'','sha256':'a'*64,'versionCode':22,'releaseId':5,'icon':'hub_icon','downloadEnabled':False}
        root['apps'].append(win)
        self.publisher.read=lambda:(copy.deepcopy(root),'sha')
        result=self.publisher.change(entry=dict(win,versionCode=23,sha256='b'*64,downloadEnabled=True))
        self.assertFalse(next(a for a in result['apps'] if a['id']=='windows')['downloadEnabled'])
