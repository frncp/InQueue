from flask import Flask, render_template, request, redirect, make_response, send_file, jsonify
from flask_mail import Mail, Message
import flask_login
import werkzeug.exceptions
import os
import pymongo
import bson
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
import qrcode
from app.documents_db_init import init_db
from app.cities import CITIES
import string
import random
import certifi

# SERVER SETTINGS
SERVER_LOCAL_ONLY = True  # True = Run it locally
SERVER_DOMAIN_NAME = 'inqueue.it' # Your domain name here

# DB Connection
mongo_client_string = "mongodb+srv://" + os.environ['DB_USER'] + ":" + os.environ['DB_PASSWORD'] + "@" + os.environ['DB_CLUSTER_NAME'] + ".mongodb.net/"+ os.environ['DB_CLIENT_NAME'] + "?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_client_string, tlsCAFile=certifi.where(), connectTimeoutMS=30000, socketTimeoutMS=None, socketKeepAlive=True, connect=False, maxPoolsize=1)
db = client[os.environ['DB_CLIENT_NAME']]
businesses_collection = db["businesses"]
bookings_collection = db["bookings"]
PDFs_collection = db["bookings_PDFs"]
accounts_collection = db["accounts"]
businesses_photo_collection = db["businesses_photo"]

# Comment next line to get default DB
init_db(businesses_collection, accounts_collection, bookings_collection, businesses_photo_collection, PDFs_collection)

# Start app
app = Flask(__name__)
app.secret_key = os.urandom(12).hex()

# Start login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Mailing settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ['EMAIL_USER']
app.config['MAIL_PASSWORD'] = os.environ['EMAIL_PASSWORD']
app.config['MAIL_DEFAULT_SENDER'] = ('inQueue', os.environ['EMAIL_USER'])
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail()
mail.init_app(app)

# Temp folder
curr_path = os.path.dirname(__file__)
try:
    os.mkdir(curr_path+"/temp")
except FileExistsError:
    pass

business_types_dict_italian = {
    "barber": "Barbiere",
    "hairdresser": "Parrucchiere",
    "beautician": "Estetista",
    "field": "Campo sportivo",
    "museum": "Museo",
    "attraction": "Luogo d'interesse",
    "freelance": "Libero professionista",
    "gym": "Palestra",
    "car-repair": "Meccanico"
}


def slot_size(query_result):
    time_format = '%H:%M'
    t1 = query_result["slots"][0]
    t2 = query_result["slots"][1]
    t_delta = datetime.strptime(t2, time_format) - datetime.strptime(t1, time_format)
    return t_delta.seconds//60


def slot_times(slot, open_time1, close_time1, open_time2, close_time2):
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
    return formatted_time_slots


def id_generator(size=8, chars=string.digits + string.ascii_letters):
    return ''.join(random.choice(chars) for _ in range(size))


def decorate_business_name(business_name):
    return business_name + "$" + id_generator()


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
    try:
        password_from_request = request.form['password']
    except werkzeug.exceptions.BadRequestKeyError as e:
        return
    email = request.form.get('email')
    query_result = accounts_collection.find_one({"email": email})
    if query_result is None:
        return
    user = User()
    user.id = email
    user.is_authenticated = (password_from_request == query_result['password'])
    return user


