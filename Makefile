.PHONY: tests_tox tests tests_integration tests_types create_requirements build
.DEFAULT_GOAL := tests

tests_tox:
	poetry run tox

tests:
	pytest tests

lint:
	poetry run black . --check

lint_fix:
	poetry run black .

clean:
	rm -rf ./build || echo ""
	rm -rf ./.tox || echo ""
	rm -rf ./bas_remote_python.egg-info || echo ""
	rm -rf ./.bas-remote-app || echo ""
	rm -rf ./.pytest_cache || echo ""
	rm -rf ./dist || echo ""

build:
	poetry build -f wheel -n
	poetry build -f sdist -n
	rm 1.0.0 || echo ""

upload_pypi:
	$(clean)
	$(build)
	twine upload dist/bas-remote-python-v2-2.0.0.tar.gz dist/*.whl

create_requirements:
	poetry export --without-hashes --without-urls -f requirements.txt --output requirements.txt
