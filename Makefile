
##
## GLOBALS
##

PYTHON_INTERPRETER=python
LIMIT=-1


##
## DOCKER COMMANDS
##

requirements:
	pip install --user -U -r requirements.txt

build-dev:
	docker build -t medias-uptodate-dev:latest -f Dockerfile-dev .

run-dev:
	docker-compose -f docker-compose-dev.yml up -d

build-prod:
	docker build -t medias-uptodate-prod:latest -f Dockerfile-prod .

update_database:
	docker run --rm -v ${PWD}:/app -v /mnt/samba_sfr:/app/datas/medias medias-uptodate-prod:latest python -m src.update_database --limit $(LIMIT) $(NAMES)

##
## PYTHON COMMANDS
##

debug:
	$(PYTHON_INTERPRETER) -m ptvsd --host 0.0.0.0 --port 3000 --wait -m ${m}
