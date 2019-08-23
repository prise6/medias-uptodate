
##
## GLOBALS
##

PYTHON_INTERPRETER=python


##
## DOCKER COMMANDS
##

requirements:
	pip install --user -U -r requirements.txt

build-dev:
	docker build -t medias-uptodate-dev:latest -f Dockerfile-dev .

run-dev:
	docker-compose -f docker-compose-dev.yml up -d

##
## PYTHON COMMANDS
##

debug:
	$(PYTHON_INTERPRETER) -m ptvsd --host 0.0.0.0 --port 3000 --wait -m ${m}
