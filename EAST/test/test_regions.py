
# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument, unused-variable
'''unit tests for features'''
import unittest
from inspect import getsourcefile as _getsourcefile
import os.path as _path

import cv2
import funclib.iolib as iolib
import opencvlib
import EAST.regions as regions
from opencvlib.view import show

class Test(unittest.TestCase):
    '''unittest for keypoints'''

    def setUp(self):
        '''setup variables etc for use in test cases
        '''
        self.pth = iolib.get_file_parts2(_path.abspath(_getsourcefile(lambda: 0)))[0]
        self.modpath = _path.normpath(self.pth)
        self.module_root = _path.normpath(opencvlib.__path__[0]) #root of opencvlib
        self.imgpath_clean = _path.normpath(_path.join(self.modpath, 'bin/clean_text.jpg'))
        self.imgpath_sa6 = _path.normpath(_path.join(self.modpath, 'bin/sa6.jpg'))
        self.img_clean = cv2.imread(self.imgpath_clean)
        self.img_sa6 = cv2.imread(self.imgpath_sa6)
        self.img_path = _path.normpath(_path.join(self.modpath, 'bin'))
        self.visualisation_path = _path.normpath(_path.join(self.modpath, 'bin/vis'))

    #@unittest.skip("Temporaily disabled while debugging")
    def test_detect(self):
        '''test'''
        for img_region, contour_pts, original_img_path, contour_group_key in regions.text_region_generator(self.img_path, self.visualisation_path):
            show(img_region)





if __name__ == '__main__':
    unittest.main(verbosity=2)