@app.route('/sw.js', methods=['GET'])
def sw_provider():
    sw = open(curr_path+'/static/sw.js', "rb")
    return send_file(sw, mimetype="text/javascript")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form['email']
    qr = accounts_collection.find_one({"email": email})
    if request.form['password'] == qr['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect('/protected/'+qr['business_name']+'/calendar')
    return 'Bad login'


@app.route('/protected/<business_name>/settings', methods=['GET', 'POST'])
@flask_login.login_required
def modify_business(business_name):
    try:
        query_result_account = accounts_collection.find_one({"email": flask_login.current_user.id})
    except AttributeError:
        return redirect('/login')
    if query_result_account["business_name"] != business_name:
        return redirect('/login')
    query_result = businesses_collection.find_one({"business_name": business_name})
    t_delta = slot_size(query_result)
    if request.method == 'GET':
        return render_template('business-change-info.html', query_result=query_result, t_delta=t_delta,
                               query_result_account=query_result_account,
                               business_types_dict_italian=business_types_dict_italian)
    else:
        # Instead of checking for eventual changes, just set everything as business asked in POST request
        new_t_delta = request.form["slot"]
        new_open_time1 = request.form["open-time1"]
        new_close_time1 = request.form["close-time1"]
        new_open_time2 = request.form["open-time2"]
        new_close_time2 = request.form["close-time2"]
        new_business_name = request.form["business_name"]
        new_business_name = decorate_business_name(new_business_name)
        # Account replacement
        account_document = {"business_name": new_business_name, "fname": request.form["fname"],
                            "lname": request.form["lname"], "email": request.form["email"], "cellphone": request.form["cellphone"],
                            "password": request.form["password"]}
        accounts_collection.delete_one({"business_name": business_name})
        accounts_collection.insert_one(account_document)
        # Business replacement
        document = {"business_name": new_business_name, "business_type": request.form["type"],
                    "open_time1": new_open_time1, "close_time1": new_close_time1, "open_time2": new_open_time2,
                    "close_time2": new_close_time2, "city": request.form["city"], "address": request.form["address"],
                    "lat": request.form["lat"], "lon": request.form["lon"],
                    "creation_date": query_result["creation_date"], "creation_time": query_result["creation_time"],
                    "rating": query_result["rating"], "ratings": query_result["ratings"]}
        businesses_collection.delete_one({"business_name": business_name})
        b_sign_up_result = businesses_collection.insert_one(document)
        # Business photo replacement

        photo = request.files['img'].read()
        if len(photo) == 0:
            photo_query_result = businesses_photo_collection.find_one({"business_name": business_name})
            photo = photo_query_result["img"]
        photo_document = {"_id": b_sign_up_result.inserted_id, "business_name": new_business_name,
                          "img": photo}
        businesses_photo_collection.delete_one({"business_name": business_name})
        businesses_photo_collection.insert_one(photo_document)

        # Array of services and time slots for the business
        num_of_services = int(request.form["num_of_services"])
        services = [str(request.form["service"])]
        service_n = 2
        while service_n <= num_of_services:
            service = request.form["service_" + str(service_n)]
            if len(service) > 0:
                services.append(service)
            service_n += 1
        businesses_collection.update_one({'_id': b_sign_up_result.inserted_id},
                                         {'$push': {"service": {'$each': services}}})

        formatted_time_slots = slot_times(new_t_delta, new_open_time1, new_close_time1, new_open_time2, new_close_time2)
        businesses_collection.update_one({'_id': b_sign_up_result.inserted_id},
                                         {'$push': {"slots": {'$each': formatted_time_slots}}})
        # Change businesses name in bookings or they won't be displayed
        bookings_collection.update_one({"business_name": business_name}, {'$set': {"business_name": new_business_name}})
        return redirect('/protected/'+new_business_name+'/settings')


@app.route('/protected/<business_name>/calendar', methods=['GET'])
@flask_login.login_required
def calendar(business_name):
    try:
        query_result_account = accounts_collection.find_one({"email": flask_login.current_user.id})
    except AttributeError:
        return redirect('/login')
    if query_result_account["business_name"] != business_name:
        return redirect('/login')

    query_result = businesses_collection.find_one({"business_name": business_name})
    return render_template('calendar.html', query_result=query_result, query_result_account=query_result_account)


@app.route('/logout')
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect("/select")


@app.route('/business-calendar', methods=["GET"])
def calendar2():
    return render_template("booking-calendar.html")


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# API TO GET HOUR SLOTS
@app.route('/getslots', methods=['GET'])
def get_slots():
    b_name = request.args.get('b_name')
    date = request.args.get('date')
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


# API TO GET CITIES
@app.route('/getcities', methods=['GET'])
def get_cities():
    return jsonify(CITIES)


# API TO GET BOOKINGS
@app.route('/protected/getbookings', methods=['GET'])
def get_bookings():
    try:
        query_result_account = accounts_collection.find_one({"email": flask_login.current_user.id})
    except AttributeError:
        return 403
    business_name = request.args.get('b_name')
    if query_result_account["business_name"] != business_name:
        return jsonify([]), 403
    bookings_db = bookings_collection.find({"business_name": business_name})
    bookings = []
    for item in bookings_db:
        bookings.append({"name": item["name"], "surname": item["surname"], "email": item["email"],
                         "cellphone": item["cellphone"], "day": item["day"], "time": item["time"],
                         "service": item["service"], "rated": item["rated"]})
    return jsonify(bookings)


@app.route('/select', methods=["POST", "GET"])
def homepage_new():
    if request.method == "GET":
        city_from_cookie = request.cookies.get("city")
        if not city_from_cookie:
            city_from_cookie = ""
        return render_template("home.html", city_from_cookie=city_from_cookie)
    else:
        city = request.form["city"]
        resp = make_response(redirect('/'+city))
        resp.set_cookie("city", value=city, max_age=60 * 60 * 24)
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
    if city not in CITIES:
        return redirect('/select')
    businesses_in_city = businesses_collection.find({"city": city})
    resp = make_response(render_template('index.html', businesses_in_city=businesses_in_city, city=city,
                                         business_types_dict_italian=business_types_dict_italian))
    resp.set_cookie("city", value=city, max_age=60 * 60 * 24)
    return resp


@app.route('/business/<business_name>', methods=["POST", "GET"])
def business_page(business_name):
    if request.method == "POST":
        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        cellphone = request.form["cellphone"]
        day = request.form["date"]
        time = request.form["time"]
        service = request.form["service"]
        today = str(date.today()).replace("/", "-", 3)
        now = datetime.now().strftime('%H:%M:%S')
        document = {"business_name": business_name, "name": fname, "surname": lname, "email": email,
                    "cellphone": cellphone, "day": day, "time": time, "service": service, "booking_date": today,
                    "booking_time": now, "rated": False}
        booking_result = bookings_collection.insert_one(document)
        if SERVER_LOCAL_ONLY:
            server_name = "http://localhost:5000"
        else:
            server_name = SERVER_DOMAIN_NAME
        rating_link = server_name + "/rating/" + str(booking_result.inserted_id)
        msg = Message(subject="Come valuti "+business_name[:-9]+"?",
                      html=render_template('email-inlined.html', user_name=fname, rating_link=rating_link),
                      recipients=[email])
        mail.send(msg)
        return redirect("/booking_confirmation/"+str(booking_result.inserted_id))
    else:
        query_result = businesses_collection.find_one({"business_name": business_name})
        today = str(date.today()).replace("/", "-", 3)
        three_months = str((datetime.today() + timedelta(days=90)).strftime("%Y/%m/%d")).replace("/", "-", 3)
        return render_template("business-info.html", query_result=query_result, today=today, three_months=three_months)


@app.route('/files/tickets/<booking_id>.pdf')
def send_booking_pdf(booking_id):
    pdf_query = PDFs_collection.find_one({"_id": booking_id})
    pdf_data = bookings_collection.find_one({"_id": ObjectId(booking_id)})
    # if pdf_query is None:
    if pdf_query is None:
        temp_path = curr_path + "/temp/"
        pdf_file_name = temp_path + booking_id + ".pdf"
        qr_file_name = temp_path + booking_id + ".jpg"
        # PDF creation
        canvas = Canvas(pdf_file_name, pagesize=(612.0, 792.0))
        canvas.drawImage(curr_path+"/logo.png", 280, 720, 50, 50, [0, 0, 0, 0, 0, 0])
        canvas.drawString(280, 700, "InQueue")
        canvas.drawString(250, 650, "IL TUO BIGLIETTO")
        canvas.drawString(100, 600, "Hai prenotato il servizio " + pdf_data["service"])
        canvas.drawString(100, 580, "Presso " + pdf_data["business_name"][:-9])
        canvas.drawString(100, 560, "In data " + pdf_data["day"] + " alle ore " + pdf_data["time"])
        canvas.drawString(50, 400, "Hai prenotato come " + pdf_data["name"] + ' ' + pdf_data["surname"] + ' (' + pdf_data["email"] + ')')
        qr_img = qrcode.make("BOOKING ID: "+booking_id+"\nNAME: "+pdf_data["name"]+"\nSURNAME: "+pdf_data["surname"]+"\nDAY: "+pdf_data["day"]+"\nTIME: "+pdf_data["time"]+"\nSERVICE: "+pdf_data["service"])
        qr_img.save(qr_file_name)
        canvas.drawImage(qr_file_name, 450, 150, 100, 100)
        canvas.save()
        file = open(pdf_file_name, "rb")
        # DB insert and retrieval
        document = {"_id": booking_id, "pdf": file.read()}
        PDFs_collection.insert_one(document)
        pdf_query = PDFs_collection.find_one({"_id": booking_id})
        # Temp file deletion
        file.close()
        os.remove(pdf_file_name)
        os.remove(qr_file_name)
    return send_file(BytesIO(pdf_query["pdf"]), mimetype="application/pdf")


@app.route('/booking_confirmation/<booking_id>')
def bookings_confirmation_page(booking_id):
    try:
        query_result = bookings_collection.find_one({"_id": ObjectId(booking_id)})
    except bson.errors.InvalidId:
        return redirect('/404/')
    if query_result is not None:
        return render_template("booked.html", query_result=query_result)
    else:
        return redirect('/404/')


@app.route("/partner", methods=["POST", "GET"])
def partners_page():
    if request.method == "POST":
        # Business details caching
        email = request.form["email"]
        business_name = request.form["business_name"]
        open_time1 = request.form["open-time1"]
        close_time1 = request.form["close-time1"]
        open_time2 = request.form["open-time2"]
        close_time2 = request.form["close-time2"]
        slot = request.form["slot"]

        # Check if account is already existing
        account_found = accounts_collection.find_one({"email": email})
        if account_found is not None:
            return "email_already_signed_up", 410

        # Decorate business_name with random string to force uniqueness
        business_name = decorate_business_name(business_name)

        # Account insert
        account_document = {"business_name": business_name, "fname": request.form["fname"],
                            "lname": request.form["lname"], "email": email, "cellphone": request.form["cellphone"],
                            "password": request.form["password"]}
        accounts_collection.insert_one(account_document)
        # Business insert
        today = str(date.today()).replace("/", "-", 3)
        now = datetime.now().strftime('%H:%M:%S')
        document = {"business_name": business_name, "business_type": request.form["type"], "open_time1": open_time1,
                    "close_time1": close_time1, "open_time2": open_time2, "close_time2": close_time2,
                    "city": request.form["city"], "address": request.form["address"], "lat": request.form["lat"],
                    "lon": request.form["lon"], "creation_date": today, "creation_time": now, "rating": float(0.0),
                    "ratings": 0}
        b_sign_up_result = businesses_collection.insert_one(document)
        # Business photo insert
        photo_document = {"_id": b_sign_up_result.inserted_id, "business_name": business_name,
                          "img": request.files['img'].read()}
        businesses_photo_collection.insert_one(photo_document)

        # Array of services and time slots for the business
        num_of_services = int(request.form["num_of_services"])
        services = [str(request.form["service"])]
        service_n = 2
        while service_n <= num_of_services:
            service = request.form["service_" + str(service_n)]
            if len(service) > 0:
                services.append(service)
            service_n += 1
        businesses_collection.update_one({'_id': b_sign_up_result.inserted_id},
                                         {'$push': {"service": {'$each': services}}})

        formatted_time_slots = slot_times(slot, open_time1, close_time1, open_time2, close_time2)
        businesses_collection.update_one({'_id': b_sign_up_result.inserted_id},
                                         {'$push': {"slots": {'$each': formatted_time_slots}}})

        return redirect("/newBusiness_confirmation/"+business_name)
    else:
        return render_template("business-creation.html")


@app.route('/rating/<booking_id>', methods=["GET", "POST"])
def rate(booking_id):
    # Check booking existence and if it's already rated
    try:
        query_result = bookings_collection.find_one({"_id": ObjectId(booking_id)})
    except bson.errors.InvalidId:
        return redirect('/404/')
    if query_result["rated"]:
        return "Business already rated ", 410

    if request.method == 'GET':
        return render_template("rate.html", query_result=query_result)
    else:
        business_name = query_result["business_name"]
        business_query_result = businesses_collection.find_one({"business_name": business_name})
        new_business_ratings = business_query_result["ratings"] + 1
        new_rating = (business_query_result["rating"]*(new_business_ratings-1))/new_business_ratings + (int(request.form["rating"])/new_business_ratings)
        businesses_collection.update_one({"business_name": business_name},
                                         {'$set': {"rating": new_rating}})
        businesses_collection.update_one({"business_name": business_name},
                                         {'$set': {"ratings": new_business_ratings}})
        bookings_collection.update_one({"business_name": business_name},
                                       {'$set': {"rated": True}})
        return redirect("/business/"+business_name)


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
def list_cities(city):
    businesses_in_city = businesses_collection.find({"city": city})
    resp = make_response(render_template('list.html', businesses_in_city=businesses_in_city, city=city,
                                         business_types_dict_italian=business_types_dict_italian))
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_debugger=True)
