from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import range
from past.utils import old_div
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.interpolate import RegularGridInterpolator
import math
from tqdm import trange

mainlabel = ""

units = "$\AA^{-1}$"

xunits = units
yunits = units
zunits = units

contours = 200
DPI = 300
format = ".png"
text = "Structure Factor"

PLOT_EWALDS=False
savelog = True
savelin = True

title_fontsize = 9

path = ""

def csplot_wlog(X, Y, Z, contours, lab, xlab, ylab, **kwargs):

    csplot(X,Y,Z,contours,lab,xlab,ylab,**kwargs)
    csplot(X,Y,np.log(Z),contours,"log_"+lab,xlab,ylab,**kwargs)


def csplot(X, Y, Z, contours, lab, xlab, ylab,**kwargs):

    title=lab+" S("+xlab+","+ylab+")"
    fname=lab+"_"+xlab+"_"+ylab
    fig, ax = plt.subplots()
    plt.suptitle(title)
    plt.xlabel(xlab)
    plt.ylabel(ylab)


    if normplot==1:
        cax=plt.contourf(X,Y,Z/np.amax(Z),contours,vmin=0.0,vmax=1.0,**kwargs)
    else:
        cax=plt.contourf(X,Y,Z,contours,**kwargs)

    # ax.set_aspect((np.amax(Y)-np.amin(Y))/(np.amax(X)-np.amin(X)))
    # ax.set_aspect('auto')
    # cbar = fig.colorbar(cax)

    plt.savefig(path+fname+format,dpi=DPI)
    plt.clf()


def sfplot(data, lcscale, **kwargs):
    """ data: plot slice through structure factor"""

    if not os.path.exists(path):
        os.makedirs(path)
    cspos = 0.0
    la = []

    lb = 0

    an = ['x', 'y', 'z']  # axes names
    for i in range(data.shape[2] - 1):
        if np.unique(data[..., i]).size > 1:
            la.append(i)
        else:
            lb = i
            cspos = data[0, 0, i]

    title = mainlabel + "\n" + text + "\n" + an[lb] + "=" + str(round(cspos, 2)) + zunits
    ltitle = mainlabel + "\n" + "log " + text + "\n" + an[lb] + "=" + str(round(cspos, 2)) + zunits

    xlab = an[la[0]]
    ylab = an[la[1]]

    filename = path + an[lb] + "=" + str(round(cspos, 2))

    xlab += "(" + xunits + ")"
    ylab += "(" + yunits + ")"

    if savelog:
        plt.suptitle(ltitle, fontsize=title_fontsize)
        plt.xlabel(xlab)
        plt.ylabel(ylab)
        max_log = np.amax(np.log(data[..., 3]))
        plt.contourf(data[..., la[0]], data[..., la[1]], np.log(data[..., 3]), contours, vmax=lcscale*max_log, **kwargs)

        plt.savefig(filename+"_log"+format, dpi=DPI)
        plt.clf()

    if savelin:
        plt.suptitle(title, fontsize=title_fontsize)
        plt.xlabel(xlab)
        plt.ylabel(ylab)
        plt.contourf(data[..., la[0]], data[..., la[1]], data[..., 3], contours, **kwargs)
        plt.savefig(filename+format, dpi=DPI)
        plt.clf()


def radial_integrate(D,Nbins,outputname):

    SF = D[:, :, :, 3]

    R = (D[:, :, :, 0]**2).astype(np.float16) + (D[:, :, :, 1]**2).astype(np.float16)+(D[:, :, :, 2]**2).astype(np.float16)
    H, E = np.histogram(R, bins=Nbins, weights=SF)
    Hc, E = np.histogram(R, bins=Nbins)
    Hc = np.where(Hc != 0, Hc, 1.0)
    H /= Hc
    H[:1] = 0.0
    H /= np.amax(H)
    plt.plot(E[:-1], H)
    plt.ylim(0, 0.2)
    plt.xlim(0.1, 0.5)
    plt.savefig(outputname, dpi=DPI)

