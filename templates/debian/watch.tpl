version=4
{%- if github %}
opts="pgpmode=none, filenamemangle=s%(?:.*?)?v?(\d[\d.]*)\.tar\.gz%@PACKAGE@-$1.tar.gz%" \
{{github}}/tags (?:.*?/)?v?(\d[\d.]*)\.tar\.gz
{% else %}
# try also https://pypi.debian.net/{{name}}/watch
opts=uversionmangle=s/(rc|a|b|c)/~$1/ \
https://pypi.debian.net/{{name}}/{{name}}-(.+)\.(?:zip|tgz|tbz|txz|(?:tar\.(?:gz|bz2|xz)))
{% endif %}
