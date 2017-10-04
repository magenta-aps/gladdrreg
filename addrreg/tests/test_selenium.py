# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import os
import sys
import unittest

from django import apps, test
from django.conf import settings
from django.test import tag

from .. import models
from .util import DUMMY_DOMAIN
from ..models import events

try:
    import selenium
except ImportError:
    selenium = None


@tag('selenium')
@unittest.skipIf(not selenium, 'selenium not installed')
class SeleniumTests(test.LiveServerTestCase):

    maxDiff = 1000

    # default to the easiest browser to install and configure -- on
    # macOS, that's Safari, obviously, and on Ubuntu that's Chrome
    # since they package its driver
    DEFAULT_DRIVER = 'Chrome' if sys.platform != 'darwin' else 'Safari'

    DRIVER_PATHS = {
        'Safari': [
            '/Applications/Safari Technology Preview.app'
            '/Contents/MacOS/safaridriver',
        ],

        'Chrome': [
            '/usr/lib/chromium-browser/chromedriver',
        ]
    }

    @classmethod
    def setUpClass(cls):
        from selenium import webdriver

        # If no display is found, try to create one
        if not os.environ.get('DISPLAY') and sys.platform != 'darwin':
            from pyvirtualdisplay import Display
            cls.display = Display(visible=0, size=(800, 600))
            cls.display.start()

        driver_name = os.environ.get('BROWSER', cls.DEFAULT_DRIVER)
        driver = getattr(webdriver, driver_name)

        if not driver:
            raise unittest.SkipTest('$BROWSER unset or invalid')

        args = {}

        for driver_path in cls.DRIVER_PATHS.get(driver_name, []):
            if os.path.isfile(driver_path):
                args.update(executable_path=driver_path)

        try:
            cls.browser = driver(**args)
        except Exception as exc:
            raise unittest.SkipTest(exc.args[0])

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        cls.browser.quit()
        # If a Xvfb display is running, clean it up
        if hasattr(cls, 'display') and cls.display:
            cls.display.stop()

    def setUp(self):
        super().setUp()

        self.inject()

        self.browser.delete_all_cookies()

    def inject(self):
        self.user_model = apps.apps.get_model(settings.AUTH_USER_MODEL)

        self.superuser = self.user_model.objects.create_superuser(
            'root', 'root@example.com', 'password',
        )

        models.State.objects.create(id=0, state_id=0, name='Bad', code=0)
        models.State.objects.create(id=1, state_id=1, name='Halfways', code=1)
        models.State.objects.create(id=2, state_id=2, name='Good', code=2)

        self.state = models.State.objects.get(name='Good')

        self.users = {}

        for l in ['A', 'B', 'C']:
            user = self.user_model.objects.create_user(
                'User' + l, 'user{}@example.com'.format(l), 'password',
                is_staff=True,
            )

            # don't grant the last user any rights
            if l < 'C':
                mun = models.Municipality.objects.create(
                    name='City ' + l, abbrev=l, code=ord(l),
                    state=self.state, sumiffiik_domain=DUMMY_DOMAIN,
                )

                for i in range(3):
                    suffix = '{}{}'.format(l, i)
                    models.Locality.objects.create(
                        name='Location' + suffix, abbrev=suffix, code=i,
                        sumiffiik_domain=DUMMY_DOMAIN, type=i + 1,
                        municipality=mun,
                    )

                rights = models.MunicipalityRights.objects.create(
                    municipality=mun,
                )
                rights.users.add(user)
                rights.save()

            self.users[user.username] = user

        user = self.user_model.objects.create_user(
            'UserAB', 'user{}@example.com'.format(l), 'password',
            is_staff=True,
        )

        for right in models.MunicipalityRights.objects.filter(
            municipality__abbrev__in=['A', 'B'],
        ):
            right.users.add(user)
            right.save()

    def await_staleness(self, element):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(self.browser, 1).until(
            EC.staleness_of(element),
        )
        self.browser.find_element_by_id("content")

    def fill_in_form(self, **kwargs):

        for field, value in kwargs.items():
            e = self.browser.find_element_by_id("id_" + field)

            if (e.tag_name == 'input' and
                    e.get_attribute('type') in ('text', 'password', 'number')):
                e.clear()
                e.send_keys(
                    value,
                )

            elif e.tag_name == 'select':
                options = e.find_elements_by_tag_name('option')

                for option in options:
                    if option.text.strip() == value:
                        # selenium is horrible; it does have code for
                        # setting options, but it only works in
                        # Firefox; instead, we use JavaScript

                        self.browser.execute_script('''
                        var f = document.getElementById('id_{field}');
                        var sel = '#id_{field} option[value="{value}"]';

                        document.querySelector(sel).selected = true;

                        '''.format(field=field,
                                   value=option.get_attribute('value')))
                        break

                else:
                    self.fail('{} not one of {}'.format(
                        value, [o.text for o in options]),
                    )

            elif (e.tag_name == 'input' and
                    e.get_attribute('type') in ('checkbox', 'radio')):
                if value != e.is_selected():
                    e.click()

            else:
                self.fail('unhandled input element (' + e.tag_name + '): ' +
                          e.get_attribute('outerHTML'))

        # clicking on invisible items using Selenium doesn't work in Chrome....
        self.browser.execute_script('''
        document.querySelector('input[type="submit"]').scrollIntoView()
        ''')

        submit = self.browser.find_element_by_css_selector(
            "input[type=submit]",
        )
        submit.click()
        self.await_staleness(submit)

    def login(self, user, password='password', expected=True):
        # logout
        self.browser.delete_all_cookies()
        self.browser.get(self.live_server_url + '/admin/logout/')
        self.browser.delete_all_cookies()
        self.browser.get(self.live_server_url)

        self.assertNotEqual(self.live_server_url, self.browser.current_url,
                            'logout failed!')

        # sanitity check the credentials
        self.client.logout()
        login_status = self.client.login(username=user, password=password)

        self.assertEqual(login_status, expected,
                         'Unexpected login status (credentials)!')

        self.fill_in_form(username=user, password=password)
        if expected:
            self.assertEquals(self.live_server_url + '/admin/',
                              self.browser.current_url,
                              'login failed')
        else:
            self.assertNotEquals(self.live_server_url + '/admin/',
                                 self.browser.current_url,
                                 'login successful')

    def get_user_modules(self, user, app):
        self.login(user)

        self.browser.get(self.live_server_url + '/admin')

        return {
            module.find_element_by_tag_name('caption').text.strip().lower(): [
                header.text.lower()
                for header in module.find_elements_by_css_selector('th')
            ]
            for module in self.browser.find_elements_by_css_selector(
                    '.module[class^=app-]'
            )
        }

    def test_user_memberships(self):
        with self.subTest('UserA'):
            self.assertTrue(self.users['UserA'].rights.exists())
            self.assertEquals(
                (self.users['UserA'].rights.all()
                 .values_list('municipality__name').get()),
                ('City A',),
            )

        with self.subTest('UserB'):
            self.assertTrue(self.users['UserB'].rights.exists())
            self.assertEquals(
                (self.users['UserB'].rights.all()
                 .values_list('municipality__name').get()),
                ('City B',),
            )

        self.assertFalse(self.users['UserC'].rights.exists())

    def test_module_list(self):
        user_modules = {
            'root': {
                'greenlandic address reference register': [
                    'addresses',
                    'b-numbers',
                    'roads',
                    'districts',
                    'localities',
                    'municipalities',
                    'postal codes',
                    'states',
                ],
                'authentication and authorization': [
                    'users',
                    'municipality rights',
                ],
            },

            'UserA': {
                'greenlandic address reference register': [
                    'addresses',
                    'b-numbers',
                    'roads',
                ],
            },
            'UserB': {
                'greenlandic address reference register': [
                    'addresses',
                    'b-numbers',
                    'roads',
                ],
            },
            'UserC': {},
        }

        for user, modules in user_modules.items():
            with self.subTest(user):
                self.assertEquals(
                    modules,
                    self.get_user_modules(user, 'addrreg'),
                )

    def test_create_superuser(self):
        # XXX: Potentiel D/E fejl, grundet manglede informations indtastning
        self.login('root')

        url = self.live_server_url + '/admin/auth/user/add/'
        self.browser.get(url)
        username = 'Suppe.Urt@styrelsen.gl'
        password = 'temmelighemmelig'

        self.fill_in_form(username=username,
                          password1=password,
                          password2=password,
                          is_staff=True,
                          is_superuser=True)
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')
        user = self.user_model.objects.get(username=username)
        self.assertEqual(user.username, username)
        # NOTE: Email cannot be set with the current form, it has to be done
        #       via. editing
        # self.assertEqual(user.email, email)

    def test_create_user(self):
        # XXX: Potentiel D/E fejl, grundet manglede informations indtastning
        self.login('root')

        url = self.live_server_url + '/admin/auth/user/add/'
        self.browser.get(url)
        username = 'Karl.Toffelsen@kommunen.gl'
        password = 'Kartoffel'

        self.fill_in_form(username=username,
                          password1=password,
                          password2=password,
                          is_staff=True,
                          is_superuser=False)
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')
        user = self.user_model.objects.get(username=username)
        self.assertEqual(user.username, username)
        # NOTE: Email, first_name and last_name cannot be set with the current
        #       form, it has to be done via. editing
        # self.assertEqual(user.email, email)
        # self.assertEqual(user.first_name, first_name)
        # self.assertEqual(user.last_name, last_name)
        url = self.live_server_url + '/admin/addrreg/municipalityrights/add/'
        self.browser.get(url)

        # We need to find the key to the 'user' element in the form.
        # We cannot simply use 'id_users_{{user.pk}}' as the HTML IDs are for
        # the many-to-many table?
        parent_element = self.browser.find_element_by_id("id_users")
        filtered_children = parent_element.find_elements_by_xpath(
            '//input[@value="' + str(user.pk) + '"]'
        )
        self.assertEqual(len(filtered_children), 1)
        users_id = filtered_children[0].get_attribute('id').lstrip('id_')

        mun = models.Municipality.objects.get(name='City A')
        # Remove old rights objects
        self.assertEqual(models.MunicipalityRights.objects.count(), 2)
        models.MunicipalityRights.objects.get(municipality=mun).delete()
        self.assertEqual(models.MunicipalityRights.objects.count(), 1)
        # Fill in the form, and generate one
        self.fill_in_form(**{'municipality': 'City A',
                             users_id: True})
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')
        self.assertEqual(models.MunicipalityRights.objects.count(), 2)
        # Check it
        rights = models.MunicipalityRights.objects.get(municipality=mun)
        self.assertIn(user, rights.users.all())

    def element_text(self, elem_id):
        return self.browser.find_element_by_id(elem_id).text.strip().lower()

    def test_frontpage(self):
        usernames = ['root', 'UserA', 'UserB', 'UserC']

        for username in usernames:
            with self.subTest(username):
                self.login(username)
                self.browser.get(self.live_server_url + '/admin')

                title = self.element_text('site-name')
                self.assertIn('greenlandic address reference register',
                              title)

                user_tools = self.element_text('user-tools')
                self.assertIn("welcome", user_tools)
                self.assertIn(username.lower(), user_tools)
                self.assertIn("change password", user_tools)
                self.assertIn("log out", user_tools)

        # Content for root, UserA and UserB is covered by test_module_list
        with self.subTest('UserC'):
            self.login('UserC')
            self.browser.get(self.live_server_url + '/admin')

            content = self.element_text('content-main')
            self.assertIn("you don't have permission to edit anything.",
                          content)

    def test_user_change_password(self):
        self.login('UserA')

        url = self.live_server_url + '/admin/password_change/'
        self.browser.get(url)

        bad_password = '1234567890'
        new_password = 'Kartoffel12'
        self.fill_in_form(old_password='password',
                          new_password1=bad_password,
                          new_password2=bad_password)
        self.assertEquals(url, self.browser.current_url,
                          'updated using bad password')

        self.fill_in_form(old_password='password',
                          new_password1=bad_password,
                          new_password2=new_password)
        self.assertEquals(url, self.browser.current_url,
                          'updated using mismatched passwords')

        self.fill_in_form(old_password='pazzw0rd',
                          new_password1=bad_password,
                          new_password2=new_password)
        self.assertEquals(url, self.browser.current_url,
                          'updated using invalid old password')

        self.fill_in_form(old_password='password',
                          new_password1=new_password,
                          new_password2=new_password)
        self.assertNotEquals(url, self.browser.current_url,
                             'did not update password')
        self.assertEqual(self.browser.current_url,
                         self.live_server_url + '/admin/password_change/done/')

        # Log out, and try to log in using new password
        self.login('UserA', new_password)

    def test_admin_change_password(self):
        # UserA wants a new password
        username = 'UserA'
        email = username + '@example.com'
        new_password = 'Kartoffel12'
        user = self.user_model.objects.get(username=username)

        # Root will change it
        self.login('root')

        url = self.live_server_url + '/admin/auth/user/'
        self.browser.get(url)

        # Search for the email
        searchbar = self.browser.find_element_by_id("searchbar")
        searchbar.send_keys(email)
        searchbar.submit()
        self.await_staleness(searchbar)

        # Pick the first (and only) result, then click it
        results = self.browser.find_element_by_id('result_list')\
                              .find_element_by_tag_name('tbody')\
                              .find_elements_by_class_name("field-username")
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.text, username)
        link = result.find_element_by_tag_name('a')
        link.click()
        self.await_staleness(link)

        # wait for next page load
        self.assertIn(
            '/admin/auth/user/' + str(user.pk) + '/change/',
            self.browser.current_url,
        )

        # Go to password reset page
        password_link = self.browser.find_element_by_id('id_password')\
                                    .find_element_by_xpath('..')\
                                    .find_element_by_class_name("help")\
                                    .find_element_by_tag_name("a")
        password_link.click()
        self.await_staleness(password_link)
        self.assertIn(
            '/admin/auth/user/' + str(user.pk) + '/password/',
            self.browser.current_url,
        )

        # Fill it in
        saved_url = self.browser.current_url
        self.fill_in_form(password1=new_password,
                          password2=new_password)
        self.assertNotEquals(saved_url, self.browser.current_url,
                             'password update failed')

        # Log out, and try to log in using new password
        self.login(username, new_password)

    def test_admin_set_user_inactive(self):
        # UserA has to be set inactive
        username = 'UserA'
        email = username + '@example.com'
        new_password = 'Kartoffel12'
        user = self.user_model.objects.get(username=username)

        # Root will change it
        self.login('root')

        url = self.live_server_url + '/admin/auth/user/'
        self.browser.get(url)

        # Search for the email
        searchbar = self.browser.find_element_by_id("searchbar")
        searchbar.send_keys(email)
        searchbar.submit()
        self.await_staleness(searchbar)

        # Pick the first (and only) result, then click it
        results = self.browser.find_element_by_id('result_list')\
                              .find_element_by_tag_name('tbody')\
                              .find_elements_by_class_name("field-username")
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.text, username)
        link = result.find_element_by_tag_name('a')
        link.click()
        self.await_staleness(link)

        # wait for next page load
        self.assertIn(
            '/admin/auth/user/' + str(user.pk) + '/change/',
            self.browser.current_url,
        )

        # Fill it in
        saved_url = self.browser.current_url
        self.fill_in_form(is_active=False)
        self.assertNotEquals(saved_url, self.browser.current_url,
                             'is_active update failed')

        # Log out, and try to log in using new password
        # We expect a login failure
        self.login(username, new_password, False)

    def test_state_change(self):
        self.login('root')

        bad_state = models.State.objects.get(name='Bad')

        url = (self.live_server_url +
               '/admin/addrreg/state/' + str(bad_state.pk) + '/change/')

        # Test setting name
        self.browser.get(url)
        self.fill_in_form(name="Horrible")
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')
        bad_state.refresh_from_db()
        self.assertEqual(bad_state.name, "Horrible")

        # Test setting code
        self.browser.get(url)
        self.fill_in_form(code=42)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')
        bad_state.refresh_from_db()
        self.assertEqual(bad_state.code, 42)

    def test_create_municipality(self):
        # Information has been provided
        mun_code = 42
        mun_name = 'Grove'
        mun_abbr = 'Gr'

        self.login('root')

        url = self.live_server_url + '/admin/addrreg/municipality/add/'
        self.browser.get(url)

        self.fill_in_form(**{'name': mun_name,
                             'abbrev': mun_abbr,
                             'code': mun_code,
                             'state_' + str(self.state.pk): True})
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')

        mun = models.Municipality.objects.get(name='Grove')
        self.assertEqual(mun.code, mun_code)
        self.assertEqual(mun.abbrev, mun_abbr)
        self.assertEqual(mun.state, self.state)

    def test_change_municipality(self):
        # Information has been provided
        mun_name = 'City A'
        mun = models.Municipality.objects.get(name=mun_name)

        mun_new_name = 'Grove'

        self.login('root')

        url = (self.live_server_url +
               '/admin/addrreg/municipality/' + str(mun.pk) + '/change/')

        self.browser.get(url)

        self.fill_in_form(name=mun_new_name)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        new_mun = models.Municipality.objects.get(name=mun_new_name)
        self.assertEqual(mun.pk, new_mun.pk)
        self.assertEqual(mun.code, new_mun.code)
        self.assertEqual(mun.abbrev, new_mun.abbrev)
        self.assertEqual(mun.state, new_mun.state)
        self.assertEqual(mun.sumiffiik, new_mun.sumiffiik)
        self.assertEqual(new_mun.name, mun_new_name)

    def test_remove_municipality(self):
        # Information has been provided
        mun_name = 'City A'
        mun = models.Municipality.objects.get(name=mun_name)

        self.login('root')

        url = (self.live_server_url +
               '/admin/addrreg/municipality/' + str(mun.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(mun.active, True)
        self.fill_in_form(active=False)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        mun.refresh_from_db()
        self.assertEqual(mun.active, False)

    def test_transfer_locality(self):
        # Information has been provided
        from_mun_name = 'City A'
        from_mun = models.Municipality.objects.get(name=from_mun_name)
        to_mun_name = 'City B'
        to_mun = models.Municipality.objects.get(name=to_mun_name)

        locality_name = 'LocationA0'
        locality = models.Locality.objects.get(name=locality_name)

        self.login('root')

        url = (self.live_server_url +
               '/admin/addrreg/locality/' + str(locality.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(locality.municipality, from_mun)
        self.fill_in_form(municipality=to_mun_name)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        locality.refresh_from_db()
        self.assertEqual(locality.municipality, to_mun)

    def test_transfer_road(self):
        # Setup test environment
        from_mun_name = 'City A'
        from_mun = models.Municipality.objects.get(name=from_mun_name)

        to_mun_name = 'City B'
        to_mun = models.Municipality.objects.get(name=to_mun_name)

        from_locality_name = 'LocationA0'
        from_locality = models.Locality.objects.get(name=from_locality_name)

        to_locality_name = 'LocationB0'
        to_locality = models.Locality.objects.get(name=to_locality_name)

        road = models.Road(
            municipality=from_mun,
            location=from_locality,
            state=self.state,
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H H Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            alternate_name='H. H. Seedorffs aqqusineq amitsoq',
            cpr_name='Hans Hartvig Seedorff\'s Street',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        road.save()

        self.login('UserAB')

        url = (self.live_server_url +
               '/admin/addrreg/road/' + str(road.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(road.location, from_locality)
        self.assertEqual(road.municipality, from_mun)
        self.fill_in_form(municipality=to_mun_name, location=to_locality_name)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        road.refresh_from_db()
        self.assertEqual(road.location, to_locality)
        self.assertEqual(road.municipality, to_mun)

        with self.subTest('events'):
            self.assertEquals(13, events.Event.objects.count())

            for event in events.Event.objects.all():
                # this can fail, but the output relies on time and UUIDs too
                # much to be testable
                event.format()

    def test_remove_locality(self):
        # Information has been provided
        locality_name = 'LocationA0'
        locality = models.Locality.objects.get(name=locality_name)

        self.login('root')

        url = (self.live_server_url +
               '/admin/addrreg/locality/' + str(locality.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(locality.active, True)
        self.assertEqual(locality.locality_state,
                         models.LocalityState.PROJECTED)
        self.fill_in_form(active=False, locality_state='Abandoned')
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        locality.refresh_from_db()
        self.assertEqual(locality.active, False)
        self.assertEqual(locality.locality_state,
                         models.LocalityState.ABANDONED)

    def test_create_postalcode(self):
        # Information has been provided
        postal_code = 8000
        postal_name = 'Aarhus'
        locality_name = 'LocationA0'
        locality = models.Locality.objects.get(name=locality_name)

        self.login('root')

        url = self.live_server_url + '/admin/addrreg/postalcode/add/'
        self.browser.get(url)

        self.fill_in_form(code=postal_code,
                          name=postal_name,
                          active=True)
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')

        postcode = models.PostalCode.objects.get(code=postal_code)
        self.assertEqual(postcode.name, postal_name)

        url = (self.live_server_url +
               '/admin/addrreg/locality/' + str(locality.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(locality.postal_code, None)
        self.fill_in_form(postal_code=(str(postal_code) + " " + postal_name))
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        locality.refresh_from_db()
        self.assertEqual(locality.postal_code, postcode)

    def test_admin_transfer_road(self):
        # Setup test environment
        from_mun_name = 'City A'
        from_mun = models.Municipality.objects.get(name=from_mun_name)

        to_mun_name = 'City B'
        to_mun = models.Municipality.objects.get(name=to_mun_name)

        from_locality_name = 'LocationA0'
        from_locality = models.Locality.objects.get(name=from_locality_name)

        to_locality_name = 'LocationB0'
        to_locality = models.Locality.objects.get(name=to_locality_name)

        road = models.Road(
            municipality=from_mun,
            location=from_locality,
            state=self.state,
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H H Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            alternate_name='H. H. Seedorffs aqqusineq amitsoq',
            cpr_name='Hans Hartvig Seedorff\'s Street',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        road.save()

        self.login('root')

        url = (self.live_server_url +
               '/admin/addrreg/road/' + str(road.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(road.municipality, from_mun)
        self.fill_in_form(municipality=to_mun_name, location=to_locality_name)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        road.refresh_from_db()
        self.assertEqual(road.location, to_locality)
        self.assertEqual(road.municipality, to_mun)

    def test_create_road(self):
        # Information has been provided
        road_name = 'TheRoad'
        road_code = 42

        locality_name = 'LocationA0'
        locality = models.Locality.objects.get(name=locality_name)

        self.login('UserA')

        url = self.live_server_url + '/admin/addrreg/road/add/'
        self.browser.get(url)
        self.fill_in_form(name=road_name,
                          code=road_code,
                          location=locality_name)
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')
        road = models.Road.objects.get(code=road_code)
        self.assertEqual(road.name, road_name)
        self.assertEqual(road.location, locality)

    def test_create_b_number(self):
        # Information has been provided
        bnumber_callname = 'The rabbithole'
        bnumber_code = 42
        bnumber_type = 'BS221B'

        locality_name = 'LocationA0'
        locality = models.Locality.objects.get(name=locality_name)

        mun_name = 'City A'
        mun = models.Municipality.objects.get(name=mun_name)

        self.login('UserA')

        url = self.live_server_url + '/admin/addrreg/bnumber/add/'
        self.browser.get(url)
        self.fill_in_form(b_callname=bnumber_callname,
                          code=bnumber_code,
                          b_type=bnumber_type,
                          location=locality_name)
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')
        bnum = models.BNumber.objects.get(code=bnumber_code)
        self.assertEqual(bnum.b_callname, bnumber_callname)
        self.assertEqual(bnum.b_type, bnumber_type)
        self.assertEqual(bnum.location, locality)
        self.assertEqual(bnum.municipality, mun)

    def test_create_address(self):
        # Information has been provided
        house_number = '13'
        house_floor = '1'
        house_room = 'mf'

        locality_name = 'LocationA0'
        locality = models.Locality.objects.get(name=locality_name)

        mun_name = 'City A'
        mun = models.Municipality.objects.get(name=mun_name)

        bnum = models.BNumber(
            municipality=mun,
            location=locality,
            state=self.state,
            code='42',
            b_callname='The Block',
            b_type='BS221B',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        bnum.save()

        road_name = 'Hans Hartvig Seedorffs Stræde'
        road_code = 1337
        road = models.Road(
            municipality=mun,
            location=locality,
            state=self.state,
            code=road_code,
            name=road_name,
            shortname='H H Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            alternate_name='H. H. Seedorffs aqqusineq amitsoq',
            cpr_name='Hans Hartvig Seedorff\'s Street',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        road.save()

        self.login('UserA')

        url = self.live_server_url + '/admin/addrreg/address/add/'
        self.browser.get(url)
        self.fill_in_form(road=(road_name + " (" + str(road_code) + ")"),
                          house_number=house_number,
                          floor=house_floor,
                          room=house_room,
                          b_number=str(bnum.pk))
        self.assertNotEquals(url, self.browser.current_url, 'addition failed')
        addr = models.Address.objects.get(b_number=bnum)
        self.assertEqual(addr.house_number, house_number)
        self.assertEqual(addr.floor, house_floor)
        self.assertEqual(addr.room, house_room)
        self.assertEqual(addr.road, road)
        self.assertEqual(addr.municipality, mun)

    def test_transfer_road_same_municipality(self):
        # Setup test environment
        from_mun_name = 'City A'
        from_mun = models.Municipality.objects.get(name=from_mun_name)

        from_locality_name = 'LocationA0'
        from_locality = models.Locality.objects.get(name=from_locality_name)

        to_locality_name = 'LocationA1'
        to_locality = models.Locality.objects.get(name=to_locality_name)

        road = models.Road(
            municipality=from_mun,
            location=from_locality,
            state=self.state,
            code=1337,
            name='Hans Hartvig Seedorffs Stræde',
            shortname='H H Seedorffs Stræde',
            # this translation is quite likely horribly wrong
            alternate_name='H. H. Seedorffs aqqusineq amitsoq',
            cpr_name='Hans Hartvig Seedorff\'s Street',
            sumiffiik_domain=DUMMY_DOMAIN,
        )
        road.save()

        self.login('UserA')

        url = (self.live_server_url +
               '/admin/addrreg/road/' + str(road.pk) + '/change/')

        self.browser.get(url)

        self.assertEqual(road.location, from_locality)
        self.fill_in_form(location=to_locality_name)
        self.assertNotEquals(url, self.browser.current_url,
                             'modification failed')

        road.refresh_from_db()
        self.assertEqual(road.location, to_locality)
