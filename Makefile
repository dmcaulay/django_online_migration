# get the project name from setup.py
PROJECT := $(shell grep 'name=' setup.py | head -n1 | cut -d '=' -f 2 | sed "s/['\", ]//g")
PYTHON := $(PWD)/env/bin/python

# specifying a value for SETTINGS on the command line or in your
# shell's environment will override the defaults listed below
ifeq ($(origin SETTINGS), undefined)
  TEST_SETTINGS := $(PROJECT).test_settings
else
  TEST_SETTINGS := $(SETTINGS)
endif

# first rule in a makefile is the default one, calling it "all" is a
# common GNU Make convention.
all: test style

env: Makefile requirements.txt
	@echo "  VENV update"
	@virtualenv env -q
	@$(PWD)/env/bin/easy_install -q -U distribute
	@$(PWD)/env/bin/easy_install -q -U pip
	$(PWD)/env/bin/pip install -r requirements.txt
	$(PYTHON) setup.py develop
	@touch -c env

test_project: env env/bin/django-admin.py
	@echo "  PROJ update"
	$(PWD)/env/bin/django-admin.py startproject test_project >/dev/null || touch -c test_project

prereqs: test_project

test: test_project style
	$(PYTHON) test_project/manage.py test $(PROJECT).tests --settings=$(TEST_SETTINGS)

style: env
	$(PWD)/env/bin/pep8 --max-line-length=500 $(PROJECT)
	$(PWD)/env/bin/pylint $(PROJECT) -E --disable=E1002,E1101,E1102,E1103,E0203,E1003 --enable=C0111,W0613 --ignore=migrations

distclean:
	rm -rf env test_project
