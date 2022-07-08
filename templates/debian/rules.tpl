#! /usr/bin/make -f

export PYBUILD_NAME={{src_name}}
{%- for key, value in exports.items() | sort %}
export {{key}}={{value}}{% endfor %}
%:
	dh $@ --with {{with}} --buildsystem=pybuild
{%- if docs and docs.sphinx_dir %}

execute_after_dh_auto_build-indep:
ifeq (,$(filter nodoc,$(DEB_BUILD_OPTIONS)))
	cd {{docs.sphinx_dir}} && \
	PYTHONPATH=$(CURDIR) http_proxy='http://127.0.0.1:9/' https_proxy='https://127.0.0.1:9/' \
	sphinx-build -N -E -T -b html . $(CURDIR)/.pybuild/docs/html/
	rm -rf $(CURDIR)/.pybuild/docs/html/.doctrees
endif
{% endif %}
