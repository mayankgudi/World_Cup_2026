from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    brackets = db.relationship(
        "BracketPrediction",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


class BracketPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    bracket_name = db.Column(db.String(150), nullable=False, default="Untitled Bracket")

    group_results = db.Column(db.JSON, nullable=False)
    third_place_ranking = db.Column(db.JSON, nullable=False)
    knockout_picks = db.Column(db.JSON, nullable=True)

    tiebreaker_goals = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )