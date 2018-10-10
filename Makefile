SRCDIR=supercell
TEST?=test

VIRTUALENV=virtualenv
VIRTUALENV_DIR=${PWD}/env
PIP=${VIRTUALENV_DIR}/bin/pip
PIP_INSTALL=${PIP} install
PYTHON=${VIRTUALENV_DIR}/bin/python

.PHONY: test
test:
	${VIRTUALENV_DIR}/bin/py.test -vvrw ${TEST} --cov ${SRCDIR} --cov-report=term:skip-covered --cov-report=xml:coverage.xml

.PHONY: virtualenv
virtualenv:
	if [ ! -e ${PIP} ]; then \
	${VIRTUALENV} -p python3.6 ${VIRTUALENV_DIR}; \
	fi
	${PIP_INSTALL} --upgrade pip

.PHONY: install
install: install-requirements
	${PYTHON} setup.py develop

.PHONY: install-requirements
install-requirements: virtualenv
	${PIP_INSTALL} -r requirements.txt

.PHONY: install-test
install-test: install
	${PIP_INSTALL} -r requirements-test.txt

.PHONY: clean
clean:
	-rm -f .DS_Store .coverage
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -depth -name '__pycache__' -exec rm -rf {} \;

.PHONY: dist-clean
dist-clean: clean
	-rm -rf ${VIRTUALENV_DIR} && \
	find . -depth -name '*.egg-info' -exec rm -rf {} \;
