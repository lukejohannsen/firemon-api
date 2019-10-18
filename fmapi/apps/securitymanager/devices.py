"""
(c) 2019 Firemon

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# Standard packages
import json
from urllib.parse import urlencode, quote
import uuid

# Local packages
from fmapi.errors import AuthenticationError, FiremonError, LicenseError
from fmapi.errors import DeviceError, DevicePackError, VersionError
from fmapi.core.response import Record
from .collectionconfigs import CollectionConfigs, CollectionConfig
from .revisions import Revisions, Revision, ParsedRevision


class Devices(object):
    """ Represents the Devices

    Args:
        sm (obj): SecurityManager()
    """

    def __init__(self, sm):
        self.sm = sm
        self.url = sm.domain_url + '/device'  # Devices URL
        self.session = sm.session

    def all(self):
        """ Get all devices

        Return:
            list: List of Device() Records

        Examples:
            >>> devices = fm.sm.devices.all()

            >>> fm.domainId = 3
            >>> devices = fm.sm.devices.all()
        """
        total = 0
        page = 0
        count = 0
        url = self.url + '?page={page}&pageSize=100'.format(page=page)
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                results = resp['results']
                total = resp['total']
                count = resp['count']
                while total > count:
                    page += 1
                    url = self.url + '?page={page}&pageSize=100'.format(page=page)
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return [Device(self, dev) for dev in results]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def get(self, *args, **kwargs):
        """ Get single device

        Args:
            *args (int): (optional) Device id to retrieve
            **kwargs (str): (optional) see filter() for available filters

        Examples:
            Get by ID
            >>> fm.sm.devices.get(21)
            vSRX-2

            Get by partial name. Case insensative.
            >>> fm.sm.devices.get(name='SONICWAll')
            SONICWALL-TZ-210-1
        """
        try:
            id = args[0]
            url = self.url + '/{id}'.format(id=str(id))
            self.session.headers.update({'Content-Type': 'application/json'})
            response = self.session.get(url)
            if response.status_code == 200:
                return Device(self, response.json())
            else:
                raise DeviceError("ERROR retrieving device! HTTP code: {}"
                                   " Server response: {}".format(
                                   response.status_code, response.text))
        except IndexError:
            id = None
        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                            "get() returned more than one result. "
                            "Check that the kwarg(s) passed are valid for this "
                            "or use filter() or all() instead."
                        )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """ Filter devices based on search parameters

        Args:
            **kwargs (str): filter parameters

        Available Filters:
            name, description, mgmtip, vendors, products, datacosllectors,
            devicegroups, devicetypes, centralsyslogs, retrieval, change,
            log, parentids, devicepackids

        Return:
            list: List of Device() Records
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.devices.filter(name='bogus')
            [bogus-ASA-support-3101, bogus.lab.securepassage.com]

            Partial IP search.
            >>> fm.sm.devices.filter(mgmtip='10.2')
            [bogus.lab.securepassage.com, Some auto test]
        """
        if not kwargs:
            raise ValueError('filter() must be passed kwargs. ')
        total = 0
        page = 0
        count = 0
        url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                            page=page, filters=urlencode(kwargs, quote_via=quote))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                results = resp['results']
                total = resp['total']
                count = resp['count']
                while total > count:
                    page += 1
                    url = self.url + '/filter?page={page}&pageSize=100&filter={filters}'.format(
                                    page=page, filters=urlencode(kwargs, quote_via=quote))
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return [Device(self, dev) for dev in results]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def search(self, arg):
        """ Filter devices based on search parameters

        Args:
            arg (str): search parameter

        Return:
            list: List of Device() Records
            None: if not found

        Examples:
            Partial name search return multiple devices
            >>> fm.sm.devices.search('bogus')
            [bogus-ASA-support-3101, bogus.lab.securepassage.com]

            Partial IP search.
            >>> fm.sm.devices.search('10.2')
            [bogus.lab.securepassage.com, Some auto test]
        """
        total = 0
        page = 0
        count = 0
        url = self.url + '?page={page}&pageSize=100&search={filter}'.format(
                            page=page, filter=arg)
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            resp = response.json()
            if resp['results']:
                results = resp['results']
                total = resp['total']
                count = resp['count']
                while total > count:
                    page += 1
                    url = url = self.url + '?page={page}&pageSize=100&search={filter}'.format(
                                    page=page, filter=arg)
                    response = self.session.get(url)
                    resp = response.json()
                    count += resp['count']
                    results.extend(resp['results'])
                return [Device(self, dev) for dev in results]
            else:
                return []
        else:
            raise DeviceError("ERROR retrieving device! HTTP code: {}"
                               " Server response: {}".format(
                               response.status_code, response.text))

    def create(self, dev_config, retrieve: bool=False):
        """  Create a new device

        Args:
            dev_config (dict): dictionary of configuration data.
            retrieve (bool): whether to kick off a manual retrieval

        Return:
            Device (obj): a Device() of the newly created device

        Examples:
            >>> config = fm.sm.dp.get('juniper_srx').template()
            >>> config['name'] = 'Conan'
            >>> config['description'] = 'A test of the API'
            >>> config['managementIp'] = '10.2.2.2'
            >>> dev = fm.sm.devices.create(config)
            Conan
        """
        assert(isinstance(dev_config, dict)), 'Configuration needs to be a dict'
        url = self.url + '?manualRetrieval={debug}'.format(debug=str(retrieve))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.post(url, json=dev_config)
        if response.status_code == 200:
            config = json.loads(response.content)
            return self.get(config['id'])
        else:
            raise DeviceError("ERROR installing device! HTTP code: {}  "
                              "Server response: {}".format(
                              response.status_code, response.text))

    def __repr__(self):
        return("<Devices(url='{}')>".format(self.url))

    def __str__(self):
        return("{}".format(self.url))


class Device(Record):
    """ Represents a device in Firemon

    Args:
        devs (obj): Devices()
        config (dict): all the things

    Attributes:
        * cc (collection configs)
        * revisions

    Examples:
        Get device by ID
        >>> dev = fm.sm.devices.get(21)
        >>> dev
        vSRX-2

        Show configuration data
        >>> dict(dev)
        {'id': 21, 'domainId': 1, 'name': 'vSRX-2', 'description': 'regression test SRX', ...}

        List all collection configs that device can use
        >>> dev.cc.all()
        [21, 46]
        >>> cc = dev.cc.get(46)

        List all revisions associated with device
        >>> dev.revisions.all()
        [76, 77, 108, 177, 178]

        Get the latest revision
        >>> rev = dev.revisions.filter(latest=True)[0]
        178
    """
    def __init__(self, devs, config):
        super().__init__(devs, config)

        self.devs = devs
        self.url = devs.sm.domain_url + '/device/{id}'.format(id=str(config['id']))  # Device id URL

        # Add attributes to Record() so we can get more info
        self.revisions = Revisions(self.devs.sm, self.id)
        self.cc = CollectionConfigs(self.devs.sm, self.devicePack.id, self.id)

    def _reload(self):
        """ Todo: Get configuration info upon change """
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.get(self.url)
        if response.status_code == 200:
            config = response.json()
            self._config = config
            self.__init__(self.devs, self._config)
        else:
            raise FiremonError('Error! unable to reload Device')

    def delete(self, deleteChildren: bool=False, a_sync: bool=False,
                    sendNotification: bool=False, postProcessing: bool=True):
        """ Delete the device (and child devices)

        Kwargs:
            deleteChildren (bool): delete all associated child devices
            a_sync (bool): ???
            sendNotification (bool): ???
            postProcessing (bool): ???

        Example:
            >>> dev = fm.sm.devices.get(17)
            >>> dev
            CSM-2

            Delete device and all child devices
            >>> dev.delete(deleteChildren=True)
            True
        """

        kwargs = {'deleteChildren': deleteChildren, 'async': a_sync,
                  'sendNotification': sendNotification, 'postProcessing': postProcessing}
        url = self.url + '?{filters}'.format(filters=urlencode(kwargs, quote_via=quote))
        response = self.session.delete(url)
        if response.status_code == 200:
            return True
        else:
            raise DeviceError("ERROR deleting device(s)! Code {}".format(response.status_code))

    def import_config(self, f_list: list) -> bool:
        """ Import config files for device to create a new revision

        Args:
            f_list (list): a list of tuples. Tuples are intended to uploaded
                as a multipart form using 'requests'. format of the data in the
                tuple is ('file', ('<file-name>', open(<path_to_file>, 'rb'), 'text/plain'))

        Example:
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> dir = '/path/to/config/files/'
            >>> f_list = []
            >>> for fn in os.listdir(dir):
            ... 	path = os.path.join(dir, fn)
            ... 	f_list.append(('file', (fn, open(path, 'rb'), 'text/plain')))
            >>> dev.import_config(f_list)
        """
        self.session.headers.update({'Content-Type': 'multipart/form-data'})
        changeUser = self.devs.sm.api.username  # Not really needed
        correlationId = str(uuid.uuid1())  # Not really needed
        url = self.url + '/rev?action=IMPORT&changeUser={}&correlationId={}'.format(
            changeUser, correlationId)  # changeUser and corId not need
        response = self.session.post(url, files=f_list)
        if response.status_code == 200:
            self.session.headers.pop('Content-type', None)
            return True
        else:
            raise FiremonError('Error: unable to upload configuration files! HTTP code: {} \
                            Content {}'.format(response.status_code, response.text))

    def import_support(self, zip_file: bytes, renormalize: bool=False):
        """ Todo: Import a 'support' file, a zip file with the expected device
        config files along with 'NORMALIZED' and meta-data files. Use this
        function and set 'renormalize = True' and mimic 'import_config'.

        NOTE: Device packs must match from the support files descriptor.json

        Args:
            zip_file (bytes): bytes that make a zip file

        Kwargs:
            renormalize (bool): defualt (False). Tell system to re-normalize from
                config (True) or use imported 'NORMALIZED' files (False)

        Example:
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> fn = '/path/to/file/vsrx-2.zip'
            >>> with open(fn, 'rb') as f:
            >>>     zip_file = f.read()
            >>> dev.import_support(zip_file)
        """
        self.session.headers.update({'Content-Type': 'multipart/form-data'})
        url = self.url + '/import?renormalize={}'.format(str(renormalize))
        files = {'file': zip_file}
        response = self.session.post(url, files=files)
        if response.status_code == 200:
            self.session.headers.pop('Content-type', None)
            return True
        else:
            raise FiremonError('Error: unable to upload zip file! HTTP code: {} \
                            Content {}'.format(response.status_code, response.text))

    def update(self, dev_config: dict, retrieve: bool=False) -> bool:
        """ Pass configuration information to update Device.

        Args:
            dev_config (dict): a dictionary containing values for a collection

        Kwargs:
            retrieve (bool): whether to kick off a manual retrieval

        Return:
            bool: True on successful update

        Examples:

            Update from dictionary

            >>> dev = fm.sm.devices.get(1)
            >>> config = dev.template()
            Modify config
            >>> config['description'] = 'internal test device'
            >>> dev.update(config)

            Update self

            >>> dev = fm.sm.devices.get(1)
            >>> dev.description = 'A random test device'
            >>> dev.update(dict(dev))
        """
        assert(isinstance(dev_config, dict)), 'Configuration needs to be a dict'
        dev_config['id'] = self._config['id']  # make sure this is set appropriately
        dev_config['devicePack'] = self._config['devicePack']  # Put all this redundant shit back in
        url = self.url + '?manualRetrieval={retrieval}'.format(retrieval=str(retrieve))
        self.session.headers.update({'Content-Type': 'application/json'})
        response = self.session.put(url, json=dev_config)
        if response.status_code == 204:
            self._reload()
            return True
        else:
            raise DeviceError("ERROR updating Device! HTTP code: {}  \
                            Content {}".format(response.status_code, response.text))

    def template(self) -> dict:
        """ Dump out current config information that can be modified and sent
        to update() current device

        Return:
            dict: current device configuration minus things that should not be touched
        """
        config = self._config.copy()
        no_no_keys = ['devicePack',
        'securityConcernIndex',
        'gpcComputeDate',
        'gpcDirtyDate',
        'gpcImplementDate',
        'gpcStatus'
        ]
        for k in no_no_keys:
            config.pop(k)

        config['devicePack'] = {'artifactId': self._config['devicePack']['artifactId']}
        return config

    def do_retrieval(self, debug: bool=False):
        """ Have current device begin a manual retrieval.

        Kwargs:
            debug (bool): ???
        """
        url = self.url + '/manualretrieval?debug={debug}'.format(debug=str(debug))
        response = self.session.post(url)
        if response.status_code == 204:
            return True
        else:
            return False

    def rule_usage(self, type: str='total'):
        """ This appears to be a very generic bit of information. Purely the
        total hits for all rules on the device.

        Kwargs:
            total (str): either 'total' or 'daily'

        Return:
            json: daily == {'hitDate': '....', 'totalHits': int}
                  total == {'totalHits': int}
        """
        url = self.url + '/ruleusagestat/{type}'.format(type=type)
        self.session.headers.update({'Accept': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise FiremonError('Error: Unable to retrieve device rule usage info')

    def get_nd_latest(self):
        """Gets the latest revision as a fully parsed object """
        url = self.url + '/rev/latest/nd/all'
        self.session.headers.update({'Accept': 'application/json'})
        response = self.session.get(url)
        if response.status_code == 200:
            return ParsedRevision(self.devs, response.json())
        else:
            raise FiremonError('Error: Unable to retrieve latest parsed revision')

    def __repr__(self):
        return("<Device(id='{}', name={})>".format(self.id, self.name))

    def __str__(self):
        return("{}".format(self.name))
