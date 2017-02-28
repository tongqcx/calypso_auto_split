#!/usr/bin/python

import os
import time
import sys
import glob

class Autocalypso(object):
	def __init__(self,submit = 'qsub vasp.pbs',stat = 'qstat',rstat = 'qstat | grep R',delete = 'qdel',\
				calypath = './calypso.x',machine = 'pbs'):
		self.CalyPsoPath = calypath
		self.submit = submit
		self.stat = stat
		self.rstat = rstat
		self.delete = delete
		self.machine = machine

	def readinput(self):
		f = open('input.dat','r')
		while True:
			line = f.readline()
			if len(line) == 0:
				break
			if 'PopSize' in line:
				self.StrNum = int(line.split('=')[1])
			if 'MaxStep' in line:
				self.GenNum = int(line.split('=')[1])
			if 'MaxTime' in line:
				self.MaxTime = int(line.split('=')[1])
			if 'NumberOfParallel' in line:
				self.NP = int(line.split('=')[1])
				if self.StrNum < self.NP:
					self.NP = self.StrNum
			if 'PickUp' in line:
				pickup = line.split('=')[1]
				if pickup == 'T':
					self.PickUp = True
				else:
					self.PickUp = False

	def checkfiles(self):
		if not os.path.exists(r'./input.dat'):
			print "No input.dat"
			sys.exit(0)
		elif not os.path.exists(r'./POTCAR'):
			print "No POTCAR"
			sys.exit(0)
		elif len(glob.glob(r'./INCAR_*')) == 0:
			print "No INCAR files"
			sys.exit(0)
		else:
			print "Check files completed!!!"

	def lpickup(self):
		if not self.PickUp:
			os.system("rm step")

	def submit_vasp(self,n):
		os.system(self.CalyPsoPath)
		if n != self.GenNum:
			self.control_vasp()

	def autorun(self):
		self.checkfiles()
		self.readinput()
		self.lpickup()
		i = 0
		while i < self.GenNum:
			self.submit_vasp(i)
			i += 1

	def control_vasp(self):
		for i in range(self.StrNum):
			os.system("rm -rf %s" %str(i+1))
			os.system("mkdir %s" % str(i+1))
			if self.machine == 'pbs':
				os.system("cp vasp.pbs POTCAR INCAR_*  %s" % str(i+1))
			elif self.machine == 'lsf':
				os.system("cp run.lsf POTCAR INCAR_*  %s" % str(i+1))
			else:
				os.system("cp vasp.sh POTCAR INCAR_*  %s" % str(i+1))
			os.system("cp POSCAR_%s  %s/CONTCAR" % (str(i+1),str(i+1)))
		totaljobid = []
		runjobid = []
		splitjobid = []
		split_run_jobid = []
		jobtime = {}
		for i in range(self.NP):
			if self.machine == 'pbs':
				id = int(os.popen(" cd %s; %s;cd .." % (str(i+1),self.submit)).read().split('.')[0])
			elif self.machine == 'lsf':
				id = int(os.popen(" cd %s; %s;cd .." % (str(i+1),self.submit)).read().split(' ')[1].\
											strip('<').strip('>'))
			else:
				id = int(os.popen(" cd %s; %s;cd .." % (str(i+1),self.submit)).read().split(' ')[3])
			splitjobid.append(id)
			jobtime[id] = 0	
		print splitjobid
		num = self.NP
		finnum = 0   
		tenode = 0
		nover = 0
		while finnum < self.StrNum:
			totaljobid = self.run_jobid(self.stat)
			runjobid = self.run_jobid(self.rstat)
			splitjobid = list(set(splitjobid).intersection(set(totaljobid)))
			split_run_jobid = list(set(splitjobid).intersection(set(runjobid)))
			for  ii in split_run_jobid:
				jobtime[ii] += 2
				if jobtime[ii] > self.MaxTime:
					print "qdel %d" % ii
					os.system("%s %s" % (self.delete,str(ii)))	
			print jobtime	
			enode = len(splitjobid)	
			if enode == 0:
				nover += 1
			if nover == 5:
				break
			if enode < tenode:
				finnum += (tenode-enode)
			tenode = enode
			fnode = self.NP-enode
			if fnode > 0:
				if num < self.StrNum:
					for i in range(fnode):
						if (num+i+1) <= self.StrNum:
							if self.machine == 'pbs':
								id = int(os.popen(" cd %s; %s ;cd .." % (str(num+i+1),self.submit)).\
												read().split('.')[0])
							elif self.machine == 'lsf':
								id = int(os.popen(" cd %s; %s ;cd .." % (str(num+i+1),self.submit)).\
										read().split(' ')[1].strip('<').strip('>'))
							else:
								id = int(os.popen(" cd %s; %s ;cd .." % (str(num+i+1),self.submit)).\
												read().split(' ')[3])
							splitjobid.append(id)
							jobtime[id] = 0	
					num += fnode
			time.sleep(2)
			#print "submitted",num, "finished",finnum
		for i in range(self.StrNum):
			os.system("cp %s/CONTCAR  CONTCAR_%s" % (str(i+1),str(i+1)))
			os.system("cp %s/OUTCAR  OUTCAR_%s" % (str(i+1),str(i+1)))

	def run_jobid(self,cmd):
		runjobid = []
		aa = os.popen('%s' % cmd).readlines()
		for line in aa:
			try:
				if self.machine == 'pbs':
					runjobid.append(int(line.split('.')[0]))
				elif self.machine == 'lsf':
					runjobid.append(int(line.split(' ')[0]))
				else:
					runjobid.append(int(line.split(' ')[0]))
			except:
				continue
		return runjobid

	def split_jobid(self):
		splitjobid = []
		for i in range(self.NP):
			splitjobid.append(int(os.popen(" cd %s;qsub vasp.pbs;cd .." % (str(i+1))).read().split('.')[0]))
		return splitjobid
				
