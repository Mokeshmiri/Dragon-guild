from flask import Flask, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

import participations_dao
import quests_dao
import sessions_dao
import users_dao
from models import User


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LOCATIONS = ["Dungeon Hall", "Enchanted Forest", "Wizard Tower"]
QUEST_TYPES = ["Combat", "Exploration", "Puzzle", "Stealth", "Magic", "Survival"]
DIFFICULTIES = ["Easy", "Medium", "Hard", "Legendary"]
ROLES = ["Warrior", "Mage", "Healer"]
ROLE_CAPACITIES = {"Warrior": 4, "Mage": 3, "Healer": 2}
IMAGE_OPTIONS = ["ember_forge.png", "moon_forest.png", "crystal_vault.png",
                 "storm_tower.png", "sunken_gate.png", "shadow_market.png"]

# fictional current time used for the eight-hour deadline
SIMULATED_CURRENT_DAY = 0
SIMULATED_CURRENT_TIME = "10:00"
CHANGE_DEADLINE_MINUTES = 8 * 60


app = Flask(__name__)
app.config["SECRET_KEY"] = "dragon-guild-secret"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# loads the logged-in user from the database
@login_manager.user_loader
def load_user(user_id):
    row = users_dao.get_user_by_id(user_id)
    if row is None:
        return None
    return User(row["id"], row["email"], row["role"])


# converts a time string into minutes
def time_to_minutes(value):
    try:
        hours, minutes = value.split(":")
        hours = int(hours)
        minutes = int(minutes)
    except ValueError:
        return None
    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        return None
    return hours * 60 + minutes


# checks whether two time intervals overlap
def intervals_overlap(start_a, duration_a, start_b, duration_b):
    # each session must start before the other one finishes
    end_a = start_a + duration_a
    end_b = start_b + duration_b
    return start_a < end_b and start_b < end_a


# checks the eight-hour participation deadline
def session_can_change_participation(session):
    session_time = session["day"] * 24 * 60 + time_to_minutes(session["start_time"])
    current_time = SIMULATED_CURRENT_DAY * 24 * 60 + time_to_minutes(SIMULATED_CURRENT_TIME)
    return session_time - current_time > CHANGE_DEADLINE_MINUTES


# calculates reserved and remaining places for each role
def get_session_stats(session_id, exclude_user_id=None):
    reserved = {role: 0 for role in ROLES}
    for row in participations_dao.session_role_counts(session_id, exclude_user_id):
        reserved[row["role"]] = row["places"]

    remaining = {
        role: max(ROLE_CAPACITIES[role] - reserved[role], 0)
        for role in ROLES
    }
    total_reserved = sum(reserved.values())
    most_requested_count = max(reserved.values())
    most_requested = [
        role for role, count in reserved.items()
        if count == most_requested_count and count > 0
    ]

    return {
        "reserved": reserved,
        "remaining": remaining,
        "total_reserved": total_reserved,
        "most_requested": most_requested,
    }


# adds display values and statistics to a session
def add_session_view_data(row):
    session = dict(row)
    session["day_name"] = DAYS[session["day"]]
    session["stats"] = get_session_stats(session["session_id"])
    session["has_participants"] = session["stats"]["total_reserved"] > 0
    session["can_change_participation"] = session_can_change_participation(session)
    return session


# loads a session or returns a not-found page
def get_session_or_404(session_id):
    row = sessions_dao.get_session(session_id)
    if row is None:
        abort(404)
    return add_session_view_data(row)


# displays validation errors to the user
def flash_errors(errors):
    for error in errors:
        flash(error, "error")


