import os
from fits_reduce.util.config import FitsReduceConfig

def test_config():
    FitsReduceConfig('%s/../../conf.INI' % os.path.dirname(__file__), 'reducer')
    return True


if __name__ == '__main__':
    test_config()