def spherical_integrate(D):
    exit()


def Plot_Ewald_Sphere_Correction_old(D,wavelength_angstroms):
    """ pass full 3d data,SF,wavelength in angstroms """

    X = D[:, 0, 0, 0]
    Y = D[0, :, 0, 1]
    Z = D[0, 0, :, 2]
    SF = D[:, :, :, 3]

    K_ES = 2.0*math.pi/wavelength_angstroms  # calculate k for incident xrays in inverse angstroms

    ES = RegularGridInterpolator((X, Y, Z), SF)

    pts = []
    for ix in range(D.shape[0]):
        xsq = X[ix]**2.0
        for iy in range(D.shape[1]):
            R = np.sqrt(xsq+Y[iy]**2.0)
            theta = np.arctan(old_div(R,K_ES))
            xnew = X[ix]*np.cos(theta)
            ynew = Y[iy]*np.cos(theta)
            znew = K_ES*(1.0-np.cos(theta))
            pts.append((X[ix], Y[iy], xnew, ynew, znew))

    pts = np.asarray(pts)

    EWD = ES(pts[:, 2:])
    EWD = EWD.reshape(D.shape[0],D.shape[1])
    plt.contourf(D[:, :, 0, 0], D[:, :, 0, 1], EWD, 200, interpolation=interp)

    plt.savefig("EWxy.png",dpi=300)
    plt.clf()

    plt.contourf(D[:, :, 0, 0], D[:, :, 0, 1], np.log(EWD), 200, interpolation=interp)

    plt.savefig("EWxylog.png", dpi=300)
    plt.clf()