# validates day, time, location and session overlaps
def validate_session_values(form, duration_minutes, exclude_session_id=None):
    errors = []

    try:
        day = int(form.get("day", ""))
    except ValueError:
        day = -1
    if day < 0 or day >= len(DAYS):
        errors.append("Choose a valid day.")

    start_time = form.get("start_time", "").strip()
    start_minutes = time_to_minutes(start_time)
    if start_minutes is None:
        errors.append("Choose a valid starting time.")

    location = form.get("location", "").strip()
    if location not in LOCATIONS:
        errors.append("Choose a valid location.")

    # check other sessions already using the selected location
    if not errors:
        for other in sessions_dao.list_sessions_by_day_location(day, location):
            if exclude_session_id and other["session_id"] == exclude_session_id:
                continue
            other_start = time_to_minutes(other["start_time"])
            if intervals_overlap(start_minutes, duration_minutes, other_start, other["duration_minutes"]):
                errors.append("This location already hosts a quest at that time.")
                break

    return {"day": day, "start_time": start_time, "location": location}, errors


# validates the mandatory quest fields
def validate_quest_values(form):
    errors = []
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    quest_type = form.get("quest_type", "").strip()
    difficulty = form.get("difficulty", "").strip()
    image_filename = form.get("image_filename", "").strip()

    try:
        duration_minutes = int(form.get("duration_minutes", ""))
    except ValueError:
        duration_minutes = 0

    if title == "":
        errors.append("Enter the quest title.")
    if duration_minutes < 1:
        errors.append("Enter a valid duration.")
    if quest_type not in QUEST_TYPES:
        errors.append("Choose a valid quest type.")
    if difficulty not in DIFFICULTIES:
        errors.append("Choose a valid difficulty.")
    if description == "":
        errors.append("Enter a short description.")
    if image_filename not in IMAGE_OPTIONS:
        errors.append("Choose one of the available quest images.")

    values = {
        "title": title,
        "duration_minutes": duration_minutes,
        "quest_type": quest_type,
        "difficulty": difficulty,
        "description": description,
        "image_filename": image_filename,
    }
    return values, errors


# checks overlaps with an adventurer's existing sessions
def user_has_time_overlap(user_id, session, exclude_session_id=None):
    new_start = time_to_minutes(session["start_time"])
    for participation in participations_dao.list_user_participations(user_id):
        if exclude_session_id and participation["session_id"] == exclude_session_id:
            continue
        if participation["day"] != session["day"]:
            continue
        existing_start = time_to_minutes(participation["start_time"])
        if intervals_overlap(
            new_start,
            session["duration_minutes"],
            existing_start,
            participation["duration_minutes"],
        ):
            return True
    return False


# validates role, places, capacity and participation limits
def validate_participation_values(form, session, existing=None):
    errors = []
    role = form.get("role", "").strip()
    try:
        places = int(form.get("places", ""))
    except ValueError:
        places = 0

    if role not in ROLES:
        errors.append("Choose a valid party role.")
    if places < 1 or places > 2:
        errors.append("You can reserve 1 or 2 places.")

    if existing and not session["can_change_participation"]:
        errors.append("This participation is too close to the session start and cannot be changed.")

    if existing is None and participations_dao.count_user_sessions(current_user.id) >= 3:
        errors.append("Each adventurer can join at most 3 quest sessions in the week.")

    if user_has_time_overlap(current_user.id, session, session["session_id"] if existing else None):
        errors.append("You already joined another quest session at that time.")

    if role in ROLES and places > 0:
        # ignore the old booking while checking an updated booking
        stats_without_user = get_session_stats(
            session["session_id"],
            exclude_user_id=current_user.id if existing else None,
        )
        if places > stats_without_user["remaining"][role]:
            errors.append(f"Not enough {role} places are available.")

    return {"role": role, "places": places}, errors


# shows the weekly quest program
@app.route("/")
def index():
    selected = {
        "day": request.args.get("day", ""),
        "quest_type": request.args.get("quest_type", ""),
        "difficulty": request.args.get("difficulty", ""),
        "available_role": request.args.get("available_role", ""),
    }
    filters = {}
    if selected["day"].isdigit() and int(selected["day"]) in range(7):
        filters["day"] = int(selected["day"])
    else:
        selected["day"] = ""
    if selected["quest_type"] in QUEST_TYPES:
        filters["quest_type"] = selected["quest_type"]
    else:
        selected["quest_type"] = ""
    if selected["difficulty"] in DIFFICULTIES:
        filters["difficulty"] = selected["difficulty"]
    else:
        selected["difficulty"] = ""
    if selected["available_role"] not in ROLES:
        selected["available_role"] = ""

    sessions = [add_session_view_data(row) for row in sessions_dao.list_sessions(filters)]
    if selected["available_role"]:
        role = selected["available_role"]
        sessions = [session for session in sessions if session["stats"]["remaining"][role] > 0]
    return render_template(
        "index.html",
        sessions=sessions,
        selected=selected,
        days=DAYS,
        quest_types=QUEST_TYPES,
        difficulties=DIFFICULTIES,
        roles=ROLES,
        role_capacities=ROLE_CAPACITIES,
    )


