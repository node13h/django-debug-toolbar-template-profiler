from setuptools import setup, find_packages
from io import open

setup(
    name='django-debug-toolbar-template-profiler',
    version='2.0.2',
    description='Displays template rendering time on the timeline',
    long_description=open('README.rst', encoding='utf-8').read(),
    long_description_content_type="text/x-rst",
    author='Sergej Alikov',
    author_email='sergej.alikov@gmail.com',
    maintainer='Adam Johnson',
    maintainer_email='me@adamj.eu',
    url='https://github.com/node13h/django-debug-toolbar-template-profiler',
    project_urls={
        "Changelog": "https://github.com/node13h/django-debug-toolbar-template-profiler/blob/master/HISTORY.rst"
    },
    license='Simplified BSD License',
    packages=find_packages(),
    install_requires=[
        'django-debug-toolbar>=2.0',
        'wrapt',
    ],
    include_package_data=True,
    zip_safe=False,                 # because we're including static files
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
