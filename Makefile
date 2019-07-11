.PHONY: default install reset check test tox readme docs publish clean

MAKE := $(MAKE) --no-print-directory
	
test:
	python setup.py test
	
develop: 
	python setup.py develop 
	
publish: 
	$(MAKE) clean
	python setup.py sdist 
	twine upload dist/*
	$(MAKE) clean
	
clean:
	@rm -Rf *.egg .cache .coverage .tox build dist docs/build htmlcov
	@find -depth -type d -name __pycache__ -exec rm -Rf {} \;
	@find -type f -name '*.pyc' -delete
test:
	python setup.py test
	
develop: 
	python setup.py develop 
	
publish: 
	git push --tags origin
	$(MAKE) clean
	python setup.py sdist 
	twine upload dist/*
	$(MAKE) clean
	
clean:
	@rm -Rf *.egg .cache .coverage .tox build dist docs/build htmlcov
	#@find . -type d -name __pycache__ -exec rm -Rf {} \;
	#@find . -type f -name '*.pyc' -delete