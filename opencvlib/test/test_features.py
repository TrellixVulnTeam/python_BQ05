'''unit tests for features'''
import unittest
from inspect import getsourcefile as _getsourcefile
import os.path as _path

import cv2
import numpy as np

import opencvlib.features as features
import funclib.iolib as _iolib



class Test(unittest.TestCase):
    '''unittest for keypoints'''

    def setUp(self):
        '''setup variables etc for use in test cases
        '''
        self.pth = _iolib.get_file_parts2(_path.abspath(_getsourcefile(lambda: 0)))[0]
        self.modpath = _path.normpath(self.pth)
        self.imgpath = _path.normpath(_path.join(self.modpath, 'bin/images/matt_pemb5.jpg'))
        self.I = cv2.imread(self.imgpath)
        self.mask = np.tri(self.I.shape[0], self.I.shape[1], dtype=int) #creates a mask where top 'sandwich' is masked out
        self.output_folder = _path.normpath(_path.join(self.modpath, 'output'))


    def test_OpenCV_DensSIFT(self):
        '''test'''
        D = features.OpenCV_DenseSIFT(self.output_folder)
        D(self.I, self.imgpath, mask=None)
        D.extract_keypoints()
        D.extract_descriptors()
        D.write()
        D.view(show=True)

        D(self.I, self.imgpath, self.mask)
        D.extract_keypoints()
        D.extract_descriptors()
        D.view(show=True)


if __name__ == '__main__':
    unittest.main()
