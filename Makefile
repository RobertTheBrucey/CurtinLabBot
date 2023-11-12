pwd := $(shell pwd)

build:
	docker build -t curtin-lab3 .

no-cache:
	docker build --no-cache -t curtin-lab3 .

run:
	docker run --rm -v "$(shell pwd)/persistence":/src/persistence -p 8010:8010 --name curtin-lab3 curtin-lab3

run-detached:
	docker run -v "$(shell pwd)/persistence":/src/persistence -p 8010:8010 --name curtin-lab3 -d --restart unless-stopped curtin-lab3

stop:
	docker stop curtin-lab3

rm:
	docker rm curtin-lab3

logs:
	docker logs -f curtin-lab3

rebuild: stop rm build run-detached
