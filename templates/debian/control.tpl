Source: {{src_name}}
Section: python
Priority: optional
Maintainer: {{maintainer}}
{%- if uploaders %}
Uploaders: {{uploaders}}{% endif %}
Build-Depends: debhelper (>= 9), dh-python,
{%- for dependency in build_depends|sort %}
               {{dependency}},{% endfor %}
Standards-Version: 4.0.0
{%- if homepage %}
Homepage: {{homepage}}{% endif %}
{%- if vcs_name and vcs_src %}
Vcs-{{vcs_name}}: {{vcs_src}}{% endif %}
{%- if vcs_browser %}
Vcs-Browser: {{vcs_browser}}{% endif %}
{%- if 'python' in interpreters %}

Package: python-{{src_name}}
Architecture: {{binary_arch}}
Depends: ${misc:Depends}, ${python:Depends},{% if binary_arch == 'any' %} ${shlibs:Depends},{% endif %}
{%- for dependency in python2_depends %}
         {{dependency}},{% endfor %}
Recommends: ${python:Recommends}
Suggests: ${python:Suggests}
Description: {{short_desc}} - Python 2.X
{{long_desc}}{% endif %}
{%- if 'python3' in interpreters %}

Package: python3-{{src_name}}
Architecture: {{binary_arch}}
Depends: ${misc:Depends}, ${python3:Depends},{% if binary_arch == 'any' %} ${shlibs:Depends},{% endif %}
{%- for dependency in python3_depends %}
         {{dependency}},{% endfor %}
Recommends: ${python3:Recommends}
Suggests: ${python3:Suggests}
Description: {{short_desc}}
{{long_desc}}{% endif %}
{%- if 'pypy' in interpreters %}

Package: pypy-{{src_name}}
Architecture: {{binary_arch}}
Depends: ${misc:Depends}, ${pypy:Depends},{% if binary_arch == 'any' %} ${shlibs:Depends},{% endif %}
{%- for dependency in pypy2_depends %}
           {{dependency}},{% endfor %}
Recommends: ${pypy:Recommends}
Suggests: ${pypy:Suggests}
Description: {{short_desc}}
{{long_desc}}{% endif %}
{%- if docs and 'sphinx_dir' in docs %}

Package: python-{{src_name}}-doc
Section: doc
Architecture: all
Priority: extra
Depends: ${misc:Depends}, ${sphinxdoc:Depends}
Description: documentation for the {{name}} Python library
 This package provides documentation for {{name}} {% endif %}
