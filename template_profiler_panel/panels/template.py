import inspect
from collections import defaultdict
from time import time

import wrapt
from debug_toolbar.panels import Panel
from debug_toolbar.panels.sql.utils import contrasting_color_generator
import django
from django.dispatch import Signal

if django.VERSION < (3, 2):
    from django.utils.translation import ugettext_lazy as _
else:
    from django.utils.translation import gettext_lazy as _
   
if django.VERSION < (3, 1):
    template_rendered = Signal(providing_args=[
        'instance', 'start', 'end', 'level', 'processing_timeline',
    ])
else:
    template_rendered = Signal()

node_element_colors = {}


def get_nodelist_timeline(nodelist, level):
    timeline = []
    for node in nodelist:
        timeline += get_node_timeline(node, level)
    return timeline


def get_node_timeline(node, level):
    """
    Get timeline for node and it's children
    """
    timeline = []
    child_nodelists = getattr(node, "child_nodelists", None)
    if child_nodelists:
        for child_nodelist_str in child_nodelists:
            child_nodelist = getattr(node, child_nodelist_str, None)
            if child_nodelist:
                timeline += get_nodelist_timeline(child_nodelist, level + 1)

    if hasattr(node, "_node_end"):
        timeline.append(
            {
                "node": node,
                "name": node,
                "start": node._node_start,
                "end": node._node_end,
                "level": level,
            },
        )
    return timeline


class TemplateProfilerPanel(Panel):
    '''
    Displays template rendering times on the request timeline
    '''

    template = 'template_profiler_panel/template.html'
    scripts = ["static/js/template_profiler.js"]

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

        from django.template import Node as DjangoNode
        node_classes = [DjangoNode]

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

            timeline = []
            if hasattr(instance, 'nodelist'):
                timeline = get_nodelist_timeline(instance.nodelist, 0)

            template_rendered.send(
                sender=instance.__class__,
                instance=instance,
                start=start,
                end=end,
                processing_timeline=timeline,
                level=stack_depth,
            )
            return result

        for template_class in template_classes:
            template_class.render = render_wrapper(template_class.render)

        @wrapt.decorator
        def render_node_wrapper(wrapped, instance, args, kwargs):
            instance._node_start = time()
            result = wrapped(*args, **kwargs)
            instance._node_end = time()
            return result

        for node_class in node_classes:
            node_class.render_annotated = render_node_wrapper(
                node_class.render_annotated)

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

    def record(self, instance, start, end, level,
               processing_timeline, **kwargs):
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
            'processing_timeline': processing_timeline,
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

    def _calc_timeline(self, start, end, processing_timeline):
        result = {}
        result['offset_p'] = self._calc_p(
            start - self.t_min, self.t_max - self.t_min)

        result['duration_p'] = self._calc_p(
            end - start, self.t_max - self.t_min)

        result['rel_duration_p'] = self._calc_p(
            result['duration_p'], 100 - result['offset_p'])

        result['relative_start'] = (start - self.t_min) * 1000.0
        result['relative_end'] = (end - self.t_min) * 1000.0

        result['processing_timeline'] = []
        max_level = 0
        for time_item in processing_timeline:
            if 'node' in time_item:
                class_name = time_item['node'].__class__.__name__
            else:
                class_name = time_item['type']
            if class_name not in node_element_colors:
                node_element_colors[class_name] = next(self.color_generator)
            bg_color = node_element_colors[class_name]
            if 'node' in time_item:
                position = time_item['node'].token.position
            else:
                position = False
            level = time_item['level'] if 'level' in time_item else 0
            if level > max_level:
                max_level = level
            result['processing_timeline'].append({
                'name': time_item['name'],
                'position': position,
                'relative_start': (time_item['start'] - self.t_min) * 1000.0,
                'relative_end': (time_item['end'] - self.t_min) * 1000.0,
                'duration': (time_item['end'] - time_item['start']) * 1000.0,
                'rel_duration_p': self._calc_p(
                    time_item['end'] - time_item['start'],
                    self.t_max - self.t_min),
                'offset_p': self._calc_p(
                    time_item['start']-self.t_min,
                    self.t_max - self.t_min),
                'bg_color': bg_color,
                'level': level,
            })
        result['max_level'] = max_level

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
                self._calc_timeline(
                    template['start'], template['end'],
                    template['processing_timeline']))

        self.total = len(self.templates)

        self.record_stats(
            {'templates': sorted(self.templates, key=lambda d: d['start']),
             'summary': sorted(summary.items(), key=lambda t: -t[1])})

        return response
