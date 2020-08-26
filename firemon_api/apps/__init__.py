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

# Local packages
from firemon_api.core.query import Request, url_param_builder

from .globalpolicycontroller import *
from .policyoptimizer import *
from .policyplanner import *
from .securitymanager import *

log = logging.getLogger(__name__)


class SwaggerApi(object):
    """Attempt to dynamically create all the APIs

    Warning:
        Most of the names are not intuitive to what they do.
        Good luck and godspeed.
    """
    
    def __init__(self, swagger: dict):
        """
        Args:
            swagger (dict): all the json from `get_api`
        """
        for path in swagger['paths'].keys():
            for verb in swagger['paths'][path].keys():
                oid = swagger['paths'][path][verb]['operationId']
                _method = self._make_method(path, verb, oid)
                setattr(self, oid, _method)

    def _make_method(self, path, verb, oid):
        if verb == 'get':
            def _method(filters=None, add_params=None, **kwargs):
                p = path.lstrip('/')
                key = p.format(**kwargs)
                filters=filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.get(add_params=add_params)
            return _method

        elif verb == 'put':
            def _method(filters=None, data=None, **kwargs):
                p = path.lstrip('/')
                key = p.format(**kwargs)
                filters=filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.put(data=data)
            return _method

        elif verb == 'post':
            def _method(filters=None, data=None, files=None, **kwargs):
                p = path.lstrip('/')
                key = p.format(**kwargs)
                filters=filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.post()
            return _method

        elif verb == 'delete':
            def _method(filters=None, **kwargs):
                p = path.lstrip('/')
                key = p.format(**kwargs)
                filters=filters
                req = Request(
                    base=self.app_url,
                    key=key,
                    filters=filters,
                    session=self.session,
                )
                return req.delete()
            return _method

class App(object):
    """Base class for Firemon Apps"""

    name = None

    def __init__(self, api):
        self.api = api
        self.session = api.session
        self.base_url = api.base_url
        self.app_url = "{url}/{name}/api".format(url=api.base_url,
                                            name=self.__class__.name)
        self.domain_url = "{url}/domain/{id}".format(url=self.app_url,
                                            id=str(self.api.domain_id))

    def get_swagger(self):
        """Attempt to auto create all api calls by reading
        the swagger api endpoint make a best guess. User must
        be authorized to read swagger to use this.

        All auto created methods get setattr on `exec` for `App`.
        """
        _swagger = self.get_api()
        setattr(self, 'exec', SwaggerApi(_swagger))

    def get_api(self):
        """Return API specs from the swagger"""

        key = 'swagger.json'
        req = Request(
            base=self.app_url,
            key=key,
            session=self.session,
        )
        return req.get()

    def __repr__(self):
        return("<App({})>".format(self.name))

    def __str__(self):
        return('{}'.format(self.name))


class SecurityManager(App):
    """ Represents Security Manager in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * centralsyslogs: CentralSyslogs()
        * collectionconfigs: CollectionConfigs()
        * collectors: Collectors()
        * collectorgroups: CollectorGroups()
        * devices: Devices()
        * dp: DevicePacks()
        * revisions: Revisions()
        * users: Users()
        * Todo: add more as needed
    """

    name = 'securitymanager'

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        self.centralsyslogconfigs = CentralSyslogConfigs(self.api, self)
        self.centralsyslogs = CentralSyslogs(self.api, self)
        self.collectionconfigs = CollectionConfigs(self.api, self)
        self.collectors = Collectors(self.api, self)
        self.collectorgroups = CollectorGroups(self.api, self)
        self.devices = Devices(self.api, self)
        self.dp = DevicePacks(self.api, self)  # Todo: create the other /plugin
        self.es = ElasticSearch(self.api, self)
        self.license = License(self.api, self)
        self.revisions = Revisions(self.api, self)
        self.users = Users(self.api, self)
        self.usergroups = UserGroups(self.api, self)
        self.siql = Siql(self.api, self)


class GlobalPolicyController(App):
    """ Represents Global Policy Controller in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    name = 'globalpolicycontroller'

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        self.policycompute = PolicyCompute(self.api, self)


class PolicyOptimizer(App):
    """ Represents Policy Optimizer in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    name = 'policyoptimizer'

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        #self.xx = EndPoint(self)


class PolicyPlanner(App):
    """ Represents Policy Planner in Firemon

    Args:
        api (obj): FiremonAPI()
        name (str): name of the application

    Valid attributes are:
        * xx: EndPoint()
    """

    name = 'policyplanner'

    def __init__(self, api):
        super().__init__(api)

        # Endpoints
        #self.xx = EndPoint(self)