SRCDIR=supercell
TEST?=test
VIRTUALENV=virtualenv

####################################################
# system python
VIRTUALENV_DIR=${PWD}/env
PIP=${VIRTUALENV_DIR}/bin/pip
PYTHON=${VIRTUALENV_DIR}/bin/python

.PHONY: test
test:
	${VIRTUALENV_DIR}/bin/py.test -vvrw ${TEST} --cov ${SRCDIR} --cov-report=term:skip-covered --cov-report=xml:coverage.xml

.PHONY: virtualenv
virtualenv:
	if [ ! -e ${PIP} ]; then \
	${VIRTUALENV} -p python ${VIRTUALENV_DIR}; \
	fi
	${PIP} install --upgrade pip

.PHONY: install
install: virtualenv
	${PIP} install -r requirements.txt;
	${PYTHON} setup.py develop;
	${PIP} install -r requirements-test.txt;


####################################################
# python 3
VIRTUALENV_DIR3=${PWD}/env3
PIP3=${VIRTUALENV_DIR3}/bin/pip
PYTHON3=${VIRTUALENV_DIR3}/bin/python

.PHONY: test3
test3:
	${VIRTUALENV_DIR3}/bin/py.test -vvrw ${TEST} --cov ${SRCDIR} --cov-report=term:skip-covered --cov-report=xml:coverage.xml

.PHONY: virtualenv3
virtualenv3:
	if [ ! -e ${PIP3} ]; then \
	${VIRTUALENV} -p python3.6 ${VIRTUALENV_DIR3}; \
	fi
	${PIP3} install --upgrade pip

.PHONY: install3
install3: virtualenv3
	${PIP3} install -r requirements.txt;
	${PYTHON3} setup.py develop;
	${PIP3} install -r requirements-test.txt;


####################################################
# python 2
VIRTUALENV_DIR2=${PWD}/env2
PIP2=${VIRTUALENV_DIR2}/bin/pip
PYTHON2=${VIRTUALENV_DIR2}/bin/python

.PHONY: test2
test2:
	${VIRTUALENV_DIR2}/bin/py.test -vvrw ${TEST} --cov ${SRCDIR} --cov-report=term:skip-covered --cov-report=xml:coverage.xml

.PHONY: virtualenv2
virtualenv2:
	if [ ! -e ${PIP2} ]; then \
	${VIRTUALENV} -p python2.7 ${VIRTUALENV_DIR2}; \
	fi
	${PIP2} install --upgrade pip

.PHONY: install2
install2: virtualenv2
	${PIP2} install -r requirements.txt;
	${PYTHON2} setup.py develop;
	${PIP2} install -r requirements-test.txt;


####################################################
.PHONY: clean
clean:
	-rm -f .DS_Store .coverage
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -depth -name '__pycache__' -exec rm -rf {} \;

.PHONY: dist-clean
dist-clean: clean
	-rm -rf ${VIRTUALENV_DIR3};
	rm -rf ${VIRTUALENV_DIR2};
	rm -rf ${VIRTUALENV_DIR};
	find . -depth -name '*.egg-info' -exec rm -rf {} \;
