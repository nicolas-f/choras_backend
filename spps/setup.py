from skbuild import setup

setup(
    name="spps",
    version="1.0.0",
    description="Spps computation code",
    cmake_args=['-DSKIPISIMPA:BOOL=ON'],
    cmake_source_dir = "I-Simpa",
    packages=['spps'],
)
