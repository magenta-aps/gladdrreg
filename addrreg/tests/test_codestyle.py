# -*- mode: python; coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

import contextlib
import io
import os

import pycodestyle

from django import test
from django.test import tag


class CodeStyleTests(test.SimpleTestCase):

    @property
    def rootdir(self):
        return os.path.dirname(os.path.dirname(__file__))

    @property
    def source_files(self):
        """Generator that yields Python sources to test"""

        for dirpath, dirs, fns in os.walk(self.rootdir):
            dirs[:] = [
                dn for dn in dirs
                if dn != 'migrations' and not dn.startswith('venv-')
            ]

            for fn in fns:
                if fn[0] != '.' and fn.endswith('.py'):
                    yield os.path.join(dirpath, fn)

    @tag('pep8')
    def test_pep8(self):
        pep8style = pycodestyle.StyleGuide()
        pep8style.init_report(pycodestyle.StandardReport)

        buf = io.StringIO()

        with contextlib.redirect_stdout(buf):
            for fn in self.source_files:
                pep8style.check_files([fn])

        assert not buf.getvalue(), \
            "Found code style errors and/or warnings:\n\n" + buf.getvalue()

    def test_source_files(self):
        sources = list(self.source_files)
        self.assert_(sources)
        self.assertGreater(len(sources), 1, sources)
