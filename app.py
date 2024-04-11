from flask import Flask, render_template, request, session, redirect, flash
from flask_cors import CORS, cross_origin
import pickle
import pandas as pd
import numpy as np
import mysql.connector
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"
cors = CORS(app)

model = pickle.load(open("Price_Prediction.pkl", "rb"))
df = pd.read_csv("Filtered_Data.csv")

# MySQL database connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='pranitha',
    port='3306',
    database='mysql'
)
mycursor = conn.cursor()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get('uname')
        email = request.form.get('uemail')
        password = request.form.get('upassword')

        # Validate password using regular expression
        if not re.match(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W).{8,}', password):
            flash('Password must contain at least one digit, one uppercase letter, one lowercase letter, one special character, and at least 8 characters long')
            return redirect("/register")

        try:
            # Check if the email already exists in the database
            mycursor.execute('''SELECT * FROM validuser WHERE email = %s''', (email,))
            result = mycursor.fetchone()
            if result:
                error_msg = 'Email already exists. Please choose a different email.'
                return render_template("register.html", error_msg=error_msg)

            # Insert the user into the database
            mycursor.execute('''INSERT INTO validuser (name, email, password) VALUES (%s, %s, %s)''', (name, email, password))
            conn.commit()
            flash('Registration successful. Please log in.')
            return redirect("/login")
        except Exception as e:
            flash('An error occurred. Please try again later.')
            print(e)
            return redirect("/register")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        mycursor.execute("SELECT * FROM validuser WHERE email = %s AND password = %s", (email, password))
        user = mycursor.fetchone()
        
        if user:
            session["user_id"] = user[0]
            return redirect("/")
        else:
            flash("Incorrect email or password.")
            return redirect("/login")
    
    return render_template("login.html")

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    
    car_models = sorted(df["name"].unique())
    companies = sorted(df["company"].unique())
    purchase_year = sorted(df["year"].unique(), reverse=True)
    fuel_types = sorted(df["fuel_type"].unique())

    companies.insert(0, "Select Company")
    purchase_year.insert(0, "Select Year")
    fuel_types.insert(0, "Select Fuel Type")
    
    return render_template("index.html", companies=companies, car_models=car_models, purchase_year=purchase_year, fuel_types=fuel_types)
@app.route("/predict", methods = ["POST"])
@cross_origin(supports_credentials = True)
def predict():
    company = request.form.get('company')
    car_model = request.form.get('car_model')
    purchase_year = request.form.get('purchase_year')
    fuel_type = request.form.get('fuel_type')
    kms_driven = request.form.get('kms_driven')

    prediction = model.predict(pd.DataFrame(columns=['name', 'company', 'year', 'kms_driven', 'fuel_type'], 
                                            data = np.array([car_model, company, purchase_year, kms_driven, fuel_type]).reshape(1, 5)))
    print(prediction)
    if prediction<0:
        return "0(Car is not preferable)"
    else:
        
        
        return str(np.round(prediction[0], 2))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
