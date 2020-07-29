# calypso_auto_split
[CALYPSO](www.calypso.cn) is a high performance structure prediction method and software, which requires only chemical compositions of given compounds under target pressure to predict stable or metastable structures.    
There have two steps in the flowchart of CALYPSO. One is structure generation and the other is local optimization of generated structures, however local optimization using DFT is too time consume.   
Hence in order to accelerate CALYPSO structure search, one method is local optimizations are parallelly performed on different compute node.
The aim of this package is to run CALYPSO with Split mode automatically, and all search processes are controlled by python scripts caly_auto_aplit.py.
## caly_auto_split.py

