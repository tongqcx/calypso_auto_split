#!/usr/bin/python -u
# 2016.4.20 09:29
__author__ = 'TQC'

import os
import re
import sys
import numpy  as np

def extract():
	lat = []
	litem = []
	temp = []
	templat = []
	a2b = 1.0/0.529177
	hartrees2eV = 27.21
	if os.path.exists('goutput'):
		fileOpen = 'goutput'
	else:
		print 'Error: no input file: goutput'
		exit(0)
	f = open(fileOpen, 'r')
	nstru = 0
	while True:
		line = f.readline()
		if len(line) == 0:
			break
		if 'NAtoms=' in line:
			litem = line.split()
			natom = int(litem[1])
		if  'Multiplicity' in  line:
			line = f.readline()
			name = line.split()[0]
		if 'Coordinates' in line:
			nstru = nstru + 1
			#if nstru==0:
			#	continue
			fw = open(str(nstru)+'_g.xyz','w')
			#fw.write("%s\n"  %  name)
			#fw.write("%15.10f\n" %  1.0)
			trtreesemp = f.readline()
			temp = f.readline()
			fw.write("%d\n" %  natom)
			fw.write("\n")
			for i in range(natom):
				templat = f.readline().split()
				#lat.append(map(float,templat[0:3]))
				lat = (map(float,templat[3:6]))
				fw.write(str(name) + ' ')
				fw.write("%15.10f\t%15.10f\t%15.10f\n" %  tuple(lat[0:3]))
			#fw.write("%s\n"  %  name)
			fw.write("\n" )
		if 'E(' in line:
			linelat = line.strip().split()
			#print linelat
			fw.write("%s\n" %  'Energy(eV)')
			ene = float(linelat[4])*hartrees2eV/natom
			fw.write("%15.10f\n"  %  ene)
		if 'Forces (Hartrees/Bohr)' in line:
			temp = f.readline()
			temp = f.readline()
			fw.write("%s\n" %  'Forces (eV/A)')
			for i in range(natom):
				templat = f.readline().split()
				lat = np.array(templat[2:5],float)
				lat1 = 	lat[0:3]*hartrees2eV*a2b
				fw.write("%15.10f\t%15.10f\t%15.10f\n" %  tuple(lat1))
			fw.close()
'''
		if 'in kB' in line:
			stress_temp = map(float,line.split()[2:8])
			stress_sort = [0.0,0.0,0.0,0.0,0.0,0.0]
			stress_sort[0] = stress_temp[0]
			stress_sort[1] = stress_temp[3]
			stress_sort[2] = stress_temp[5]
			stress_sort[3] = stress_temp[1]
			stress_sort[4] = stress_temp[4]
			stress_sort[5] = stress_temp[2]
			stress = stress_sort
			#print stress
			#fw.write("%15.10f\t%15.10f\t%15.10f\t%15.10f\t%15.10f\t%15.10f\n" %  tuple(stress))
		if 'POSITION'  in line:
			f.readline()
			for i in range(natom):
				litem = map(float,f.readline().split())
				fw.write("%15.10f\t%15.10f\t%15.10f\t%15.10f\t%15.10f\t%15.10f\n" %  tuple(litem))
				#fw.write("	%s\n" % "F")
				#fw.write("%15.10f\t%15.10f\t%15.10f\n" %  tuple(litem[0:3]))
		if 'energy  without entropy' in line:
			energy = float(line.split()[3].strip())
			fw.write("%15.11f %15.11f\n"  %  (energy,energy/natom))
			#fw.write("	%s\n"  %  "E")
			fw.write("%15.10f\t%15.10f\t%15.10f\t%15.10f\t%15.10f\t%15.10f\n" %  tuple(stress))
			#fw.write("	%s\n"  %  "S")
			fw.close()'''
	#f.close()
def extract_last():
	lat = []
	litem = []
	temp = []
	templat = []
	pos = []
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
			name = line.split()[0]
		if 'Coordinates' in line:
			nstru = nstru + 1
			if nstru == ns:
				#fw = open('glast.xyz','w')
				f.readline()
				f.readline()
				for i in range(natom):
					templat = f.readline().split()
					lat = (map(float,templat[3:6]))
					pos.append(lat)
	pos = np.array(pos,float)
	#print pos,name
	return (name,pos)
if __name__ == '__main__':
	#nns = int(sys.argv[1])
	#print nns
	extract()
