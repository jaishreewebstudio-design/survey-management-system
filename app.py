from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

import sqlite3
import json

from functools import wraps

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

app.secret_key = "survey_management_system_secret_key_2026"

DATABASE = "survey.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE,
        timeout=20
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA busy_timeout = 20000"
    )

    return conn


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    conn = get_db()

    try:

        conn.executescript("""

        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            mobile TEXT,

            password TEXT NOT NULL,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );


        CREATE TABLE IF NOT EXISTS surveys (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            description TEXT,

            created_by INTEGER,

            status TEXT DEFAULT 'draft',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            published_at TEXT,

            FOREIGN KEY(created_by)
                REFERENCES users(id)
        );


        CREATE TABLE IF NOT EXISTS survey_questions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            survey_id INTEGER NOT NULL,

            question TEXT NOT NULL,

            question_type TEXT NOT NULL,

            options TEXT DEFAULT '[]',

            required INTEGER DEFAULT 0,

            question_order INTEGER DEFAULT 0,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(survey_id)
                REFERENCES surveys(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS responses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            survey_id INTEGER NOT NULL,

            user_id INTEGER,

            name TEXT,

            email TEXT,

            answers TEXT NOT NULL,

            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(survey_id)
                REFERENCES surveys(id)
                ON DELETE CASCADE,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
        );

        """)


        # ====================================================
        # DATABASE MIGRATIONS
        # ====================================================

        migrations = {

            "users": {
                "mobile": "TEXT",
                "created_at": "TEXT"
            },

            "surveys": {
                "description": "TEXT",
                "created_by": "INTEGER",
                "status": "TEXT",
                "created_at": "TEXT",
                "published_at": "TEXT"
            },

            "survey_questions": {
                "question": "TEXT",
                "question_type": "TEXT",
                "options": "TEXT",
                "required": "INTEGER",
                "question_order": "INTEGER",
                "created_at": "TEXT"
            },

            "responses": {
                "survey_id": "INTEGER",
                "user_id": "INTEGER",
                "name": "TEXT",
                "email": "TEXT",
                "answers": "TEXT",
                "submitted_at": "TEXT"
            }
        }


        for table, columns in migrations.items():

            existing_columns = {
                row["name"]
                for row in conn.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            }

            for column, column_type in columns.items():

                if column not in existing_columns:

                    conn.execute(
                        f"""
                        ALTER TABLE {table}
                        ADD COLUMN {column} {column_type}
                        """
                    )


        # ====================================================
        # DEFAULT DATA FIXES
        # ====================================================

        conn.execute("""
            UPDATE surveys
            SET status = 'draft'
            WHERE status IS NULL
               OR status = ''
        """)


        conn.execute("""
            UPDATE survey_questions
            SET options = '[]'
            WHERE options IS NULL
               OR options = ''
        """)


        conn.execute("""
            UPDATE survey_questions
            SET question_order = id
            WHERE question_order IS NULL
               OR question_order = 0
        """)


        conn.execute("""
            UPDATE responses
            SET submitted_at = CURRENT_TIMESTAMP
            WHERE submitted_at IS NULL
               OR submitted_at = ''
        """)


        conn.commit()


        print("==========================================")
        print("DATABASE READY")
        print("DATABASE:", DATABASE)
        print("==========================================")


    except Exception as e:

        conn.rollback()

        print("DATABASE ERROR:", e)

        raise

    finally:

        conn.close()


# ============================================================
# CURRENT USER
# ============================================================

def current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None


    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT
                id,
                name,
                email,
                mobile
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()


        return user

    finally:

        conn.close()


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if current_user() is None:

            session.clear()

            if request.path.startswith("/api/"):

                return jsonify(
                    success=False,
                    message="Please login again."
                ), 401


            return redirect(
                url_for("login_page")
            )


        return function(*args, **kwargs)


    return wrapper


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route("/")
def home():

    if current_user():

        return redirect(
            url_for("dashboard")
        )


    return redirect(
        url_for("login_page")
    )


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@app.route("/login")
def login_page():

    return render_template(
        "login.html"
    )


