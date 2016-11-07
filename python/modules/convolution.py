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
na = np.newaxis


# -------------------------------
# 2D Convolution layer
# -------------------------------

class Convolution(Module):

    def __init__(self, filtersize=(5,5,3,32), stride = (2,2)):
        '''
        filtersize = (h,w,d,n)
        '''

        self.fh, self.fw, self.fd, self.n = filtersize
        self.stride = stride

        self.W = np.random.normal(0,1./(self.fh*self.fw*self.fd)**.5, filtersize)
        self.B = np.zeros([self.n])


    def forward(self,X):
        '''
        Realizes the forward pass of an input through the convolution layer.

        Parameters
        ----------
        X : numpy.ndarray
            a network input, shaped (N,H,W,D), with
            N = batch size
            H, W, D = input size in heigth, width, depth

        Returns
        -------
        Y : numpy.ndarray
            the layer outputs.
        '''

        self.X = X
        N,H,W,D = X.shape

        hf, wf, df, nf  = self.W.shape
        hstride, wstride = self.stride
        numfilters = self.n

        #assume the given pooling and stride parameters are carefully chosen.
        Hout = (H - hf) / hstride + 1
        Wout = (W - wf) / wstride + 1

        #initialize pooled output
        self.Y = np.zeros((N,Hout,Wout,numfilters))

        for i in xrange(Hout):
            for j in xrange(Wout):
                x = X[:, i*hstride:i*hstride+hf: , j*wstride:j*wstride+wf: , : ]
                y = np.tensordot(x,self.W,axes = ([1,2,3],[0,1,2]))
                self.Y[:,i,j,:] = y + self.B

        return self.Y


    def backward(self,DY):

        self.DY = DY
        N,Hout,Wout,numfilters = DY.shape

        hf, wf, df, numfilters = self.W.shape
        hstride, wstride = self.stride

        W = self.W[na,...] # extend for N axis in input. is 5-tensor now: N,hf,wf,df,numfilters

        DX = np.zeros_like(self.X,dtype=np.float)

        for i in xrange(Hout):
            for j in xrange(Wout):
                #dy = DY[:,i:i+1,j:j+1,None,:] # N,1,1,numfilters, extended to N,1,1,df,numfilters
                #DX[:,i*hstride:i*hstride+hf , j*wstride:j*wstride+wf , : ] += (W * dy).sum(axis=4)  #sum over all the filters

                for n in xrange(numfilters):
                    for b in range(N):
                        dy = DY[b,i,j,n] # N gradient values, one per sample for the current output voxel
                        DX[b,i*hstride:i*hstride+hf , j*wstride:j*wstride+wf , : ] += self.W[...,n] * dy

        return DX




    def update(self,lrate):

        N,Hx,Wx,Dx = self.X.shape
        N,Hout,Wout,Dout = self.DY.shape

        hf,wf,df,numfilters = self.W.shape
        hstride, wstride = self.stride

        self.DW = np.zeros_like(self.W,dtype=np.float) # hf, wf, df, numfilters

        for i in xrange(Hout):
            for j in xrange(Wout):
                '''
                x = self.X[:, i*hstride:i*hstride+hf , j*wstride:j*wstride+wf , :] # N,hf,wf,df
                x = x[...,None] # N, hf, wf, df, nf=1
                dy = self.DY[:,i:i+1,j:j+1,None,:] # N, Hout=1, Wout=1, df=1, nf
                # hf, wf, df, nf
                self.DW += (x * dy).sum(axis=0) # hf, wf, df, nf
                '''

                for b in xrange(N):
                    x = self.X[b,i*hstride:i*hstride+hf , j*wstride:j*wstride+wf , :] # hf,wf,df
                    for n in xrange(numfilters):
                        dy = self.DY[b,i,j,n]
                        self.DW[...,n] += x*dy


        self.DB = self.DY.sum(axis=(0,1,2))

        self.W -= lrate * self.DW
        self.B -= lrate * self.DB


        def clean(self):
            self.X = None
            self.Y = None
            self.DW = None
            self.DB = None




    def lrp(self,R, *args, **kwargs):

        N,Hout,Wout,numfilters = R.shape

        hf,wf,df,numfilters = self.W.shape
        hstride, wstride = self.stride

        W = self.W[None,...] # extend for N axis in input. is 5-tensor now: N,hf,wf,df,numfilters

        Rx = np.zeros_like(self.X,dtype=np.float)

        for i in xrange(Hout):
            for j in xrange(Wout):
                x = self.X[:, i*hstride:i*hstride+hf , j*wstride:j*wstride+wf , : , None] # N,hf,wf,df,numfilters . extended for numfilters = 1.
                Z = W * x #input activations
                Zsum = Z.sum(axis=(1,2,3),keepdims=True) + self.B[None,...] # sum over filter tensors to proportionally distribute over each filter's input
                Z = Z / Zsum #proportional input activations per filter.
                Z[np.isnan(Z)] = 1e-12
                #STABILIZATION. ADD sign2-fxn: MAKE SMARTER

                # might cause relevance increase, sneaking in another axis?
                r = R[:,i:i+1,j:j+1,None,:] #N, 1, 1, numfilters, extended to N,1,1,df,numfilters
                r = (Z * r).sum(axis=4) # N, hf, wf, df  ; df = Dx
                Rx[:,i*hstride:i*hstride+hf: , j*wstride:j*wstride+wf: , : ] += r #distribute relevance propoprtional to input activations per filter

        return Rx