from time import time
from collections import defaultdict
from inspect import stack

from django.dispatch import Signal
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.panels.sql.utils import contrasting_color_generator

from django.template import Template as DjangoTemplate

try:
    jinja_import = True
    from jinja2 import Template as JinjaTemplate
except ImportError:
    jinja_import = False

template_rendered = Signal(
    providing_args=['instance', 'start', 'end', 'level'])


def template_render_wrapper_django(self, context):
    t_start = time()
    result = DjangoTemplate.tp_saved_render(self, context)
    t_end = time()

    template_rendered.send(
        sender=DjangoTemplate, instance=self, start=t_start, end=t_end,
        level=len(stack()))

    return result


def template_render_wrapper_jinja(self, context):
    t_start = time()
    result = JinjaTemplate.tp_saved_render(self, context)
    t_end = time()

    template_rendered.send(
        sender=JinjaTemplate, instance=self, start=t_start, end=t_end,
        level=len(stack()))

    return result


DjangoTemplate.engine = DjangoTemplate
DjangoTemplate.tp_saved_render = DjangoTemplate.render
DjangoTemplate.render = template_render_wrapper_django

if jinja_import:
    JinjaTemplate.engine = JinjaTemplate
    JinjaTemplate.tp_saved_render = JinjaTemplate.render
    JinjaTemplate.render = template_render_wrapper_jinja


class TemplateProfilerPanel(Panel):
    '''
    Displays template rendering times on the request timeline
    '''

    template = 'template_profiler_panel/template.html'
    colors = None
    templates = None
    color_generator = None
    t_min = 0
    t_max = 0
    total = 0

    def __init__(self, *args, **kwargs):
        self.colors = {}
        self.templates = []
        self.color_generator = contrasting_color_generator()
        super(TemplateProfilerPanel, self).__init__(*args, **kwargs)

    @property
    def nav_title(self):
        return _('Template Profiler')

    @property
    def nav_subtitle(self):
        return _('{} calls in {:.2f} ms').format(
            self.total, (self.t_max - self.t_min) * 1000.0)

    @property
    def title(self):
        return _('Template Rendering Time')

    def _get_color(self, level):
        return self.colors.setdefault(level, next(self.color_generator))

    def record(self, sender, instance, start, end, level, **kwargs):

        bg = self._get_color(level)
        text = '#ffffff' if int(bg[1:], 16) < 0x8fffff else '#000000'
        color = {'bg': bg, 'text': text}

        self.templates.append({
            'start': start,
            'end': end,
            'time': (end - start) * 1000.0,
            'level': level,
            'name': instance.name,
            'color': color,
        })

    def enable_instrumentation(self):
        template_rendered.connect(self.record)

    def disable_instrumentation(self):
        template_rendered.disconnect(self.record)

    def _calc_p(self, part, whole):
        return (part / whole) * 100.0

    def _calc_timeline(self, start, end):
        result = {}
        result['offset_p'] = self._calc_p(
            start - self.t_min, self.t_max - self.t_min)

        result['duration_p'] = self._calc_p(
            end - start, self.t_max - self.t_min)

        result['rel_duration_p'] = self._calc_p(
            result['duration_p'], 100 - result['offset_p'])

        return result

    def process_response(self, request, response):
        summary = defaultdict(float)

        # Collect stats
        for template in self.templates:
            if self.t_min == 0:
                self.t_min = template['start']
            elif template['start'] < self.t_min:
                self.t_min = template['start']

            if template['end'] > self.t_max:
                self.t_max = template['end']

            summary[template['name']] += template['time']

        # Calc timelines
        for template in self.templates:
            template.update(
                self._calc_timeline(template['start'], template['end']))

        self.total = len(self.templates)

        self.record_stats(
            {'templates': sorted(self.templates, key=lambda d: d['start']),
             'summary': sorted(summary.items(), key=lambda t: -t[1])})
