'''
@author: Sebastian Lapuschkin
@author: Gregoire Montavon
@maintainer: Sebastian Lapuschkin
@contact: sebastian.lapuschkin@hhi.fraunhofer.de
@date: 14.08.2015
@version: 1.2+
@copyright: Copyright (c)  2015, Sebastian Lapuschkin, Alexander Binder, Gregoire Montavon, Klaus-Robert Mueller
@license : BSD-2-Clause
'''

import numpy as np
from module import Module

# -------------------------------
# Rectification layer
# -------------------------------
class Rect(Module):
    '''
    Rectification Layer
    '''

    def forward(self,X):
        self.Y = np.maximum(0,X)
        return self.Y


    def backward(self,DY):
        return DY*(self.Y!=0)


    def clean(self):
        self.Y = None