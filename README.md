# calypso_auto_split
[CALYPSO](www.calypso.cn) is a high performance structure prediction method and software. It requires only chemical compositions of given compounds under aim pressure or temperature to predict stable or metastable structures. 
Two key steps in CALYPSO are structure generation and structure optimization, however structure optimization is too time consume. So for accelatrating CALYPSO structure search, optimization tasks could be parallelly performed on different compute node.
The aim of this package is to run CALYPSO on Split mode, and all prediction step are contralled by python scrapts.
