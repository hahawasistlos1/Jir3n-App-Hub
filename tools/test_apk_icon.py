import io
import unittest
import zipfile
from PIL import Image
from tools.apk_icon import extract_icon, icon_path


class IconTests(unittest.TestCase):
    def png(self, size, color):
        output=io.BytesIO()
        Image.new('RGBA',size,color).save(output,format='PNG')
        return output.getvalue()

    def extract(self, files, badging):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w') as archive:
            for name,data in files.items(): archive.writestr(name,data)
        output.seek(0)
        return extract_icon(output,badging)

    def test_adaptive_icon_uses_matching_largest_legacy_bitmap(self):
        data=self.extract({
            'res/mipmap-anydpi-v26/app_icon.xml':b'adaptive xml',
            'res/mipmap-mdpi-v4/app_icon.png':self.png((48,48),'red'),
            'res/mipmap-xxxhdpi-v4/app_icon.png':self.png((192,192),'blue'),
            'res/drawable/notification.png':self.png((512,512),'green'),
        },"application-icon-640:'res/mipmap-anydpi-v26/app_icon.xml'")
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual((192,192),image.size)
            self.assertEqual((0,0,255,255),image.getpixel((0,0)))

    def test_images_are_bounded_and_reencoded(self):
        data=self.extract({'res/mipmap/icon.png':self.png((1024,1024),'red')},"application: label='App' icon='res/mipmap/icon.png'")
        with Image.open(io.BytesIO(data)) as image: self.assertEqual((256,256),image.size)
        self.assertTrue(icon_path(data).startswith('icons/'))
        self.assertEqual(icon_path(data),icon_path(bytes(data)))

    def test_corrupt_and_oversized_icons_do_not_break_import(self):
        for data in (b'not a picture',self.png((3000,10),'red')):
            self.assertIsNone(self.extract({'res/mipmap/icon.png':data},"application-icon-160:'res/mipmap/icon.png'"))

    def test_vector_only_retains_placeholder_instead_of_unrelated_artwork(self):
        self.assertIsNone(self.extract({'res/mipmap/icon.xml':b'vector','res/drawable/art.png':self.png((48,48),'red')},"application-icon-160:'res/mipmap/icon.xml'"))
