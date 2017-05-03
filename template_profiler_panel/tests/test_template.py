# coding: utf-8

from __future__ import absolute_import
import unittest
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'template_profiler_panel.tests.dummy_settings'

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from django.core.wsgi import get_wsgi_application
from django.template import Context, Template

from template_profiler_panel.panels.template import TemplateProfilerPanel, template_rendered


class TemplateProfilerPanelTestCase(unittest.TestCase):
    def setUp(self):
        super(TemplateProfilerPanelTestCase, self).setUp()
        self.panel = TemplateProfilerPanel(MagicMock())
        self.panel.record_stats = MagicMock()
        self.template_rendered_receiver = MagicMock()
        self.request = MagicMock()
        self.response = MagicMock()
        template_rendered.connect(self.template_rendered_receiver)

    def tearDown(self):
        template_rendered.disconnect(self.template_rendered_receiver)

    def test_render_wrapped(self):
        t = Template('')
        t.render(Context({}))

        self.assertGreater(self.template_rendered_receiver.call_count, 0)

    def test_process_response_disabled_instrumentation(self):
        t = Template('')
        t.render(Context({}))

        self.panel.process_response(self.request, self.response)

        args = self.panel.record_stats.call_args[0][0]
        self.assertEqual(len(args['templates']), 0)
        self.assertEqual(len(args['summary']), 0)

    def test_process_response_enabled_instrumentation(self):
        self.panel.enable_instrumentation()

        t = Template('')
        t.render(Context({}))

        self.panel.process_response(self.request, self.response)
        self.panel.disable_instrumentation()

        args = self.panel.record_stats.call_args[0][0]
        self.assertEqual(len(args['templates']), 1)
        self.assertEqual(len(args['summary']), 1)

    def test_title(self):
        self.assertTrue(self.panel.title)

    def test_template(self):
        self.assertTrue(self.panel.template)


if __name__ == '__main__':
    application = get_wsgi_application()
    unittest.main()

