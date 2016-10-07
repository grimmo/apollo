# Apollo

If you have to daily power on many computers in many differents subnets, this web application helps accomplishing this task in a simple centralized way.

You install a client on a single pc for every subnet you need to wake up computers on. The client queries the central server at startup and gets a list
of computers and mac addresses to send WOL packets to in his subnet. The client proceeds to send WOL packets to each computer in the list.
The computer running the client to wake up other computers must turn on automatically via bios or be always-on.

If you need to add a new computer you can use a simple form in the webapp or launch the client using the `-r` parameter. It will register the computer to the server.
If you need to disable a computer from turning on, you disable it from the list in the web application.

The server supports RESTful URLs for most of its functions, i.e.:

a POST/PUT request to

```
http://<server_address>//computers/<hostname>/enable/
```

or 

```
http://<server_address>//computers/<hostname>/disable/
```

to toggle a computer from being turned on.

```
http://<server_address>/computers/<hostname>/remove/
```

to remove a computer from the list.

no HTTPS or authentication is supported at the moment. This project is still in early stage.


## Installation

This project requires *Python 2.7.x* and *Flask 0.11*
Use of virtualenv is recommended.

```bash
git clone https://github.com/grimmo/apollo.git
virtualenv --python=python2.7 venv
source venv/bin/activate
pip install -r ./requirements.txt
```

Create the database using the schema provided in apollo_schema.sql:

```bash
python
>>>from apollo import init_db  
>>>init_db()
```

Exit the Python interpreter with Ctrl-D

Prepare to run Flask

```bash
export FLASK_APP=apollo.py
export FLASK_DEBUG=1
flask run
```

If everything is ok, your output should be similar to this:
```bash
 * Serving Flask app "apollo"
 * Forcing debug mode on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger pin code: XXX-XXX-XXX
```


That's it!
