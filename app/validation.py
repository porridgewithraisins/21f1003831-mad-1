from app.utils import TrackerType, is_number, is_timestamp, Result


def validate_user(form):
    username = form.get("username")
    password = form.get("password")

    if not username:
        return Result(err="Username is required")

    if not password:
        return Result(err="Password is required")

    if not (2 < len(username) < 20):
        return Result(err="Username must be between 2 and 20 characters long")

    if not (8 < len(password) < 255):
        return Result(err="Password must be between 8 and 255 characters long")

    return Result(ok=(username, password))


def validate_tracker(form):
    name = form.get("name")
    type = form.get("type")
    settings = form.get("settings")

    if not (name and len(name) < 50):
        return Result(err="Invalid name")

    if not type:
        return Result(err="Invalid type")

    if type not in (TrackerType.QUAL, TrackerType.QUANT):
        return Result(err="Invalid type")

    if type == TrackerType.QUAL and not 2 < (length := len(settings.split(","))) < 10:
        return Result(
            err=f"Need at least 2 choices, and at most 10 choices, but received {length}"
        )

    return Result(ok=(name, type, settings))


def validate_log(tracker, form):
    timestamp = form.get("timestamp")
    value = form.get("value")
    note = form.get("note")

    if not is_timestamp(timestamp):
        return Result(err="Invalid timestamp")
    if tracker.type == TrackerType.QUAL and value not in tracker.settings:
        return Result(err="Expected one of: " + tracker.settings)
    if tracker.type == TrackerType.QUANT and not is_number(value):
        return Result(err="Expected numerical value for this tracker")
    if note and len(note) > 255:
        return Result(err="Note cannot be longer than 255 characters")
    return Result(ok=(timestamp.replace(" ", "T"), value, note))
