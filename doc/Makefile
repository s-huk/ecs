generate: readme template fields

#setup:
#	pip install --user --upgrade --requirement ./scripts/requirements.txt

#clean:
#	rm schema.csv schema.md
#	# Clean all markdown files for use-cases
#	find ./use-cases -type f -name '*.md' -not -name 'README.md' -print0 | xargs -0 rm --

readme:
	cat intro.md > ../README.md
	echo >> ../README.md
	echo "## Felder" >> ../README.md
	echo >> ../README.md
	python doc.py >> ../README.md
#	cat docs/use-cases-header.md >> README.md
#	python scripts/use-cases.py --stdout=true >> README.md
#	cat docs/implementing.md >> README.md
#	cat docs/about.md >> README.md

template:
#	go get github.com/elastic/go-ucfg/yaml
#	go get github.com/elastic/beats/libbeat/template
#	go run scripts/template.go > ./template.json

fields:
#	cat schemas/*.yml > fields.tmp.yml
#	sed -i.bak 's/^/    /g' fields.tmp.yml
#	sed -i.bak 's/---//g' fields.tmp.yml
#	cat scripts/fields_header.yml > fields.yml
#	cat fields.tmp.yml >> fields.yml
#	rm -f fields.tmp.yml fields.tmp.yml.bak

#.PHONY: generate schemas fmt check setup clean readme template fields
