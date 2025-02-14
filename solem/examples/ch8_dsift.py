from PIL import Image
from pylab import *
from numpy import *

from solem.PCV.localdescriptors import dsift, sift

"""
This is the dense SIFT illustration, it will reproduce the plot
in Figure 8-2.
"""

dsift.process_image_dsift('./data/empire.jpg', 'empire.sift', 90, 40, True)
l, d = sift.read_features_from_file('empire.sift')

im = array(Image.open('./data/empire.jpg'))
sift.plot_features(im, l, True)
show()
