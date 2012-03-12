import pkg_resources
import pipsupport

def get_dependencies(package_name, calls=0):
    """ Main entry function.  This will return the list of dependencies of the
    given package name.

    How does it do this?

     - Try to import the package
     - If it's not installed, install it.
     - Try to import it again
     - If it's not installed, give up.
     - If it is installed, use the pkg_resources module to find its
       dependencies, and their dependencies, and so on.
    """

    if calls > 2:
        raise Exception("I tried installing %s %i times.  Fail." %
                        (package_name, calls))
    try:
        package = __import__(package_name)
    except ImportError as e:
        pipsupport.install_distributions([package_name])
        return get_dependencies(package_name, calls + 1)

    requires = [
        r.project_name for r in
        pkg_resources.get_distribution(package_name).requires()
    ]
    return requires

def test():
    print get_dependencies('tw2.core')

if __name__ == '__main__':
    test()
