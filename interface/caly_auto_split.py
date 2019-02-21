'''
Description: 
    Running CALYPSO interface and surface structure search with Split mode automatically.
Usage:
    nohup python caly_auto_split.py  --jobms=JOBMS --extexec=EXTEXEC --calypath=CALYPATH
    --jobms       Defining the Job Managemant System pbs|lsf|yh|slurm
    --extexec     Defining the external program to run optimization task vasp|DFTB+|gulp
    --calypath    Defining the location of calypso.x
Date: 2019.02.18
Author: Qunchao Tong<tqc@calypso.cn>
Modified:
'''
#!/usr/bin/python

import os
import time
import sys
try:
    import argparse
except:
    print ''' No libargparse, please install it
              if you have installed pip tool, you need run
              pip install argparse'''
    sys.exit(0)

class Autocalypso(object):
    def __init__(self,submit = 'qsub vasp.pbs',\
                      stat = 'qstat',\
                      rstat = 'qstat | grep R',\
                      delete = 'qdel',\
                      calypath = './calypso.x',\
                      machine = 'pbs',\
                      extexec = 'vasp'):

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
        self.GenNum = self.MaxStep		
        self.NumberOfParallel = 5
        self.PickUp = False
        self.NumberOfLocalOptim = 3
        self.f = open('split_calypso.log','w')
        self.sleeptime = 2

    def readinput(self):
    
        self.StrNum = int(self.get_input_para('PopSize',30))
        self.NP = int(self.get_input_para('NumberOfParallel',5))
        self.MaxStep = int(self.get_input_para('MaxStep',1000))
        self.MaxTime = int(self.get_input_para('MaxTime',1800))
        self.PickUp = self.get_input_para('PickUp','F')

        if self.StrNum < self.NP:
            self.NP = self.StrNum

        if self.PickUp == 'F':
            self.lPickUp = False
        else:
            self.lPickUp = True
        print self.lPickUp
        if not self.lPickUp:
            os.system('rm step')
            os.system('rm -rf results')

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
                print 'There is no vasp.pbs file!!!'
                print 'A new vasp.pbs script has been written, and you should modify it!'
                self.writevasppbs()
                sys.exit(0)
        elif self.machine == 'lsf':
            if not os.path.exists(r'./run.lsf'):
                print 'No run.lsf file!!!'
                print 'A new run.lsf script has been written, and you should modify it!'
                self.writerunlsf()
                sys.exit(0)
        elif self.machine == 'yh':
            if not os.path.exists(r'./vasp.sh'):
                print 'No vasp.sh file!!!'
                print 'A new vasp.sh script has been written, and you should modify it!'
                self.writeyh()
                sys.exit(0)
        elif self.machine == 'slurm':
            if not os.path.exists(r'./submit.sh'):
                print 'No submit.sh file!!!'
                print 'A new submit.sh script has been written, and you should modify it!'
                self.writeslurm()
                sys.exit(0)
        if not os.path.exists(r'./input.dat'):
            print 'No input.dat'
            sys.exit(0)
        elif not os.path.exists(r'./POTCAR-*'):
            print 'No POTCAR'
            sys.exit(0)
        elif len(glob.glob(r'./INCAR-*')) == 0:
            print 'No INCAR files'
            sys.exit(0)
        else:
            print 'Check files completed!!!'

    def autorun(self):
        self.checkfiles()
        self.readinput()
        i = 1
        while i <= self.GenNum:
            self.f.write("=================" + str(i) + " ITERATION ==================" )
            self.f.flush()
            self.submit_vasp(i)
            i += 1

    def submit_vasp(self,n):
        self.f.write("caly_auto_split call CALYPSO generare structure\n" )
        os.system(self.CalyPsoPath)
        self.f.write("caly_auto_split submit structure relax job\n" )
        self.control_vasp(n)

    def control_vasp(self,nstep):
        for i in range(self.StrNum):
            if self.machine == 'pbs':
                os.system('cp vasp.pbs  results/Generation_%s/Indv_%s' % (str(nstep),str(i+1)))
            elif self.machine == 'lsf':
                os.system('cp run.lsf POTCAR INCAR_*  %s' % str(i+1))
            elif self.machine == 'yh':
                os.system('cp vasp.sh POTCAR INCAR_*  %s' % str(i+1))
            elif self.machine == 'slurm':
                os.system('cp submit.sh POTCAR INCAR_*  %s' % str(i+1))
        self.f.write("Set structure relax jobs finished\n")

        totaljobid = []
        runjobid = []
        splitjobid = []
        split_run_jobid = []
        jobtime = {}
        for i in range(self.NP):
            if self.machine == 'pbs':
                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s;cd ../../..' % (str(nstep),str(i+1),self.submit)).read().split('.')[0])

            elif self.machine == 'lsf':
                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s;cd ../../..' % (str(nstep),str(i+1),self.submit)).read().split(' ')[1].\
                                            strip('<').strip('>'))

            elif self.machine == 'yh':
                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s;cd ../../..' % (str(nstep),str(i+1),self.submit)).read().split(' ')[3])

            elif self.machine == 'slurm':
                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s;cd ../../..' % (str(nstep),str(i+1),self.submit)).read().split(' ')[3])

            splitjobid.append(id)
            jobtime[id] = 0 
        self.f.write("Submit structure relax jobs finished\n")
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
                    print 'qdel %d' % ii
                    os.system('%s %s' % (self.delete,str(ii)))  
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
                        if (num+i+1) <= self.StrNum:
                            if self.machine == 'pbs':
                                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s ;cd ../../..' % (str(nstep),str(num+i+1),self.submit)).\
                                     read().split('.')[0])

                            elif self.machine == 'lsf':
                                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s ;cd ../../..' % (str(nstep),str(num+i+1),self.submit)).\
                                     read().split(' ')[1].strip('<').strip('>'))

                            elif self.machine == 'yh':
                                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s ;cd ../../..' % (str(nstep),str(num+i+1),self.submit)).\
                                     read().split(' ')[3])

                            elif self.machine == 'slurm':
                                id = int(os.popen(' cd results/Generation_%s/Indv_%s; %s ;cd ../../..' % (str(nstep),str(num+i+1),self.submit)).\
                                     read().split(' ')[3])
                            splitjobid.append(id)
                            jobtime[id] = 0 
                    num += fnode
            time.sleep(self.sleeptime)
        self.f.write("Structure relax jobs finished\n")
        for i in range(self.StrNum):
            if not os.path.exists(r'./results/Generation_%s/Indv_%s/.done.' % (str(nstep),str(i+1))):
                print 'Optimization has trouble in Generation_' + str(nstep) + '/Indv_' + str(i+1)
                sys.exit(0)

    def run_jobid(self,cmd):
        runjobid = []
        aa = os.popen('%s' % cmd).readlines()
        for line in aa:
            try:
                if self.machine == 'pbs':
                    runjobid.append(int(line.split('.')[0]))
                elif self.machine == 'lsf':
                    runjobid.append(int(line.split(' ')[0]))
                elif self.machine == 'yh':
                    runjobid.append(int(line.strip().split(' ')[0]))
                elif self.machine == 'slurm':
                    runjobid.append(int(line.strip().split(' ')[0]))
            except:
                continue
        return runjobid
                
    def writevasppbs(self,nodes = '1',ppn = '12',walltime = '01:00:00'):
        f = open('vasp.pbs','w')
        f.write('#!/bin/bash\n')
        f.write('#PBS -l nodes=%s:ppn=%s\n' % (nodes,ppn))
        f.write('#PBS -j oe\n')
        f.write('#PBS -V\n')
        f.write('#PBS -l walltime=%s\n' % walltime)
        f.write('cd $PBS_O_WORKDIR\n')
        f.write('python surface_run.py  ' +  self.extexec + '  > log\n')
        f.close()

    def writerunlsf(self,nodes = '1',ppn = '12'):
        f = open('run.lsf','w')
        f.write('#!/bin/sh\n')
        f.write('#BSUB -n 12\n')
        f.write("#BSUB -R 'span[ptile=12]'\n")
        f.write('python surface_run.py  ' +  self.extexec + '  > log\n')
        f.close()

    def writeyh(self):  
        f = open('vasp.sh','w')
        f.write('#!/bin/bash\n')
        f.write('python surface_run.py  ' +  self.extexec + '  > log\n')
        f.close()
            
    def writeslurm(self):
        f = open('submit.sh','w')
        f.write('#!/bin/bash\n')
        f.write('source $MODULESHOME/init/sh\n')
        f.write('module purge\n')
        f.write('module add app_env/slurm\n')
        f.write('module add app_env/vasp-5.4.1\n')
        f.write('python surface_run.py  ' +  self.extexec + '  > log\n')
        f.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--jobms', default='pbs', help='Defining the Job Managemant System pbs|lsf|yh|slurm')
    parser.add_argument('--extexec', default='vasp', help='Defining the external program to run optimization task vasp|DFTB+|gulp')
    parser.add_argument('--calypath', default='./calypso.x', help='Defining the location of calypso.x')
    opt = parser.parse_args()

    if opt.jobms == 'pbs':
        a = Autocalypso(calypath = opt.calypath, extexec = opt.extexec)
    elif opt.jobms == 'lsf':
        submit = 'bsub run.lsf'
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
        submit = 'sbatch -n 12  -p normal submit.sh'
        stat = 'squeue'
        rstat = 'squeue | grep   "\<R\>" '
        delete = 'scancel'
        a = Autocalypso(submit,stat,rstat,delete,machine = 'slurm', calypath = opt.calypath, extexec = opt.extexec)
    else:
        print 'Unknowm Job Management System, the default is pbs'
        a = Autocalypso()
    a.autorun()
