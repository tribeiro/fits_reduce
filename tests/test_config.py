import os
from util.config import FitsReduceConfig

__author__ = 'william'


def test_config():
    FitsReduceConfig('%s/../conf.INI' % os.path.dirname(__file__), 'reducer')
    return True


if __name__ == '__main__':
    test_config()