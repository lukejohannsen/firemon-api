"""
(c) 2021 Firemon

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
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record, JsonField
from firemon_api.core.query import Request, url_param_builder, RequestError
from firemon_api.core.utils import _build_dict

log = logging.getLogger(__name__)


class Zone(Record):
    """Device Zone Object `Record`.

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>>
    """

    _ep_name = "zoneobject"
    _is_domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)

    def _url_create(self):
        """ General self._url create. What is normally 'deviceId'. <sigh> """
        url = f"{self._ep_url}/{self.deviceid}"
        return url

    def save(self):
        raise NotImplementedError("Writes are not supported.")

    def update(self):
        raise NotImplementedError("Writes are not supported.")


class Zones(Endpoint):
    """Device Zone Object Endpoint.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        device_id (int): Device id

    Examples:
        >>> fm.sm.zones.get('GigabitEthernet0/7')
    """

    ep_name = "zoneobject/paged-search"
    _is_domain_url = True

    def __init__(self, api, app, record=Zone, device_id: int = None):
        super().__init__(api, app, record=Zone)
        self._device_id = device_id

    def _make_filters(self, values):
        """Yet another filter that is doing its own thing. """
        filters = {"q": values[next(iter(values))]}
        return filters

    def all(self):
        """Get all `Record`"""
        if self._device_id:
            all_key = f"device/{self._device_id}/{self.__class__.ep_name}"
        else:
            all_key = f"{self.__class__.ep_name}"

        req = Request(
            base=self.domain_url,
            key=all_key,
            session=self.session,
        )

        revs = [self._response_loader(i) for i in req.get()]
        return sorted(revs, key=lambda x: x.deviceid, reverse=True)

    def get(self, *args, **kwargs):
        """Query and retrieve individual Zones. Spelling matters.

        Args:
            *args: zone name (name)
            **kwargs: key value pairs in a zone dictionary

        Return:
            Zone(object): a Zone(object)

        Examples:

        >>> fm.sm.zones.get('GigabitEthernet0/7')

        >>> fm.sm.dp.get(matchId='6014fd68-010d-4437-80cb-8fd4807ba73b')

        """

        zone_all = self.all()
        try:
            # Only getting exact matches
            id = args[0]
            zone_l = [zone for zone in zone_all if zone.name == id]
            if len(zone_l) > 1:
                raise ValueError(
                    "get() returned more than one result."
                    "Check the kwarg(s) passed are valid or"
                    "use filter() or all() instead."
                )
            elif len(zone_l) == 1:
                return zone_l[0]
            else:
                raise Exception(f"The requested zone: {id} could not " "be found")
        except IndexError:
            id = None

        if not id:
            filter_lookup = self.filter(**kwargs)
            if filter_lookup:
                if len(filter_lookup) > 1:
                    raise ValueError(
                        "get() returned more than one result."
                        "Check the kwarg(s) passed are valid or"
                        "use filter() or all() instead."
                    )
                else:
                    return filter_lookup[0]
            return None

    def filter(self, **kwargs):
        """Retrieve a filtered list of Zones

        Args:
            **kwargs: key value pairs in a device pack dictionary

        Return:
            list: a list of Zone(object)

        Examples:

        >>> fm.sm.zones.filter(type="ANY")
        """

        zone_all = self.all()
        if not kwargs:
            raise ValueError("filter must have kwargs")

        return [zone for zone in zone_all if kwargs.items() <= dict(zone).items()]


class FmZone(Record):
    """Firemon System Zone `Record`.

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()

    Examples:
        >>>
    """

    _ep_name = "zone"
    _is_domain_url = True

    def __init__(self, config, app):
        super().__init__(config, app)


class FmZones(Endpoint):
    """Firemon System Zone Endpoint.

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
        device_id (int): Device id

    Examples:
        >>>
    """

    ep_name = "zone"
    _is_domain_url = True

    def __init__(self, api, app, record=FmZone, device_id: int = None):
        super().__init__(api, app, record=FmZone)
        self._device_id = device_id
