#!/usr/bin/python -u
# 2016.4.20 09:29
__author__ = 'TQC'

import os
import re
import sys
import numpy  as np
import  glob
class  G09toVASP(object):
    def __init__(self):
    	self.name = ''
    	self.pos = []
    	self.ene = 0.0
       	
    def Read_Goutput(self):
    	lat = []
    	litem = []
    	linelat = []
    	a2b = 1.0/0.529177
    	hartrees2eV = 27.21
    	if os.path.exists('goutput'):
    		fileOpen = 'goutput'
    	else:
    		print 'Error: no input file: goutput'
    		exit(0)
    	f = open(fileOpen, 'r')
    	nstru = 0
    	ns = int(os.popen("grep 'E('  goutput   | wc -l").read().split()[0])
    	ns += 1
    	while True:
    		line = f.readline()
    		if len(line) == 0:
    			break
    		if 'NAtoms=' in line:
    			litem = line.split()
    			natom = int(litem[1])
    		if  'Multiplicity' in  line:
    			line = f.readline()
    			self.name = line.split()[0]
    		if 'Coordinates' in line:
    			nstru = nstru + 1
    			if nstru == ns:
    				#fw = open('glast.xyz','w')
    				f.readline()
    				f.readline()
    				for i in range(natom):
    					templat = f.readline().split()
    					lat = (map(float,templat[3:6]))
    					self.pos.append(lat)
    		if 'E(' in line:
    			linelat = line.strip().split()
    			self.ene = float(linelat[4])*hartrees2eV/natom
    	self.pos = np.array(self.pos,float)
    	#print pos,name
    	#return (name,pos,ene)
    
    def G09toVASP(self):
        (natom,dim) = self.pos.shape
        x = self.pos[:,0]
        y = self.pos[:,1]
        z = self.pos[:,2]
        vacuum = '15   15    15'
        va = map(float,vacuum.split())
        lat = []
    
        lat.append(max(x) - min(x) + va[0])
        lat.append(max(y) - min(y) + va[1])
        lat.append(max(z) - min(z) + va[2])
    
        pos = []
        for i in range(natom) :
            a = ( x[i] - 0.5 * (min(x) + max(x)) ) / lat[0] + 0.5
            b = ( y[i] - 0.5 * (min(y) + max(y)) ) / lat[1] + 0.5
            c = ( z[i] - 0.5 * (min(z) + max(z)) ) / lat[2] + 0.5
            pos.append([a,b,c])
    
        f = open("CONTCAR", 'w')
        f.write('g09tovasp\n' +
                '1.0\n' +
                ("%12.6f" % lat[0]) + ("%12.6f" % 0.0 ) + ("%12.6f" % 0.0 ) + "\n" +
                ("%12.6f" % 0.0 ) + ("%12.6f" % lat[1]) + ("%12.6f" % 0.0 ) + "\n" +
                ("%12.6f" % 0.0 ) + ("%12.6f" % 0.0 )  + ("%12.6f" % lat[2] + "\n") )
        f.write(str(self.name) + '\n')
        f.write( ( "%d" % natom )+ "\n" + 
                "Direct\n")
        for i in range(natom) : 
            f.write( ("%20.10f" %pos[i][0]) + ("%20.10f" %pos[i][1]) + ("%20.10f" %pos[i][2]) + "\n" )
        f.close()
        f = open('OUTCAR','w')
        f.write('energy  without entropy=  %15.10f\n' % self.ene)
        #f.write(str(self.ene)+'\n')
        f.close()
    
    
    def Read_Dposcar(self,fa):
    	lat = []
    	pos = []
    	line1 = []
    	f1 = open(fa,'r')
    	line1 = f1.readlines()
    	f1.close()
    	name = str(line1[0].split()[0])
    	try:
    		na = int(line1[5].split()[0])
    	except:
    		name = str(line1[5].strip())
    		del line1[5]
    		na = int(line1[5].split()[0])
    	for a in range(3):
    		lat.append(line1[2+a].split())
    	for a in range(na):
    		pos.append(line1[7+a].split()[0:3])
    	lat = np.array(lat,float)
    	pos = np.array(pos,float)
    	cpos = np.dot(pos,lat)
    	return na,name,lat,cpos
    
    def POSCARtoG09(self,finput):
        '''conver the POSCAR file to g.xyz'''
        try: 
            f = open(finput, 'r')
        except:
            print "No file:",finput
            sys.exit(0)
        (na,name,lat,pos) = Read_Dposcar(finput)
        foutfile = str(finput.split('_')[1]) + '.xyz'
        f = open(foutfile,'w')
        #f.write(str(na) + '\n')
        #f.write('1:p1(1)\n')
        for i in range(na):
    	    f.write(str(name) + ' ')
    	    f.write(' %15.10f %15.10f %15.10f\n' % tuple(pos[i]))
        f.write('\n')
    
    def VASPtoG09(self):
        carfile = glob.glob('POSCAR_*')
        if len(carfile) == 0:
            print "*.vasp file not exits"
            sys.exit(0)
        for finput in carfile:
            #print finput
            POSCARtoG09(finput)

if __name__ == '__main__':
	a = G09toVASP()
	a.VASPtoG09()
