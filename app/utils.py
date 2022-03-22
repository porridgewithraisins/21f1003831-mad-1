import json
import os
import zipfile
from collections import namedtuple
from datetime import datetime
from enum import Enum
from matplotlib import pyplot as plt


def is_number(x):
    try:
        float(x)
        return True
    except (ValueError, TypeError):
        return False


def is_timestamp(t):
    try:
        datetime.fromisoformat(t)
        return True
    except (ValueError, TypeError):
        return False


class TrackerType(str, Enum):
    QUANT = "Quantitative"
    QUAL = "Qualitative"


Result = namedtuple("Result", "ok err", defaults=(None, None))


def get_user_folder(user):
    return f"instance/user_data/{user.username}_{user.id}"


def export_data(user):
    user_folder = get_user_folder(user)
    exports_folder = f"{user_folder}/exports"
    os.makedirs(exports_folder, exist_ok=True)

    metadata_file = f"{exports_folder}/metadata.json"
    metadata = {}

    for tracker in user.trackers:
        filename = f"{exports_folder}/{tracker.name}_{tracker.id}.csv"
        file = open(filename, "w")
        file.write("timestamp, value, note\n")
        for log in tracker.logs:
            file.write(f"{log.timestamp},{log.value},{log.note}\n")
        file.close()
        metadata[tracker.id] = {"type": tracker.type, "settings": tracker.settings}

    with open(metadata_file, "w") as file:
        file.write(json.dumps(metadata))

    zip_filename = f"{exports_folder}/out.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in os.listdir(exports_folder):
            if file.endswith(".csv") or file.endswith(".json"):
                zip_file.write(f"{exports_folder}/{file}", file)
                os.remove(f"{exports_folder}/{file}")
    return zip_filename


def import_data(user, zip):
    user_folder = get_user_folder(user)
    imports_folder = f"{user_folder}/imports"
    os.makedirs(imports_folder, exist_ok=True)

    zip_file = f"{imports_folder}/in.zip"
    zip.save(zip_file)

    with zipfile.ZipFile(zip_file, "r") as zip_file:
        zip_file.extractall(imports_folder)
        # we need not use secure_filename as zipfile takes care of this on both the extract
        # and extractall methods

    metadata_file = f"{imports_folder}/metadata.json"
    with open(metadata_file, "r") as file:
        metadata = json.loads(file.read())

    for file in os.listdir(imports_folder):
        if file.endswith(".csv"):
            id = file.split("_")[1].split(".")[0]
            name = file.split("_")[0]
            type = metadata[id]["type"]
            settings = metadata[id]["settings"]

            tracker = user.trackers.create(name=name, type=type, settings=settings)

            with open(f"{imports_folder}/{file}", "r") as file:
                next(file)  # skip header row
                for line in file:
                    timestamp, value, note = line.split(",")
                    tracker.logs.create(timestamp=timestamp, value=value, note=note)


def plot(tracker, image_loc):
    # plot a time series of logs
    plt.figure(figsize=(12, 6))
    x = [datetime.fromisoformat(log.timestamp) for log in tracker.logs]
    y = [log.value for log in tracker.logs]
    if tracker.type == TrackerType.QUANT:
        y = [float(log.value) for log in tracker.logs]
    plt.scatter(x, y)
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title(f"{tracker.user.username}'s {tracker.name} tracker")
    plt.savefig(image_loc)
