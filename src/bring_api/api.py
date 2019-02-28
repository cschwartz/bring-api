#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         fibonacci = bring_api.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import logging
import requests
import time
import attr
from typing import Optional

__author__ = "Christian Schwartz"
__copyright__ = "Christian Schwartz"
__license__ = "mit"

_logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class BringItem(object):
    name: str
    specification: str

    def is_unspecified(self):
        return not self.specification

    def __str__(self):
        if self.is_unspecified():
            return "{0}".format(self.name)
        else:
            return "{0} ({1})".format(self.name, self.specification)


@attr.s(auto_attribs=True)
class BringList:
    name: str
    uuid: str
    _api: 'BringApi'
    _last_query: Optional[float] = None

    def add(self, item, specification=""):
        self._api.raw_list_add(self.uuid, item, specification)
        self._update()

    def purchase(self, item):
        self._api.raw_list_purchase(self.uuid, item)
        self._update()

    def purchase_items(self):
        self._update_if_required()
        return self._purchase

    def recently_items(self):
        self._update_if_required()
        return self._recently

    def __str__(self):
        self._update_if_required()

        list_format = "{0} (Purchase: {1}, Recently: {2})"

        return list_format.format(self.name,
                                  len(self.purchase_items()),
                                  len(self.recently_items()))

    def _update_if_required(self):
        if self._check_update_required():
            self._update()

    def _check_update_required(self):
        return (not self._last_query or
                self._last_query + self._api.refresh_time < time.time())

    def _update(self):
        data = self._api.raw_list(self.uuid)
        self._last_query = time.time()

        self._status = data["status"]
        self._purchase = [BringItem(item["name"],
                                    item["specification"])
                          for item in data["purchase"]]
        self._recently = [BringItem(item["name"],
                                    item["specification"])
                          for item in data["recently"]]


@attr.s(auto_attribs=True)
class BringApi:
    AUTH_URL = "https://api.getbring.com/rest/v2/bringauth"
    LISTS_URL = "https://api.getbring.com/rest/v2/bringusers/{0}/lists"
    LIST_URL = "https://api.getbring.com/rest/v2/bringlists/{0}"

    user_uuid: str
    access_token: str
    refresh_time: int = 10*60

    def lists(self):
        url = self.LISTS_URL.format(self.user_uuid)
        headers = self.authorized_bring_headers()
        lists_response = requests.get(url,
                                      headers=headers)
        lists_response.raise_for_status()
        lists = lists_response.json()["lists"]
        return [BringList(item["name"],
                item["listUuid"],
                self) for item in lists]

    def raw_list_add(self, list_uuid, item, specification):
        item_data = {
            "uuid": list_uuid,
            "purchase": item,
            "specification": specification
        }

        list_response = requests.put(self.LIST_URL.format(list_uuid),
                                     data=item_data,
                                     headers=self.authorized_bring_headers())
        list_response.raise_for_status()

    def raw_list_purchase(self, list_uuid, item):
        item_data = {
            "uuid": list_uuid,
            "recently": item
        }
        list_response = requests.put(self.LIST_URL.format(list_uuid),
                                     data=item_data,
                                     headers=self.authorized_bring_headers())
        list_response.raise_for_status()

    def raw_list(self, list_uuid):
        list_response = requests.get(self.LIST_URL.format(list_uuid),
                                     headers=self.authorized_bring_headers())
        list_response.raise_for_status()

        return list_response.json()

    @classmethod
    def authenticate(cls, email, password):
        auth_data = {
            "email": email,
            "password": password
        }

        response = requests.post(cls.AUTH_URL,
                                 data=auth_data,
                                 headers=cls.bring_headers())

        response.raise_for_status()
        auth_response = response.json()

        user_uuid = auth_response["uuid"]
        access_token = auth_response["access_token"]

        return BringApi(user_uuid, access_token)

    def authorized_bring_headers(self):
        return {
            **self.bring_headers(),
            "Authorization": "Bearer {0}".format(self.access_token),
            "X-BRING-USER-UUID": self.user_uuid
        }

    @classmethod
    def bring_headers(cls):
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
            "X-BRING-CLIENT": "webApp",
            "X-BRING-CLIENT-SOURCE": "webApp",
            "X-BRING-COUNTRY": "DE",
            "X-BRING-API-KEY": "cof4Nc6D8saplXjE3h3HXqHH8m7VU2i1Gs0g85Sp",
            "X-BRING-CLIENT-INSTANCE-ID": "Web-dbwoh1VmlMaGf7RyIcPnLUnGbyd8iwn2"
        }
