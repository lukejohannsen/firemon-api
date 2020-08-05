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
import logging
from urllib.parse import urlencode, quote
import uuid

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from .devicepacks import DevicePack
from .collectionconfigs import CollectionConfigs
from .revisions import Revisions, NormalizedData

log = logging.getLogger(__name__)


class Device(Record):
    """Device Record

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

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
        {'id': 21, 'domainId': 1, 'name': 'vSRX-2',
            'description': 'regression test SRX', ...}

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

    _domain_url = True
    ep_name = 'device'
    extendedSettingsJson = JsonField
    devicePack = DevicePack

    def __init__(self, config , app):
        super().__init__(config, app)

        #self.url = '{ep}/{id}'.format(ep=self.ep_url, 
        #                                id=config['id'])
        self._no_no_keys = ['securityConcernIndex',
                            'gpcComputeDate',
                            'gpcDirtyDate',
                            'gpcImplementDate',
                            'gpcStatus',
                           ]

        # Add attributes to Record() so we can get more info
        self.revisions = Revisions(self.app.api, 
                                   self.app, 
                                   device_id=config['id'])

        self.collectionconfigs = CollectionConfigs(self.app.api, 
                                self.app, 
                                device_id=config['id'],
                                devicepack_id=config['devicePack']['id'])

    def save(self, retrieve: bool=False) -> bool:
        """Saves changes to an existing object.
        Checks the state of `_diff` and sends the entire
        `serialize` to Request.put().

        Kwargs:
            retrieve (bool): Perform manual retrieval on save

        Return:
            (bool): True if PUT request was successful.

        >>> dev = fm.sm.devices.get(name='vsrx3')
        >>> dev.description
        AttributeError: 'Device' object has no attribute 'description'
        >>> dev.attr_set('description','Virtual SRX - DC 3')
        >>> dev.save()
        True
        >>>
        """
        if self.id:
            diff = self._diff()
            if diff:
                serialized = self.serialize()
                # Make sure this is set appropriately. Cannot change.
                serialized['id'] = self._config['id']
                # Put all this redundant nonsense back in. Why api, why?
                serialized['devicePack'] = self._config['devicePack']
                params = {'manualRetrieval': retrieve}
                req = Request(
                    base=self.url,
                    filters=params,
                    session=self.session,
                )
                return req.put(serialized)

        return False

    def update(self, data: dict, retrieve: bool=False) -> bool:
        """Update an object with a dictionary.
        Accepts a dict and uses it to update the record and call save().
        For nested and choice fields you'd pass an int the same as
        if you were modifying the attribute and calling save().

        Args:
            data (dict): Dictionary containing the k/v to update the
            record object with.

        Returns:
            bool: True if PUT request was successful.

        Example:
        >>> dev = fm.sm.devices.get(1)
        >>> dev.update({
        ...   "name": "foo2",
        ...   "description": "barbarbaaaaar",
        ... })
        True
        """

        for k, v in data.items():
            self.attr_set(k, v)
        return self.save(retrieve=retrieve)

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

        filters = {'deleteChildren': deleteChildren, 'async': a_sync,
                  'sendNotification': sendNotification,
                  'postProcessing': postProcessing}

        req = Request(
            base=self.url,
            filters=filters,
            session=self.session,
        )
        return req.delete()

    def rev_export(self, meta: bool=True):
        """Export latest configuration files as a zip file 
        
        Support files include all NORMALIZED data and other meta data.
        Raw configs include only those files as found by Firemon 
        during a retrieval.
        
        Kwargs:
            meta (bool): True gets a SUPPORT file. False is Raw only

        Returns:
            bytes: file

        Example:
            >>> import os
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> support = dev.rev_export()
            >>> with open('support.zip', 'wb') as f:
            ...   f.write(support)
            ...
            38047
        """
        if meta:
            key = 'export'
        else:
            key = 'export/config'
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.get_content()


    def config_import(self, f_list: list,
                      change_user=None,
                      correlation_id=None) -> bool:
        """Import config files for device to create a new revision

        Args:
            f_list (list): a list of tuples. Tuples are intended to uploaded
            as a multipart form using 'requests'. format of the data in the
            tuple is:
            ('file', ('<file-name>', open(<path_to_file>, 'rb'), 'text/plain'))

        Kwargs:
            change_user (str): A name for display field
            correlation_id (str): A UUID1

        Example:
            >>> import os
            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> dir = '/path/to/config/files/'
            >>> f_list = []
            >>> for fn in os.listdir(dir):
            ...     path = os.path.join(dir, fn)
            ...     f_list.append(('file', (fn, open(path, 'rb'), 'text/plain')))
            >>> dev.import_config(f_list)
        """
        if not change_user:
            # Not needed as server will go on its merry way with nothing
            change_user = '{}:[firemon_api]'.format(self.app.api.username)
        if not correlation_id:
            # Not needed as server will generate one for us. But... whatever.
            correlation_id = str(uuid.uuid1())
        filters = {'action': 'IMPORT', 'changeUser': change_user,
                    'correlationId': correlation_id}
        key = 'rev'

        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        )
        return req.post(files=f_list)

    def support_import(self, zip_file: bytes, renormalize: bool=False):
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

            >>> dev = fm.sm.devices.get(name='vsrx-2')
            >>> fn = 'vsrx-2.zip'
            >>> path = '/path/to/file/vsrx-2.zip'
            >>> dev.import_support((fn, open(path, 'rb'))
        """
        filters = {'renormalize': renormalize}
        files = {'file': zip_file}
        key = 'import'

        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        )
        return req.post(files=files)

    def retrieval_exec(self, debug: bool=False):
        """Execute a manual retrieval for device.

        Kwargs:
            debug (bool): Unsure what this does
        """
        key = 'manualretrieval'
        filters = {'debug': debug}

        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        )
        return req.post()

    def rule_usage(self, type: str='total'):
        """Get rule usage for device.
        total hits for all rules on the device.

        Kwargs:
            type (str): either 'total' or 'daily'

        Return:
            json: daily == {'hitDate': '....', 'totalHits': int}
                  total == {'totalHits': int}
        """
        key = 'ruleusagestat/{type}'.format(type=type)
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.get()

    def nd_problem(self):
        """Retrieve problems with latest normalization
        """
        key = 'device/{id}/nd/problem'.format(id=self.id)
        req = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        )
        return req.get()

    def nd_latest_get(self):
        """Gets the latest revision as a fully parsed object """
        key = 'rev/latest/nd/all'
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return NormalizedData(req.get(), self.app)

    def ssh_key_remove(self):
        """Remove ssh key from all Collectors for Device.

        Notes:
            SSH Key location: /var/lib/firemon/dc/.ssh/known_hosts
        """
        key = 'sshhostkey'
        req = Request(
            base=self.url,
            key=key,
            session=self.session,
        )
        return req.put()

    def __repr__(self):
        if len(str(self.id)) > 10:
            id = '{}...'.format(self.id[0:9])
        else:
            id = self.id
        if len(self.name) > 10:
            name = '{}...'.format(self.name[0:9])
        else:
            name = self.name
        return("<Device(id='{}', name='{}')>".format(id, name))

    def __str__(self):
        return("{}".format(self.name))


class Devices(Endpoint):
    """ Represents the Devices

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = 'device'
    _domain_url = True

    def __init__(self, api, app, record=Device):
        super().__init__(api, app, record=Device)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {'search': values[next(iter(values))]}
        return filters

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
        filters = {'manualRetrieval': retrieve}
        req = Request(
            base=self.url,
            filters=filters,
            session=self.session,
        ).post(data=dev_config)

        return self._response_loader(req)