# ------------------------------------------------------------
# REGISTER
# ------------------------------------------------------------

@app.route("/register")
def register_page():

    return render_template(
        "register.html"
    )


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html"
    )


# ------------------------------------------------------------
# ADD SURVEY
# ------------------------------------------------------------

@app.route("/add-survey")
@login_required
def add_survey():

    return render_template(
        "add-survey.html"
    )


# ------------------------------------------------------------
# ALL SURVEYS
# ------------------------------------------------------------

@app.route("/surveys")
@login_required
def surveys():

    return render_template(
        "surveys.html"
    )


# ------------------------------------------------------------
# EDIT SURVEY
# ------------------------------------------------------------

@app.route("/edit-survey/<int:survey_id>")
@login_required
def edit_survey_page(survey_id):

    return render_template(
        "edit-survey.html",
        survey_id=survey_id
    )


# ------------------------------------------------------------
# VIEW SURVEY
# ------------------------------------------------------------

@app.route("/view-survey/<int:survey_id>")
@login_required
def view_survey_page(survey_id):

    return render_template(
        "view-survey.html",
        survey_id=survey_id
    )


# ------------------------------------------------------------
# RESPONSES PAGE
# ------------------------------------------------------------

@app.route("/responses")
@login_required
def responses():

    return render_template(
        "responses.html"
    )


# ------------------------------------------------------------
# SUCCESS PAGE
# ------------------------------------------------------------

@app.route("/success")
@login_required
def success():

    return render_template(
        "success.html"
    )


# ============================================================
# REGISTER API
# ============================================================

@app.post("/api/register")
def api_register():

    data = request.get_json(
        silent=True
    ) or {}


    name = str(
        data.get("name", "")
    ).strip()


    email = str(
        data.get("email", "")
    ).strip().lower()


    mobile = str(
        data.get("mobile", "")
    ).strip()


    password = str(
        data.get("password", "")
    )


    confirm_password = str(
        data.get("confirm_password", "")
    )


    if not name:

        return jsonify(
            success=False,
            message="Name is required."
        ), 400


    if not email:

        return jsonify(
            success=False,
            message="Email is required."
        ), 400


    if not password:

        return jsonify(
            success=False,
            message="Password is required."
        ), 400


    if password != confirm_password:

        return jsonify(
            success=False,
            message="Passwords do not match."
        ), 400


    if len(password) < 6:

        return jsonify(
            success=False,
            message="Password must be at least 6 characters."
        ), 400


    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                mobile,
                password
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                email,
                mobile,
                generate_password_hash(password)
            )
        )


        conn.commit()


        return jsonify(
            success=True,
            message="Registration successful."
        ), 201


    except sqlite3.IntegrityError:

        return jsonify(
            success=False,
            message="Email already registered."
        ), 409


    finally:

        conn.close()


# ============================================================
# LOGIN API
# ============================================================

@app.post("/api/login")
def api_login():

    data = request.get_json(
        silent=True
    ) or {}


    email = str(
        data.get("email", "")
    ).strip().lower()


    password = str(
        data.get("password", "")
    )


    if not email or not password:

        return jsonify(
            success=False,
            message="Email and password are required."
        ), 400


    conn = get_db()

    try:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    finally:

        conn.close()


    if not user:

        return jsonify(
            success=False,
            message="Invalid email or password."
        ), 401


    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify(
            success=False,
            message="Invalid email or password."
        ), 401


    session.clear()

    session["user_id"] = user["id"]

    session["user_name"] = user["name"]

    session["user_email"] = user["email"]


    return jsonify(
        success=True,
        message="Login successful.",
        redirect=url_for("dashboard")
    )


# ============================================================
# LOGOUT API
# ============================================================

