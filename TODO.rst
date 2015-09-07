* documentation
* support settings from stdeb.cfg configuration file
* 'Environment :: X11 Applications' or 'Intended Audience :: End Users/Desktop' → private module
* --dput-cmd
* generate result/build.sh if --build-cmd not set
* generate debdiff if .dsc or .changes files are available
* convert upstream version (alpha → ~alpha, etc.)
* use aioredis to cache coroutines

debian/copyright
----------------
integrate below tools if they're useful
* licencecheck
* license-reconcile
* /usr/lib/cdbs/licensecheck2dep5

debian/control
--------------
* use XB-Python-Egg-Name / XB-Python-Egg-Version while generating dependencies
  (also in dh_python{2,3}?)
* parse setup.cfg to get build dependencies from
  [bdist_deb] → build-requires or even [bdist_rpm]

sphinx docs
-----------
* use setup.cfg's settings, example:
  [build_sphinx]
  source-dir = doc/source
  build-dir = doc/build
