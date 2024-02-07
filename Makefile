export PYTHON_COMMAND=python3.11



setup:
	$(PYTHON_COMMAND) -m pip install poetry
	poetry env use $(PYTHON_COMMAND)
	poetry run pip install --upgrade pip

install:
	poetry lock
	poetry install

isort:
	poetry run isort --skip-glob=.tox .

format:
	poetry run black climate_change

lint:
	make isort
	make format
	poetry run pylint  --extension-pkg-whitelist='pydantic' climate_change
	poetry run flake8 climate_change
	poetry run mypy --ignore-missing-imports --install-types --non-interactive --package climate_change

test:
	poetry run pytest --verbose --color=yes --cov=climate_change

env:
	poetry shell

requirements:
	poetry export --without-hashes --with-credentials -f requirements.txt

minimum-requirements:
	poetry export --without-hashes --with-credentials -f requirements.txt | grep -e ml3-repo-manager -e pyyaml -e -- > requirements.txt