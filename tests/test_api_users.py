# coding: utf-8
from .base import MyApiTestCase
import json
from privacyidea.lib.resolver import (save_resolver)
from privacyidea.lib.realm import (set_realm)
from privacyidea.lib.user import User
from privacyidea.lib.token import init_token, remove_token
from privacyidea.lib.policy import set_policy, delete_policy, SCOPE, ACTION
from six.moves.urllib.parse import urlencode

PWFILE = "tests/testdata/passwd"


class APIUsersTestCase(MyApiTestCase):

    parameters = {'Driver': 'sqlite',
                  'Server': '/tests/testdata/',
                  'Database': "testuser-api.sqlite",
                  'Table': 'users',
                  'Encoding': 'utf8',
                  'Map': '{ "username": "username", \
                    "userid" : "id", \
                    "email" : "email", \
                    "surname" : "name", \
                    "givenname" : "givenname", \
                    "password" : "password", \
                    "phone": "phone", \
                    "mobile": "mobile"}'
    }

    def test_00_get_empty_users(self):
        with self.app.test_request_context('/user/',
                                           method='GET',
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            self.assertTrue(b'"status": true' in res.data, res.data)
            self.assertTrue(b'"value": []' in res.data, res.data)

    def test_01_get_passwd_user(self):
        # create resolver
        with self.app.test_request_context('/resolver/r1',
                                           data=json.dumps({u"resolver": u"r1",
                                                 u"type": u"passwdresolver",
                                                 u"fileName": PWFILE}),
                                           method='POST',
                                           headers={"Authorization": self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            self.assertTrue(res.json['result']['status'], res.json)
            self.assertEqual(res.json['result']['value'], 1, res.json)
        
        # create realm
        realm = u"realm1"
        resolvers = u"r1, r2"
        with self.app.test_request_context('/realm/{0!s}'.format(realm),
                                           data={u"resolvers": resolvers},
                                           method='POST',
                                           headers={"Authorization": self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json
            value = result.get("result").get("value")
            self.assertTrue('r1' in value["added"], res.data)
            self.assertTrue('r2' in value["failed"], res.data)
                   
        # get user list
        with self.app.test_request_context('/user/',
                                           query_string=urlencode({u"realm":
                                                                       realm}),
                                           method='GET',
                                           headers={"Authorization": self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json
            value = result.get("result").get("value")
            unames = [x.get('username') for x in value]
            self.assertIn("cornelius", unames, value)
            self.assertIn("corny", unames, value)

        # get user list with search dict
        with self.app.test_request_context('/user/',
                                           query_string=urlencode({u"username":
                                                                       "cornelius"}),
                                           method='GET',
                                           headers={"Authorization": self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json
            value = result.get("result").get("value")
            unames = [x.get('username') for x in value]
            self.assertIn("cornelius", unames, value)
            self.assertNotIn("corny", unames, value)

        # get user with a non existing realm
        with self.app.test_request_context('/user/',
                                           query_string=urlencode({"realm":
                                                            "non_existing"}),
                                           method='GET',
                                           headers={"Authorization": self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json
            value = result.get("result").get("value")
            unames = [x.get('username') for x in value]
            self.assertNotIn("cornelius", unames, value)
            self.assertNotIn("corny", unames, value)

    def test_02_create_update_delete_user(self):
        realm = "sqlrealm"
        resolver = "SQL1"
        parameters = self.parameters
        parameters["resolver"] = resolver
        parameters["type"] = "sqlresolver"

        rid = save_resolver(parameters)
        self.assertTrue(rid > 0, rid)

        (added, failed) = set_realm(realm, [resolver])
        self.assertEqual(len(failed), 0)
        self.assertEqual(len(added), 1)

        # CREATE a user
        with self.app.test_request_context('/user/',
                                           method='POST',
                                           data={"user": "wordy",
                                                 "resolver": resolver,
                                                 "surname": "zappa",
                                                 "givenname": "frank",
                                                 "email": "f@z.com",
                                                 "phone": "12345",
                                                 "mobile": "12345",
                                                 "password": "12345"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value") > 6, result.get("value"))

        # Get users
        with self.app.test_request_context('/user/',
                                           method='GET',
                                           query_string=urlencode(
                                               {"username": "wordy"}),
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"))
            self.assertEqual(result.get("value")[0].get("username"), "wordy")

        # Update by administrator. Set the password to "passwort"
        with self.app.test_request_context('/user/',
                                           method='PUT',
                                           query_string=urlencode(
                                               {"user": "wordy",
                                                "resolver": resolver,
                                                "password": "passwort"}),
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value"))

        # Get user authentication and update by user.
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "wordy@{0!s}".format(realm),
                                                 "password": "passwort"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            # In self.at_user we store the user token
            wordy_auth_token = result.get("value").get("token")
            # check that this is a user
            role = result.get("value").get("role")
            self.assertTrue(role == "user", result)

        # Even if a user specifies another username, the username is
        # overwritten by his own name!
        with self.app.test_request_context('/user/',
                                           method='PUT',
                                           query_string=urlencode(
                                               {"user": "wordy2",
                                                "resolver": resolver,
                                                "password": "newPassword"}),
                                           headers={'Authorization':
                                                        wordy_auth_token}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value"))

        # Although the user "wordy" tried to update the password of user
        # "wordy2", he updated his own password.
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": "wordy@{0!s}".format(realm),
                                                 "password": "newPassword"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            # In self.at_user we store the user token
            wordy_auth_token = result.get("value").get("token")
            # check that this is a user
            role = result.get("value").get("role")
            self.assertTrue(role == "user", result)

        # Delete the users
        with self.app.test_request_context('/user/{0!s}/{1!s}'.format(resolver, "wordy"),
                                           method='DELETE',
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value"))

    def test_03_create_update_delete_unicode_user(self):
        realm = "sqlrealm"
        resolver = "SQL1"
        parameters = self.parameters
        parameters["resolver"] = resolver
        parameters["type"] = "sqlresolver"

        rid = save_resolver(parameters)
        self.assertTrue(rid > 0, rid)

        (added, failed) = set_realm(realm, [resolver])
        self.assertEqual(len(failed), 0)
        self.assertEqual(len(added), 1)

        # CREATE a user
        with self.app.test_request_context('/user/',
                                           method='POST',
                                           data={"user": u"wördy",
                                                 "resolver": resolver,
                                                 "surname": "zappa",
                                                 "givenname": "frank",
                                                 "email": "f@z.com",
                                                 "phone": "12345",
                                                 "mobile": "12345",
                                                 "password": "12345"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value") > 6, result.get("value"))

        # Get users
        with self.app.test_request_context('/user/',
                                           method='GET',
                                           query_string=urlencode(
                                               {"username": u"wördy".encode('utf-8')}),
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"))
            self.assertEqual(result.get("value")[0].get("username"), u"wördy")

        # Update by administrator. Set the password to "passwort"
        with self.app.test_request_context('/user/',
                                           method='PUT',
                                           query_string=urlencode(
                                               {"user": u"wördy".encode('utf-8'),
                                                "resolver": resolver,
                                                "password": "passwort"}),
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value"))

        # Get user authentication and update by user.
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": u"wördy@{0!s}".format(realm).encode('utf-8'),
                                                 "password": "passwort"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            # In self.at_user we store the user token
            wordy_auth_token = result.get("value").get("token")
            # check that this is a user
            role = result.get("value").get("role")
            self.assertTrue(role == "user", result)

        # Even if a user specifies another username, the username is
        # overwritten by his own name!
        with self.app.test_request_context('/user/',
                                           method='PUT',
                                           query_string=urlencode(
                                               {"user": u"wördy2".encode('utf-8'),
                                                "resolver": resolver,
                                                "password": "newPassword"}),
                                           headers={'Authorization':
                                                        wordy_auth_token}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value"))

        # Although the user "wördy" tried to update the password of user
        # "wördy2", he updated his own password.
        with self.app.test_request_context('/auth',
                                           method='POST',
                                           data={"username": u"wördy@{0!s}".format(realm).encode('utf-8'),
                                                 "password": "newPassword"}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            # In self.at_user we store the user token
            wordy_auth_token = result.get("value").get("token")
            # check that this is a user
            role = result.get("value").get("role")
            self.assertTrue(role == "user", result)

        # Delete the users
        with self.app.test_request_context(u'/user/{0!s}/{1!s}'.format(resolver, u"wördy").encode('utf-8'),
                                           method='DELETE',
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("value"))

    def test_10_additional_attributes(self):
        from privacyidea.lib.policy import set_policy, ACTION, SCOPE, delete_policy
        with self.app.test_request_context('/user/attribute',
                                           method='POST',
                                           data={"user": "cornelius@realm1",
                                                 "key": "newattribute",
                                                 "value": "newvalue"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 403, res)
            result = res.json.get("result")
            self.assertFalse(result.get("status"), res.data)
            self.assertEqual(result.get("error").get("message"),
                             "You are not allowed to set this custom user attribute!")

        # Allow to set custom attributes
        set_policy("custom_attr", scope=SCOPE.ADMIN,
                   action="{0!s}=:*:*".format(ACTION.SET_USER_ATTRIBUTES))

        with self.app.test_request_context('/user/attribute',
                                           method='POST',
                                           data={"user": "cornelius@realm1",
                                                 "key": "newattribute",
                                                 "value": "newvalue"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            self.assertTrue(result.get("value") >= 0)

        # Now we verify if the user has the additional attribute:
        with self.app.test_request_context('/user/attribute',
                                           method='GET',
                                           data={"user": "cornelius@realm1"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            self.assertIn("newattribute", result.get("value"))
            self.assertEqual(result.get("value").get("newattribute"), "newvalue")

        with self.app.test_request_context('/user/attribute',
                                           method='GET',
                                           data={"user": "cornelius@realm1",
                                                 "key": "newattribute"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            self.assertEqual(result.get("value"), "newvalue")

        # Now we check, if the additional attribute is also contained in the
        # user listing
        delete_policy("custom_attr")
        with self.app.test_request_context('/user/',
                                           method='GET',
                                           data={"realm": "realm1"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            additional_attribute_found = False
            # check in the user list for the username=cornelius
            for user in result.get("value"):
                if user.get("username") == "cornelius":
                    self.assertEqual(user.get("newattribute"), "newvalue")
                    additional_attribute_found = True
            self.assertTrue(additional_attribute_found)

        # Now we search for the one explicit user
        with self.app.test_request_context('/user/',
                                           method='GET',
                                           data={"realm": "realm1",
                                                 "username": "cornelius"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            # check in the user list for the username=cornelius
            self.assertEqual(len(result.get("value")), 1)
            self.assertEqual(result.get("value")[0].get("newattribute"), "newvalue")

        # The additional attribute should also be returned, if the user authenticates successfully.
        init_token({"serial": "SPASS1", "type": "spass", "pin": "test"}, user=User("cornelius", self.realm1))
        set_policy(name="POL1", scope=SCOPE.AUTHZ, action=ACTION.ADDUSERINRESPONSE)
        with self.app.test_request_context('/validate/check',
                                           method='POST',
                                           data={"user": "cornelius@realm1",
                                                 "pass": "test"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            details = res.json.get("detail")
            user_data = details.get("user")
            self.assertIn("newattribute", user_data)
            self.assertEqual(user_data.get("newattribute"), "newvalue")
        remove_token("SPASS1")
        delete_policy("POL1")

        # Now we delete the additional user attribute
        set_policy("custom_attr", scope=SCOPE.ADMIN,
                   action="{0!s}=*".format(ACTION.DELETE_USER_ATTRIBUTES))
        with self.app.test_request_context('/user/attribute/newattribute/cornelius/realm1',
                                           method='DELETE',
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            self.assertTrue(result.get("value") >= 0)

        # and verify, that it is gone
        with self.app.test_request_context('/user/attribute',
                                           method='GET',
                                           data={"user": "cornelius@realm1"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            self.assertTrue(result.get("status"), res.data)
            self.assertNotIn("newattribute", result.get("value"))

        # Check, which attributes the admin is allowed to set or delete
        set_policy("custom_attr", scope=SCOPE.ADMIN,
                   action="{0!s}=:hello: one two".format(ACTION.SET_USER_ATTRIBUTES))
        set_policy("custom_attr2", scope=SCOPE.ADMIN,
                   action="{0!s}=:hello2: * :hello: three".format(ACTION.SET_USER_ATTRIBUTES))
        set_policy("custom_attr3", scope=SCOPE.ADMIN,
                   action="{0!s}=:*: on off".format(ACTION.SET_USER_ATTRIBUTES))
        set_policy("custom_attr4", scope=SCOPE.ADMIN,
                   action="{0!s}=*".format(ACTION.DELETE_USER_ATTRIBUTES))
        with self.app.test_request_context('/user/editable_attributes/',
                                           method='GET',
                                           data={"user": "cornelius@realm1"},
                                           headers={'Authorization': self.at}):
            res = self.app.full_dispatch_request()
            self.assertTrue(res.status_code == 200, res)
            result = res.json.get("result")
            value = result.get("value")
            self.assertIn("delete", value)
            self.assertEqual(value.get("delete"), ['*'])
            self.assertIn("set", value)
            setables = value.get("set")
            self.assertIn("*", setables)
            self.assertIn("hello", setables)
            self.assertIn("hello2", setables)
            self.assertEqual(["on", "off"], setables.get("*"))
            self.assertEqual(["one", "two", "three"], setables.get("hello"))
            self.assertEqual(["*"], setables.get("hello2"))

        delete_policy("custom_attr")
        delete_policy("custom_attr2")
        delete_policy("custom_attr3")
        delete_policy("custom_attr4")