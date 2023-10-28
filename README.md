# SOC

Getting started:

Create a virtual environment:
```
$ python3 -m venv .venv (only do this for first time setup)
$ source .venv/bin/activate
```
Update pip and install setuptools and raylib:
```
python3 -m pip install --upgrade pip
python3 -m pip install setuptools
python3 -m pip install raylib
```
Or use this to automate the above process
```
pip install -r requirements.txt
```

# Basic Raylib Game Loop
def main():
    pr.init_window(800, 600, "Game")
    pr.set_target_fps(60)
    while not pr.window_should_close():
        # user input

        # update

        # render
        pr.begin_drawing()
        pr.clear_background(pr.WHITE)


        pr.end_drawing()

    pr.close_window()
