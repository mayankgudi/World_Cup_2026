import os
import json
import smtplib
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from worldcup_logic import generate_round_of_32
from models import db, BracketPrediction, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash

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
            return redirect(url_for("login", next=request.path))

        return route_function(*args, **kwargs)

    return wrapper

@app.route("/")
def home():
    current_user = get_current_user()

    user_has_bracket = False

    if current_user:
        user_has_bracket = BracketPrediction.query.filter_by(
            user_id=current_user.id
        ).count() >= 1

    return render_template(
        "home.html",
        current_user=current_user,
        user_has_bracket=user_has_bracket
    )


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.query.get(user_id)

def current_user_is_admin():
    current_user = get_current_user()

    if not current_user:
        return False

    return bool(current_user.is_admin)

# Needed so Flask can use session storage.
app.secret_key = "world-cup-predictor-secret-key"

# --------------------------------
#            Constants
# --------------------------------

GROUPS = {
    "A": [
        {"name": "Czechia", "flag": "wc_flags/czechia.svg"},
        {"name": "Mexico", "flag": "wc_flags/mexico.svg"},
        {"name": "South Africa", "flag": "wc_flags/south_africa.svg"},
        {"name": "South Korea", "flag": "wc_flags/korea.svg"},
    ],

    "B": [
        {"name": "Bosnia & Herzegovina", "flag": "wc_flags/bosnia.svg"},
        {"name": "Canada", "flag": "wc_flags/canada.svg"},
        {"name": "Qatar", "flag": "wc_flags/qatar.svg"},
        {"name": "Switzerland", "flag": "wc_flags/swiss.svg"},
    ],

    "C": [
        {"name": "Brazil", "flag": "wc_flags/brazil.svg"},
        {"name": "Haiti", "flag": "wc_flags/haiti.svg"},
        {"name": "Morocco", "flag": "wc_flags/morocco.svg"},
        {"name": "Scotland", "flag": "wc_flags/scotland.svg"},
    ],

    "D": [
        {"name": "Australia", "flag": "wc_flags/australia.svg"},
        {"name": "Paraguay", "flag": "wc_flags/paraguay.svg"},
        {"name": "Turkiye", "flag": "wc_flags/turkey.svg"},
        {"name": "USA", "flag": "wc_flags/usa.svg"},
    ],

    "E": [
        {"name": "Curacao", "flag": "wc_flags/curacao.svg"},
        {"name": "Ecuador", "flag": "wc_flags/ecuador.svg"},
        {"name": "Germany", "flag": "wc_flags/germany.svg"},
        {"name": "Ivory Coast", "flag": "wc_flags/ivory_coast.svg"},
    ],

    "F": [
        {"name": "Japan", "flag": "wc_flags/japan.svg"},
        {"name": "Netherlands", "flag": "wc_flags/netherlands.svg"},
        {"name": "Sweden", "flag": "wc_flags/sweden.svg"},
        {"name": "Tunisia", "flag": "wc_flags/tunisia.svg"},
    ],

    "G": [
        {"name": "Belgium", "flag": "wc_flags/belgium.svg"},
        {"name": "Egypt", "flag": "wc_flags/egypt.svg"},
        {"name": "Iran", "flag": "wc_flags/iran.svg"},
        {"name": "New Zealand", "flag": "wc_flags/new_zealand.svg"},
    ],

    "H": [
        {"name": "Cape Verde", "flag": "wc_flags/cape_verde.svg"},
        {"name": "Saudi Arabia", "flag": "wc_flags/saudi.svg"},
        {"name": "Spain", "flag": "wc_flags/spain.svg"},
        {"name": "Uruguay", "flag": "wc_flags/uruguay.svg"},
    ],

    "I": [
        {"name": "France", "flag": "wc_flags/france.svg"},
        {"name": "Iraq", "flag": "wc_flags/iraq.svg"},
        {"name": "Norway", "flag": "wc_flags/norway.svg"},
        {"name": "Senegal", "flag": "wc_flags/senegal.svg"},
    ],

    "J": [
        {"name": "Algeria", "flag": "wc_flags/algeria.svg"},
        {"name": "Argentina", "flag": "wc_flags/argentina.svg"},
        {"name": "Austria", "flag": "wc_flags/austria.svg"},
        {"name": "Jordan", "flag": "wc_flags/jordan.svg"},
    ],

    "K": [
        {"name": "Colombia", "flag": "wc_flags/colombia.svg"},
        {"name": "DR Congo", "flag": "wc_flags/congo.svg"},
        {"name": "Portugal", "flag": "wc_flags/portugal.svg"},
        {"name": "Uzbekistan", "flag": "wc_flags/uzbekistan.svg"},
    ],

    "L": [
        {"name": "Croatia", "flag": "wc_flags/croatia.svg"},
        {"name": "England", "flag": "wc_flags/england.svg"},
        {"name": "Ghana", "flag": "wc_flags/ghana.svg"},
        {"name": "Panama", "flag": "wc_flags/panama.svg"},
    ],
}


