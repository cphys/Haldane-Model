import os   #used for creating output filenames
import sys
import scipy
import kwant
import numpy as np
import multiprocessing
import tinyarray as ta
from functions import spectrum
from functions import haldaneModel
from types import SimpleNamespace

defaultcpu = 4

try:
    cpus = multiprocessing.cpu_count()

except NotImplementedError:
    cpus = defaultcpu   # arbitrary default


######### Arguments passed from script #####
muResolution = sys.argv[1]
kResolution = sys.argv[2]
width = sys.argv[3]
bound = 'infinite'
tVal = 1.0
t2Val = 0.0

muRangeMax = 0.25
muRangeMin = -muRangeMax
kRangeMax = np.pi
kRangeMin = -kRangeMax
mus = np.linspace(muRangeMin, muRangeMax, muResolution)
k = (4 / 3) * np.linspace(kRangeMin, kRangeMax, kResolution)
############################################


####### Creates Diretories for files #######
cwd=os.getcwd()

folderName = 'muRes{muResolution}_kRes{kResolution}_width{width}_boundary{bound}_t{tVal:.2f}_t2{t2Val:.2f}'.format(muResolution=muResolution,kResolution=kResolution,width=width,bound=bound,tVal=tVal,t2Val=t2Val, fmt='%s')

dirName1 = os.path.join(cwd,'data',folderName,'pos')
dirName2 = os.path.join(cwd,'data',folderName,'neg')

if not os.path.exists(dirName1):
    os.makedirs(dirName1)
if not os.path.exists(dirName2):
    os.makedirs(dirName2)
#############################################


infiniteSystem = haldaneModel(w = width, boundary = bound)

def paralelFunc(imu):
    p = SimpleNamespace(t = tVal, t_2 = t2Val, m=imu, phi=np.pi/2)
    fname1 = os.path.join(dirName1, 'mu{imu}.txt'.format(imu=imu,fmt='%s'))
    fname2 = os.path.join(dirName2, 'mu{imu}.txt'.format(imu=imu,fmt='%s'))
    data = spectrum(infiniteSystem, p, res = kResolution, k_x=k, k_y=k, return_energies=True)
    dim1 = len(data)
    dim2 = len(data[0])
    index1 = np.linspace(0,dim1-1,dim1)
    index2 = np.linspace(0,dim2-1,dim2)
    func1 = np.array([[data[int(j)][int(i)][0] for i in index1] for j in index2])
    func2 = np.array([[data[int(j)][int(i)][1] for i in index1] for j in index2])
    np.savetxt(fname1,func1)
    np.savetxt(fname2,func2)


pool = multiprocessing.Pool(processes=cpus)
data = pool.map(paralelFunc, mus)
pool.close()
pool.join()

