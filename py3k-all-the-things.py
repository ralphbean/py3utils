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

    return result


import multiprocessing as mp
pool = mp.Pool(100)


def populate():
    print "Getting the list of all packages."
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    packages = client.list_packages()
    print "Complete!"

    print "Ingesting %i packages." % len(packages)
    # Do it in parallel to go faster
    results = pool.map(ingest_package, packages)
    print "Complete!  Found %i packages." % len(results)

    # pprint.pprint(d['packages'][0]['releases'][0]['data']['classifiers'])
    fname = 'pypi-shelve.db'
    print "Storing to shelve %r" % fname
    with cm(shelve.open(fname)) as d:
        d['packages'] = results

    print "Complete!"


if __name__ == '__main__':
    print "Scraping pypi..."
    populate()
    print "Complete!"
