import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models.chatbot import process_query
from models.database import db, User, QueryLog

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Use a strong key in production

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postAnuj02@localhost:5432/rag_human_rights"
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///D:/sem 6/6_Sem_Project/RAG_HumanRights_Chatbot/instance/site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# ----------------------
# Authentication Routes
# ----------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session.get("username", "User")  # Default to "User" if not found
    return render_template("index.html", username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username  # Store the username in session
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid email or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        
        # new_user = User(email=email, password=hashed_password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)  # Remove username from session
    return redirect(url_for("login"))


# ----------------------
# Query Handling Route
# ----------------------
import markdown

@app.route("/get_response", methods=["POST"])
def get_response():
    if "user_id" not in session:
        return jsonify({"success": False, "response": "Please log in to continue."})

    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"success": False, "response": "No query provided."})

    try:
        response = process_query(query)  # Get response from chatbot
        
        # Convert markdown to HTML before sending
        formatted_response = markdown.markdown(response)

        # Save query to database
        new_query = QueryLog(user_id=session["user_id"], query=query, response=formatted_response)
        db.session.add(new_query)
        db.session.commit()

        return jsonify({"success": True, "response": formatted_response})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "response": "Error processing query."})


# ----------------------
# Run the Flask app
# ----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
