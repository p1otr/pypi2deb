#! /usr/bin/make -f

export PYBUILD_NAME={{src_name}}
{%- for key, value in exports.items() | sort %}
export {{key}}={{value}}{% endfor %}
%:
	dh $@ --with {{with}} --buildsystem=pybuild
{%- if docs and docs.sphinx_dir %}

override_dh_auto_build:
	dh_auto_build
	cd {{docs.sphinx_dir}} && \
	PYTHONPATH=$(CURDIR) http_proxy= https_proxy= \
	sphinx-build -N -E -T -b html . $(CURDIR)/.pybuild/docs/html/
	rm -rf $(CURDIR)/.pybuild/docs/html/.doctrees
{% endif %}
