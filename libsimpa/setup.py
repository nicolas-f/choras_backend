from skbuild import setup

setup(
    name="libsimpa",
    version="1.0.0",
    description="Libsimpa library",
    cmake_args=['-DLIBSIMPA_ONLY:BOOL=ON',
        '-DCMAKE_CXX_FLAGS=-w',
        '-DCMAKE_C_FLAGS=-w',
        '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON'
                ],
    cmake_source_dir = "I-Simpa",
    packages=['I-Simpa'],
)
