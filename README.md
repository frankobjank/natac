# natac

Free & open source networked game implemented in Python, inspired by Klaus Teuber's *Settlers of Catan* for MacOS and Linux.

![Screenshot](./assets/Screenshot.png)

Python 3.11.5 was the version of Python used for development.

To play, one person needs to start a server, and all players need to start a client from the terminal using the instructions below:

Create a virtual environment

```sh
# only run venv for first time setup
python3 -m venv .venv

# start a venv
source .venv/bin/activate
```

The required modules are listed below:
cffi==1.17.1
inflection==0.5.1
pycparser==2.21
raylib==5.0.0.3

Use this to install the requirements at once:

```sh
pip install -r requirements.txt
```

To start a server, include the IP address (IPv4) you want to use. The default value is 127.0.0.1 (a local IP address to help with debugging).

```sh
python3 main.py server IP_address
```

And to run the client:

```sh
python3 main.py
```
