Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {{name}}
Upstream-Contact: {{author}}
Source: {{homepage}}

Files: *
Copyright: {{copyright}}
License: {{license_name}}

Files: debian/*
Copyright: {{deb_copyright}}
License: {{deb_license_name}}

License: {{license_name}}
{{license}}
{%- if license_name != deb_license_name %}

License: {{deb_license_name}}
{{deb_license}}
{% endif %}
