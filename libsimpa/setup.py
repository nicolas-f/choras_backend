from skbuild import setup
import sys

cmake_args = [
    '-DLIBSIMPA_ONLY:BOOL=ON',
    '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON'
]

# Force Visual Studio generator on Windows
if sys.platform == 'win32':
    cmake_args.extend([
        '-GVisual Studio 17 2022',
        '-A', 'x64'
    ])
else:
    cmake_args.extend([
        '-DCMAKE_CXX_FLAGS=-w',
        '-DCMAKE_C_FLAGS=-w'
    ])

setup(
    name="libsimpa",
    version="1.0.0",
    description="Libsimpa library",
    cmake_args=cmake_args,
    cmake_source_dir = "I-Simpa",
    packages=['I-Simpa'],
)
