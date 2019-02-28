#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from bring_api.api import BringApi
import json
import vcr
import dotenv
import os
import requests

__author__ = "Christian Schwartz"
__copyright__ = "Christian Schwartz"
__license__ = "mit"


def scrub(strings, replacement_prefix="replaced"):
    def before_record_response(response):
        body_string = response['body']['string']
        if body_string:
            json_body = json.loads(body_string)
            replaced_attributes = {
                k: "{0}_{1}".format(replacement_prefix, k)
                for k in strings
            }
            json_body.update(replaced_attributes)
            response['body']['string'] = json.dumps(json_body).encode("UTF-8")
        return response
    return before_record_response


sanitizing_vcr = vcr.VCR(filter_post_data_parameters=['email', 'password'],
                         filter_headers=['authorization'],
                         before_record_response=scrub(['access_token',
                                                       'refresh_token',
                                                       'email',
                                                       'name',
                                                       'photoPath']),
                         decode_compressed_response=True,
                         cassette_library_dir="fixtures/vcr_cassettes",
                         path_transformer=vcr.VCR.ensure_suffix('.yaml'))


class TestBringAuthentication:
    def setup_method(self):
        dotenv.load_dotenv()
        self._bring_email = os.getenv("BRING_EMAIL")
        self._bring_password = os.getenv("BRING_PASSWORD")

    @sanitizing_vcr.use_cassette
    def test_authenticate(self):
        api = BringApi.authenticate(self._bring_email, self._bring_password)
        assert api

    @sanitizing_vcr.use_cassette
    def test_authenticate_fails(self):
        with pytest.raises(requests.exceptions.HTTPError):
            BringApi.authenticate(self._bring_email, "wrong_password")


class TestBringLists:
    def setup_method(self):
        dotenv.load_dotenv()
        self._bring_email = os.getenv("BRING_EMAIL")
        self._bring_password = os.getenv("BRING_PASSWORD")

    @sanitizing_vcr.use_cassette
    def test_returns_valid_lists(self):
        api = api = self._prepare_webservice()
        lists = api.lists()

        assert self._named_item("Test-List", lists)

    @sanitizing_vcr.use_cassette
    def test_add_item_unspecified(self):
        api = api = self._prepare_webservice()
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)

        test_list.add("Bread")

        item = self._named_item("Bread", test_list.purchase_items())
        assert item
        assert item.is_unspecified()

    @sanitizing_vcr.use_cassette
    def test_add_item_specified(self):
        api = self._prepare_webservice()
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)

        test_list.add("Bread", "2")

        item = self._named_item("Bread", test_list.purchase_items())
        assert item
        assert item.specification == "2"

    @sanitizing_vcr.use_cassette
    def test_remove_item(self):
        api = self._prepare_webservice()
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)
        test_list.add("Bread")

        test_list.purchase("Bread")

        assert not self._named_item("Bread", test_list.purchase_items())
        assert self._named_item("Bread", test_list.recently_items())

    @sanitizing_vcr.use_cassette
    def test_unspecified_item_to_string(self):
        api = self._prepare_webservice()
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)

        test_list.add("Bread")

        item = self._named_item("Bread", test_list.purchase_items())
        assert str(item) == "Bread"

    @sanitizing_vcr.use_cassette
    def test_specified_item_to_string(self):
        api = self._prepare_webservice()
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)

        test_list.add("Bread", "2")

        item = self._named_item("Bread", test_list.purchase_items())
        assert str(item) == "Bread (2)"

    @sanitizing_vcr.use_cassette
    def test_list_to_string(self):
        api = self._prepare_webservice()
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)

        test_list.add("Bread", "2")

        assert str(test_list) == "Test-List (Purchase: 1, Recently: 0)"

    def _named_item(self, name, named_list):
        return next(filter(lambda l: l.name == name, named_list), None)

    def _prepare_webservice(self):
        api = BringApi.authenticate(self._bring_email, self._bring_password)
        lists = api.lists()
        test_list = self._named_item("Test-List", lists)
        if self._named_item("Bread", test_list.purchase_items()):
            test_list.purchase("Bread")

        # We usually try not to assert in setup code.
        # However, as we're testing against a 'live' API
        # it seems prudent to verify the desired state of the
        # SUT.
        assert not self._named_item("Bread", test_list.purchase_items())

        return api
