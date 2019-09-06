History
-------

Pending Release
---------------

.. Insert new release notes below this line

* Improve instrumentation to avoid interfering with other monkey patches on
  ``Template.render()``
  (`Commit a961216 <https://github.com/node13h/django-debug-toolbar-template-profiler/commit/a96121620d48c0d8f2c8b4e6eaf18eb265a5b48e>`__).
* Prevent installation with django-debug-toolbar 2.0+ since the panel is not
  currently compatible
  (`Commit f0b8b50 <https://github.com/node13h/django-debug-toolbar-template-profiler/commit/f0b8b50da92e160fcf878c4deabb598b2e901dd3>`__).
* Instrument Jinja2 templates
  (`PR #5 <https://github.com/node13h/django-debug-toolbar-template-profiler/pull/5>`__).
* Skip templates as configured in django-debug-toolbar's
  ``SKIP_TEMPLATE_PREFIXES`` setting
  (`PR #11 <https://github.com/node13h/django-debug-toolbar-template-profiler/pull/11>`__).

1.0.2 (2017-05-03)
------------------

* Add Python 3 trove classifier
  (`PR #4 <https://github.com/node13h/django-debug-toolbar-template-profiler/pull/4>`__).
* Fix GitHub URL
  (`PR #2 <https://github.com/node13h/django-debug-toolbar-template-profiler/pull/2>`__).

Prior history can be seen on the `GitHub master
history <https://github.com/node13h/django-debug-toolbar-template-profiler/commits/master>`__.
