help:
	@echo "deps - downloads dependecies"
	@echo "setup - setup the development enviroment. virtualenv, dependecy downloads"

apt:
	@echo "Running: sudo apt-get install python python-pip python-virtualenv libssl-dev build-essential"
#	@echo "Running: sudo apt-get install python3 python3-pip python3-virtualenv python3-venv libssl-dev build-essential"	
	@echo
	sudo apt-get install python python-pip python-virtualenv libssl-dev build-essential
#	sudo apt-get install python3 python3-pip python3-virtualenv python3-venv libssl-dev build-essential

.venv: apt
	if [ ! -e ".venv/bin/activate_this.py" ] ; then python3 -m venv --clear .venv ; fi
#	if [ ! -e ".venv/bin/activate_this.py" ] ; then virtualenv --clear .venv ; fi

deps: .venv
	. .venv/bin/activate && pip3 install -U -r requirements.txt
#	. .venv/bin/activate && pip install -U -r requirements.txt
	@echo
	@echo
	@echo "Please IGNORE any message like 'Failed building wheel for [...]', it's all still working fine."
	@echo
	@echo

setup: .venv deps
	./run-testbundle.sh -i
