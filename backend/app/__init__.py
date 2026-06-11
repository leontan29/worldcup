from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["SECRET_KEY"]

    CORS(app, origins=os.environ.get("CORS_ORIGINS", "").split(","), supports_credentials=True)

    from .routes import auth, teams, matches, venues, leaderboards, standings, predictions, user, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(teams.bp)
    app.register_blueprint(matches.bp)
    app.register_blueprint(venues.bp)
    app.register_blueprint(leaderboards.bp)
    app.register_blueprint(standings.bp)
    app.register_blueprint(predictions.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)

    return app
