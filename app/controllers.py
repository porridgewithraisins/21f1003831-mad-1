import os
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash

from app.models import User
from app.utils import export_data, import_data, plot
from app.validation import validate_log, validate_tracker, validate_user

bp = Blueprint("controllers", __name__)


@bp.before_request
def before_request():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = User.get(id=user_id)
    if not g.user and request.endpoint not in ["controllers.login", "controllers.register"]:
        flash("You must be logged in", "error")
        return redirect("/login")


@bp.get("/")
def index():
    return render_template("index.html", user=g.user)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    result, err = validate_user(request.form)

    if err:
        flash(err, "error")
        return redirect(request.url)

    username, password = result

    exists = User.get(username=username)

    if exists:
        flash(f"Username {username} already exists", "error")
        return redirect(request.url)

    user = User(username=username, password=generate_password_hash(password))

    session["user_id"] = user.id

    return redirect("/")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    result, err = validate_user(request.form)

    if err:
        flash(err, "error")
        return redirect(request.url)

    username, password = result

    user = User.get(username=username)
    if not user or not user.compare_password(password):
        flash("Invalid username or password", "error")
        return redirect("/login")

    session["user_id"] = user.id
    return redirect("/")


@bp.get("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")


@bp.route("/profile")
def profile():
    user = g.user
    tracker_count = user.trackers.count()
    log_count = sum(len(tracker.logs) for tracker in user.trackers)
    return render_template(
        "profile.html", username=user.username, tracker_count=tracker_count, log_count=log_count
    )


@bp.route("/trackers", methods=["GET", "POST"])
def trackers():
    if request.method == "GET":
        trackers = g.user.trackers
        ordered = sorted(trackers.logs, key=lambda l: l.timestamp, reverse=True)
        last_accessed = ordered[0].timestamp if ordered else "Never"
        return render_template(
            "trackers.html", trackers=g.user.trackers, last_accessed=last_accessed
        )

    (name, type, settings), err = validate_tracker(request.form)

    if err:
        flash(err, "error")
        return redirect(request.url)

    g.user.trackers.create(name=name, type=type, settings=settings)

    flash("Tracker created", "success")
    return redirect("/trackers")


@bp.route("/trackers/<int:tracker_id>", methods=["GET", "POST"])
def tracker(tracker_id):
    tracker = g.user.trackers.select(lambda t: t.id == tracker_id).first()
    if not tracker:
        flash("Tracker not found", "error")
        return redirect("/trackers")

    if request.method == "GET":
        return render_template("tracker.html", tracker=tracker)

    result, err = validate_tracker(request.form)

    if err:
        flash(err, "error")
        return redirect(request.url)

    tracker.name, tracker.type, tracker.settings = result

    flash("Tracker updated", "success")
    return redirect("/trackers")


@bp.get("/trackers/<int:tracker_id>/delete")
def delete_tracker(tracker_id):
    tracker = g.user.trackers.select(lambda t: t.id == tracker_id).first()
    if not tracker:
        flash("Tracker not found", "error")
        return redirect("/trackers")
    tracker.delete()
    flash("Tracker deleted", "success")
    return redirect("/trackers")


@bp.route("/trackers/<int:tracker_id>/logs", methods=["GET", "POST"])
def logs(tracker_id):
    tracker = g.user.trackers.select(lambda t: t.id == tracker_id).first()
    if not tracker:
        flash("Tracker not found", "error")
        return redirect("/trackers")
    if request.method == "GET":
        filename = f"images/{tracker.id}.png"
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "static", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        plot(tracker, filepath)
        return render_template(
            "logs.html",
            tracker=tracker,
            now=datetime.now().isoformat().rsplit(".")[0].rsplit(":", maxsplit=1)[0],
            image_url=url_for("static", filename=filename),
        )

    result, err = validate_log(tracker, request.form)

    if err:
        flash(err, "error")
        return redirect(request.url)

    timestamp, value, note = result
    tracker.logs.create(timestamp=timestamp, value=value, note=note)

    flash("Log added successfully", "success")
    return redirect(request.url)


@bp.route("/trackers/<int:tracker_id>/logs/<int:log_id>", methods=["GET", "POST"])
def log(tracker_id, log_id):
    tracker = g.user.trackers.select(lambda t: t.id == tracker_id).first()
    if not tracker:
        flash("Tracker not found", "error")
        return redirect("/trackers")
    log = tracker.logs.select(lambda l: l.id == log_id).first()
    if not log:
        flash("Log not found", "error")
        return redirect("/trackers")

    if request.method == "GET":
        print(log.timestamp)
        return render_template("log.html", log=log)

    result, err = validate_log(tracker, request.form)

    if err:
        flash(err, "error")
        return redirect(request.url)

    log.timestamp, log.value, log.note = result

    flash("Log updated successfully", "success")
    return redirect(request.url)


@bp.get("/trackers/<int:tracker_id>/logs/<int:log_id>/delete")
def delete_log(tracker_id, log_id):
    tracker = g.user.trackers.select(lambda t: t.id == tracker_id).first()
    if not tracker:
        flash("Tracker not found", "error")
        return redirect("/trackers")
    log = tracker.logs.select(lambda l: l.id == log_id).first()
    if not log:
        flash("Log not found", "error")
        return redirect("/trackers")

    log.delete()

    flash("Log deleted successfully", "success")
    return redirect(f"/trackers/{tracker_id}/logs")


@bp.get("/export")
def export():
    zip_filename = export_data(g.user)
    return send_file(os.path.join("..", zip_filename), as_attachment=True)


@bp.route("/import", methods=["GET", "POST"])
def _import():

    if request.method == "GET":
        return render_template("import.html")

    zipfile = request.files["file"]

    if not (zipfile and zipfile.filename and zipfile.filename.endswith(".zip")):
        flash("Invalid file", "error")
        return redirect("/")

    import_data(g.user, zipfile)

    flash("Data imported successfully", "success")

    return redirect("/trackers")
