SRCDIR=supercell
TEST?=test
VIRTUALENV_DIR=${PWD}/env
PIP=${VIRTUALENV_DIR}/bin/pip
PYTHON=${VIRTUALENV_DIR}/bin/python

.PHONY: all
all: virtualenv install

.PHONY: virtualenv
virtualenv:
	if [ ! -e ${PIP} ]; then python3 -m venv ${VIRTUALENV_DIR}; fi
	${PIP} install --upgrade pip

.PHONY: install
install: virtualenv
	${PIP} install -r requirements.txt
	${PIP} install -e .
	${PIP} install -r requirements-test.txt

.PHONY: test
test:
	${VIRTUALENV_DIR}/bin/py.test -vvrw ${TEST} --cov ${SRCDIR} --cov-report=term:skip-covered --cov-report=xml:coverage.xml

.PHONY: clean
clean:
	-rm -f .DS_Store .coverage
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -depth -name '__pycache__' -exec rm -rf {} \;

.PHONY: dist-clean
dist-clean: clean
	rm -rf ${VIRTUALENV_DIR};
	find . -depth -name '*.egg-info' -exec rm -rf {} \;
