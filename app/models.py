from pony.orm import Database, Optional, PrimaryKey, Required, Set
from werkzeug.security import check_password_hash

db = Database()


class User(db.Entity):
    username = Required(str, unique=True)
    password = Required(str)
    trackers = Set(lambda: Tracker)

    def compare_password(self, password):
        return check_password_hash(self.password, password)


class Tracker(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    type = Required(str)
    settings = Optional(str, nullable=True)
    logs = Set(lambda: Log)
    user = Required(lambda: User)


class Log(db.Entity):
    id = PrimaryKey(int, auto=True)
    timestamp = Required(str)
    value = Required(str)
    note = Optional(str)
    tracker = Required(lambda: Tracker)