@app.post("/api/logout")
def api_logout():

    session.clear()


    return jsonify(
        success=True,
        message="Logout successful."
    )


# ============================================================
# DASHBOARD API
# ============================================================

@app.get("/api/dashboard")
@login_required
def api_dashboard():

    conn = get_db()

    try:

        total_users = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM users
            """
        ).fetchone()["count"]


        total_surveys = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM surveys
            """
        ).fetchone()["count"]


        active_surveys = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM surveys
            WHERE status IN ('active', 'published')
            """
        ).fetchone()["count"]


        draft_surveys = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM surveys
            WHERE status = 'draft'
            """
        ).fetchone()["count"]


        total_responses = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            """
        ).fetchone()["count"]


    finally:

        conn.close()


    return jsonify(
        success=True,
        data={
            "total_users": total_users,
            "total_surveys": total_surveys,
            "active_surveys": active_surveys,
            "draft_surveys": draft_surveys,
            "total_responses": total_responses
        }
    )


# ============================================================
# SURVEY QUESTION SETTINGS
# ============================================================

ALLOWED_TYPES = {
    "multiple_choice",
    "short_answer",
    "rating_scale",
    "dropdown",
    "checkbox",
    "likert_scale"
}


OPTION_TYPES = {
    "multiple_choice",
    "rating_scale",
    "dropdown",
    "checkbox",
    "likert_scale"
}


# ============================================================
# CLEAN QUESTIONS
# ============================================================

def clean_questions(questions):

    if not isinstance(questions, list):

        return None, "Questions must be a list."


    if len(questions) != 6:

        return None, (
            "Survey must contain exactly 6 questions."
        )


    cleaned = []


    for index, item in enumerate(
        questions,
        1
    ):

        if not isinstance(item, dict):

            return None, (
                f"Question {index} is invalid."
            )


        text = str(
            item.get(
                "question",
                ""
            )
        ).strip()


        question_type = str(
            item.get(
                "question_type",
                "short_answer"
            )
        ).strip().lower()


        if not text:

            return None, (
                f"Please enter Question {index}."
            )


        if question_type not in ALLOWED_TYPES:

            return None, (
                f"Invalid question type for Question {index}."
            )


        options = item.get(
            "options",
            []
        )


        if not isinstance(
            options,
            list
        ):

            options = []


        options = [

            str(option).strip()

            for option in options

            if str(option).strip()

        ]


        if (
            question_type in OPTION_TYPES
            and not options
        ):

            return None, (
                f"Question {index} needs options."
            )


        cleaned.append({

            "question": text,

            "question_type": question_type,

            "options": options,

            "required":
                1 if item.get("required")
                else 0

        })


    return cleaned, None


# ============================================================
# INSERT QUESTIONS
# ============================================================

def insert_questions(
    conn,
    survey_id,
    questions
):

    conn.execute(
        """
        DELETE FROM survey_questions
        WHERE survey_id = ?
        """,
        (survey_id,)
    )


    for order, question in enumerate(
        questions,
        1
    ):

        conn.execute(
            """
            INSERT INTO survey_questions
            (
                survey_id,
                question,
                question_type,
                options,
                required,
                question_order
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                survey_id,

                question["question"],

                question["question_type"],

                json.dumps(
                    question["options"],
                    ensure_ascii=False
                ),

                question["required"],

                order
            )
        )


# ============================================================
# CREATE SURVEY API
# ============================================================

