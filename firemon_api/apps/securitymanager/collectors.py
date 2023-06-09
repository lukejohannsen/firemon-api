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
import uuid

# Local packages
from firemon_api.core.endpoint import Endpoint
from firemon_api.core.response import Record
from firemon_api.core.query import Request, url_param_builder

from .devices import Device

log = logging.getLogger(__name__)


class Collector(Record):
    """Represents the Data Collector

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "collector"

    def __init__(self, config, app):
        super().__init__(config, app)

    def status(self):
        """Get status of Collector"""
        key = f"status/{self.id}"
        req = Request(
            base=self._ep_url,
            key=key,
            session=self._session,
        )
        return req.get()

    def devices(self):
        """Get all devices assigned to collector"""
        key = "device"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return [Device(config, self._app) for config in req.get()]


class Collectors(Endpoint):
    """Represents the Data Collectors

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "collector"

    def __init__(self, api, app, record=Collector):
        super().__init__(api, app, record=Collector)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {"search": values[next(iter(values))]}
        return filters

    def save_usage(self, config, async_aggregation: bool = True):
        """Save usage

        Args:
            config (dict): dictionary of usage data.
                {
                    "endDate": "YYYY-MM-DDTHH:mm:ss+0000",
                    "ruleUsages": [
                        {
                            "deviceId": <id>,
                            "ruleId": <rule guid>,
                            "hitCount": int,
                            "sources": [
                                {
                                    "id": <guid for?>,
                                    "parentId": <guid for?>,
                                    "hitCount": int
                                }
                            ],
                            "destinations": [
                                <same as sources>
                            ],
                            "services": [
                                <same as sources>
                            ],
                            "apps": [
                                <same as sources>
                            ],
                            "users": [
                                <same as sources>
                            ]
                        }
                    ]
                }
            async_aggregation (bool): ?

        Return:
            ? (?): ?

        """
        filters = {"asyncAggregation": async_aggregation}
        key = "usage"
        req = Request(
            base=self.url,
            key=key,
            filters=filters,
            session=self.session,
        )

        return req.post(json=config)


class CollectorGroup(Record):
    """Represents the Collector Group

    Args:
        config (dict): dictionary of things values from json
        app (obj): App()
    """

    _ep_name = "collector/group"

    def __init__(self, config, app):
        super().__init__(config, app)

    def member_set(self, cid):
        """Assign a Collector to Group.

        note: no changes if device is already assigned.

        Args:
            cid (int): Collector ID
        """
        key = f"member/{cid}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.put()

    # def member_unset(self, cid):
    # Need to get this working to make set useful
    #    pass

    def device_set(self, id):
        """Assign a Device
        note: no changes if device is already assigned. How to unassign?

        Args:
            id (int): Device id
        """
        key = f"member/{id}"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.put()

    def assigned(self):
        """Get assigned devices"""
        key = f"assigned"
        req = Request(
            base=self._url,
            key=key,
            session=self._session,
        )
        return req.get()


class CollectorGroups(Endpoint):
    """Represents the Data Collector Groups

    Args:
        api (obj): FiremonAPI()
        app (obj): App()

    Kwargs:
        record (obj): default `Record` object
    """

    ep_name = "collector/group"

    def __init__(self, api, app, record=CollectorGroup):
        super().__init__(api, app, record=CollectorGroup)

    def _make_filters(self, values):
        # Only a 'search' for a single value. Take all key-values
        # and use the first key's value for search query
        filters = {"search": values[next(iter(values))]}
        return filters

    def count(self):
        return len(self.all())
