from django.dispatch import Signal

template_rendered = Signal(providing_args=['instance', 'start', 'end', 'level'])
