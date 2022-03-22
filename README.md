# Quantified Self

To run the app, first setup a virtual environment with

`python3 -m venv env`

Then, activate the virtual environment with the command specific to your shell (the command for the bash shell is given below)

`source ./env/bin/activate`

Then, install all dependencies with `pip install -r requirements.txt`. You also need sqlite installed.

Then, start the server with `FLASK_APP=app flask run`

You should now see the app if you visit `http://localhost:5000` in your browser