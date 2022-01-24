import json

import flask
from flask import Flask, render_template, redirect, url_for, request, flash, abort
# import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from datetime import datetime
import os, requests, re

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

uri = os.environ.get("DATABASE_URL", "sqlite:///cafes.db")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    cafes = relationship("Cafe", back_populates="author")


class Cafe(db.Model):
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(250))
    coffee_price = db.Column(db.String(250))
    city = db.Column(db.String(250), nullable=False)
    country = db.Column(db.String(250), nullable=False)
    author = relationship("User", back_populates="cafes")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)


db.create_all()


@app.route("/register", methods=["POST"])
def register():
    form = RegisterForm()
    print(form.current_url.data)
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            # User already exists
            flash("You've already signed up with that email, log in instead or use a different email to register.")
            return redirect(form.current_url.data + "?error=registration")

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(form.current_url.data)
    print(form.errors)
    return redirect(form.current_url.data + "?error=registration")


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    print(form)
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist in our database, please try again or register.")
            return redirect(form.current_url.data + "?error=login")
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(form.current_url.data + "?error=login")
        else:
            login_user(user)
            return redirect(url_for("home"))
    print(form.errors)
    return redirect(form.current_url.data + "?error=login")


@app.route('/logout')
def logout():
    print("logging out")
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    loginForm = LoginForm()
    registrationForm = RegisterForm()
    cafes = Cafe.query.all()
    locations = {}
    for cafe in cafes:
        if not cafe.country in locations.keys():
            locations[cafe.country] = []
        if not cafe.city in locations[cafe.country]:
            locations[cafe.country].append(cafe.city)
    print(locations)
    return render_template("cities-list.html", loginForm=loginForm, registrationForm=registrationForm,
                           locations=locations)


@app.route("/delete_cafe/<cafe_id>", methods=["POST", "GET"])
def delete_cafe(cafe_id):
    selectedCafe = Cafe.query.get(cafe_id)
    if request.method == 'GET' and current_user.id == selectedCafe.author.id:
        db.session.delete(selectedCafe)
        db.session.commit()
        return redirect(url_for("home"))
    else:
        abort(401)


@app.route("/city/<city_name>", methods=["POST", "GET"])
def city(city_name):
    loginForm = LoginForm()
    registrationForm = RegisterForm()
    cafes = Cafe.query.filter_by(city=city_name).all()
    print(cafes)
    return render_template("city.html", cafes=cafes, city=city_name, loginForm=loginForm,
                           registrationForm=registrationForm)


@app.route("/convertURL", methods=["POST"])
def convert_url_to_latlang():
    headers = {
        'User-agent': "Mozilla/5.0"
    }
    response = requests.get(request.form["url"], headers=headers, allow_redirects=True)
    cafe = Cafe.query.get(request.form["id"])
    print(response.url)
    for r in response.history:
        print(r.status_code)

    print(response.status_code)
    print(response.url)
    print(response.headers)
    print(response.cookies)

    print(cafe)
    regex = r"@(.*),(.*),(.*)/"
    result = re.search(regex, response.url)
    data = None
    if result is None:
        # print(response.text)
        newtext = response.text
        regex = r"@([\d\.-]{5,12}),([\d\.-]{5,12}),"
        result = re.search(regex, newtext)
        print(result.groups())
    if result is not None:
        data = result.groups()
        cafe.lat = data[0]
        cafe.long = data[1]
        db.session.commit()
        return (f"{data[0]},{data[1]}")

    return (f"")
    pass


@app.route("/addCafe", methods=["POST", "GET"])
@login_required
def add_cafe():
    if request.method == 'POST':
        data = request.form;
        print(data["name"])

        if not current_user.is_authenticated:
            flash("You need to login to add cafe")
            return redirect("add_cafe" + "?error=login")
        new_cafe = Cafe(
            name=data["name"],
            map_url="#",
            img_url=data["image-link"],
            location=data["address"],
            has_sockets=data["sockets"] == "True",
            has_toilet=data["toilet"] == "True",
            has_wifi=data["wifi"] == "True",
            can_take_calls=data["calls"] == "True",
            seats=data["seats"],
            coffee_price="$" + data["price"],
            city=data["city"],
            country=data["country"],
            author=current_user,
            lat=data["lat"],
            long=data["long"]
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect("/city/" + data["city"])
    loginForm = LoginForm()
    registrationForm = RegisterForm()
    return render_template("add-cafe.html", loginForm=loginForm, registrationForm=registrationForm)


@app.route("/editCafe/<cafe_id>", methods=["POST", "GET"])
@login_required
def edit_cafe(cafe_id):
    selectedCafe = Cafe.query.get(cafe_id)
    if request.method == 'POST':
        data = request.form;
        print(data)
        if not current_user.id == selectedCafe.author.id:
            abort(401)
        selectedCafe.img_url = data["image-link"]
        selectedCafe.has_sockets = data["sockets"] == "True"
        selectedCafe.has_toilet = data["toilet"] == "True"
        selectedCafe.has_wifi = data["wifi"] == "True"
        selectedCafe.can_take_calls = data["calls"] == "True"
        selectedCafe.seats = data["seats"]
        selectedCafe.coffee_price = "$" + data["price"]
        db.session.commit()
        return redirect("/city/" + data["city"])
    loginForm = LoginForm()
    registrationForm = RegisterForm()
    if not current_user.id == selectedCafe.author.id:
        abort(401)
    return render_template("edit-cafe.html", loginForm=loginForm, registrationForm=registrationForm, cafe=selectedCafe)


@app.route("/viewCafe/<id>", methods=["POST", "GET"])
def view_cafe(id):
    selectedCafe = Cafe.query.get(id)
    loginForm = LoginForm()
    registrationForm = RegisterForm()
    return render_template("view-cafe.html", cafe=selectedCafe, loginForm=loginForm, registrationForm=registrationForm)


@app.errorhandler(404)
def custom_404(error):
    return "Where are you going bro?", 404


@app.errorhandler(401)
def custom_401(error):
    return "You are not authorized bro", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}


@login_manager.unauthorized_handler
def unauthorized():
    return "You are required to login bro", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}


if __name__ == "__main__":
    app.run(debug=True)
