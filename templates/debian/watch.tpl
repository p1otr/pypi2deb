# try also https://pypi.debian.net/{{name}}/watch
version=3
opts=uversionmangle=s/(rc|a|b|c)/~$1/ \
https://pypi.debian.net/{{name}}/{{name}}-(.+)\.(?:zip|tgz|tbz|txz|(?:tar\.(?:gz|bz2|xz)))

