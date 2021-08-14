#! /usr/bin/env python

from __future__ import division
from __future__ import print_function
from builtins import range
# from past.utils import old_div
import numpy as np
import math
import os.path
import dens2
import plot2d as p2d
import tqdm  # progress bar
from tqdm import trange
import platform
import matplotlib.pyplot as plt  # must be imported after anything that imports mayavi/mlab
import argparse
import warnings

XRAY_WAVELENGTH = 1.54

parser = argparse.ArgumentParser(description='Calculate 3d Structure Factor')

parser.add_argument('-i', '--input', default='', type=str, help='Input topolgy and trajectory basename')
parser.add_argument('-top', '--topology', default='', type=str, help='Input topolgy filename')
parser.add_argument('-traj', '--trajectory', default='', type=str, help='Input trajectory filename')
parser.add_argument('--cscale', default=1, type=float, help='Scale color map on plots')
parser.add_argument('--lcscale', default=1, type=float, help='Scale color map on log plots')
parser.add_argument('-fi', '--first_frame', default=0, type=int, help='frame to start at')
parser.add_argument('-e', '--end_frame', default=-1, type=int, help='frame to end at')
parser.add_argument('-fr', '--force_recompute', default=0, type=int, help='force recomputing SF (if >=1) or trajectory and SF(if >=2)')
#parser.add_argument('-o', '--output', default='', type=str, help='override output basename')

#random trajectory parameters
parser.add_argument('-RC', '--random_counts', default=0, type=int, help='set this to specify number of random particles to use')
parser.add_argument('-RT', '--random_timesteps', default=1, type=int, help='set this to specify number of random timesteps to use')
parser.add_argument('-RL', '--random_label', default="R3", type=str, help='set this to specify the element type of the random particle')

#parser.add_argument('-HL', '--hex_label', default="R3", type=string, help='set this to specify the element type of the hexagonal lattice')


parser.add_argument('-LX', '--lattice_x', default=0, type=int, help='set this to specify the number of lattice points in the X direction')
parser.add_argument('-LY', '--lattice_y', default=1, type=int, help='set this to specify the number of lattice points in the Y direction')
parser.add_argument('-LZ', '--lattice_z', default=1, type=int, help='set this to specify the number of lattice points in the Z direction')

# parser.add_argument('-LN', '--lattice_x', default=0, type=int, help='set this to override the number of lattice points in each direction')


parser.add_argument('-LL', '--lattice_label', default="R3", type=str, help='set this to specify the element label of lattice particles')

parser.add_argument('-SR', '--spatial_resolution', default=1.0, type=float,help='set this to specify the spatial resolution for the density grid')
parser.add_argument('--ewload', action="store_true")
parser.add_argument('-RN', '--random_noise', default=0, type=int,help='set this to a positive value to use random noise'
                    ' for testing.  A conventional trajectory must still be loaded.  The number of timesteps to be used'
                    ' will be scaled by this integer')
parser.add_argument('-RS', '--random_seed', default=1, type=int,help='Set the random seed from the command line')

parser.add_argument('-NBR', '--number_bins_rad', default=0, type=int,help='Set this to a nonzero value to use that many'
                    'radial bins.  These bins will be scaled such that they contain roughly the same number of points')
parser.add_argument('--rzscale', default=1, type=float
)
args = parser.parse_args()

location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))  # Directory this script is in

warnings.simplefilter("ignore", RuntimeWarning)


theta = math.pi/3.0  # theta for monoclinic unit cell
ucell = np.array([[1, 0, 0], [np.cos(theta), np.sin(theta), 0], [0, 0, 1]])

np.random.seed = args.random_seed  # args.random_noise
p2d.NBINSRAD = args.number_bins_rad

if args.random_noise > 0:

    dens2.RANDOM_NOISE = args.random_noise

if len(args.input) > 0:
    basename = args.input
    top_file = args.input+".gro"
    traj_file = args.input+".trr"
else:
    top_file = args.topology
    traj_file = args.trajectory
    basename = args.topology.rsplit('.', 1)[0]

# if len(args.output)>0:
# 	basename=args.output

print("running on", platform.system(), platform.release(), platform.version())

if platform.system() == "Windows":  # path separators
    fd = "\\"
else:
    import load_traj as lt
    fd = "/"

label = "out_"+basename

tfname = label+"_traj"
sfname = label+"_sf"

Nlat = args.lattice_x * args.lattice_y * args.lattice_z

