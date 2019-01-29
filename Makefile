VENV=	venv


venv:
	python3 -m venv venv
	$(VENV)/bin/pip3 install -r requirements.txt

scan:	
	$(VENV)/bin/python read_aztec.py

clean:
	rm -fr $(VENV)