def Plot_Ewald_Sphere_Correction(D, wavelength_angstroms, cscale=1, lcscale=1, **kwargs):
    """ pass full 3d data,SF,wavelength in angstroms """
    # cscale : factor by which to scale the maximum value of the colorbar
    # lcscale : factor by which to scale the maximum value of the colorbar

    if not os.path.exists(path):
        os.makedirs(path)

    X = D[:, 0, 0, 0]
    Y = D[0, :, 0, 1]
    Z = D[0, 0, :, 2]
    SF = D[:, :, :, 3]

    K_ES = 2.0*math.pi/wavelength_angstroms  # calculate k for incident xrays in inverse angstroms

    ES = RegularGridInterpolator((X, Y, Z), SF, bounds_error=False)

    xypts = []
    for ix in range(D.shape[0]):
        xsq = X[ix]**2.0
        for iy in range(D.shape[1]):
            theta = np.arctan(old_div(np.sqrt(xsq + Y[iy]**2.0),K_ES))
            xypts.append((X[ix]*np.cos(theta), Y[iy]*np.cos(theta), K_ES*(1.0 - np.cos(theta))))

    xzpts=[]
    for ix in range(D.shape[0]):
        xsq = X[ix]**2.0
        for iz in range(D.shape[2]):
            theta = np.arctan(old_div(np.sqrt(xsq + Z[iz]**2.0),K_ES))
            xzpts.append((X[ix]*np.cos(theta), K_ES*(1.0-np.cos(theta)), Z[iz]*np.cos(theta)))

    yzpts = []
    for iy in range(D.shape[1]):
        ysq = Y[iy]**2.0
        for iz in range(D.shape[2]):
            theta = np.arctan(old_div(np.sqrt(ysq+Z[iz]**2.0),K_ES))
            yzpts.append((K_ES*(1.0-np.cos(theta)), Y[iy]*np.cos(theta), Z[iz]*np.cos(theta)))

    xypts = np.asarray(xypts)
    xzpts = np.asarray(xzpts)
    yzpts = np.asarray(yzpts)

    EWDxy = ES(xypts)
    EWDxz = ES(xzpts)
    EWDyz = ES(yzpts)

    EWDxy = EWDxy.reshape(D.shape[0], D.shape[1])
    EWDxz = EWDxz.reshape(D.shape[0], D.shape[2])
    EWDyz = EWDyz.reshape(D.shape[1], D.shape[2])

    title = "Ewald Corrected Structure Factor \n $\lambda=$"+str(wavelength_angstroms)+" $\AA$   $k_{ew}=$"+str(round(K_ES,2))+" $\AA^{-1}$"
    ltitle = 'log ' + title

    xlab = 'x (' + units + ")"
    ylab = 'y (' + units + ")"
    zlab = 'z (' + units + ")"

    fname = "Ewald_"

    plt.figure(1)
    plt.suptitle(title)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    EWDmax_xy = np.amax(EWDxy)
    plt.contourf(D[:, :, 0, 0], D[:, :, 0, 1], EWDxy, contours, vmax=cscale*EWDmax_xy, **kwargs)
    plt.savefig(path + fname + "xy" + format, dpi=DPI)
    plt.clf()

    plt.figure(2)
    plt.suptitle(ltitle)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    EWDmax_xylog = np.amax(np.log(EWDxy))
    plt.contourf(D[:, :, 0, 0], D[:, :, 0, 1], np.log(EWDxy), contours, vmax=lcscale*EWDmax_xylog, **kwargs)
    plt.savefig(path + fname + "xylog" + format, dpi=DPI)
    plt.clf()

    plt.figure(3)
    plt.suptitle(title)
    plt.xlabel(xlab)
    plt.ylabel(zlab)
    EWDmax_xz = np.amax(EWDxz)
    plt.contourf(D[:, 0, :, 0], D[:, 0, :, 2], EWDxz, contours, vmax=cscale*EWDmax_xz, **kwargs)
    plt.savefig(path + fname + "xz" + format, dpi=DPI)
    plt.clf()

    plt.figure(4)
    plt.suptitle(ltitle)
    plt.xlabel(xlab)
    plt.ylabel(zlab)
    EWDmax_xzlog = np.amax(np.log(EWDxz))
    plt.contourf(D[:, 0, :, 0], D[:, 0, :, 2], np.log(EWDxz), contours, vmax=lcscale*EWDmax_xzlog, **kwargs)
    lims = [np.amax(D[:, 0, :, 0]), np.amax(D[:, 0, :, 2])]
    qmax = min(lims)
    plt.xlim([-qmax, qmax])
    plt.ylim([-qmax, qmax])
    plt.savefig(path + fname + "xzlog" + format, dpi=DPI)
    plt.clf()

    plt.figure(5)
    plt.suptitle(title)
    plt.xlabel(ylab)
    plt.ylabel(zlab)
    EWDmax_yz = np.amax(EWDyz)
    plt.contourf(D[0, :, :, 1], D[0, :, :, 2], EWDyz, contours, vmax=cscale*EWDmax_yz, **kwargs)
    plt.savefig(path + fname + "yz" + format, dpi=DPI)
    plt.clf()

    plt.figure(6)
    plt.suptitle(ltitle)
    plt.xlabel(ylab)
    plt.ylabel(zlab)
    EWDmax_yzlog = np.amax(np.log(EWDyz))
    plt.contourf(D[0, :, :, 1], D[0, :, :, 2], np.log(EWDyz), contours, vmax=lcscale*EWDmax_yzlog, **kwargs)
    # plt.xlim([-2.5, 2.5])
    # plt.ylim([-2.5, 2.5])
    plt.savefig(path + fname + "yzlog" + format, dpi=DPI)
    plt.clf()


