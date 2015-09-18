PyPI to Debian
==============


* ``py2dsp`` - converts PyPI package to Debian source package
* ``pypi2debian`` - converts PyPI repository to Debian repository


features
~~~~~~~~

* uses PyPI metadata
* supports Python 2.X, 3.X and PyPy
* guesses build dependencies
* creates -doc package with Sphinx regenerated documentation
* generates ITP email template
* easy to override / customise
* uses Debian tools to generate files if possible
* integrates with dh-python's tools


examples
~~~~~~~~

* ``py2dsp jinja2`` will download, unpack and debianize jinja2 in ./result/jinja2-2.8/
* ``py2dsp jinja2-2.8.tar.gz`` will unpack and debianize jinja2 in ./result/jinja2-2.8/
* ``py2dsp ./result/jinja2-2.8/`` will debianize Jinja2 in provided directory

if debian/changelog didn't exist, above commands will also create
jinja2_2.8-0~py2deb.mail file with ITP (intend to package) template

* ``pypi2debian`` will convert PyPI packages to Debian source packages in ./result directory
* ``pypi2debian --build-cmd "sbuild -c unstable"`` as above, but will also try
  to build these packages using sbuild (if "unstable" schroot is already set up)
* ``pypi2debian --python3 --classifiers 'Operating System :: POSIX :: Linux'``
  will create only python3-foo packages for all Linux compatible packages.
  See list `classifiers page`_ for possible ``--classifiers`` values

.. _classifiers page: https://pypi.python.org/pypi?%3Aaction=list_classifiers


overrides
~~~~~~~~~

To override pypi2deb's auto detected values and auto generated files use
overrides mechanism.

Each package has its own subdirectory in ./overrides dir (can be changed via
``PYPI2DEB_OVERRIDES_PATH`` env. variable) - complete files, modified templates
(``.tpl`` files) or ``ctx.json`` file can be stored there.
Each file that doesn't have ``.tpl`` extension will be copied to the result
directory, including f.e. debian/patches dir.

``ctx.json`` file in overrides/foo/ directory will overwrite auto detected
values (see list below). For the same purpose `py2dsp` section in setup.cfg
file can be used.

To provide different templates for all packages, point pypi2deb to them via
``PYPI2DEB_TEMPLATES_PATH`` env. variable.

To use different PyPI server - set ``PYPI_JSON_URL`` and ``PYPI_XMLRPC_URL``
env. variables.

ctx values
----------
* `author` - upstream author's name
* `author_email` - upstream author's email
* `binary_arch` - binary package's architecture
* `build_depends` - build dependencies
* `clean_files` - files to remove in clean step
* `copyright` - upstream copyrights (one line)
* `deb_copyright` - Debian packaging copyrights 
* `deb_license_name` - Debian packaging license name
* `debian_revision` - 0~pypi2deb by default
* `description` - project's raw description
* `distribution` - Debian's suite
* `email` - maintainer's email
* `exports` - variables exported in ``debian/rules``
* `homepage` - project's homepage
* `interpreters` - supported Python interpreters (python, python3, pypy)
* `license` - license's full text
* `license_name` - license name
* `maintainer` - maintainer's full name
* `name` - upstream project name
* `src_name` - debianized upstream project name
* `summary` - package's short description
* `uploaders` - co-maintainers of the package
* `vcs_browser` - URL to web-browsable copy of the Version Control System repository
* `vcs_name` - VCS name, f.e. Git, Svn, etc.
* `vcs_src` -  location of the Version Control System
* `version` - upstream version
* `with` - list of dh's ``--with`` extensions
* `docs`

  * `sphinx_dir` - directory with documentation (Sphinx)
  * `files` - list of files / dirs to be installed as documentation
  * `examples` - list of example files / dirs
  * `examples_dir` - relative path to directory with examples

