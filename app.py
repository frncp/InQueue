from flask import Flask, render_template, url_for, request, redirect, send_from_directory, make_response, send_file
import requests
import json
from http import cookies

import pymongo
from pymongo import MongoClient
import base64
import bson
from bson.binary import Binary
from datetime import date, datetime
from io import BytesIO

from passwords import DB_USER, DB_PASSWORD

# import ssl
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain('certificate.crt', 'private.key')

# DB Connection
mongo_client_string = "mongodb+srv://" + DB_USER + ":" + DB_PASSWORD + "@cluster0.dfin1.mongodb.net/sample_airbnb?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_client_string)
db = client["inQueue"]
collection = db["businesses"]
# Start app
app = Flask(__name__)

@app.route('/home')
def homepage_new():
    return render_template("home.html")

@app.route('/')
def homepage():
    city_from_cookie = request.cookies.get("city")

    if not city_from_cookie:
        # set_cookie(lat, value=lat, max_age=60*60*24)
        # set_cookie(lon, value=lon, max_age=60*60*24)
        rendered_template = render_template('index.html', city="clicca")
        return make_response(rendered_template)
    else:
        return render_template('index.html', city=city_from_cookie)


@app.route('/business/<name>', methods=["POST", "GET"])
def businesspage(name):
    if request.method == "POST":
        name = request.form["fname"]
        surname = request.form["lname"]
        email = request.form["email"]
        cellphone = request.form["cellphone"]
        day = request.form["date"]
        time = request.form["slot2"]
        service = request.form["service"]
        operator = request.form["operator"]
        # document = {"name": name, "surname": surname, "email": email, "cellphone": cellphone, "day": day,
        #            "open_time": open_time, "close_time": close_time, "service": service, "operator": operator}

        return redirect(url_for("confirmationpage"))
        # TODO: Add parameters to function
    else:
        return render_template("business-info.html", bsname=name)


@app.route('/confirmation')
def confirmationpage():
    return render_template("booked.html")
    # TODO: Add parameters to function


@app.route("/partner", methods=["POST", "GET"])
def partnerspage():
    if request.method == "POST":
        img = request.files['img'].read()
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        cellphone = request.form["cellphone"]
        business_name = request.form["bname"]
        open_time = request.form["open-time"]
        close_time = request.form["close-time"]
        service = request.form["service"]
        operator = request.form["operator"]
        today = str(date.today()).replace("/", "-", 3)
        now = datetime.now().strftime('%H:%M:%S')
        document = {"img": img, "fname": fname, "lname": lname, "email": email, "cellphone": cellphone,
                    "business_name": business_name, "open_time": open_time, "close_time": close_time,
                    "service": service, "operator": operator, "creation_date": today, "creation_time": now}
        collection.insert_one(document)
        return redirect(url_for("confirmationpage"))
    else:
        return render_template("business-creation.html")


# @app.route('/<path:filename>')
# def send_file(filename):
#     return send_from_directory(app.static_folder, filename)

@app.route('/photos/<business_name>_<creation_date>_<creation_time>.jpg', methods=["GET"])
def send_business_image(business_name, creation_date, creation_time):
    document = collection.find_one({"business_name": business_name, "creation_date": creation_date,
                                    "creation_time": creation_time})
    photo = BytesIO(document["img"])
    return send_file(photo, mimetype="image/gif")


if __name__ == "__main__":
    # Server starting
    local_only = True  # True = Accessible only in local loop; False = Accessible also from out of intranet
    if local_only:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', port=8150, debug=False)  # Port forwarding needed on router
    # app.run(host='0.0.0.0', port='8150', debug=True, ssl_context=context)
