from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

_DIST = os.path.join(os.path.dirname(__file__), '../../frontend/dist')


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ["SECRET_KEY"]

    CORS(app, origins=os.environ.get("CORS_ORIGINS", "").split(","), supports_credentials=True)

    from .routes import auth, teams, matches, venues, leaderboards, standings, predictions, user, admin
    from .auth import activity
    app.register_blueprint(auth.bp)
    app.register_blueprint(teams.bp)
    app.register_blueprint(matches.bp)
    app.register_blueprint(venues.bp)
    app.register_blueprint(leaderboards.bp)
    app.register_blueprint(standings.bp)
    app.register_blueprint(predictions.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(activity.bp)

    if os.path.isdir(_DIST):
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_spa(path):
            full = os.path.join(_DIST, path)
            if path and os.path.isfile(full):
                return send_from_directory(_DIST, path)
            return send_from_directory(_DIST, 'index.html')

    return app
