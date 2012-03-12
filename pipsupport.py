import os
import subprocess
import sys


def install_distributions(distributions):
    """ Installs distributions with pip! """

    pipsecutable = os.path.sep.join(
        sys.executable.split(os.path.sep)[:-1] + ['pip'])
    cmd = '%s install %s' % (pipsecutable, ' '.join(distributions))
    status = subprocess.call(cmd, shell=True)
