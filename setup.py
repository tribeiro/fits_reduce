from distutils.core import setup

setup(
    name='fits_reduce',
    version='0.1',
    packages=['fits_reduce', 'fits_reduce.main', 'fits_reduce.util'],
    url='https://github.com/pablogsal/fits_reduce/',
    license='BSD',
    author='Pablo Galindo Salgado',
    author_email='pablogsal@gmail.com',
    description='A robotic image reducer for robotic telescopes',
    install_requires=['astropy',
                      'colorlog',
                      'ccdproc>=0.3.3'],
    scripts=['scripts/reducer',
             'scripts/t80s_imarith.py',
             'scripts/t80s_imcombine.py',
             'scripts/t80s_preproc.py',]
)
