import os
import json
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from worldcup_logic import generate_round_of_32
from models import db, BracketPrediction, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return route_function(*args, **kwargs)

    return wrapper


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.query.get(user_id)

# Needed so Flask can use session storage.
app.secret_key = "world-cup-predictor-secret-key"

GROUPS = {
    "A": ["Czechia", "Mexico", "South Africa", "South Korea"],
    "B": ["Bosnia & Herzegovina", "Canada", "Qatar", "Switzerland"],
    "C": ["Brazil", "Haiti", "Morocco", "Scotland"],
    "D": ["Australia", "Paraguay", "Turkiye", "USA"],
    "E": ["Curacao", "Ecuador", "Germany", "Ivory Coast"],
    "F": ["Japan", "Netherlands", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Cape Verde", "Saudi Arabia", "Spain", "Uruguay"],
    "I": ["France", "Iraq", "Norway", "Senegal"],
    "J": ["Algeria", "Argentina", "Austria", "Jordan"],
    "K": ["Colombia", "DR Congo", "Portugal", "Uzbekistan"],
    "L": ["Croatia", "England", "Ghana", "Panama"],
}


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not username or not email or not password:
            return render_template(
                "register.html",
                error="All fields are required."
            )

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return render_template(
                "register.html",
                error="That username or email is already taken."
            )

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        session["username"] = new_user.username

        return redirect(url_for("group_stage"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form["username_or_email"].strip()
        password = request.form["password"]

        user = User.query.filter(
            (User.username == username_or_email) |
            (User.email == username_or_email.lower())
        ).first()

        if not user or not check_password_hash(user.password_hash, password):
            return render_template(
                "login.html",
                error="Invalid username/email or password."
            )

        session["user_id"] = user.id
        session["username"] = user.username

        return redirect(url_for("group_stage"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def group_stage():
    if request.method == "POST":
        group_results = {}

        for group_letter in GROUPS:
            group_results[group_letter] = {
                "first": request.form[f"{group_letter}_first"],
                "second": request.form[f"{group_letter}_second"],
                "third": request.form[f"{group_letter}_third"],
                "fourth": request.form[f"{group_letter}_fourth"],
            }

        # Save group results so the next page can use them.
        session["group_results"] = group_results

        return redirect(url_for("third_place"))

    return render_template("group_stage.html", groups=GROUPS)


@app.route("/third-place", methods=["GET", "POST"])
@login_required
def third_place():
    group_results = session.get("group_results")

    if not group_results:
        return redirect(url_for("group_stage"))

    third_place_teams = []

    for group_letter, results in group_results.items():
        third_place_teams.append({
            "group": group_letter,
            "team": results["third"]
        })

    if request.method == "POST":
        third_place_ranking = []

        for rank_number in range(1, 13):
            group_letter = request.form[f"rank_{rank_number}"]
            third_place_ranking.append(group_letter)

        session["third_place_ranking"] = third_place_ranking

        return redirect(url_for("bracket"))

    return render_template(
        "third_place.html",
        third_place_teams=third_place_teams
    )


@app.route("/bracket")
@login_required
def bracket():
    group_results = session.get("group_results")
    third_place_ranking = session.get("third_place_ranking")

    if not group_results:
        return redirect(url_for("group_stage"))

    if not third_place_ranking:
        return redirect(url_for("third_place"))

    error = None
    bracket_games = None
    bracket_name = ""

    try:
        bracket_games = generate_round_of_32(group_results, third_place_ranking)
    except Exception as e:
        error = str(e)

    editing_bracket_id = session.get("editing_bracket_id")

    if editing_bracket_id:
        prediction = BracketPrediction.query.get(editing_bracket_id)
        if prediction:
            bracket_name = prediction.bracket_name

    return render_template(
        "bracket.html",
        bracket=bracket_games,
        error=error,
        third_place_ranking=third_place_ranking,
        editing_bracket_id=editing_bracket_id,
        saved_knockout_picks=session.get("knockout_picks"),
        bracket_name=bracket_name
    )


@app.route("/save-bracket", methods=["POST"])
@login_required
def save_bracket():
    group_results = session.get("group_results")
    third_place_ranking = session.get("third_place_ranking")

    if not group_results or not third_place_ranking:
        return redirect(url_for("group_stage"))

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    bracket_name = request.form.get("bracket_name", "").strip()

    if not bracket_name:
        bracket_name = f"{current_user.username}'s Bracket"

    knockout_picks_raw = request.form.get("knockout_picks", "{}")
    knockout_picks = json.loads(knockout_picks_raw)

    editing_bracket_id = session.get("editing_bracket_id")

    if editing_bracket_id:
        prediction = BracketPrediction.query.get_or_404(editing_bracket_id)

        if prediction.user_id != current_user.id:
            return redirect(url_for("saved_brackets"))

        prediction.bracket_name = bracket_name
        prediction.group_results = group_results
        prediction.third_place_ranking = third_place_ranking
        prediction.knockout_picks = knockout_picks

        db.session.commit()

        session.pop("editing_bracket_id", None)
        session.pop("knockout_picks", None)

        return redirect(url_for("view_bracket", prediction_id=prediction.id))

    bracket_count = BracketPrediction.query.filter_by(
        user_id=current_user.id
    ).count()

    if bracket_count >= 3:
        return render_template(
            "bracket.html",
            bracket=generate_round_of_32(group_results, third_place_ranking),
            error="You have already submitted the maximum of 3 brackets.",
            third_place_ranking=third_place_ranking,
            editing_bracket_id=None,
            saved_knockout_picks=None,
            bracket_name=bracket_name
        )

    prediction = BracketPrediction(
        username=current_user.username,
        user_id=current_user.id,
        bracket_name=bracket_name,
        group_results=group_results,
        third_place_ranking=third_place_ranking,
        knockout_picks=knockout_picks
    )

    db.session.add(prediction)
    db.session.commit()

    return redirect(url_for("view_bracket", prediction_id=prediction.id))

@app.route("/saved/<int:prediction_id>")
@login_required
def view_bracket(prediction_id):
    prediction = BracketPrediction.query.get_or_404(prediction_id)

    return render_template(
        "saved_bracket.html",
        prediction=prediction
    )


@app.route("/saved")
@login_required
def saved_brackets():
    predictions = BracketPrediction.query.order_by(
        BracketPrediction.created_at.desc()
    ).all()

    return render_template(
        "all_brackets.html",
        predictions=predictions
    )

@app.route("/delete-bracket/<int:prediction_id>", methods=["POST"])
@login_required
def delete_bracket(prediction_id):
    current_user = get_current_user()

    prediction = BracketPrediction.query.get_or_404(prediction_id)

    if prediction.user_id != current_user.id:
        return redirect(url_for("saved_brackets"))

    db.session.delete(prediction)
    db.session.commit()

    return redirect(url_for("saved_brackets"))


@app.route("/edit-bracket/<int:prediction_id>")
@login_required
def edit_bracket(prediction_id):
    current_user = get_current_user()

    prediction = BracketPrediction.query.get_or_404(prediction_id)

    if prediction.user_id != current_user.id:
        return redirect(url_for("saved_brackets"))

    session["editing_bracket_id"] = prediction.id
    session["group_results"] = prediction.group_results
    session["third_place_ranking"] = prediction.third_place_ranking
    session["knockout_picks"] = prediction.knockout_picks

    return redirect(url_for("bracket"))


@app.route("/new-bracket")
@login_required
def new_bracket():
    user_id = session.get("user_id")
    username = session.get("username")

    session.pop("group_results", None)
    session.pop("third_place_ranking", None)
    session.pop("knockout_picks", None)
    session.pop("editing_bracket_id", None)

    session["user_id"] = user_id
    session["username"] = username

    return redirect(url_for("group_stage"))


@app.route("/reset")
@login_required
def reset():
    user_id = session.get("user_id")
    username = session.get("username")

    session.pop("group_results", None)
    session.pop("third_place_ranking", None)
    session.pop("knockout_picks", None)
    session.pop("editing_bracket_id", None)

    session["user_id"] = user_id
    session["username"] = username

    return redirect(url_for("group_stage"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)