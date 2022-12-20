Source: {{src_name}}
Section: python
Priority: optional
Maintainer: {{maintainer}}
{%- if uploaders %}
Uploaders: {{uploaders}}{% endif %}
Build-Depends: debhelper-compat (= 13),
               dh-python,
{%- for dependency in build_depends|sort %}
               {{dependency}},{% endfor %}
Standards-Version: 4.6.1.0
Testsuite: autopkgtest-pkg-pybuild
{%- if homepage %}
Homepage: {{homepage}}{% endif %}
{%- if vcs_name and vcs_src %}
Vcs-{{vcs_name}}: {{vcs_src}}{% endif %}
{%- if vcs_browser %}
Vcs-Browser: {{vcs_browser}}{% endif %}
Rules-Requires-Root: no
{%- if 'python3' in interpreters %}

Package: python3-{{src_name}}
Architecture: {{binary_arch}}
Depends: ${misc:Depends}, ${python3:Depends},{% if binary_arch == 'any' %} ${shlibs:Depends},{% endif %}
{%- for dependency in python3_depends %}
         {{dependency}},{% endfor %}
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
Depends: ${misc:Depends}, ${sphinxdoc:Depends}
Description: documentation for the {{name}} Python library
 This package provides documentation for {{name}} {% endif %}