@app.post("/api/surveys")
@login_required
def api_create_survey():

    data = request.get_json(
        silent=True
    ) or {}


    title = str(
        data.get(
            "title",
            ""
        )
    ).strip()


    description = str(
        data.get(
            "description",
            ""
        )
    ).strip()


    questions, error = clean_questions(
        data.get(
            "questions",
            []
        )
    )


    if not title:

        return jsonify(
            success=False,
            message="Please enter a survey title."
        ), 400


    if error:

        return jsonify(
            success=False,
            message=error
        ), 400


    conn = get_db()

    try:

        cursor = conn.execute(
            """
            INSERT INTO surveys
            (
                title,
                description,
                created_by,
                status
            )
            VALUES (?, ?, ?, 'draft')
            """,
            (
                title,
                description,
                session["user_id"]
            )
        )


        survey_id = cursor.lastrowid


        insert_questions(
            conn,
            survey_id,
            questions
        )


        conn.commit()


        return jsonify(
            success=True,
            message="Survey saved as draft.",
            survey_id=survey_id
        ), 201


    except Exception as e:

        conn.rollback()


        return jsonify(
            success=False,
            message=str(e)
        ), 500


    finally:

        conn.close()


# ============================================================
# GET ALL SURVEYS
# ============================================================

@app.get("/api/surveys")
@login_required
def api_get_surveys():

    conn = get_db()

    try:

        rows = conn.execute(
            """
            SELECT

                s.id,

                s.title,

                s.description,

                s.status,

                s.created_at,

                s.published_at,

                (
                    SELECT COUNT(*)
                    FROM survey_questions q
                    WHERE q.survey_id = s.id
                ) AS question_count,

                (
                    SELECT COUNT(*)
                    FROM responses r
                    WHERE r.survey_id = s.id
                ) AS response_count

            FROM surveys s

            ORDER BY s.id DESC
            """
        ).fetchall()


        surveys_list = []


        for row in rows:

            surveys_list.append({

                "id":
                    row["id"],

                "title":
                    row["title"],

                "description":
                    row["description"] or "",

                "status":
                    row["status"] or "draft",

                "question_count":
                    row["question_count"] or 0,

                "response_count":
                    row["response_count"] or 0,

                "created_at":
                    row["created_at"],

                "published_at":
                    row["published_at"]

            })


    finally:

        conn.close()


    return jsonify(
        success=True,
        surveys=surveys_list
    )


# ============================================================
# GET ONE SURVEY
# ============================================================

