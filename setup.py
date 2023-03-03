from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Game Table Controller',
    ext_modules=cythonize(['VisionService.pyx', 'BluetoothService.pyx', 'HidService.pyx', 'perspective_transform.pyx', 'Controller.py']),
    zip_safe=False,
)