TEAM_CODES = {
    "Czechia": "CZE",
    "Mexico": "MEX",
    "South Africa": "RSA",
    "South Korea": "KOR",

    "Bosnia & Herzegovina": "BIH",
    "Canada": "CAN",
    "Qatar": "QAT",
    "Switzerland": "SUI",

    "Brazil": "BRA",
    "Haiti": "HAI",
    "Morocco": "MAR",
    "Scotland": "SCO",

    "Australia": "AUS",
    "Paraguay": "PAR",
    "Turkiye": "TUR",
    "USA": "USA",

    "Curacao": "CUW",
    "Ecuador": "ECU",
    "Germany": "GER",
    "Ivory Coast": "CIV",

    "Japan": "JPN",
    "Netherlands": "NED",
    "Sweden": "SWE",
    "Tunisia": "TUN",

    "Belgium": "BEL",
    "Egypt": "EGY",
    "Iran": "IRN",
    "New Zealand": "NZL",

    "Cape Verde": "CPV",
    "Saudi Arabia": "KSA",
    "Spain": "ESP",
    "Uruguay": "URU",

    "France": "FRA",
    "Iraq": "IRQ",
    "Norway": "NOR",
    "Senegal": "SEN",

    "Algeria": "ALG",
    "Argentina": "ARG",
    "Austria": "AUT",
    "Jordan": "JOR",

    "Colombia": "COL",
    "DR Congo": "COD",
    "Portugal": "POR",
    "Uzbekistan": "UZB",

    "Croatia": "CRO",
    "England": "ENG",
    "Ghana": "GHA",
    "Panama": "PAN",
}


SCORING_RULES = {
    "group_winner": 2,
    "group_runner_up": 2,
    "third_place_top_8": 1,
    "round_of_32": 1,
    "round_of_16": 2,
    "quarterfinal": 4,
    "semifinal": 8,
    "third_place_match": 10,
    "final": 20,
}

MAX_POINTS = {
    "group_stage": 48,
    "third_place_race": 8,
    "knockout": 94,
    "total": 150,
}




# --------------------------------
#           Functions
# --------------------------------

def get_team_code(team_name):
    return TEAM_CODES.get(team_name, team_name[:3].upper())


def get_team_flag(team_name):
    for teams in GROUPS.values():
        for team in teams:
            if team["name"] == team_name:
                return team["flag"]

    return "wc_flags/usa.svg"


def get_team_object(team_name):
    for teams in GROUPS.values():
        for team in teams:
            if team["name"] == team_name:
                return team

    return {
        "name": team_name,
        "flag": "wc_flags/placeholder.svg"
    }


def get_ordered_groups_for_display():
    saved_group_results = session.get("group_results")

    if not saved_group_results:
        return GROUPS

    ordered_groups = {}

    for group_letter, teams in GROUPS.items():
        saved_group = saved_group_results.get(group_letter)

        if not saved_group:
            ordered_groups[group_letter] = teams
            continue

        ordered_team_names = [
            saved_group.get("first"),
            saved_group.get("second"),
            saved_group.get("third"),
            saved_group.get("fourth"),
        ]

        ordered_groups[group_letter] = [
            get_team_object(team_name)
            for team_name in ordered_team_names
            if team_name
        ]

    return ordered_groups


