'''
Description: 
    Running CALYPSO structure search with Split mode automatically on cluster. 

Usage:
    nohup python caly_auto_split.py  --jobms=JOBMS --extexec=EXTEXEC --calypath=CALYPATH
    --jobms       Defining the Job Managemant System pbs|lsf|yh|slurm
    --extexec     Defining the external command to run optimization task, Default 'mpirun -np 20 ./vasp > log'
    --calypath    Defining the location of calypso.x, Default './calypso.x'

Author: 
    Qunchao Tong<tqc@calypso.cn>

Date: 2019.02.18

Modified:
'''
#!/usr/bin/python

import os
import time
import sys
import glob
try:
    import argparse
except:
    print ''' No libargparse, please install it
              if you have installed pip tool, you need run
              pip install argparse'''
    sys.exit(0)

class Autocalypso(object):
    def __init__(self,\
                 submit = 'qsub vasp.pbs',\
                 stat = 'qstat',\
                 rstat = 'qstat | grep R',\
                 delete = 'qdel',\
                 machine = 'pbs',\
                 calypath = './calypso.x',\
                 extexec = 'mpirun -np 20 ./vasp > log'):

        self.CalyPsoPath = calypath
        self.submit = submit
        self.stat = stat
        self.rstat = rstat
        self.delete = delete
        self.machine = machine
        self.extexec = extexec
        self.MaxTime = 3600
        self.StrNum = 30
        self.MaxStep = 20
        self.NumberOfParallel = 5
        self.PickUp = False
        self.NumberOfLocalOptim = 3
        self.f = open('split_calypso.log','w')
        self.sleeptime = 2
        self.NumLocOpt = 3

    def readinput(self):
        if not os.path.exists(r'./input.dat'):
            print 'input.dat not exit'
            sys.exit(0)
    
        self.StrNum = int(self.get_input_para('PopSize',30))
        self.NP = int(self.get_input_para('NumberOfParallel',5))
        self.MaxStep = int(self.get_input_para('MaxStep',1000))
        self.MaxTime = int(self.get_input_para('MaxTime',1800))
        self.NumLocOpt = int(self.get_input_para('NumberOfLocalOptim',3))
        self.PickUp = self.get_input_para('PickUp','F')

        if self.StrNum < self.NP:
            self.NP = self.StrNum

        if self.PickUp == 'F':
            self.lPickUp = False
        else:
            self.lPickUp = True

        if not self.lPickUp:
            if os.path.exists(r'./step'):
                os.system('rm step')
            if os.path.exists(r'./results'):
                os.system('rm -rf results')

        self.GenNum = self.MaxStep		
        

    def get_input_para(self,chara,n):
        line = os.popen('grep %s input.dat' % chara).read()
        if line == '':
            return n
        if line[0] == '#':
            return n
        else:
            return line.split('=')[1].strip()

    def checkfiles(self):
        if self.machine == 'pbs':
            if not os.path.exists(r'./vasp.pbs'):
                print 'vasp.pbs not exit'
                print 'A new vasp.pbs script has been written, and you should modify it!'
                self.writevasppbs()
                sys.exit(0)
        elif self.machine == 'lsf':
            if not os.path.exists(r'./run.lsf'):
                print 'run.lsf not exit'
                print 'A new run.lsf script has been written, and you should modify it!'
                self.writerunlsf()
                sys.exit(0)
        elif self.machine == 'yh':
            if not os.path.exists(r'./vasp.sh'):
                print 'vasp.sh not exit'
                print 'A new vasp.sh script has been written, and you should modify it!'
                self.writeyh()
                sys.exit(0)
        elif self.machine == 'slurm':
            if not os.path.exists(r'./vasp.sh'):
                print 'submit.sh not exit'
                print 'A new submit.sh script has been written, and you should modify it!'
                self.writeyh()
                sys.exit(0)

        if len(glob.glob(r'./POTCAR')) == 0:
            print 'POTCAR not exit'
            sys.exit(0)
        elif len(glob.glob(r'./INCAR_*')) == 0:
            print 'INCAR_* not exit'
            sys.exit(0)
        else:
            print 'Check files completed!!!'

    def submit_vasp(self):
        os.system(self.CalyPsoPath)
        self.control_vasp()

    def autorun(self):
        self.readinput()
        self.checkfiles()
        i = 0
        while i < self.GenNum:
            self.submit_vasp()
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
                id = int(os.popen(" cd %s; %s;cd .." % (str(i+1),self.submit)).read().split(' ')[1].strip('<').strip('>'))
            else:
                id = int(os.popen(" cd %s; %s;cd .." % (str(i+1),self.submit)).read().split(' ')[3])
            splitjobid.append(id)
            jobtime[id] = 0	
        #print splitjobid
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
                jobtime[ii] += self.sleeptime
                if jobtime[ii] > self.MaxTime:
                    #print "qdel %d" % ii
                    os.system("%s %s" % (self.delete,str(ii)))	
            #print jobtime	
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
                        if (num + i + 1) <= self.StrNum:
                            if self.machine == 'pbs':
                                id = int(os.popen(" cd %s; %s ;cd .." % (str(num+i+1),self.submit)).read().split('.')[0])
                            elif self.machine == 'lsf':
                                id = int(os.popen(" cd %s; %s ;cd .." % (str(num+i+1),self.submit)).read().split(' ')[1].strip('<').strip('>'))
			    else:
                                id = int(os.popen(" cd %s; %s ;cd .." % (str(num+i+1),self.submit)).read().split(' ')[3])
                            splitjobid.append(id)
                            jobtime[id] = 0	
                    num += fnode
            time.sleep(self.sleeptime)

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

