""" Recursively list the dependencies of a pypi distribution.

For instance:

     % python dependencies.py tw2.jquery
    ---------------------------------------------------------
    | The list of dependencies according to pypi.python.org |
    ---------------------------------------------------------
    {
        "tw2.jquery": {
            "tw2.core": {
                "WebOb": {},
                "simplejson": {},
                "PasteDeploy": {},
                "speaklater": {},
                "decorator": {}
            },
            "tw2.forms": {
                "tw2.core": {
                    "WebOb": {},
                    "simplejson": {},
                    "PasteDeploy": {},
                    "speaklater": {},
                    "decorator": {}
                }
            }
        }
    }

"""

import json
import pkg_resources
import pipsupport
import sys

from collections import OrderedDict


def get_dependencies(package_name, calls=0):
    """ Return the list of dependencies of the given package name.

    How does it do this?

     - Check if the package is installed with pkg_resources.
     - If it's not installed, install it.
     - Check with pkg_resources again.
     - If it's not installed, give up.
     - If it is installed, use the pkg_resources module to find its
       dependencies, and their dependencies, and so on.
    """

    if calls > 2:
        raise Exception("I tried installing %s %i times.  Fail." %
                        (package_name, calls))
    try:
        return [
            r.project_name for r in
            pkg_resources.get_distribution(package_name).requires()
        ]
    except pkg_resources.DistributionNotFound as e:
        pipsupport.install_distributions([package_name])
        return get_dependencies(package_name, calls + 1)


def build_dep_tree(package_name):
    """
    Recursively call get_dependencies and format the tree as an OrderedDict
    """

    node = OrderedDict()
    for dep in get_dependencies(package_name):
        node[dep] = build_dep_tree(dep)

    if not node:
        return {}

    return node


def main():
    """ Main entry point. """

    if not sys.argv[1:]:
        print "No packages specified."
        sys.exit(1)

    deps = {}
    for arg in sys.argv[1:]:
        deps[arg] = build_dep_tree(arg)

    msg = "| The list of dependencies according to pypi.python.org |"
    print '-' * len(msg)
    print msg
    print '-' * len(msg)
    print json.dumps(deps, indent=4)


if __name__ == '__main__':
    main()