# shows all details for one quest session
@app.route("/sessions/<int:session_id>")
def session_detail(session_id):
    session = get_session_or_404(session_id)
    participation = None
    if current_user.is_authenticated and current_user.role == "adventurer":
        participation = participations_dao.get_participation_by_user_session(current_user.id, session_id)
    return render_template(
        "session_detail.html",
        session=session,
        participation=participation,
        roles=ROLES,
        role_capacities=ROLE_CAPACITIES,
    )


# registers a new adventurer
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        errors = []
        email_parts = email.split("@")

        if len(email_parts) != 2 or email_parts[0] == "" or "." not in email_parts[1]:
            errors.append("Enter a valid email address.")
        if users_dao.get_user_by_email(email):
            errors.append("This email is already registered.")
        if password == "":
            errors.append("Enter a password.")

        if errors:
            flash_errors(errors)
            return render_template("register.html", email=email)

        users_dao.create_user(email, password)
        flash("Registration completed. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# logs in an existing user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = users_dao.get_user_by_email(email)

        if user is None or user["password"] != password:
            flash("Invalid email or password.", "error")
            return render_template("login.html", email=email)

        login_user(User(user["id"], user["email"], user["role"]))
        flash(f"Welcome, {user['email']}.", "success")
        return redirect(url_for("profile"))

    return render_template("login.html")


# logs out the current user
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# shows the correct profile for the logged-in role
@app.route("/profile")
@login_required
def profile():
    if current_user.role == "guild_master":
        quests = []
        for quest in quests_dao.list_quests():
            quest_data = dict(quest)
            quest_data["sessions"] = [
                add_session_view_data(row)
                for row in sessions_dao.list_sessions_for_quest(quest["id"])
            ]
            quests.append(quest_data)
        return render_template("profile_guild_master.html", quests=quests, roles=ROLES)

    participations = []
    for row in participations_dao.list_user_participations(current_user.id):
        item = dict(row)
        item["day_name"] = DAYS[item["day"]]
        item["can_change_participation"] = session_can_change_participation(item)
        participations.append(item)
    return render_template("profile_adventurer.html", participations=participations)


# creates or updates an adventurer participation
@app.route("/sessions/<int:session_id>/join", methods=["POST"])
@login_required
def join_session(session_id):
    if current_user.role != "adventurer":
        flash("The Guild Master can browse sessions but cannot join them.", "error")
        return redirect(url_for("session_detail", session_id=session_id))

    session = get_session_or_404(session_id)
    existing = participations_dao.get_participation_by_user_session(current_user.id, session_id)
    values, errors = validate_participation_values(request.form, session, existing)

    if errors:
        flash_errors(errors)
        return redirect(url_for("session_detail", session_id=session_id))

    if existing:
        participations_dao.update_participation(existing["id"], values["role"], values["places"])
        flash("Your participation was updated.", "success")
    else:
        participations_dao.create_participation(current_user.id, session_id, values["role"], values["places"])
        flash("You joined the quest session.", "success")
    return redirect(url_for("session_detail", session_id=session_id))


# cancels a participation before the deadline
@app.route("/participations/<int:participation_id>/delete", methods=["POST"])
@login_required
def delete_participation(participation_id):
    participation = participations_dao.get_participation(participation_id)
    if participation is None:
        abort(404)
    if int(participation["user_id"]) != int(current_user.id):
        abort(403)

    session = get_session_or_404(participation["session_id"])
    if not session["can_change_participation"]:
        flash("This participation can no longer be cancelled.", "error")
        return redirect(url_for("profile"))

    participations_dao.delete_participation(participation_id)
    flash("Participation cancelled.", "success")
    return redirect(url_for("profile"))


# creates a quest together with its first session
@app.route("/guild/quests/new", methods=["GET", "POST"])
@login_required
def new_quest():
    if current_user.role != "guild_master":
        abort(403)

    if request.method == "POST":
        quest_values, quest_errors = validate_quest_values(request.form)
        session_values, session_errors = validate_session_values(
            request.form,
            quest_values["duration_minutes"],
        )
        errors = quest_errors + session_errors
        if errors:
            flash_errors(errors)
            values = quest_values.copy()
            values.update(session_values)
            return render_template(
                "quest_form.html",
                values=values,
                image_options=IMAGE_OPTIONS,
                days=DAYS,
                locations=LOCATIONS,
                quest_types=QUEST_TYPES,
                difficulties=DIFFICULTIES,
            )

        quest_id = quests_dao.create_quest(
            quest_values["title"],
            quest_values["duration_minutes"],
            quest_values["quest_type"],
            quest_values["difficulty"],
            quest_values["description"],
            quest_values["image_filename"],
        )
        sessions_dao.create_session(quest_id, session_values["day"], session_values["start_time"], session_values["location"])
        flash("Quest and first session created.", "success")
        return redirect(url_for("profile"))

    return render_template(
        "quest_form.html",
        values={},
        image_options=IMAGE_OPTIONS,
        days=DAYS,
        locations=LOCATIONS,
        quest_types=QUEST_TYPES,
        difficulties=DIFFICULTIES,
    )


# adds another session to an existing quest
@app.route("/guild/quests/<int:quest_id>/sessions/new", methods=["GET", "POST"])
@login_required
def new_session(quest_id):
    if current_user.role != "guild_master":
        abort(403)

    quest = quests_dao.get_quest(quest_id)
    if quest is None:
        abort(404)

    if request.method == "POST":
        values, errors = validate_session_values(request.form, quest["duration_minutes"])
        if errors:
            flash_errors(errors)
            return render_template(
                "session_form.html",
                quest=quest,
                session=values,
                action="Create",
                days=DAYS,
                locations=LOCATIONS,
            )

        sessions_dao.create_session(quest_id, values["day"], values["start_time"], values["location"])
        flash("Quest session created.", "success")
        return redirect(url_for("profile"))

    return render_template(
        "session_form.html",
        quest=quest,
        session={},
        action="Create",
        days=DAYS,
        locations=LOCATIONS,
    )


# edits a session that has no participants
@app.route("/guild/sessions/<int:session_id>/edit", methods=["GET", "POST"])
@login_required
def edit_session(session_id):
    if current_user.role != "guild_master":
        abort(403)

    session = get_session_or_404(session_id)

    if session["has_participants"]:
        flash("This session already has adventurers and cannot be modified.", "error")
        return redirect(url_for("profile"))

    if request.method == "POST":
        values, errors = validate_session_values(
            request.form,
            session["duration_minutes"],
            exclude_session_id=session_id,
        )
        if errors:
            flash_errors(errors)
            session.update(values)
            return render_template(
                "session_form.html",
                quest=session,
                session=session,
                action="Update",
                days=DAYS,
                locations=LOCATIONS,
            )

        sessions_dao.update_session(session_id, values["day"], values["start_time"], values["location"])
        flash("Quest session updated.", "success")
        return redirect(url_for("profile"))

    return render_template(
        "session_form.html",
        quest=session,
        session=session,
        action="Update",
        days=DAYS,
        locations=LOCATIONS,
    )


# cancels a session that has no participants
@app.route("/guild/sessions/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_session(session_id):
    if current_user.role != "guild_master":
        abort(403)

    session = get_session_or_404(session_id)

    if session["has_participants"]:
        flash("This session has adventurers and cannot be cancelled.", "error")
        return redirect(url_for("profile"))

    sessions_dao.delete_session(session_id)
    flash("Quest session cancelled.", "success")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True)
