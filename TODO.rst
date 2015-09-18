* documentation
* tests
* support settings from stdeb.cfg configuration file
* --upload-cmd
* generate result/build.sh if --build-cmd not set
* generate debdiff if .dsc or .changes files are available
* convert upstream version (alpha → ~alpha, etc.)
* generate autopkgtest (DEP-8)
* use aioredis to cache coroutines
* --application (install to private dir, do not prefix binary package with interpreter name, etc.)
* 'Environment :: X11 Applications' or 'Intended Audience :: End Users/Desktop' → private module
* point mk-origtargz to --copyright-file if available in overrides

debian/copyright
----------------
integrate below tools if they're useful

* licencecheck
* license-reconcile
* /usr/lib/cdbs/licensecheck2dep5

debian/control
--------------
* use XB-Python-Egg-Name while generating dependencies
  (also in dh_python{2,3}?)
* parse setup.cfg to get build dependencies from
  ``[bdist_deb] → build-requires`` or even ``[bdist_rpm]``

sphinx docs
-----------
* use setup.cfg's settings, example:

  | [build_sphinx]
  | source-dir = doc/source
  | build-dir = doc/build
