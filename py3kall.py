# Copyright (C) 2012 Ralph Bean <rbean@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from contextlib import closing as cm
import shelve
import xmlrpclib

fname = 'pypi-shelve.db'

py3_classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
]


def ingest_package(package, tries=0):
    print "Processing package", package
    result = {
        'name': package,
        'releases': [],
    }

    # Bail if we keep failing.
    if tries > 3:
        print " ** Some error collecting package", package
        return result

    try:
        client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')

        for release in client.package_releases(package):  # show_hidden=True):
            data = client.release_data(package, release)
            result['releases'].append({
                'name': release,
                'data': data
            })
    except Exception as e:
        return ingest_package(package, tries + 1)
    
    #print result
    return result


def populate():
    print "Getting the list of all packages."
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    packages = client.list_packages()[:3]
    print "Ridiculous!  Found %i packages." % len(packages)
    
    print "Ingesting %i packages." % len(packages)
    with cm(shelve.open(fname, writeback=True)) as d:
        d['packages'] = d.get('packages', {})

        for package in packages:
            if package not in d['packages']:
                result = ingest_package(package)
                d['packages'][result['name']] = result
                d.sync()
            else:
                print "Skipping          ", package
    print "Complete!"


def is_python3(package):
    ver = package['releases'][0]['data']['classifiers']
    if ver in py3_classifiers:
        return True

def main():
    print "Scraping pypi..."
    populate()
    print "Complete!"
    with cm(shelve.open(fname)) as d:
        ostensibly_in_py3 = filter(is_python3, d['packages'].values())
        ostensibly_not_in_py3 = filter(
            lambda p: not is_python3(p), d['packages'].values()
        )

    print "In py3:", len(ostensibly_in_py3)
    print "Not in py3:", len(ostensibly_not_in_py3)

if __name__ == str('__main__'):
    main()