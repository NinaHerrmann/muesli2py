import os
from setuptools import setup, Extension, Command
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import numpy as np
from os.path import join as pjoin

mpi_compile_args = os.popen("mpic++ --showme:compile").read().strip().split(' ')
mpi_link_args = os.popen("mpic++ --showme:link").read().strip().split(' ')


class cuda_setup():

    def find_in_path(name, path):
        """Find a file in a search path"""

        # Adapted fom http://code.activestate.com/recipes/52224
        for dir in path.split(os.pathsep):
            binpath = pjoin(dir, name)
            if os.path.exists(binpath):
                return os.path.abspath(binpath)
        return None

    def locate_cuda(self):
        """Locate the CUDA environment on the system
        Returns a dict with keys 'home', 'nvcc', 'include', and 'lib64'
        and values giving the absolute path to each directory.
        Starts by looking for the CUDAHOME env variable. If not found,
        everything is based on finding 'nvcc' in the PATH.
        """
        CUDA = self.locate_cuda()

        # First check if the CUDAHOME env variable is in use
        if 'CUDAHOME' in os.environ:
            home = os.environ['CUDAHOME']
            nvcc = pjoin(home, 'bin', 'nvcc')
        else:
            # Otherwise, search the PATH for NVCC
            nvcc = self.find_in_path('nvcc', os.environ['PATH'])
            if nvcc is None:
                raise EnvironmentError('The nvcc binary could not be '
                                       'located in your $PATH. Either add it to your path, '
                                       'or set $CUDAHOME')
            home = os.path.dirname(os.path.dirname(nvcc))

        cudaconfig = {'home': home, 'nvcc': nvcc,
                      'include': pjoin(home, 'include'),
                      'lib64': pjoin(home, 'lib64')}
        for k, v in iter(cudaconfig.items()):
            if not os.path.exists(v):
                raise EnvironmentError('The CUDA %s path could not be '
                                       'located in %s' % (k, v))
        return cudaconfig

    try:
        numpy_include = np.get_include()
    except AttributeError:
        numpy_include = np.get_numpy_include()

    def get_module(self):
        CUDA = self.locate_cuda()
        return Extension('muesli_utils', sources=['muesli_utils.cu', 'src/da.py'],
                         include_dirs=[np.get_include(), CUDA['include']],
                         library_dirs=['/usr/include/boost/', CUDA['lib64']],
                         language='c++',
                         libraries=['/usr/include/boost/chrono', 'cudart', '/usr/lib/x86_64-linux-gnu/openmpi/lib'],
                         extra_compile_args={'gcc': [],
                                             'nvcc': [
                                                 '-arch=sm_61', '--ptxas-options=-v', '-c',
                                                 '--compiler-options', "'-fPIC'", '-lmpi_cxx', '-lmpi', '-Xcompiler',
                                                 '-fopenmp'
                                             ], 'openmp': "-fopenmp", 'mpi': ' '.join(mpi_compile_args)
                                             },  # (["-fopenmp"] + mpi_compile_args),
                         runtime_library_dirs=[CUDA['lib64']],
                         extra_link_args=(["-fopenmp"] + mpi_link_args)
                         )


# Run the customize_compiler
class custom_build_ext(build_ext):
    def build_extensions(self):
        self.customize_compiler_for_nvcc(self.compiler)
        build_ext.build_extensions(self)


def customize_compiler_for_nvcc(self):
    """Inject deep into distutils to customize how the dispatch
    to gcc/nvcc works.
    If you subclass UnixCCompiler, it's not trivial to get your subclass
    injected in, and still have the right customizations (i.e.
    distutils.sysconfig.customize_compiler) run on it. So instead of going
    the OO route, I have this. Note, it's kindof like a wierd functional
    subclassing going on.
    """

    # Tell the compiler it can processes .cu
    self.src_extensions.append('.cu')

    # Save references to the default compiler_so and _comple methods
    default_compiler_so = self.compiler_so
    super = self._compile
    CUDA = self.locate_cuda()

    # Now redefine the _compile method. This gets executed for each
    # object but distutils doesn't have the ability to change compilers
    # based on source extension: we add it.
    def _compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
        if os.path.splitext(src)[1] == '.cu':
            # use the cuda for .cu files
            self.set_executable('compiler_so', CUDA['nvcc'])
            # use only a subset of the extra_postargs, which are 1-1
            # translated from the extra_compile_args in the Extension class
            # /usr/lib/x86_64-linux-gnu/openmpi/include/
            # -I/usr/lib/x86_64-linux-gnu/openmpi/include/openmpi -I/usr/lib/x86_64-linux-gnu/openmpi/include -pthread
            print(extra_postargs['mpi'])
            postargs = extra_postargs['nvcc'] + mpi_compile_args
        else:
            postargs = extra_postargs['gcc'] + extra_postargs['openmp'] + mpi_compile_args

        super(obj, src, ext, cc_args, postargs, pp_opts)
        # Reset the default compiler_so, which we might have changed for cuda
        self.compiler_so = default_compiler_so

    # Inject our redefined _compile method into the class
    self._compile = _compile
