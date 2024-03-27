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







@app.route('/add_place', methods=['POST'])
def add_place():
    place_name = request.form['place_name']
    
    # Check if the collection already exists
    if place_name in db.list_collection_names():
        return jsonify({'message': f'Collection {place_name} already exists'}), 400
    
    # Create a new collection
    db.create_collection(place_name)
    

    
    return jsonify({'message': f'Collection {place_name} created successfully'}), 200








# Inserting data into particular places ------------

@app.route('/insert_item',methods = ['GET','POST'])
def insert():

# note we use direct request.form but in this method we will not get default value none
# but if we use .get then we can get default value None
# both the methods are usefull
    place_name = request.args.get('place_name')    
    if request.method=='POST':
         itemName = request.form['itemName']
         itemCategory = request.form['itemCategory']
         username = request.form['username']
         userEmail = request.form['userEmail']
         date = request.form['date']
         status = request.form['status']
         description = request.form['description']
         place_name = request.form.get('place_name')

         insert_data = {
            'itemName': itemName,
            'itemCategory': itemCategory,
            'username': username,
            'userEmail': userEmail,
            'date': date,
            'status': status,
            'description': description,
            'place': place_name,
         }
    
        # accesing the collection from db
         place_collection = db[place_name]
         result = place_collection.insert_one(insert_data)
         # Check if insertion was successful
         print(place_name)
         if result.inserted_id:
            return 'Data inserted successfully!'
         else:
            return 'Failed to insert data.'


    # print(place_name)
    return render_template('insert.html',place_name=place_name)







#--------------- update ----------------------

@app.route('/update_card',methods = ['GET','POST'])
def update_card():

    
    username = request.form.get('username')
    place = request.form.get('place_name')
    # print(place)
    get_collection_of_place = db[place]
    req_doc = get_collection_of_place.find_one({'username':username})
    return render_template('update.html',documents=req_doc)



# # ----------- update main  when click one button final this will updayte the records--------------- 

@app.route('/update_card_main', methods=['GET', 'POST'])
def update_card_main():
    if request.method == 'POST':
        try:
            # Extract form data
            itemName = request.form['itemName']
            itemCategory = request.form['itemCategory']
            username = request.form['username'].strip()
            userEmail = request.form['userEmail']
            date = request.form['date']
            status = request.form['status']
            description = request.form['description']
            place_name = request.form.get('place_name')
            
          
            
            # Get collection
            place_collection = db[place_name]
            print(place_collection.name)
   

            update_data = {
             'itemName': itemName,
             'itemCategory': itemCategory,
             'username': username,
             'userEmail': userEmail,
             'date': date,
             'status': status,
             'description': description,
             'place': place_name,
             }

            print(update_data)
            # place_collection.update_one({'username':username},{'$set':update_data})
             # Perform update operation
            cur = current_user.username
            print(username)
            print(cur)
            result = place_collection.update_one({'username': username}, {'$set': update_data})
            print("Update Result:", result.raw_result)


            # Check if any update was successful
            print("Data updated successfully!")
            return 'Data updated successfully!'
        except Exception as e:
            print("Error:", e)
            return 'Failed to update data. Error: ' + str(e)
    else:
        return 'Invalid request method. Only POST requests are allowed.'






#--------------- delete card ----------------------

@app.route('/delete_card',methods = ['GET','POST'])
def delete_card():

  if current_user.is_authenticated:
    cur = current_user.username

    main_user = request.form['username']
    place = request.form['place_name']
    print(main_user)
    print(cur)

    if cur == main_user:
        place_collection = db[place]
        result = place_collection.delete_one({'username':main_user})
        print(result)
    else:
        return "login again to delete the specific card or the card you are trying to delete is not yours!!!"

    return "Card Deleted Successfully"

  else :
   return  "Login First to delete the card"







# founder section -------------------------------------

@app.route('/founder',methods = ['POST','GET'])
def founder():
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
        return render_template('founder.html', place_name=place_name, documents=documents, collections=collections_to_display)

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

            return render_template('founder.html', place_name=place_name, documents=documents, collections=collections_to_display)
        
        
        # If no place name is provided, render the template with available collections
        exclude_collections = ['users']
        all_collections = db.list_collection_names()
        collections_to_display = [c for c in all_collections if c not in exclude_collections]
        return render_template('founder.html', collections=collections_to_display)    






if __name__ == '__main__':
    app.run(debug=True, port=5001)