def writevasppbs(nodes = '1',ppn = '12',walltime = '01:00:00',vasppath = '/public/apps/vasp5.3.5/vasp'):
	f = open('vasp.pbs','w')
	f.write('#!/bin/bash\n')
	f.write('#PBS -l nodes=%s:ppn=%s\n' % (nodes,ppn))
	f.write('#PBS -j oe\n')
	f.write('#PBS -V\n')
	f.write('#PBS -l walltime=%s\n' % walltime)
	f.write('cd $PBS_O_WORKDIR\n')
	f.write("num_in=`ls -l |grep 'INCAR_' |wc -l`\n")
	f.write('for(( i=1; i<=num_in; i++ ));\n')
	f.write('do\n')
	f.write('\tcp INCAR_$i INCAR\n')
	f.write('\tcp CONTCAR POSCAR\n')
	f.write('\tmpirun -np %s  %s > out_$i\n' % (ppn,vasppath))
	f.write('done\n')
	f.close()

def writerunlsf(nodes = '1',ppn = '12',vasppath = '/data3/home/mym/apps/vasp/vasp.5.3.2'):
	f = open('run.lsf','w')
	f.write('#!/bin/sh\n')
	f.write('#BSUB -q vasp\n')
	f.write('#BSUB -app vasp\n')
	f.write('#BSUB -a intelmpi\n')
	f.write('#BSUB -o %J.lsf.output\n')
	f.write('#BSUB -n 12\n')
	f.write('#BSUB -R "span[ptile=12]"\n')
	f.write("num_in=`ls -l |grep 'INCAR_' |wc -l`\n")
	f.write('for(( i=1; i<=num_in; i++ ));\n')
	f.write('do\n')
	f.write('\tcp INCAR_$i INCAR\n')
	f.write('\tcp CONTCAR POSCAR\n')
	f.write('\tmpirun -np %s  %s > out_$i\n' % (ppn,vasppath))
	f.write('done\n')
	f.close()

def writeyh():	
	f = open('vasp.sh','r')
	f.write('#!/bin/bash\n')
	f.write("num_in=`ls -l |grep 'INCAR_' |wc -l`\n")
	f.write('for(( i=1; i<=num_in; i++ ));\n')
	f.write('do\n')
	f.write('\tcp INCAR_$i INCAR\n')
	f.write('\tcp CONTCAR POSCAR\n')
	f.write('yhrun -N 1 -n 12 -p TH_NET /vol-th/home/maym/software/vasp.5.4.1/bin/vasp_std > vasp.log 2>&1')
	f.write('done\n')
	f.close()
			
if __name__ == '__main__':
	#sys.exit(0)
	if len(sys.argv) == 1:
		if not os.path.exists(r'./vasp.pbs'):
			print "No vasp.pbs file!!!"
			print "We will generate another file, maybe you need change it!!!"
			writevasppbs()
			sys.exit(0)
		a = Autocalypso()
	elif 'pbs' in sys.argv[1].lower():
		if not os.path.exists(r'./vasp.pbs'):
			print "No vasp.pbs file!!!"
			print "We will generate another file, maybe you need change it!!!"
			writevasppbs()
			sys.exit(0)
		a = Autocalypso()
	elif 'lsf' in sys.argv[1].lower():
		if not os.path.exists(r'./run.lsf'):
			print "No run.lsf file!!!"
			print "We will generate another file, maybe you need change it!!!"
			writerunlsf()
			sys.exit(0)
		submit = 'bsub run.lsf'
		stat = 'bjobs'
		rstat = 'bjobs | grep RUN'
		delete = 'bkill'
		a = Autocalypso(submit,stat,rstat,delete,machine = 'lsf')
	elif 'yh' in sys.argv[1].lower():
		if not os.path.exists(r'./vasp.sh'):
			print "No vasp.sh file!!!"
			print "We will generate another file, maybe you need change it!!!"
			writeyh()
			sys.exit(0)
		submit = 'yhbatch -p TH_NET -N 1 -n 12 vasp.sh'
		stat = 'yhq'
		rstat = 'yhq | grep R'
		delete = 'yhcancel'
		a = Autocalypso(submit,stat,rstat,delete,machine = 'yh')
	#sys.exit(0)
	a.autorun()
