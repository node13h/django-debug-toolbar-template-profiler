======================================
django-debug-toolbar-template-profiler
======================================

.. image:: https://img.shields.io/pypi/v/django-debug-toolbar-template-profiler.svg
       :target: https://pypi.python.org/pypi/django-debug-toolbar-template-profiler

An extra panel for
`django-debug-toolbar <https://django-debug-toolbar.readthedocs.io>`__
that displays time spent rendering each template.

For example:

.. image:: https://raw.githubusercontent.com/node13h/django-debug-toolbar-template-profiler/master/screenshot.png

Installation
============

First, you'll need to install and configure django-debug-toolbar as per its
`installation instructions
<https://django-debug-toolbar.readthedocs.io/en/latest/installation.html>`__.

Second, install this package:

.. code-block:: sh

    pip install django-debug-toolbar-template-profiler

Third, add it to your installed apps - order doesn't matter but after
`debug_toolbar` will keep it neatly grouped:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "debug_toolbar",
        "template_profiler_panel",
        # ...
    ]

Fourth, configure django-debug-toolbar's ``DEBUG_TOOLBAR_PANELS`` setting
`as per its documentation
<https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-panels>`__
to include the panel. You'll need to copy the default and add the panel at the
end:

.. code-block:: python

    DEBUG_TOOLBAR_PANELS = [
        # ...
        "template_profiler_panel.panels.template.TemplateProfilerPanel",
    ]

After this, you should see the "Template Profiler" panel when you load the
toolbar. Both Django and Jinja2 template ``render()`` calls will be measured.