#	def split_jobid(self):
#		splitjobid = []
#		for i in range(self.NP):
#			splitjobid.append(int(os.popen(" cd %s;qsub vasp.pbs;cd .." % (str(i+1))).read().split('.')[0]))
#		return splitjobid
        
    def writevasppbs(self):
        f = open('vasp.pbs','w')
        f.write('#!/bin/bash\n')
        f.write('#PBS -l nodes=1:ppn=20\n')
        f.write('#PBS -j oe\n')
        f.write('#PBS -V\n')
        f.write('cd $PBS_O_WORKDIR\n')
        f.write('for(( i=1; i<=' + str(self.NumLocOpt) + '; i++ ));\n')
        f.write('do\n')
        f.write('cp INCAR_$i INCAR\n')
        f.write('cp CONTCAR POSCAR\n')
        f.write(self.extexec + '\n')
        f.write('done\n')
        f.close()
    
    def writerunlsf(self):
        f = open('run.lsf','w')
        f.write('#!/bin/sh\n')
        f.write('#BSUB -o %J.lsf.output\n')
        f.write('#BSUB -n 12\n')
        f.write('#BSUB -R "span[ptile=12]"\n')
        f.write('for(( i=1; i<=' + str(self.NumLocOpt) + '; i++ ));\n')
        f.write('do\n')
        f.write('cp INCAR_$i INCAR\n')
        f.write('cp CONTCAR POSCAR\n')
        f.write(self.extexec + '\n')
        f.write('done\n')
        f.close()
    
    def writeyh(self):	
        f = open('vasp.sh','r')
        f.write('#!/bin/bash\n')
        f.write('for(( i=1; i<=' + str(self.NumLocOpt) + '; i++ ));\n')
        f.write('do\n')
        f.write('cp INCAR_$i INCAR\n')
        f.write('cp CONTCAR POSCAR\n')
        f.write(self.extexec + '\n')
        f.write('done\n')
        f.close()
			
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--jobms', default='pbs', help='Defining the Job Managemant System pbs|lsf|yh|slurm')
    parser.add_argument('--extexec', default='mpirun -np 12 ./vasp > log', help=''' Defining the external command to run optimization task. Default is 'mpirun -np 12 ./vasp > log' ''')
    parser.add_argument('--calypath', default='./calypso.x', help='Defining the location of calypso.x. Default is ./calypso.x')
    opt = parser.parse_args()

    if opt.jobms == 'pbs':
        a = Autocalypso(calypath = opt.calypath, extexec = opt.extexec)
    elif opt.jobms == 'lsf':
        submit = 'bsub < run.lsf'
        stat = 'bjobs'
        rstat = 'bjobs | grep RUN'
        delete = 'bkill'
        a = Autocalypso(submit,stat,rstat,delete,machine = 'lsf', calypath = opt.calypath, extexec = opt.extexec)
    elif opt.jobms == 'yh':
        submit = 'yhbatch -p TH_NET -N 1 -n 12 vasp.sh'
        stat = 'yhqueue'
        rstat = 'yhqueue | grep   "\<R\>" '
        delete = 'yhcancel'
        a = Autocalypso(submit,stat,rstat,delete,machine = 'yh', calypath = opt.calypath, extexec = opt.extexec)
    elif opt.jobms == 'slurm':
        submit = 'sbatch -p TH_NET -N 1 -n 12 vash.sh'
        stat = 'squeue'
        rstat = 'squeue | grep   "\<R\>" '
        delete = 'scancel'
        a = Autocalypso(submit,stat,rstat,delete,machine = 'slurm', calypath = opt.calypath, extexec = opt.extexec)
    else:
        print 'Unknowm Job Management System, the default is pbs'
        a = Autocalypso()
    a.autorun()