if Nlat > 0:

    boxsize = 100.0

    Nx = args.lattice_x
    Ny = args.lattice_y
    Nz = args.lattice_z

    Nsteps = 1

    dims = np.ones((Nsteps, 3))*boxsize
    coords = np.zeros((Nsteps, Nlat, 3))

    cbufx = np.linspace(0, boxsize, Nx, endpoint=False)
    cbufy = np.linspace(0, boxsize, Ny, endpoint=False)
    cbufz = np.linspace(0, boxsize, Nz, endpoint=False)

    cbx,cby,cbz = np.meshgrid(cbufx,cbufy,cbufz)

    coords[0,:,0] = cbx.reshape((Nlat))
    coords[0,:,1] = cby.reshape((Nlat))
    coords[0,:,2] = cbz.reshape((Nlat))

    sfname = 'lattice_'+str(Nx)+"_"+str(Ny)+"_"+str(Nz)

    name = np.zeros(Nlat,dtype=object)
    mass = np.zeros(Nlat)
    typ = np.zeros(Nlat,dtype=object)

    typ[:]=args.lattice_label

    print("saving...")
    np.savez_compressed(sfname,dims=dims,coords=coords,name=name,typ=typ)
    rad = dens2.load_radii("%s/radii.txt" % location) # load radii definitions from file
    print("computing SF...")

    dens2.compute_sf(coords, dims, typ, sfname, rad, ucell, args.spatial_resolution) # compute time-averaged 3d structure factor and save to sfname.npz

elif args.random_counts > 0:	#create a random trajectory

    spcheck = 0  #check if simulating a single particle.

    Rboxsize = 100.0
    BUFFsize = 10000000
    sfname = 'RND'

    print("generating random trajectory...")
    Rsteps = args.random_timesteps
    Ratoms = args.random_counts #100000#0

    dims = np.ones((Rsteps, 3)) * Rboxsize
    coords = np.random.random((Rsteps, Ratoms, 3)) * dims[0,:]

    name = np.zeros(Ratoms,dtype=object)
    mass = np.zeros(Ratoms)
    typ = np.zeros(Ratoms,dtype=object)

    typ[:] = args.random_label

    print("saving...")
    np.savez_compressed("RAND",dims=dims,coords=coords,name=name,typ=typ)
    rad = dens2.load_radii("%s/radii.txt" % location) # load radii definitions from file
    print("computing SF...")

    dens2.compute_sf(coords, dims, typ, sfname, rad, ucell, args.spatial_resolution) # compute time-averaged 3d structure

else:  #load trajectory or npz file

    if args.force_recompute > 0 or not os.path.isfile(sfname+".npz"):			#check to see if SF needs to be calculated
        if args.force_recompute > 1 or not os.path.isfile(tfname+".npz"): 		#check to see if trajectory needs to be processed
            if platform.system() == "Windows":  										#This part must be done in an environment that can import MDAnalysis
                print("Unable to process trajectory file on Windows")
                exit()
            else:
                print("processing trajectory file "+traj_file)
                lt.process_gro_mdtraj(top_file, traj_file, tfname)   					#Process trajectory into numpy array.
                print('done')

        traj = np.load(tfname+".npz")							#load processed trajectory
        rad = dens2.load_radii("%s/radii.txt" % location)					#load radii definitions from file

        dens2.compute_sf(traj['coords'][args.first_frame:args.end_frame,...],traj['dims'][args.first_frame:args.end_frame,...],traj['typ'],sfname,rad,ucell,args.spatial_resolution) #compute time-averaged 3d structure factor and save to sfname.npz

print("reloading SF...")
dpl = np.load(sfname+".npz")  # load 3d SF

grid = dpl['kgridplt']

p2d.mainlabel = basename			# title for plots

dir = p2d.mainlabel+"_plots"+fd	 # set up directories for saving plots
sfdir = dir+"structure_factor"+fd
sfsubdir = sfdir+"additional_plots"+fd
EWdir = dir+"Ewald_Corrected"+fd

print("making plots...")
if True:
    print("Ewald plots")
    p2d.path = EWdir
    p2d.Plot_Ewald_triclinic(grid, XRAY_WAVELENGTH, ucell, args.ewload, rzscale=args.rzscale)		#compute Ewald-corrected SF cross sections in xy,xz,yz planes
    print("EW done")
if True:
    print("xy,yz,xz plots")
    p2d.path = dir + sfdir
    p2d.radial_integrate(grid, 750, dir+"radial.png")

if False:  #additional slices through SF
    print("additional plots")
    Nsteps = 8
    p2d.path = sfsubdir+"xplots"+fd
    p2d.savelin = False
    for i in tqdm.tqdm(range(0, grid.shape[0], grid.shape[0]/Nsteps)):
        p2d.sfplot(grid[i, :, :, :])

    p2d.path = sfsubdir+"yplots"+fd
    for i in tqdm.tqdm(range(0, grid.shape[1], grid.shape[1]/Nsteps)):
        p2d.sfplot(grid[:, i, :, :])

    p2d.path = sfsubdir+"zplots"+fd
    for i in tqdm.tqdm(range(0, grid.shape[1], grid.shape[2]/Nsteps)):
        p2d.sfplot(grid[:, :, i, :])
