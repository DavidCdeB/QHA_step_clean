# 
# This script extracts ET, TS EL E0 from many outputs and prints out:
# V vs F @ each Temperature.
# These files are needed for the last step of the QHA methodology,
# where we need tables of F vs V 
# in order to then compute P=dF/dV and then G(P,T)

import re
import os
import glob
from itertools import islice
import numpy as np
import sys
import shutil
import subprocess

os.system("rm -Rf F_vs_V_*")

n_volume = []
path='./'
template = os.path.join(path, '*.out')

# Setting the number of formula units as a raw_input:
n_F_u = raw_input("""
Please type as an integer the number of formula units in the primitive cell. 
For example, Calcite I contains 2 formula units in the primitive (rombohedral) cell and 6 formula units in the crystallographic (hexagonal) cell. Thus, the number to be introduced is:   2 <and press ENTER>
""")

n_F_u = float(n_F_u)
n_F_u = int(float(n_F_u))

# Extracting each thermodynamic variable:
ET = []
TS = []
EL = []
E0 = []
VOLUME_EACH = []
T = []

for fname in glob.glob(template):
  print fname
  f = open(fname, 'r')
  real_part = False

  for line in f:

        if re.match(r"^ ET            :", line):
         start = line.find(':') + 8
         end = line.find(':') + 22
         result_ET = line[start:end]
         ET.append(result_ET)

        if re.match(r"^ TS            :", line):
         start = line.find(':') + 8
         end = line.find(':') + 22
         result_TS = line[start:end]
         TS.append(result_TS)

        if re.match(r"^ EL            :", line):
         start = line.find(':') + 4
         end = line.find(':') + 22
         result_EL = line[start:end]
         EL.append(result_EL)

        if re.match(r"^ E0            :", line):
         start = line.find(':') + 8
         end = line.find(':') + 22
         result_E0 = line[start:end]
         E0.append(result_E0)

        if re.match(r"^ AT \(T =", line):
         start = line.find('T =') + 4
         end = line.find('K')
         result_Temperatures = line[start:end]
         T.append(result_Temperatures)

        if 'LATTICE PARAMETERS  (ANGSTROMS AND DEGREES) - PRIMITIVE CELL' in line:  
                  print "line 1 = ", line
                  f.next()
                  each_volume_times_4 = []
                  each_volume_times_100 = []
                  
                  parameters = (''.join(islice(f, 1)))
                  columns = parameters.split()
                  each_volume = columns[6]
                  print 'each_volume = ', each_volume

                  VOLUME_EACH.append(each_volume)

# Transform each element of the list from <str> to <float64>:
VOLUME_EACH = [float(i) for i in VOLUME_EACH]
EL = [float(i) for i in EL]
E0 = [float(i) for i in E0]
ET = [float(i) for i in ET]
TS = [float(i) for i in TS]
T = [float(i) for i in T]

# Transform each element of the list to a numpy array:
VOLUME_EACH = np.array(VOLUME_EACH)
EL = np.array(EL)
E0 = np.array(E0)
ET = np.array(ET)
TS = np.array(TS)
T = np.array(T)

# Divide per F.U.:
VOLUME_EACH = VOLUME_EACH/n_F_u
EL = EL/n_F_u
E0 = E0/n_F_u
ET = ET/n_F_u
TS = TS/n_F_u

output_array = np.vstack((VOLUME_EACH, EL)).T
np.savetxt('EL_vs_V.dat', output_array, header="Volume           EL", fmt="%0.13f")
os.system("sort -k1 -n EL_vs_V.dat -o EL_vs_V.dat")

EL_plus_E0 = EL + E0

output_array = np.vstack((VOLUME_EACH, EL_plus_E0)).T
np.savetxt('EL_plus_E0_vs_V.dat', output_array, header="Volume           EL+E0", fmt="%0.13f")
os.system("sort -k1 -n EL_plus_E0_vs_V.dat -o EL_plus_E0_vs_V.dat")

n_volume = len(VOLUME_EACH)

n_T = len(T) / n_volume

ET = np.reshape(ET, (n_volume, n_T))
TS = np.reshape(TS, (n_volume, n_T))
T  = np.reshape(T, (n_volume, n_T))

rows = ET.shape[0]
cols = ET.shape[1]

rows = ET.shape[0]
cols = ET.shape[1]

F_all = []
for x, indx_EL, indx_E0 in zip(range(0, rows), range(len(EL)), range(len(E0))):
    aux = []    
    for y in range(0, cols):
        F = EL[indx_EL] + E0[indx_E0] + ET[x,y] - TS[x,y]
        aux.append(F)
    F_all.append(aux)

# Transform to a np.array:
F_all = np.array(F_all)

cols_T = T.shape[1]
rows_T = T.shape[0]

F_all_each_V_at_cte_T = []
for indx, t  in zip(range(0, cols), range(0, cols_T) ):
   aux_T = T[:,t] 
   aux_F = F_all[:,indx]
   print ' aux_F = ', aux_F
   print ' aux_T[0] = ', aux_T[0]

   output_array = np.vstack((VOLUME_EACH, aux_F)).T
   print 'shape(output_array) =', output_array.shape
   output_array_sorted_on_V = output_array[output_array[:,0].argsort()]
   np.savetxt('F_vs_V_%0.2fK.dat'  %aux_T[0], output_array_sorted_on_V, header="Volume           F at %0.2fK" %aux_T[0], fmt="%0.13f")
   os.makedirs('F_vs_V_%0.2fK' %aux_T[0])
   shutil.move("./F_vs_V_%0.2fK.dat" %aux_T[0], "./F_vs_V_%0.2fK" %aux_T[0])

#for t in range(0, cols_T):
#   aux_T = T[:,t]
#   os.makedirs('F_vs_V_%0.2fK' %aux_T[0])
   
os.system('rm -Rf EL_vs_V')
os.system('mkdir EL_vs_V')
os.system('mv EL_vs_V.dat  ./EL_vs_V')

os.system('rm -Rf EL_plus_E0_vs_V')
os.system('mkdir EL_plus_E0_vs_V')
os.system('mv EL_plus_E0_vs_V.dat  ./EL_plus_E0_vs_V')

os.system('rm -Rf G_PT')
os.system('mkdir G_PT')
os.system('mv  F_vs_V_* ./G_PT')

#os.system('mv InTerSect_EL_level.py ./EL_vs_V')