def Plot_Ewald_triclinic(D, wavelength_angstroms, ucell, **kwargs):  #pass full 3d data,SF,wavelength in angstroms

    if not os.path.exists(path):
        os.makedirs(path)

    X = D[:, 0, 0, 0]
    Y = D[0, :, 0, 1]
    Z = D[0, 0, :, 2]
    SF = D[:, :, :, 3]

    a1 = ucell[0]
    a2 = ucell[1]
    a3 = ucell[2]

    b1 = old_div((np.cross(a2,a3)),(np.dot(a1,np.cross(a2,a3))))
    b2 = old_div((np.cross(a3,a1)),(np.dot(a2,np.cross(a3,a1))))
    b3 = old_div((np.cross(a1,a2)),(np.dot(a3,np.cross(a1,a2))))

    Dnew = np.zeros_like(D)

    for ix in trange(D.shape[0]):
        Dnew[ix, :, :, 0:3] += X[ix]*b1
    for iy in trange(D.shape[1]):
        Dnew[:, iy, :, 0:3] += Y[iy]*b2
    for iz in trange(D.shape[2]):
        Dnew[:, :, iz, 0:3] += Z[iz]*b3

    D = Dnew

    K_ES = 2.0*math.pi/wavelength_angstroms  #calculate k for incident xrays in inverse angstroms

    ES = RegularGridInterpolator((X, Y, Z), SF, bounds_error=False)

    #angle averaging
    xyzpts = []
    print("setting up points for radial integration")
    for ix in trange(D.shape[0]):
        for iy in range(D.shape[1]):
            for iz in range(D.shape[2]):
                # xyzpts.append((X[ix],Y[iy],Z[iz]))
                xyzpts.append((D[ix, iy, iz, 0], D[ix, iy, iz, 1], D[ix, iy, iz, 2]))

    xyzpts = np.asarray(xyzpts)
    EWDxyz = ES(xyzpts)

    rpts = np.sqrt(xyzpts[:, 0]**2.0 + xyzpts[:, 1]**2.0)

    Hcount, XEC, YEC = np.histogram2d(rpts, xyzpts[:, 2], bins=(X, Z))

    Hval, XEV, YEV = np.histogram2d(rpts, xyzpts[:, 2], weights=EWDxyz, normed=True, bins=(X, Z))

    Hrz = Hval / Hcount

    Hrz = np.ma.masked_invalid(Hrz)

    for ir in range(old_div(Hrz.shape[0], 2)):
        Hrz[-ir - 1 + old_div(Hrz.shape[0], 2), :] = Hrz[ir + 1 + old_div(Hrz.shape[0], 2), :]

    exev = old_div((XEV[1] - XEV[0]), 0.5)
    eyev = old_div((YEV[1] - YEV[0]), 0.5)
    XMG, YMG = np.meshgrid(XEV+exev, YEV+eyev)  # changed XEV+eyev to XEV+exev -- pull request eventually with other changes

    # fig, ax = plt.subplots()
    # cax = ax.pcolormesh(XMG[:-1, :], YMG[:-1, :], Hrz.T, vmin=0.0, vmax=0.005*np.max(Hrz))
    # cax = plt.imshow(XMG[0, :], YMG[0, :], Hrz.T, vmin=0.0, vmax=0.005*np.max(Hrz))
    # cax.set_edgecolor('face')
    # cbar = fig.colorbar(cax)

    plt.pcolormesh(XMG[:-1, :], YMG[:-1, :], Hrz.T, vmin=0.0, vmax=0.005*np.amax(Hrz))
    plt.savefig(path+"rzplot"+format, dpi=DPI)
    plt.clf()

    xypts = []
    xyflat = []
    for ix in range(D.shape[0]):
        xsq = X[ix] ** 2.0
        for iy in range(D.shape[1]):
            theta = np.arctan(np.sqrt(xsq + Y[iy] ** 2.0) / K_ES)
            xypts.append((X[ix] * np.cos(theta), Y[iy] * np.cos(theta), K_ES * (1.0 - np.cos(theta))))
            xyflat.append((X[ix], Y[iy], 0.0))

    xzpts = []
    xzflat = []
    for ix in range(D.shape[0]):
        xsq= X[ix] ** 2.0
        for iz in range(D.shape[2]):
            theta=np.arctan(np.sqrt(xsq + Z[iz] ** 2.0) / K_ES)
            xzpts.append((X[ix] * np.cos(theta), K_ES * (1.0 - np.cos(theta)), Z[iz] * np.cos(theta)))
            xzflat.append((X[ix], 0.0, Z[iz]))

    yzpts = []
    yzflat = []
    for iy in range(D.shape[1]):
        ysq = Y[iy] ** 2.0
        for iz in range(D.shape[2]):
            theta = np.arctan(np.sqrt(ysq + Z[iz] ** 2.0) / K_ES)
            yzpts.append((K_ES * (1.0 - np.cos(theta)), Y[iy] * np.cos(theta), Z[iz] * np.cos(theta)))
            yzflat.append((0.0, Y[iy], Z[iz]))

    xypts = np.asarray(xypts)
    xzpts = np.asarray(xzpts)
    yzpts = np.asarray(yzpts)

    xyflat = np.asarray(xyflat)
    xzflat = np.asarray(xzflat)
    yzflat = np.asarray(yzflat)

    EWDxy = ES(xypts)
    EWDxz = ES(xzpts)
    EWDyz = ES(yzpts)

    EWDxyflat = ES(xyflat)
    EWDxzflat = ES(xzflat)
    EWDyzflat = ES(yzflat)

    EWDxy = EWDxy.reshape(D.shape[0],D.shape[1])
    EWDxz = EWDxz.reshape(D.shape[0],D.shape[2])
    EWDyz = EWDyz.reshape(D.shape[1],D.shape[2])

    EWDxyflat = EWDxyflat.reshape(D.shape[0],D.shape[1])
    EWDxzflat = EWDxzflat.reshape(D.shape[0],D.shape[2])
    EWDyzflat = EWDyzflat.reshape(D.shape[1],D.shape[2])

    title = "Ewald Corrected Structure Factor \n $\lambda=$"+str(wavelength_angstroms)+" $\AA$   $k_{ew}=$"+str(round(K_ES,2))+" $\AA^{-1}$"
    ltitle = 'log ' + title

    xlab = 'x ('+units + ")"
    ylab = 'y ('+units + ")"
    zlab = 'z ('+units + ")"

    fname = "Ewald_"

    plt.suptitle(title)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.contourf(D[:,:,0,0],D[:,:,0,1],EWDxy,contours,**kwargs)
    plt.savefig(path+fname+"xy"+format,dpi=DPI)
    plt.clf()

    Nx = D.shape[0]
    Ny = D.shape[1]
    Nz = D.shape[2]

    lax = ['x','y','z']


    ewlab="Ewald"
    flab="Flat"

    iax1 = 0
    iax2 = 1

    if PLOT_EWALDS:
        csplot_wlog(D[:,:,Nz/2,iax1],D[:,:,Nz/2,iax2],EWDxy,contours,ewlab,lax[iax1],lax[iax2],**kwargs)

    csplot_wlog(D[:,:,Nz/2,iax1],D[:,:,Nz/2,iax2],EWDxyflat,contours,flab ,lax[iax1],lax[iax2],**kwargs)


    iax1=0
    iax2=2

    if PLOT_EWALDS:
        csplot_wlog(D[:,Ny/2,:,iax1],D[:,Ny/2,:,iax2],EWDxz,contours,ewlab,lax[iax1],lax[iax2],**kwargs)

    csplot_wlog(D[:,Ny/2,:,iax1],D[:,Ny/2,:,iax2],EWDxzflat,contours,flab,lax[iax1],lax[iax2],**kwargs)

    iax1 = 1
    iax2 = 2

    if PLOT_EWALDS:
        csplot_wlog(D[Nx/2,:,:,iax1],D[Nx/2,:,:,iax2],EWDyz,contours,ewlab,lax[iax1],lax[iax2],**kwargs)

    csplot_wlog(D[Nx/2,:,:,iax1],D[Nx/2,:,:,iax2],EWDyzflat,contours,flab,lax[iax1],lax[iax2],**kwargs)

    # xypts=[]
    # for ix in xrange(D.shape[0]):
		# xsq=X[ix]**2.0
		# for iy in xrange(D.shape[1]):
		# 	theta=np.arctan(np.sqrt(xsq+Y[iy]**2.0)/K_ES)
		# 	xypts.append((X[ix]*np.cos(theta),Y[iy]*np.cos(theta),K_ES*(1.0-np.cos(theta))))
    #
    # xzpts=[]
    # for ix in xrange(D.shape[0]):
		# xsq=X[ix]**2.0
		# for iz in xrange(D.shape[2]):
		# 	theta=np.arctan(np.sqrt(xsq+Z[iz]**2.0)/K_ES)
		# 	xzpts.append((X[ix]*np.cos(theta),K_ES*(1.0-np.cos(theta)),Z[iz]*np.cos(theta)))
    #
    # yzpts=[]
    # for iy in xrange(D.shape[1]):
		# ysq=Y[iy]**2.0
		# for iz in xrange(D.shape[2]):
		# 	theta=np.arctan(np.sqrt(ysq+Z[iz]**2.0)/K_ES)
		# 	yzpts.append((K_ES*(1.0-np.cos(theta)),Y[iy]*np.cos(theta),Z[iz]*np.cos(theta)))
    #
    # xypts=np.asarray(xypts)
    # xzpts=np.asarray(xzpts)
    # yzpts=np.asarray(yzpts)
    #
    # EWDxy=ES(xypts)
    # EWDxz=ES(xzpts)
    # EWDyz=ES(yzpts)
    #
    # EWDxy=EWDxy.reshape(D.shape[0],D.shape[1])
    # EWDxz=EWDxz.reshape(D.shape[0],D.shape[2])
    # EWDyz=EWDyz.reshape(D.shape[1],D.shape[2])
    #
    # title="Ewald Corrected Structure Factor \n $\lambda=$"+str(wavelength_angstroms)+" $\AA$   $k_{ew}=$"+str(round(K_ES,2))+" $\AA^{-1}$"
    # ltitle='log ' + title
    #
    # xlab='x ('+units + ")"
    # ylab='y ('+units + ")"
    # zlab='z ('+units + ")"
    #
    # fname="Ewald_"
    #
    # plt.suptitle(title)
    # plt.xlabel(xlab)
    # plt.ylabel(ylab)
    # plt.contourf(D[:,:,0,0],D[:,:,0,1],EWDxy,contours,**kwargs)
    # plt.savefig(path+fname+"xy"+format,dpi=DPI)
    # plt.clf()
    #
    # plt.suptitle(ltitle)
    # plt.xlabel(xlab)
    # plt.ylabel(ylab)
    # plt.contourf(D[:,:,0,0],D[:,:,0,1],np.log(EWDxy),contours,**kwargs)
    # plt.savefig(path+fname+"xylog"+format,dpi=DPI)
    # plt.clf()
    #
    # plt.suptitle(title)
    # plt.xlabel(xlab)
    # plt.ylabel(zlab)
    # plt.contourf(D[:,0,:,0],D[:,0,:,2],EWDxz,contours,**kwargs)
    # plt.savefig(path+fname+"xz"+format,dpi=DPI)
    # plt.clf()
    #
    # plt.suptitle(ltitle)
    # plt.xlabel(xlab)
    # plt.ylabel(zlab)
    # plt.contourf(D[:,0,:,0],D[:,0,:,2],np.log(EWDxz),contours,**kwargs)
    # plt.savefig(path+fname+"xzlog"+format,dpi=DPI)
    # plt.clf()
    #
    # plt.suptitle(title)
    # plt.xlabel(ylab)
    # plt.ylabel(zlab)
    # plt.contourf(D[0,:,:,1],D[0,:,:,2],EWDyz,contours,**kwargs)
    # plt.savefig(path+fname+"yz"+format,dpi=DPI)
    # plt.clf()
    #
    # plt.suptitle(ltitle)
    # plt.xlabel(ylab)
    # plt.ylabel(zlab)
    # plt.contourf(D[0,:,:,1],D[0,:,:,2],np.log(EWDyz),contours,**kwargs)
    # plt.savefig(path+fname+"yzlog"+format,dpi=DPI)
    # plt.clf()