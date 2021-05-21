from flask import Flask, render_template, url_for, request, redirect


app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("index.html", city="Napoli")

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


if __name__ == "__main__":
    app.run(debug=True)

