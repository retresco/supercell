0.8.2 - (unreleased)
---------------------

New Features
~~~~~~~~~~~~

* Add configuration via environment variables. The load precedence of service
  configurations is:

  environment variables > command line arguments > config file


Bugfixes / Improvements
~~~~~~~~~~~~~~~~~~~~~~~

* Requirements update:
    * tornado: >=4.2.1,<=5.1.1
    * schematics: >= 1.1.1

* Due to a security risk, query values in responding error messages encode
  html (<,>,&) now

* HTTP response status 406 if no matching provider is found. If the request is
  not parsable (400) and no matching provider (406) the responded http status is
  406.

Development Changes
~~~~~~~~~~~~~~~~~~~

* Add gitlab-ci configuration to the project to run automatic testing
  The configuration is not part of the released package

* Add Makefile to build and test the project in python 2.7, 3.6 and a local version
  To build and test the project run:

  .. code-block:: bash

    make install test

  The Makefile is not part of the released package

Migration
~~~~~~~~~



0.8.1 - (May 2, 2018)
---------------------

- added option to suppress (successful) health check logs in an application

0.8.0 - (March 8, 2018)
-----------------------

- new load model from arguments helper for request handlers
- provides decorator with new partial option for partial validation
- added support for partial validation in case of JsonProvider
- NOTE: with schematics < 2.0.1, ModelType isn't properly partially validated
- added python3.6 travis integration
- removed python2.6 support

0.7.4 - (March 8, 2018)
-----------------------

- add patch to http verbs that consume models
- add Content-Type and Consumer for json patches

0.7.3 - (April 21, 2017)
------------------------

- extend RequestHandler for async-await syntax compatibility

0.7.2 - (March 17, 2017)
------------------------

- allow to log forwarded requests differently if X-Forwarded-For is set
- improved error mechanism to be consistent in error writing
- updated requirements to newer versions

0.7.1 - (February 3, 2017)
--------------------------

- schematics BaseError handling
- changes necessary for moving truemped->retresco

0.7.0 - (August 24, 2015)
-------------------------

- Updated requires.io badge
- Removed buildout
- Tornado 4.2.1
- Python 3.4 compatibility


0.6.3 - (January 12, 2015)
--------------------------

- Add pytest to mocked sys.argv

0.6.2 - (December 28, 2014)
---------------------------

- Simplify integration testing of services

0.6.1 - (December 23, 2014)
---------------------------

- Optionally install signal handlers
- Fix: the exception is called NotImplementedError.
- Fix minor typo in @provides docstring

0.6.0 - (April 24, 2014)
------------------------

- add graceful shutdown
- allow logging to `stdout`
- Enable log file name with pid
- General base class for middleware decorators
- Typed query params deal with validation of query params

0.5.0 -
---------------------------

- add a NoContent (204) http response
- upgrade schematics to 0.9-4 (#7, #8)
- add a text/html provider for rendering html using tornado.template

0.4.0 - (December 09, 2013)
---------------------------

- Raise HTTPError when not returning a model
- A ValueError thrown by Model initialization returns a 400 Error
- fix for broken IE6 accept header
- allow latin1 encoded urls
- show-config, show-config-name and show-config-file-order
- enable tornado debug mode in the config
- Only add future callbacks if it is a future in the
  request handler
- Unittests using py.test
- HTTP Expires header support
- Caching configurable when adding the handlers
- Stats collecting using scales
- Fixed logging configuration

0.3.0 - (July, 16, 2013)
------------------------

- Introduce health checks into supercell
- Add a test for mapping ctypes with encodings

0.2.5 - (July 16, 2013)
-----------------------

- Only call finish() if the handler did not
- Minor fix for accessing the app in environments

0.2.4 - (July 10, 2013)
-----------------------

- Add the `@s.cache` decorator


0.2.3 - (July 4, 2013)
----------------------

- Allow binding to a socket via command line param
- Use MediaType.ApplicationJson instead of the plain string
- Add managed objects and their access in handlers


0.1.0 - (July 3, 2013)
----------------------

- Use the async decorator instead of gen.coroutine
- Application integration tests
- Initial base service with testing
- Add the initial default environment
- No Python 3.3 because schematics is not compatible
- Request handling code, working provider/consumer
- Base consumer and consumer mapping
- Cleaned up code for provider logic
- Working provider logic and accept negotiation
- Fixing FloatType on Python 3.3
- Initial provider logic
- PyPy testing, dependencies and py2.6 unittest2
- Decorators simplified and working correctly
- Unused import
- Fixing iteritems on dicts in Py 3.3
- Fixing sort comparator issue on Py 3.3
- fix string format in Python 2.6
- Fixing test requirements
- nosetests
- travis-ci
