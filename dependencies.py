""" Recursively list the dependencies of a pypi distribution.

For instance:

     % virtualenv --system-site-packages scratch
     % source scratch/bin/activate
     (scratch)% python dependencies.py tw2.jquery

    -----------------------------------------
    | Gathering dependencies for tw2.jquery |
    -----------------------------------------
    ---------------------------------------------------------
    | The list of dependencies according to pypi.python.org |
    ---------------------------------------------------------
    {
        "tw2.jquery": {
            "tw2.core": {
                "WebOb": {},
                "simplejson": {},
                "PasteDeploy": {},
                "weberror": {
                    "WebOb": {},
                    "Tempita": {},
                    "Pygments": {},
                    "Paste": {}
                }
            },
            "tw2.forms": {
                "tw2.core": {
                    "WebOb": {},
                    "simplejson": {},
                    "PasteDeploy": {},
                    "weberror": {
                        "WebOb": {},
                        "Tempita": {},
                        "Pygments": {},
                        "Paste": {}
                    }
                }
            },
            "formencode": {}
        }
    }
    -------------------------------------------------------
    | Trying to figure out what of these pkgs are in yum. |
    -------------------------------------------------------
    + WebOb
    + Tempita
    + Pygments
    + Paste
    + simplejson
    + PasteDeploy
    + weberror
    - tw2.core
    - tw2.forms
    + formencode
    - tw2.jquery

"""

import json
import pkg_resources
import pipsupport
import re
import sys

from collections import OrderedDict

yumobj = None
try:
    import yum
    yumobj = yum.YumBase()
    yumobj.setCacheDir()
except ImportError:
    pass


def get_pypi_dependencies(package_name, calls=0):
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
        return get_pypi_dependencies(package_name, calls + 1)


def build_dep_tree(package_name):
    """
    Recursively call get_pypi_dependencies and format the tree as an
    OrderedDict
    """

    node = OrderedDict()
    for dep in get_pypi_dependencies(package_name):
        node[dep] = build_dep_tree(dep)

    if not node:
        return {}

    return node


def camel2dashes(name):
    return '-'.join([s.lower() for s in
           re.findall(r'([A-Z][a-z0-9]+|[a-z0-9]+|[A-Z0-9]+)', name)])


def in_yum(pkg_name):
    possible_names = [
        pkg_name,
        'python-' + pkg_name,
        'python-' + pkg_name.lower(),
        'python-' + camel2dashes(pkg_name),
    ]
    return len(
        sum([
            yumobj.pkgSack.searchNevra(name=possible_name)
            for possible_name in possible_names
        ], [])
    ) != 0


def count_keys(deps):
    if not deps:
        return {}
    counts = {}
    for key in deps:
        counts[key] = 1

    for child in deps.values():
        child_counts = count_keys(child)
        for key, value in child_counts.iteritems():
            counts[key] = counts.get(key, 0) + value

    return counts


def uniqify_preserving_order(seq):
    """ http://www.peterbe.com/plog/uniqifiers-benchmark """

    seen = {}
    result = []
    for item in seq:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result


def special_flatten(deps):
    if not deps:
        return []

    flattened = []
    for v in deps.values():
        flattened += special_flatten(v)
    flattened += deps
    flattened = uniqify_preserving_order(flattened)
    return flattened


def print_header(msg):
    msg = "| %s |" % msg
    print '-' * len(msg)
    print msg
    print '-' * len(msg)


def main():
    """ Main entry point. """

    if not sys.argv[1:]:
        print "No packages specified."
        sys.exit(1)

    deps = {}
    for arg in sys.argv[1:]:
        print_header("Gathering dependencies for %s" % arg)
        deps[arg] = build_dep_tree(arg)

    print_header("The list of dependencies according to pypi.python.org")
    print json.dumps(deps, indent=4)

    if not yumobj:
        msg = "Couldn't import yum.  You may need to symlink it in."
        print_header(msg)
        sys.exit(1)

    print_header("Trying to figure out what of these pkgs are in yum.")

    # Order distributions by children first
    pypi_dists = special_flatten(deps)

    for pkg_name in pypi_dists:
        if not in_yum(pkg_name):
            print "-",
        else:
            print "+",

        print pkg_name


if __name__ == '__main__':
    main()