@app.get("/api/surveys/<int:survey_id>")
@login_required
def api_get_survey(survey_id):

    conn = get_db()

    try:

        survey = conn.execute(
            """
            SELECT
                id,
                title,
                description,
                created_by,
                status,
                created_at,
                published_at
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        ).fetchone()


        if not survey:

            return jsonify(
                success=False,
                message="Survey not found."
            ), 404


        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,)
        ).fetchall()


        questions = []


        for row in question_rows:

            try:

                options = json.loads(
                    row["options"] or "[]"
                )

            except Exception:

                options = []


            questions.append({

                "id":
                    row["id"],

                "question":
                    row["question"],

                "question_type":
                    row["question_type"],

                "options":
                    options,

                "required":
                    bool(row["required"]),

                "question_order":
                    row["question_order"]

            })


        result = dict(survey)

        result["description"] = (
            result["description"] or ""
        )

        result["questions"] = questions


        return jsonify(
            success=True,
            survey=result
        )


    finally:

        conn.close()


# ============================================================
# VIEW SURVEY RESPONSE API
# ============================================================

@app.get("/api/surveys/<int:survey_id>/view")
@login_required
def api_view_survey(survey_id):

    conn = get_db()

    try:

        survey = conn.execute(
            """
            SELECT
                id,
                title,
                description,
                status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        ).fetchone()


        if not survey:

            return jsonify(
                success=False,
                message="Survey not found."
            ), 404


        response = conn.execute(
            """
            SELECT
                id,
                user_id,
                name,
                email,
                answers,
                submitted_at
            FROM responses
            WHERE survey_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (survey_id,)
        ).fetchone()


        if not response:

            return jsonify(
                success=False,
                message="No response found for this survey."
            ), 404


        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (survey_id,)
        ).fetchall()


        try:

            answers = json.loads(
                response["answers"] or "{}"
            )

        except Exception:

            answers = {}


        question_list = []


        for row in question_rows:

            try:

                options = json.loads(
                    row["options"] or "[]"
                )

            except Exception:

                options = []


            question_id = str(
                row["id"]
            )


            answer = None


            if question_id in answers:

                answer = answers[question_id]

            elif str(row["question_order"]) in answers:

                answer = answers[
                    str(row["question_order"])
                ]

            elif row["question"] in answers:

                answer = answers[
                    row["question"]
                ]


            question_list.append({

                "id":
                    row["id"],

                "question":
                    row["question"],

                "question_type":
                    row["question_type"],

                "options":
                    options,

                "required":
                    bool(row["required"]),

                "question_order":
                    row["question_order"],

                "answer":
                    answer

            })


        return jsonify(

            success=True,

            survey={

                "id":
                    survey["id"],

                "title":
                    survey["title"],

                "description":
                    survey["description"] or "",

                "status":
                    survey["status"] or "draft"

            },

            response={

                "id":
                    response["id"],

                "user_id":
                    response["user_id"],

                "name":
                    response["name"] or "",

                "email":
                    response["email"] or "",

                "submitted_at":
                    response["submitted_at"],

                "answers":
                    answers

            },

            questions=question_list

        )


    finally:

        conn.close()


# ============================================================
# UPDATE SURVEY
# ============================================================

@app.put("/api/surveys/<int:survey_id>")
@login_required
def api_update_survey(survey_id):

    data = request.get_json(
        silent=True
    ) or {}


    title = str(
        data.get(
            "title",
            ""
        )
    ).strip()


    description = str(
        data.get(
            "description",
            ""
        )
    ).strip()


    questions, error = clean_questions(
        data.get(
            "questions",
            []
        )
    )


    if not title:

        return jsonify(
            success=False,
            message="Please enter a survey title."
        ), 400


    if error:

        return jsonify(
            success=False,
            message=error
        ), 400


    conn = get_db()

    try:

        survey = conn.execute(
            """
            SELECT
                id,
                created_by,
                status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        ).fetchone()


        if not survey:

            return jsonify(
                success=False,
                message="Survey not found."
            ), 404


        if survey["created_by"] != session["user_id"]:

            return jsonify(
                success=False,
                message="You cannot edit this survey."
            ), 403


        if survey["status"] == "closed":

            return jsonify(
                success=False,
                message="Closed survey cannot be edited."
            ), 400


        conn.execute(
            """
            UPDATE surveys
            SET
                title = ?,
                description = ?
            WHERE id = ?
            """,
            (
                title,
                description,
                survey_id
            )
        )


        insert_questions(
            conn,
            survey_id,
            questions
        )


        conn.commit()


        return jsonify(
            success=True,
            message="Survey updated successfully."
        )


    except Exception as e:

        conn.rollback()


        return jsonify(
            success=False,
            message=str(e)
        ), 500


    finally:

        conn.close()


# ============================================================
# PUBLISH SURVEY
#
# IMPORTANT:
#
# Add Survey = draft
#
# Publish Survey = published
#
# Publish ke baad ONLY 1 response record create hota hai.
#
# Isi wajah se Responses ka count +1 hoga.
# ============================================================

