import inspect
from collections import defaultdict
from time import time

import wrapt
from django.dispatch import Signal
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.panels.sql.utils import contrasting_color_generator


template_rendered = Signal(providing_args=['instance', 'start', 'end', 'level'])


class TemplateProfilerPanel(Panel):
    '''
    Displays template rendering times on the request timeline
    '''

    template = 'template_profiler_panel/template.html'

    def __init__(self, *args, **kwargs):
        self.colors = {}
        self.templates = []
        self.color_generator = contrasting_color_generator()
        self.t_min = 0
        self.t_max = 0
        self.total = 0
        self.monkey_patch_template_classes()
        self.is_enabled = False
        template_rendered.connect(self.record)
        super(TemplateProfilerPanel, self).__init__(*args, **kwargs)

    have_monkey_patched_template_classes = False

    @classmethod
    def monkey_patch_template_classes(cls):
        if cls.have_monkey_patched_template_classes:
            return

        from django.template import Template as DjangoTemplate
        template_classes = [DjangoTemplate]

        try:
            from jinja2 import Template as Jinja2Template
        except ImportError:
            pass
        else:
            template_classes.append(Jinja2Template)

        @wrapt.decorator
        def render_wrapper(wrapped, instance, args, kwargs):
            start = time()
            result = wrapped(*args, **kwargs)
            end = time()

            stack_depth = 1
            current_frame = inspect.currentframe()
            while True:
                current_frame = current_frame.f_back
                if current_frame is None:
                    break
                stack_depth += 1

            template_rendered.send(
                sender=instance.__class__,
                instance=instance,
                start=start,
                end=end,
                level=stack_depth,
            )
            return result

        for template_class in template_classes:
            template_class.render = render_wrapper(template_class.render)

        cls.have_monkey_patched_template_classes = True

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

    def record(self, instance, start, end, level, **kwargs):
        if not self.enabled:
            return

        template_name = instance.name
        # Logic copied from django-debug-toolbar:
        # https://github.com/jazzband/django-debug-toolbar/blob/5d095f66fde8f10b45a93c0b35be0a85762b0458/debug_toolbar/panels/templates/panel.py#L77
        is_skipped_template = isinstance(template_name, str) and (
            template_name.startswith("debug_toolbar/")
            or template_name.startswith(
                tuple(self.toolbar.config["SKIP_TEMPLATE_PREFIXES"])
            )
        )
        if is_skipped_template:
            return

        bg = self._get_color(level)
        text = '#ffffff' if int(bg[1:], 16) < 0x8fffff else '#000000'
        color = {'bg': bg, 'text': text}

        self.templates.append({
            'start': start,
            'end': end,
            'time': (end - start) * 1000.0,
            'level': level,
            'name': template_name,
            'color': color,
        })

    def enable_instrumentation(self):
        self.is_enabled = True

    def disable_instrumentation(self):
        self.is_enabled = False

    def _calc_p(self, part, whole):
        # return the percentage of part or 100% if whole is zero
        return (part / whole) * 100.0 if whole else 100.0

    def _calc_timeline(self, start, end):
        result = {}
        result['offset_p'] = self._calc_p(
            start - self.t_min, self.t_max - self.t_min)

        result['duration_p'] = self._calc_p(
            end - start, self.t_max - self.t_min)

        result['rel_duration_p'] = self._calc_p(
            result['duration_p'], 100 - result['offset_p'])

        return result

    def process_request(self, request):
        response = super(TemplateProfilerPanel, self).process_request(request)

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

        return response