def get_password_reset_serializer():
    return URLSafeTimedSerializer(app.secret_key)


def generate_password_reset_token(email):
    serializer = get_password_reset_serializer()

    return serializer.dumps(
        email,
        salt="password-reset-salt"
    )


def verify_password_reset_token(token, expiration_seconds=1800):
    serializer = get_password_reset_serializer()

    try:
        email = serializer.loads(
            token,
            salt="password-reset-salt",
            max_age=expiration_seconds
        )
        return email

    except SignatureExpired:
        return None

    except BadSignature:
        return None


def send_password_reset_email(to_email, reset_link):
    mail_server = os.getenv("MAIL_SERVER")
    mail_port = int(os.getenv("MAIL_PORT", "587"))
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_sender = os.getenv("MAIL_DEFAULT_SENDER", mail_username)

    if not all([mail_server, mail_username, mail_password, mail_sender]):
        print("Password reset link:", reset_link)
        return

    message = EmailMessage()
    message["Subject"] = "Reset your World Cup Bracket Challenge password"
    message["From"] = mail_sender
    message["To"] = to_email

    message.set_content(
        f"""
You requested a password reset for your World Cup Bracket Challenge account.

Click the link below to reset your password:

{reset_link}

This link expires in 30 minutes.

If you did not request this, you can ignore this email.
"""
    )

    with smtplib.SMTP(mail_server, mail_port) as server:
        server.starttls()
        server.login(mail_username, mail_password)
        server.send_message(message)



def add_flags_to_bracket(bracket_games):
    for game in bracket_games:
        game["team_1_flag"] = get_team_flag(game["team_1"])
        game["team_2_flag"] = get_team_flag(game["team_2"])

    return bracket_games


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

        next_page = request.args.get("next")

        if next_page:
            return redirect(next_page)

        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")




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

        next_page = request.args.get("next")

        if next_page:
            return redirect(next_page)

        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None

    if request.method == "POST":
        email = request.form["email"].strip().lower()

        user = User.query.filter_by(email=email).first()

        message = "If an account exists with that email, a password reset link has been sent."

        if user:
            token = generate_password_reset_token(user.email)

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            send_password_reset_email(user.email, reset_link)

    return render_template(
        "forgot_password.html",
        message=message
    )


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_password_reset_token(token)

    if not email:
        return render_template(
            "reset_password.html",
            error="This password reset link is invalid or has expired.",
            token=None
        )

    user = User.query.filter_by(email=email).first()

    if not user:
        return render_template(
            "reset_password.html",
            error="This password reset link is invalid.",
            token=None
        )

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not password or not confirm_password:
            return render_template(
                "reset_password.html",
                error="Both password fields are required.",
                token=token
            )

        if password != confirm_password:
            return render_template(
                "reset_password.html",
                error="Passwords do not match.",
                token=token
            )

        if len(password) < 8:
            return render_template(
                "reset_password.html",
                error="Password must be at least 8 characters long.",
                token=token
            )

        user.password_hash = generate_password_hash(password)
        db.session.commit()

        return redirect(url_for("login", reset_success="1"))

    return render_template(
        "reset_password.html",
        token=token
    )


@app.route("/groups", methods=["GET", "POST"])
@login_required
def group_stage():
    if request.method == "POST":
        group_results = {}

        try:
            for group_letter in GROUPS:
                group_results[group_letter] = {
                    "first": request.form[f"{group_letter}_first"],
                    "second": request.form[f"{group_letter}_second"],
                    "third": request.form[f"{group_letter}_third"],
                    "fourth": request.form[f"{group_letter}_fourth"],
                }

            session["group_results"] = group_results

            return redirect(url_for("third_place"))

        except KeyError:
            return render_template(
                "group_stage.html",
                groups=GROUPS,
                get_team_code=get_team_code,
                get_team_flag=get_team_flag,
                saved_group_results=session.get("group_results"),
                editing_bracket_id=session.get("editing_bracket_id"),
                error="Please fill every position in every group."
            )

    return render_template(
        "group_stage.html",
        groups=GROUPS,
        get_team_code=get_team_code,
        get_team_flag=get_team_flag,
        saved_group_results=session.get("group_results"),
        editing_bracket_id=session.get("editing_bracket_id")
    )


