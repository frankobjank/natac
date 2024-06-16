# natac

Free & open source networked game implemented in Python, inspired by Klaus Teuber's *Settlers of Catan* for MacOS and Linux.

![Screenshot](./assets/Screenshot.png)


Python 3.11.5 was the version of Python used for development.

To play, you only need to download the executable called natac. You can also start a server or start a client from the terminal using the instructions below:

Create a virtual environment
```
python3 -m venv .venv (only do this for first time setup)
source .venv/bin/activate
```
The required modules are listed below:<br>
cffi==1.15.1<br>
inflection==0.5.1<br>
pycparser==2.21<br>
raylib==5.0.0.2<br>

Use this to install the requirements:
```
pip install -r requirements.txt
```
To start a server, include the IP address (IPv4) you want to use:
```
python3 main.py server IP_address
```
And to run the client:
```
python3 main.py
```
