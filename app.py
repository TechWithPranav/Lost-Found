import secrets
import os
from flask import Flask, render_template, redirect, request, session, url_for, flash,jsonify
from pymongo import MongoClient
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from bson import ObjectId  # Import ObjectId from bson module

app = Flask(__name__)

#sdfshh
# Generate a secure secret key
secret_key = secrets.token_hex(16)

# Set the secret key securely from environment variable or fallback to a default value
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secret_key)

client = MongoClient('mongodb://localhost:27017/')
db = client['Lost_And_Found']
users_collection = db['users']

login_manager = LoginManager()
login_manager.init_app(app)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, username):
        self.username = username
    def get_id(self):
        return str(self.username)    

# Load user from database
@login_manager.user_loader
def load_user(username):
    user_data = users_collection.find_one({'username': username})
    if user_data:
        return User(user_data['username'])
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html', current_user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname']
        middlename = request.form['middlename']
        lastname = request.form['lastname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        dob = request.form['dob']
        mobile = request.form['mobile']

        if users_collection.find_one({'username': username}):
            flash('Username already taken. Please choose a different username.', 'error')
            return redirect(url_for('signup'))

        new_user = {
            'firstname': firstname,
            'middlename': middlename,
            'lastname': lastname,
            'username': username,
            'email': email,
            'password': password,
            'address': address,
            'dob': dob,
            'mobile': mobile
        }
        users_collection.insert_one(new_user)
        flash('Signup successful. You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = users_collection.find_one({'username': username, 'password': password})

        if user_data:
            user = User(user_data['username'])
            print(user)
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))



@app.route('/profile',methods = ['GET','POST'])
def profile():

    user_data = users_collection.find_one({'username':current_user.username})
    return render_template('profile.html',user_data= user_data)    






# ------------loster ---------------- 





@app.route('/loster', methods=['GET', 'POST'])
def loster():
    documents = None
    if request.method == 'POST':
        # Handle POST requests
        place_data = request.json
        place_name = place_data.get('placeName')

        # Fetch documents from the collection associated with place_name
        collection = db[place_name]
        documents = list(collection.find())

         # Get all collections to display in the dropdown
        all_collections = db.list_collection_names()
        collections_to_display = [c for c in all_collections if c not in ['users']]

        # Redirect to the same route with place_name as query parameter
        return render_template('loster.html', place_name=place_name, documents=documents, collections=collections_to_display)

    else:
        # Handle GET requests
        place_name = request.args.get('place_name')
        if place_name:
            # Fetch documents from the collection associated with place_name
            collection = db[place_name]
            documents = list(collection.find())

            
            # Get all collections to display in the dropdown
            all_collections = db.list_collection_names()
            collections_to_display = [c for c in all_collections if c not in ['users']]

            return render_template('loster.html', place_name=place_name, documents=documents, collections=collections_to_display)
        
        
        # If no place name is provided, render the template with available collections
        exclude_collections = ['users']
        all_collections = db.list_collection_names()
        collections_to_display = [c for c in all_collections if c not in exclude_collections]
        return render_template('loster.html', collections=collections_to_display)





# @app.route('/loster_handler', methods=['GET', 'POST'])
# def loster_handler():

#     documents = None
#     if request.method == 'POST':
#         # Get the place name from the JSON data in the request
#         place_data = request.json
#         place_name = place_data.get('placeName')

#         # Fetch documents from the collection associated with place_name
#         collection = db.get_collection(place_name)
#         documents = list(collection.find())


#         # Redirect to the same route but with GET method to render the template
#         return redirect(url_for('loster_handler', place_name=place_name,documents=documents))
    
#     # Get the place name from the query parameters if it exists
#     place_name = request.args.get('place_name')

#     collection = db.get_collection(place_name)
#     documents = list(collection.find())
#     # Render the template with the place name
#     return render_template('loster_handler.html', place_name=place_name,documents=documents)






@app.route('/add_place', methods=['POST'])
def add_place():
    place_name = request.form['place_name']
    
    # Check if the collection already exists
    if place_name in db.list_collection_names():
        return jsonify({'message': f'Collection {place_name} already exists'}), 400
    
    # Create a new collection
    db.create_collection(place_name)
    

    
    return jsonify({'message': f'Collection {place_name} created successfully'}), 200





# temp purpose 









if __name__ == '__main__':
    app.run(debug=True, port=5001)
