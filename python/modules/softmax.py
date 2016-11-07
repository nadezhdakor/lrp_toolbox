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
# Softmax layer
# -------------------------------
class SoftMax(Module):
    '''
    Softmax Layer
    '''

    def forward(self,X):
        self.X = X
        self.Y = np.exp(X) / np.exp(X).sum(axis=1,keepdims=True)
        return self.Y


    def lrp(self,R,*args,**kwargs):
        return R*self.X


    def clean(self):
        self.X = None
        self.Y = None