def get_third_place_teams_for_display():
    group_results = session.get("group_results")
    saved_ranking = session.get("third_place_ranking")

    if not group_results:
        return []

    third_place_teams_by_group = {}

    for group_letter, results in group_results.items():
        third_place_team = results["third"]

        third_place_teams_by_group[group_letter] = {
            "group": group_letter,
            "team": third_place_team,
            "flag": get_team_flag(third_place_team)
        }

    if not saved_ranking:
        return list(third_place_teams_by_group.values())

    ordered_third_place_teams = []

    for group_letter in saved_ranking:
        if group_letter in third_place_teams_by_group:
            ordered_third_place_teams.append(
                third_place_teams_by_group[group_letter]
            )

    for group_letter, item in third_place_teams_by_group.items():
        if group_letter not in saved_ranking:
            ordered_third_place_teams.append(item)

    return ordered_third_place_teams


@app.route("/third-place", methods=["GET", "POST"])
@login_required
def third_place():
    group_results = session.get("group_results")

    if not group_results:
        return redirect(url_for("group_stage"))

    if request.method == "POST":
        third_place_ranking = []

        try:
            for i in range(1, 13):
                third_place_ranking.append(request.form[f"rank_{i}"])
        except KeyError:
            return render_template(
                "third_place.html",
                third_place_teams=get_third_place_teams_for_display(),
                saved_third_place_ranking=session.get("third_place_ranking"),
                error="Please select exactly 8 third-place teams."
            )

        session["third_place_ranking"] = third_place_ranking

        return redirect(url_for("bracket"))

    return render_template(
        "third_place.html",
        third_place_teams=get_third_place_teams_for_display(),
        saved_third_place_ranking=session.get("third_place_ranking")
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
        bracket_games = add_flags_to_bracket(bracket_games)
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

    if bracket_count >= 1:
        return render_template(
            "bracket.html",
            bracket=add_flags_to_bracket(generate_round_of_32(group_results, third_place_ranking)),
            error="You have already submitted a bracket. You may only submit 1 bracket per account.",
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
    current_user = get_current_user()
    prediction = BracketPrediction.query.get_or_404(prediction_id)

    if prediction.user_id != current_user.id and not current_user.is_admin:
        return redirect(url_for("saved_brackets"))

    return render_template(
        "saved_bracket.html",
        prediction=prediction,
        get_team_flag=get_team_flag
    )


@app.route("/saved")
@login_required
def saved_brackets():
    current_user = get_current_user()

    predictions = BracketPrediction.query.order_by(
        BracketPrediction.created_at.desc()
    ).all()

    user_has_bracket = BracketPrediction.query.filter_by(
        user_id=current_user.id
    ).count() >= 1

    return render_template(
        "all_brackets.html",
        predictions=predictions,
        get_team_flag=get_team_flag,
        user_has_bracket=user_has_bracket,
        current_user_is_admin=current_user.is_admin
    )

@app.route("/delete-bracket/<int:prediction_id>", methods=["POST"])
@login_required
def delete_bracket(prediction_id):
    current_user = get_current_user()

    prediction = BracketPrediction.query.get_or_404(prediction_id)

    user_owns_bracket = prediction.user_id == current_user.id
    user_is_admin = current_user.is_admin

    if not user_owns_bracket and not user_is_admin:
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
    current_user = get_current_user()

    bracket_count = BracketPrediction.query.filter_by(
        user_id=current_user.id
    ).count()

    if bracket_count >= 1:
        return redirect(url_for("saved_brackets", error="limit_reached"))

    session.pop("group_results", None)
    session.pop("third_place_ranking", None)
    session.pop("knockout_picks", None)
    session.pop("editing_bracket_id", None)

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