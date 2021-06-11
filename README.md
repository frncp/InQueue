<p align="center"><img src="logo.png" width="150" /></p>

# InQueue
<p align="center">
    <img src="https://img.shields.io/badge/license-Apache%202-blue" />
    <img src="https://img.shields.io/badge/university project-red" />
</p>

InQueue is a small **web application** aimed at helping people with **booking a service in their area**. 
This is a university project made for the 2021 edition of the Tecnologie Web (Web Technologies) course at the [*Università degli Studi di Napoli Parthenope*](https://github.com/uniparthenope).

| :exclamation:  This project was made for learning purposes only |
|-----------------------------------------------------------------|

You can test it by visiting [inqueue.it](https://inqueue.it).

## How to get started (fast)
**Requirements**: Docker.
If you don't have Docker installed, follow [these instructions](https://docs.docker.com/engine/install/) to start.

1. Add your MongoDB Atlas account credentials to the file `/docker/.env.dev`
2. Run `docker-compose -f docker-compose.yml --env-file ./ .env.dev up --build` on your terminal
3. Open your browser and connect to [localhost:5000](http://localhost:5000)

## How to get started (the hard way)
### Setting up the database
1. Create a MongoDB database
2. Create a file named *`passwords.py`* in the root folder and insert the following parameters
  - `DB_USER = your_DB_username` (the name of the database user)
  - `DB_PASSWORD = your_DB_password` (the password for the database user)

### Installing the requirements
1. Open your terminal in the root folder
2. Install Python 3 on your machine if you haven't it installed already.
   To find out if you have Python 3 installed type `python3 --version` and press enter.
   To install Python 3 on your machine, follow the [instructions given here](https://www.python.org/downloads/). 
3. Create a virtual envirorment by giving the command `python3 -m venv env`
4. Install all the requirements with `python3 -m pip install -r requirements.txt`

### Executing
1. Type `python3 app.py` to start the server
2. Open your browser and reach the page [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
3. ????
4. PROFIT!!! Congratulations, now you can try the web app. Unfortunately, you'll have to add some data on your database to start using it.

## Technologies
To build this app the following technologies have been used:
- HTML5
- CSS3 (Bootstrap mainly)
- Javascript
- Python (Flask)
- MongoDB (Atlas)
- Nominatim (OpenStreetMap)

## Open source components
- Leaflet ([LICENSE](https://github.com/Leaflet/Leaflet/blob/master/LICENSE))
- Bootstrap (licensed under the [MIT License](https://github.com/twbs/bootstrap/blob/main/LICENSE))
- Flask (licensed under the [BSD 3-Clause "New" or "Revised" License](https://github.com/pallets/flask/blob/main/LICENSE.rst))
- qrcode ([LICENSE](https://github.com/lincolnloop/python-qrcode/blob/master/LICENSE))
- reportlab
- js-year-calendar (licensed under the [Apache License 2.0·](https://github.com/year-calendar/js-year-calendar/blob/master/LICENSE)
- star-rating.js (licensed under the [MIT License](https://github.com/pryley/star-rating.js/blob/master/LICENSE)

## Assets
Here's a list of the assets we used and their authors:
- *static/images/barber.png, static/images/lawyer.png, static/images/mechanic.png* made by <a href="https://www.flaticon.com/authors/monkik" title="monkik">monkik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
- *static/images/soccer-field.png* made by <a href="https://www.flaticon.com/authors/dinosoftlabs" title="DinosoftLabs">DinosoftLabs</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
- *static/images/calendar.png, static/images/column.png, static/images/nail-polish.png, static/images/settings.png* made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
- *static/images/muscle.png* made by <a href="https://www.flaticon.com/authors/darius-dan" title="Darius Dan">Darius Dan</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
- *static/images/logout.png* made by <a href="https://www.flaticon.com/authors/pixel-perfect" title="Pixel perfect">Pixel perfect</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
- *static/images/down-arrow.png* made by <a href="https://smashicons.com/" title="Smashicons">Smashicons</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>

## Authors
The authors of this project are
- Antonio Morelli [@antoniototimorelli](https://github.com/antoniototimorelli)
- Mattia Ripoli [@ManOnSaturn](https://github.com/ManOnSaturn)
- Francesco Pollasto [@frncp](https://github.com/frncp)
