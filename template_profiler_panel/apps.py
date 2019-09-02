import inspect
from time import time

import wrapt
from django.apps import AppConfig

from template_profiler_panel.signals import template_rendered


class TemplateProfilerPanelAppConfig(AppConfig):
    name = "template_profiler_panel"
    verbose_name = "Debug Toolbar Template Profiler Panel"

    def ready(self):
        self.monkey_patch_template_classes()

    def monkey_patch_template_classes(self):
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
