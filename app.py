from flask import Flask, render_template, url_for, request, redirect, send_from_directory, make_response
import requests
import json
from http import cookies
import pymongo
from pymongo import MongoClient
from passwords import DB_USER, DB_PASSWORD
# import ssl
# context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# context.load_cert_chain('certificate.crt', 'private.key')

app = Flask(__name__)
@app.route('/')
def homepage():
    city_from_cookie = request.cookies.get("city")

    if not city_from_cookie:
        # set_cookie(lat, value=lat, max_age=60*60*24)
        # set_cookie(lon, value=lon, max_age=60*60*24)
        rendered_template = render_template('index.html', city="clicca")
        return make_response(rendered_template)
    # elif request.cookies.get("lat"):
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
        return redirect(url_for("confirmationpage"))
        # TODO: Add parameters to function
    else:
        return render_template("business-info.html", bsname=name)

@app.route('/confirmation')
def confirmationpage():
    return render_template("booked.html")
    # TODO: Add parameters to function

@app.route("/partner")
def partnerspage():
    return render_template("business-creation.html")

@app.route('/<path:filename>')
def send_file(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    mongo_client_string = "mongodb+srv://"+DB_USER+":"+DB_PASSWORD+"@cluster0.dfin1.mongodb.net/sample_airbnb?retryWrites=true&w=majority"
    client = pymongo.MongoClient(mongo_client_string)
    db = client.test
    local_only = True # True = Accessible only in local loop; False = Accessible also from out of intranet
    if local_only:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', port='8150', debug=False) # Port forwarding needed on router
    # app.run(host='0.0.0.0', port='8150', debug=True, ssl_context=context)