@app.post("/api/surveys/<int:survey_id>/publish")
@login_required
def api_publish_survey(survey_id):

    conn = get_db()

    try:

        survey = conn.execute(
            """
            SELECT
                id,
                title,
                created_by,
                status
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        ).fetchone()


        if not survey:

            return jsonify(
                success=False,
                message="Survey not found."
            ), 404


        if survey["created_by"] != session["user_id"]:

            return jsonify(
                success=False,
                message="You cannot publish this survey."
            ), 403


        if survey["status"] == "published":

            return jsonify(
                success=False,
                message="Survey is already published."
            ), 400


        if survey["status"] == "closed":

            return jsonify(
                success=False,
                message="Closed survey cannot be published."
            ), 400


        question_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM survey_questions
            WHERE survey_id = ?
            """,
            (survey_id,)
        ).fetchone()["count"]


        if question_count != 6:

            return jsonify(
                success=False,
                message=(
                    "Survey must contain exactly "
                    "6 questions."
                )
            ), 400


        # ----------------------------------------------------
        # GET CURRENT USER
        # ----------------------------------------------------

        user = current_user()


        if user is None:

            return jsonify(
                success=False,
                message="Please login again."
            ), 401


        # ----------------------------------------------------
        # PUBLISH SURVEY
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE surveys
            SET
                status = 'published',
                published_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (survey_id,)
        )


        # ----------------------------------------------------
        # CREATE RESPONSE
        #
        # IMPORTANT:
        # Publish Survey itself creates ONE response.
        #
        # Answers are empty because there is no
        # Fill Survey page in your system.
        # ----------------------------------------------------

        cursor = conn.execute(
            """
            INSERT INTO responses
            (
                survey_id,
                user_id,
                name,
                email,
                answers
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                survey_id,

                user["id"],

                user["name"],

                user["email"],

                json.dumps(
                    {},
                    ensure_ascii=False
                )
            )
        )


        response_id = cursor.lastrowid


        # ----------------------------------------------------
        # GET UPDATED TOTAL
        # ----------------------------------------------------

        total_responses = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            """
        ).fetchone()["count"]


        # ----------------------------------------------------
        # GET UPDATED SURVEY RESPONSE COUNT
        # ----------------------------------------------------

        survey_response_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,)
        ).fetchone()["count"]


        conn.commit()


        return jsonify(

            success=True,

            message="Survey published successfully.",

            survey_id=survey_id,

            response_id=response_id,

            total_responses=total_responses,

            survey_response_count=survey_response_count

        )


    except Exception as e:

        conn.rollback()


        print(
            "PUBLISH ERROR:",
            e
        )


        return jsonify(
            success=False,
            message=str(e)
        ), 500


    finally:

        conn.close()


# ============================================================
# DELETE SURVEY
# ============================================================

