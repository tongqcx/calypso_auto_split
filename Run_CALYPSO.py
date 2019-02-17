'''
Description:
    Runing CALYPSO in single node with Split mode
Usage:
    nohup python Run_CALYPSO.py --vaspcmd=./vasp --calycmd=./calypso.x --totproc=24 --jobproc=6 > log &
    vaspcmd: the path of VASP
    totproc: the total core in machine
    jobproc: the number of cores for each job
    calycmd: the path of CALYPSO
Author:
    Qunchao Tong<tqc@calypso.cn>
    If you have any question, please contact Qunchao
Date:
    2019.01.25 Fri.
Modified:
    2019.01.26 Add function get_input_para
'''

import sys
import os
import time 
try:
    import argparse
except:
    print ''' No libargparse, please install it
              if you have installed pip tool, you need run
              pip install argparse'''
    sys.exit(0)

class Run_calypso():

    def __init__(self, VASPCMD = '/public/apps/vasp_std',\
                       TOTPROC = 20,\
                       JOBPROC = 4,\
                       CALYCMD = './calypso.x'):

        self.totproc = TOTPROC
        self.vaspcmd = VASPCMD
        self.calycmd = CALYCMD
        self.jobproc = JOBPROC
        self.num_jobs = int(self.totproc / self.jobproc)
        self.PopSize = int(self.get_input_para('PopSize',30))
        self.NumberOfLocalOptim = int(self.get_input_para('NumberOfLocalOptim',3))
        self.MaxStep = int(self.get_input_para('MaxStep',1000))
        self.MaxTime = int(self.get_input_para('MaxTime',3600))
        self.PickUp = self.get_input_para('PickUp','F')
        if self.PickUp == 'F':
            self.lPickUp = False
        else:
            self.lPickUp = True
        print self.lPickUp
        if not self.lPickUp:
            os.system('rm step')
            os.system('rm -rf results')

        self.writescript()
        self.sleeptime = 2
        self.count = int(self.MaxTime / self.sleeptime)

        #print self.vaspcmd, self.calycmd
        #print self.totproc, self.jobproc
        #print self.PopSize, self.NumberOfLocalOptim, self.MaxStep, self.lPickUp
        #sys.exit(0)

    def get_input_para(self,chara,n):
        if not os.path.exists(r'./input.dat'):
            print 'input.dat not exist'
            sys.exit(0)
        line = os.popen('grep %s input.dat' % chara).read()
        if line == '':
            return n
        if line[0] == '#':
            return n
        else:
            return line.split('=')[1].strip()
        

    def get_job_num(self):
        vasp_num = int(os.popen("ps ux | grep %s  | grep  '\<R\>' | wc -l" % self.vaspcmd).read().split()[0])
        jobs_num = int(vasp_num / self.jobproc)
        return jobs_num

    def run_calypso(self):
        os.system(self.calycmd)

    def set_vaspjobs(self,i):
        if os.path.exists(r'./%s' % str(i)):
            os.system('rm -rf %s' % str(i))
        os.system('mkdir %s' % str(i))
        os.system('cp INCAR_*  POTCAR %s' % str(i))
        os.system('cp POSCAR_%s %s/CONTCAR' %  (str(i),str(i)))
        os.system('cp submit_vasp.sh %s' % str(i))

    def deal_vasp(self):
        for i in range(self.PopSize):
            if os.path.exists(r'./%s/CONTCAR' % str(i+1)):
                os.system('cp %s/CONTCAR  CONTCAR_%s' % (str(i+1),str(i+1)))
            else:
                print i + 1,'th VASP JOB WRONG NO CONTCAR'
            if os.path.exists(r'./%s/OUTCAR' % str(i+1)):
                os.system('cp %s/OUTCAR  OUTCAR_%s' % (str(i+1),str(i+1)))
            else:
                print i + 1,'th VASP JOB WRONG NO OUTCAR'
                os.system('echo 0 > OUTCAR_%s' % str(i+1))

    def submit_vasp(self,n):
        os.system('cd  %s ; nohup bash submit_vasp.sh & cd ..' % str(n))
             
    def Run_single_step(self):
        self.run_calypso()
        for i in range(self.num_jobs):
            self.set_vaspjobs(i + 1)
            self.submit_vasp(i + 1)
        index = self.num_jobs
        #while index < self.PopSize:
        nover = 0
        mover = 0
        tover = 0
        while True:
            time.sleep(self.sleeptime)
            tover += 1
            jobs_num = self.get_job_num()
            if jobs_num == 0:
                nover += 1
            if nover == 10:
                break
            if tover == self.count:
                os.system("killall %s" % self.vaspcmd)
                break
            print jobs_num,index
            if jobs_num < self.num_jobs:
                mover += 1
            if (index < self.PopSize and mover == 2):
                index += 1
                self.set_vaspjobs(index)
                self.submit_vasp(index)
                mover = 0
                nover = 0
                tover = 0
        self.deal_vasp()

    def Run(self):
        for i in range(self.MaxStep):
            self.Run_single_step()

    def writescript(self):
        f = open('submit_vasp.sh','w')
        f.write('#!/bin/bash\n')
        f.write('''num_in=`ls -l |grep 'INCAR_' |wc -l`\n''')
        f.write('for(( i=1; i<=%s; i++ ))\n' %  str(self.NumberOfLocalOptim))
        f.write('do\n')
        f.write('\tcp INCAR_$i INCAR\n')
        f.write('\tcp CONTCAR POSCAR\n')
        f.write('\tmpirun -np %d  %s > vasp.log_$i\n' % (self.jobproc, self.vaspcmd))
        f.write('done\n')
        f.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--totproc', type=int, default=24, help='The total core in this machine')
    parser.add_argument('--jobproc', type=int, default=6, help='The number of cores for each job')
    parser.add_argument('--vaspcmd', default='./vasp', help='The path of VASP')
    parser.add_argument('--calycmd', default='./calypso.x', help='The path of CALYPSO')
    opt = parser.parse_args()
    a = Run_calypso(VASPCMD = opt.vaspcmd, \
                    TOTPROC = opt.totproc, \
                    JOBPROC = opt.jobproc, \
                    CALYCMD = opt.calycmd)
    a.Run()
