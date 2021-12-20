import django
if django.VERSION < (4, 0):
    default_app_config = "template_profiler_panel.apps.TemplateProfilerPanelAppConfig"
