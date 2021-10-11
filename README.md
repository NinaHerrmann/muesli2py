# ALPHA muesli2py
muesli2py is developed to supply the functionalities of muesli in python code. For a minimal prototype the following features are essential:
- [ ] configure setup.py to support 
    - [x] mpi
    - [ ] cuda ([probably a good example](https://github.com/rmcgibbo/npcuda-example/blob/master/cython/setup.py))
    - [ ] (openacc)
    - [x] openmp
- [ ] support for DA/DM (distributed arrays - distributed matrices)
    - [ ] nparray ([C-API](https://numpy.org/doc/stable/user/c-info.html), [writing extension modules](https://numpy.org/doc/stable/user/c-info.how-to-extend.html#writing-an-extension-module))
    - [ ] native arrays
- [ ] map + variations
- [ ] ...

Features which are not essential for a first prototype
- [ ] DA/DM 
    - [ ] support of more than 2 dimensions  
- [ ] other skeletons


## Supporting Documentation
- [Parsing arguments between C and python](https://docs.python.org/3/c-api/arg.html)
- [Object Structures](https://docs.python.org/3/c-api/structures.html)