@app.delete("/api/surveys/<int:survey_id>")
@login_required
def api_delete_survey(survey_id):

    conn = get_db()

    try:

        survey = conn.execute(
            """
            SELECT
                id,
                created_by
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        ).fetchone()


        if not survey:

            return jsonify(
                success=False,
                message="Survey not found."
            ), 404


        if survey["created_by"] != session["user_id"]:

            return jsonify(
                success=False,
                message="You cannot delete this survey."
            ), 403


        # Delete responses first

        conn.execute(
            """
            DELETE FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,)
        )


        # Delete questions

        conn.execute(
            """
            DELETE FROM survey_questions
            WHERE survey_id = ?
            """,
            (survey_id,)
        )


        # Delete survey

        conn.execute(
            """
            DELETE FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        )


        conn.commit()


        return jsonify(
            success=True,
            message="Survey deleted successfully."
        )


    except Exception as e:

        conn.rollback()


        return jsonify(
            success=False,
            message=str(e)
        ), 500


    finally:

        conn.close()


# ============================================================
# GET RESPONSES
# ============================================================

@app.get("/api/responses")
@login_required
def api_get_responses():

    conn = get_db()

    try:

        rows = conn.execute(
            """
            SELECT

                r.id,

                r.survey_id,

                r.user_id,

                r.name,

                r.email,

                r.submitted_at,

                s.title AS survey_title

            FROM responses r

            LEFT JOIN surveys s
                ON s.id = r.survey_id

            ORDER BY r.id DESC
            """
        ).fetchall()


        result = []


        for row in rows:

            result.append({

                "id":
                    row["id"],

                "survey_id":
                    row["survey_id"],

                "user_id":
                    row["user_id"],

                "survey_title":
                    row["survey_title"]
                    or "Survey",

                "name":
                    row["name"]
                    or "Unknown",

                "email":
                    row["email"]
                    or "Not available",

                "submitted_at":
                    row["submitted_at"]

            })


    finally:

        conn.close()


    return jsonify(

        success=True,

        total_responses=len(result),

        responses=result

    )


# ============================================================
# GET SINGLE RESPONSE
# ============================================================

@app.get("/api/responses/<int:response_id>")
@login_required
def api_get_single_response(response_id):

    conn = get_db()

    try:

        response = conn.execute(
            """
            SELECT
                r.id,
                r.survey_id,
                r.user_id,
                r.name,
                r.email,
                r.answers,
                r.submitted_at,
                s.title AS survey_title,
                s.description AS survey_description
            FROM responses r
            LEFT JOIN surveys s
                ON s.id = r.survey_id
            WHERE r.id = ?
            """,
            (response_id,)
        ).fetchone()


        if not response:

            return jsonify(
                success=False,
                message="Response not found."
            ), 404


        try:

            answers = json.loads(
                response["answers"] or "{}"
            )

        except Exception:

            answers = {}


        question_rows = conn.execute(
            """
            SELECT
                id,
                question,
                question_type,
                options,
                required,
                question_order
            FROM survey_questions
            WHERE survey_id = ?
            ORDER BY question_order, id
            """,
            (response["survey_id"],)
        ).fetchall()


        questions = []


        for row in question_rows:

            try:

                options = json.loads(
                    row["options"] or "[]"
                )

            except Exception:

                options = []


            answer = None


            question_id = str(
                row["id"]
            )


            if question_id in answers:

                answer = answers[question_id]

            elif str(row["question_order"]) in answers:

                answer = answers[
                    str(row["question_order"])
                ]

            elif row["question"] in answers:

                answer = answers[
                    row["question"]
                ]


            questions.append({

                "id":
                    row["id"],

                "question":
                    row["question"],

                "question_type":
                    row["question_type"],

                "options":
                    options,

                "required":
                    bool(row["required"]),

                "question_order":
                    row["question_order"],

                "answer":
                    answer

            })


        return jsonify(

            success=True,

            response={

                "id":
                    response["id"],

                "survey_id":
                    response["survey_id"],

                "user_id":
                    response["user_id"],

                "name":
                    response["name"] or "",

                "email":
                    response["email"] or "",

                "submitted_at":
                    response["submitted_at"],

                "answers":
                    answers

            },

            survey={

                "title":
                    response["survey_title"]
                    or "Survey",

                "description":
                    response["survey_description"]
                    or ""

            },

            questions=questions

        )


    finally:

        conn.close()


# ============================================================
# SURVEY STATISTICS
# ============================================================

@app.get("/api/surveys/<int:survey_id>/statistics")
@login_required
def survey_statistics(survey_id):

    conn = get_db()

    try:

        survey = conn.execute(
            """
            SELECT
                id,
                title
            FROM surveys
            WHERE id = ?
            """,
            (survey_id,)
        ).fetchone()


        if not survey:

            return jsonify(
                success=False,
                message="Survey not found."
            ), 404


        total = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM responses
            WHERE survey_id = ?
            """,
            (survey_id,)
        ).fetchone()["count"]


    finally:

        conn.close()


    return jsonify(

        success=True,

        survey_id=survey_id,

        survey_title=survey["title"],

        total_responses=total

    )


# ============================================================
# ERROR HANDLER - 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    if request.path.startswith("/api/"):

        return jsonify(
            success=False,
            message="API endpoint not found."
        ), 404


    return """
    <h1>404 - Page Not Found</h1>
    """, 404


# ============================================================
# ERROR HANDLER - 500
# ============================================================

@app.errorhandler(500)
def server_error(error):

    if request.path.startswith("/api/"):

        return jsonify(
            success=False,
            message="Internal server error."
        ), 500


    return """
    <h1>500 - Internal Server Error</h1>
    """, 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )