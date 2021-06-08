from flask import Flask, render_template, url_for, request, redirect, send_from_directory, make_response, send_file, jsonify
from flask_mail import Mail, Message
import flask_login
import requests
import json
from http import cookies

import pymongo
from pymongo import MongoClient, errors
import base64
import bson
from bson.binary import Binary
from bson.objectid import ObjectId

from datetime import date, datetime, timedelta
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
import os

from passwords import DB_USER, DB_PASSWORD

import string
import random

# import ssl

import certifi


# SERVER SETTINGS
SERVER_NO_FORWARD = False # True = Flask default configuration, run it locally (for testing, debug)
SERVER_LOCAL_ONLY = False  # False = Accessible also from out of intranet
SERVER_DOMAIN_NAME = 'inqueue.it' # Your domain name here


# DATABASE SETTINGS
'''
[!] IMPORTANT:
        We use MongoDB Atlas for managing our database.
        To use your own, create a file in the root of this folder named 'passwords.py' and add the following text:
        # --------

          DB_USER = # your DB USER
          DB_PASSWORD = # your DB PASSWORD  

            # (this file is gitignored, so you can keep it safely on you machine)

        # -------

'''
DB_CLIENT_NAME = "inQueue" # Add your MongoDB client name here


# DB Connection
mongo_client_string = "mongodb+srv://" + DB_USER + ":" + DB_PASSWORD + "@cluster0.dfin1.mongodb.net/"+ DB_CLIENT_NAME + "?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_client_string, tlsCAFile=certifi.where())
db = client[DB_CLIENT_NAME]
businesses_collection = db["businesses"]
bookings_collection = db["bookings"]
PDFs_collection = db["bookings_PDFs"]
accounts_collection = db["accounts"]
businesses_photo_collection = db["businesses_photo"]
# Start app
app = Flask(__name__)
app.secret_key = 'super secret string'
# Start login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
# Mailing settings
# app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_SERVER'] = 'authsmtp.securemail.pro'
# app.config['MAIL_PORT'] = 2525
# app.config['MAIL_PORT'] = 587
app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = '54bb2a794dc163'
# app.config['MAIL_USERNAME'] = 'antoniototimorelli@gmail.com'
app.config['MAIL_USERNAME'] = 'no-reply@inqueue.it'
# app.config['MAIL_PASSWORD'] = '84f0fbad4c7117'
# app.config['MAIL_PASSWORD'] = 'zzecqsiwqmklrtus'
app.config['MAIL_PASSWORD'] = 'gj5-tj!UFXDC6J_'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail()
mail.init_app(app)

business_types_dict_italian = {
    "barber": "Barbiere",
    "beautician": "Estetista",
    "hairdresser": "Parrucchiere",
    "field": "Campo sportivo",
    "museum": "Museo",
    "attraction": "Luogo d'interesse",
    "freelance": "Libero professionista"
}


def id_generator(size=8, chars=string.digits + string.ascii_letters):
    return ''.join(random.choice(chars) for _ in range(size))


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(email):
    query_result = accounts_collection.find_one({"email": email})
    if query_result is None:
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    query_result = accounts_collection.find_one({"email": email})
    if query_result is None:
        return
    user = User()
    user.id = email
    print(user.is_authenticated) # Check values when it appears, mattia's
    user.is_authenticated = (request.form['password'] == query_result['password'])
    print(user.is_authenticated)
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    if request.form['password'] == (accounts_collection.find_one({"email": email}))['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect(url_for('protected'))

    return 'Bad login'


@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/getdates&<b_name>&<date>', methods=['GET'])
def get_dates(b_name, date):
    query_result = businesses_collection.find_one({"business_name": b_name}, {"slots": 1})
    query_result2 = bookings_collection.find({"business_name": b_name, "day": date})
    available_hours = []
    for element in query_result["slots"]:
        found = False
        for element_2 in query_result2:
            if element == element_2["time"]:
                found = True
        if not found:
            available_hours.append(element)
    return jsonify(available_hours)


@app.route('/select', methods=["POST", "GET"])
def homepage_new():
    if request.method == "GET":
        city_from_cookie = request.cookies.get("city")
        if not city_from_cookie:
            city_from_cookie = ""
        return render_template("home.html", city_from_cookie=city_from_cookie)
    else:
        city = request.form["city"]
        lat = request.form["lat"]
        print("latitudine settata", lat)
        lon = request.form["lon"]
        resp = make_response(redirect('/'+city))
        resp.set_cookie("city", value=city, max_age=60 * 60 * 24)
        resp.set_cookie("lat", value=lat, max_age=60 * 60)
        resp.set_cookie("lon", value=lon, max_age=60 * 60)
        return resp


@app.route('/')
def homepage():
    city_from_cookie = request.cookies.get("city")
    if not city_from_cookie:
        return redirect("/select")
    else:
        return redirect("/"+str(city_from_cookie))


@app.route('/<city>')
def city_home(city):
    lat_from_cookie = request.cookies.get("lat")
    lon_from_cookie = request.cookies.get("lon")
    print(lat_from_cookie)
    print(lon_from_cookie)
    businesses_in_city = businesses_collection.find({"city": city})
    resp = make_response(render_template('index.html', businesses_in_city=businesses_in_city, city=city, business_types_dict_italian=business_types_dict_italian))
    try:
        resp.set_cookie("lat", value=lat_from_cookie, max_age=0)
        resp.set_cookie("lon", value=lon_from_cookie, max_age=0)
    except TypeError:
        print("Cookie not set")
        # TODO: assume coords of a city based on the center of it
    return resp


@app.route('/business/<business_name>', methods=["POST", "GET"])
def business_page(business_name):
    if request.method == "POST":
        name = request.form["fname"]
        surname = request.form["lname"]
        email = request.form["email"]
        cellphone = request.form["cellphone"]
        day = request.form["date"]
        time = request.form["time"]
        service = request.form["service"]
        today = str(date.today()).replace("/", "-", 3)
        now = datetime.now().strftime('%H:%M:%S')
        document = {"business_name": business_name, "name": name, "surname": surname, "email": email,
                    "cellphone": cellphone, "day": day, "time": time, "service": service, "booking_date": today,
                    "booking_time": now}
        booking_result = bookings_collection.insert_one(document)
        msg = Message("Hello",
                      sender=("inQueue", "no-reply@inqueue.it"),
                      recipients=[email])
        msg.body = "Funzia?"
        mail.send(msg)
        return redirect("/booking_confirmation/"+str(booking_result.inserted_id))
    else:
        query_result = businesses_collection.find_one({"business_name": business_name})
        today = str(date.today()).replace("/", "-", 3)
        three_months = str((datetime.today() + timedelta(days=90)).strftime("%Y/%m/%d")).replace("/", "-", 3)
        return render_template("business-info.html", query_result=query_result, today=today, three_months=three_months)


@app.route('/files/tickets/<booking_id>.pdf')
def send_booking_pdf(booking_id):
    query_result = PDFs_collection.find_one({"_id": booking_id})
    pdf_data = bookings_collection.find_one({"_id": ObjectId(booking_id)})
    if query_result is None:
        file_name = curr_path + "\\temp\\" + booking_id + ".pdf"
        # PDF creation
        logo = open("logo.png", "rb")
        canvas = Canvas(file_name, pagesize=(612.0, 792.0))
        canvas.drawString(100, 700, "Let's write something into this")
        service = pdf_data["service"]
        business_name = pdf_data["business_name"]        
        canvas.save()
        file = open(file_name, "rb")
        # DB insert and retrieval
        document = {"_id": booking_id, "pdf": file.read()}
        PDFs_collection.insert_one(document)
        query_result = PDFs_collection.find_one({"_id": booking_id})
        # Temp file deletion
        file.close()
        os.remove(file_name)
    return send_file(BytesIO(query_result["pdf"]), mimetype="application/pdf")


@app.route('/booking_confirmation/<booking_id>')
def bookings_confirmation_page(booking_id):
    try:
        query_result = bookings_collection.find_one({"_id": ObjectId(booking_id)})
    except bson.errors.InvalidId:
        return redirect('/404/')
    if query_result is not None:
        service = query_result["service"]
        business_name = query_result["business_name"]
        day = query_result["day"]
        time = query_result["time"]
        # Use parameters found from query
        return render_template("booked.html", service=service, business_name=business_name, day=day, time=time)
    else:
        return redirect('/404/')
    # TODO: Add parameters to function


@app.route("/partner", methods=["POST", "GET"])
def partners_page():
    if request.method == "POST":
        # Account
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        password = request.form["password"]
        cellphone = request.form["cellphone"]
        # Business
        img = request.files['img'].read()
        business_name = request.form["bname"]
        business_type = request.form["type"]
        open_time1 = request.form["open-time1"]
        close_time1 = request.form["close-time1"]
        open_time2 = request.form["open-time2"]
        close_time2 = request.form["close-time2"]
        slot = request.form["slot"]
        # Business position
        city = request.form["city"]
        address = request.form["address"]
        lat = request.form["lat"]
        lon = request.form["lon"]
        # Check if account is already existing
        account_found = accounts_collection.find_one({"email": email})
        if account_found is not None:
            return redirect("/email_already_signed_up")  # TODO
        # Decorate business_name with random string to force uniqueness
        business_name = business_name + "$" + id_generator()
        # Business services
        num_of_services = int(request.form["num_of_services"])
        services = [str(request.form["service"])]
        service_n = 2
        while service_n <= num_of_services:
            service = request.form["service_"+str(service_n)]
            if len(service) > 0:
                services.append(service)
            service_n += 1

        # Time slots
        delta = timedelta(
            minutes=int(slot)
        )
        # Morning slots
        time = datetime.strptime(open_time1, '%H:%M')
        slots = []
        close_time = datetime.strptime(close_time1, '%H:%M')
        if time > close_time:
            close_time = close_time.replace(day=2)
        while time < close_time:
            slots.append(time)
            time = time + delta
        formatted_time_slots = []
        for time_slot in slots:
            formatted_time_slots.append(time_slot.strftime('%H:%M'))
        # Evening slots
        time = datetime.strptime(open_time2, '%H:%M')
        slots_2 = []
        close_time_2 = datetime.strptime(close_time2, '%H:%M')
        if time > close_time_2:
            close_time_2 = close_time_2.replace(day=2)
        while time < close_time_2:
            slots_2.append(time)
            time = time + delta
        for time_slot in slots_2:
            formatted_time_slots.append(time_slot.strftime('%H:%M'))

        # Time of creation to insert in DB
        today = str(date.today()).replace("/", "-", 3)
        now = datetime.now().strftime('%H:%M:%S')
        account_document = {"business_name": business_name, "fname": fname, "lname": lname, "email": email,
                            "cellphone": cellphone, "password": password}
        accounts_collection.insert_one(account_document)
        document = {"business_name": business_name, "business_type": business_type, "open_time1": open_time1, "close_time1": close_time1,
                    "open_time2": open_time2, "close_time2": close_time2, "city": city, "address": address, "lat": lat,
                    "lon": lon, "creation_date": today, "creation_time": now}
        b_sign_up_result = businesses_collection.insert_one(document)
        photo_document = {"_id": b_sign_up_result.inserted_id, "business_name": business_name, "img": img}
        businesses_photo_collection.insert_one(photo_document)

        businesses_collection.update_one({'_id': b_sign_up_result.inserted_id},
                                         {'$push': {"service": {'$each': services}}})
        businesses_collection.update_one({'_id': b_sign_up_result.inserted_id},
                                         {'$push': {"slots": {'$each': formatted_time_slots}}})

        return redirect("/newBusiness_confirmation/"+business_name)
    else:
        #msg = Message("Hello",
        #              sender=("inQueue", "no-reply@inqueue.it"),
        #              recipients=["mattiarip@gmail.com"])
        #msg.body = "Funzia?"
        #mail.send(msg)
        return render_template("business-creation.html")

# TODO
@app.route('/newBusiness_confirmation/<business_name>', methods=["GET"])
def partner_confirmation_page(business_name):
    business_document = businesses_collection.find_one({"business_name": business_name})
    account_document = accounts_collection.find_one({"business_name": business_name})
    return render_template("signed-up.html", business_document=business_document, account_document=account_document)


@app.route('/photos/<business_name>.jpg', methods=["GET"])
def send_business_image(business_name):
    document = businesses_photo_collection.find_one({"business_name": business_name})
    photo = BytesIO(document["img"])
    return send_file(photo, mimetype="image/gif")


@app.route('/list/<city>', methods=["GET"])
def list(city):
    # These cookies do not exists, since they are deleted after first usage in main page
    lat_from_cookie = request.cookies.get("lat")
    lon_from_cookie = request.cookies.get("lon")
    businesses_in_city = businesses_collection.find({"city": city})
    resp = make_response(render_template('list.html', businesses_in_city=businesses_in_city, city=city, business_types_dict_italian=business_types_dict_italian))
    try:
        resp.set_cookie("lat", value=lat_from_cookie, max_age=0)
        resp.set_cookie("lon", value=lon_from_cookie, max_age=0)
    except TypeError:
        print("Cookie not set")
        # TODO: assume coords of a city based on the center of it
    return resp


if __name__ == "__main__":
    curr_path = os.path.dirname(__file__)
    try:
        os.mkdir(curr_path+"/temp")
    except FileExistsError:
        pass
    https_available = False
    try:
        # SSL cert approach commented out to test the other one
        # context = ssl.SSLContext()
        # context.load_cert_chain(curr_path + '/cert.pem', curr_path + '/privkey.pem')
        context = (curr_path + '/cert.pem', curr_path + '/privkey.pem')
        https_available = True # True = create https page
    except FileNotFoundError:
        print("HTTPs certification files not found")
    # Server starting
    if SERVER_NO_FORWARD and SERVER_LOCAL_ONLY:
        app.run(debug=True)
    elif SERVER_LOCAL_ONLY and (not SERVER_NO_FORWARD):
        if https_available:
            app.run(debug=True, port=443, ssl_context=context)
        else:
            app.run(debug=True, port=80)
    else:
        # Port forwarding needed on router
        app.config['SERVER_NAME'] = SERVER_DOMAIN_NAME
        if https_available:
            app.run(host='0.0.0.0', port=443, debug=True, ssl_context=context)
        else:
            app.run(host='0.0.0.0', port=80, debug=True)
