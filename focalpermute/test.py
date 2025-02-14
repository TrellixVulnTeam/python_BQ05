#pylint: skip-file
'''test stuff focalpermute'''
from __future__ import print_function
from __future__ import absolute_import

import numpy as np

from . import mediandistance as md
import funclib.statslib as statslib
from . import heatmap_conditionals as hc

#region mediandistance
def median_distance():
    a = np.arange(25).reshape(5,5).astype(float)
    a[0][0] = np.nan
    a[0][1] = 0
    a = md.bin_array_quartile(a)
    print(a)
    z=1

def md_get_results():
    md.get_results()
    z = 1

def kappas():
    md.kappas()

def heatmap_conditionals():
    hc.plot()
#endregion



#region Module Level Calls
#md_get_results()
#kappas()


#
heatmap_conditionals()
#endregion