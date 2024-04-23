import secrets
import os
from flask import Flask, render_template, redirect, request, session, url_for, flash,jsonify
from pymongo import MongoClient
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from bson import ObjectId  # Import ObjectId from bson module
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
import requests


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Ensure this directory exists
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB

#sdfshh
# Generate a secure secret key
secret_key = secrets.token_hex(16)

# Set the secret key securely from environment variable or fallback to a default value
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secret_key)

client = MongoClient('mongodb://localhost:27017/')
db = client['Lost_And_Found']
users_collection = db['users']
history = db['history']
mcq_solved_verified = db['mcq_solved_verified']

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
        collections_to_display = [c for c in all_collections if c not in ['users','history','mcq_solved_verified']]

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
            collections_to_display = [c for c in all_collections if c not in ['users','history','mcq_solved_verified']]

            return render_template('loster.html', place_name=place_name, documents=documents, collections=collections_to_display)
        
        
        # If no place name is provided, render the template with available collections
        exclude_collections = ['users','history','mcq_solved_verified']
        all_collections = db.list_collection_names()
        collections_to_display = [c for c in all_collections if c not in exclude_collections]
        return render_template('loster.html', collections=collections_to_display)






# item details for loster ----------------

@app.route('/item/<item_id>/<place>')
def item_detail(item_id,place):
    collection = db[place]
    item = collection.find_one({'_id': ObjectId(item_id)})
    # print(collection)
    # print(item)
    if item:
        return render_template('item_detail.html', doc=item)
    else:
        return 'Item not found', 404
    



# item details for founder ----------------

@app.route('/item_detail2/<item_id>/<place>')
def item_detail2(item_id,place):
    collection = db[place]
    item = collection.find_one({'_id': ObjectId(item_id)})

    verified_mcq_collection = db['mcq_solved_verified']  
         
    print(item.get('username'))
    print(item_id)
    print(current_user.username)
    if (item.get('username')) == (current_user.username):
        veri_mcq = verified_mcq_collection.find_one({'id_user': item_id})  
    else:
        veri_mcq = False

    if item:
        return render_template('item_detail2.html', doc=item,veri_mcq=veri_mcq)
    else:
        return 'Item not found', 404









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
    
    DEFAULT_IMAGE_URL = 'https://via.placeholder.com/150'

    if request.method=='POST':
         itemName = request.form['itemName']
         itemCategory = request.form['itemCategory']
         username = request.form['username']
         userEmail = request.form['userEmail']
         date = request.form['date']
         status = request.form['status']
         description = request.form['description']
         place_name = request.form.get('place_name')

         item_image  = request.files['itemImage']
        #  print(item_image)
         if item_image and item_image.filename != '' and allowed_file(item_image.filename):
             filename = secure_filename(item_image.filename)
             mimetype = item_image.mimetype
             image_data = item_image.read()
             image_b64 = base64.b64encode(image_data).decode('utf-8')
         else:
             # No file uploaded, or the wrong file type was provided
             filename = 'default'
             mimetype = 'image/png'
             image_b64 = base64.b64encode(requests.get(DEFAULT_IMAGE_URL).content).decode('utf-8')

         if status == "Found":
             question1 = request.form['question1']
             answer1 = request.form['answer1']             
             question2 = request.form['question2']
             answer2 = request.form['answer2']             
             question3 = request.form['question3']
             answer3 = request.form['answer3']

             insert_data = {
                'itemName': itemName,
                'itemCategory': itemCategory,
                'username': username,
                'userEmail': userEmail,
                'date': date,
                'status': status,
                'description': description,
                'place': place_name,
                'image': {
                    'filename': filename,
                    'mimetype': mimetype,
                     'data': image_b64
                },
                'question1':question1,
                'answer1':answer1,
                'question2':question2,
                'answer2':answer2,
                'question3':question3,
                'answer3':answer3,

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


                 
         insert_data = {
            'itemName': itemName,
            'itemCategory': itemCategory,
            'username': username,
            'userEmail': userEmail,
            'date': date,
            'status': status,
            'description': description,
            'place': place_name,
            'image': {
              'filename': filename,
              'mimetype': mimetype,
              'data': image_b64
             }
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}








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
    DEFAULT_IMAGE_URL = 'https://via.placeholder.com/150'
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

            item_image  = request.files['itemImage']
        #  print(item_image)
            if item_image and item_image.filename != '' and allowed_file(item_image.filename):
             filename = secure_filename(item_image.filename)
             mimetype = item_image.mimetype
             image_data = item_image.read()
             image_b64 = base64.b64encode(image_data).decode('utf-8')
            else:
             # No file uploaded, or the wrong file type was provided
             filename = 'default'
             mimetype = 'image/png'
             image_b64 = base64.b64encode(requests.get(DEFAULT_IMAGE_URL).content).decode('utf-8')
            
            cur = current_user.username 

            if cur == username:

          
            
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
                'image': {
                 'filename': filename,
                 'mimetype': mimetype,
                 'data': image_b64
             }
             }

             print(update_data)
             # place_collection.update_one({'username':username},{'$set':update_data})
             # Perform update operation
             cur = current_user.username
             print(username)
             print(cur)
             result = place_collection.update_one({'username': username}, {'$set': update_data})
             print("Update Result:", result.raw_result)
             return 'Data updated successfully!'


             # Check if any update was successful
            else:
             return 'The card your trying to delete not yours or please login again'
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
    item_name = request.form.get('itemName')
    place = request.form['place_name']
    print(main_user)
    print(cur)
    print(item_name)
    print(place)

    if cur == main_user:
        place_collection = db[place]
        # Query to find the document with the matching item name and username
        query = {'itemName': item_name, 'username': main_user}
    
       # Delete the matching document if it exists
        result = place_collection.delete_one(query)
        print(result)
    else:
        return "login again to delete the specific card or the card you are trying to delete is not yours!!!"

    return "Card Deleted Successfully"

  else :
   return  "Login First to delete the card"
  


#--------------- user_verified by founder ----------------------

@app.route('/user_verified',methods = ['GET','POST'])
def user_verified():

  if current_user.is_authenticated:
    cur = current_user.username

    main_user = request.form['username']
    item_name = request.form['itemName']
    userEmail = request.form['userEmail']
    place = request.form['place_name']
    # Get the current date and time
    current_datetime = datetime.now()
    
    # Convert the datetime object to a string if needed
    current_date_str = current_datetime.strftime('%Y-%m-%d')
    current_time_str = current_datetime.strftime('%H:%M:%S')

    print(main_user)
    print(cur)

    if cur == main_user:
        place_collection = db[place]
        # Query to find the document with the matching item name and username
        query = {'itemName': item_name, 'username': main_user}
    

        # store in database to track history of found items and loster has satified

        insert_data = {
            'itemName': item_name,
            'username': main_user,
            'userEmail': userEmail,
            'date': current_date_str,
            'time': current_time_str,
            'place': place,
        }
    
        # accesing the collection from db
        history = db["history"]
        result = history.insert_one(insert_data)
         # Check if insertion was successful
 
        if result.inserted_id:
            result2 = place_collection.delete_one(query)
            print(result2)
            return 'User Verified successfully!'
        
        else:
            return 'Failed to track data.'

    else:
        return "login again to verify user and delete the specific card or the card you are trying to delete is not yours!!!"

  else :
     return  "Login First to verify the card"












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
        collections_to_display = [c for c in all_collections if c not in ['users','history','mcq_solved_verified']]

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
            collections_to_display = [c for c in all_collections if c not in ['users','history','mcq_solved_verified']]

            return render_template('founder.html', place_name=place_name, documents=documents, collections=collections_to_display)
        
        
        # If no place name is provided, render the template with available collections
        exclude_collections = ['users','history','mcq_solved_verified']
        all_collections = db.list_collection_names()
        collections_to_display = [c for c in all_collections if c not in exclude_collections]
        return render_template('founder.html', collections=collections_to_display)    



# recoverd section -------------------------------------
@app.route('/recoverd',methods = ['GET','POST'])
def recoverd():
   if request.method == 'POST':
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']

        # Query MongoDB collection to get documents within the specified date range
        # accesing the collection from db
        history = db["history"]
        recovered_items = list(history.find({'date': {'$gte': start_date_str, '$lte': end_date_str}}))
        print(start_date_str)
        print(end_date_str)
        print(recovered_items)


        return render_template('recoverd.html', items=recovered_items)
   return render_template('recoverd.html',items=[])
  
    



# verification of mcq ------------- 

# @app.route('/verified_mcq', methods=['POST','GET'])
# def verify_mcq():
#     data = request.get_json()
#     verified = data.get('verified', False)
#     username = data.get('username', False)
#     id_user = data.get('id_user', False)

#     if verified:
#         # Assume `mcq_verified` is your collection in MongoDB
#         # Store verification status
#         db.mcq_solved_verified.insert_one({'verified': True,'username':username,'id_user':id_user})

#         return jsonify({'success': True}), 200
#     else:
#         return jsonify({'success': False, 'message': 'Verification failed'}), 400

@app.route('/verified_mcq', methods=['GET', 'POST'])
def verify_mcq():

    data = None
    verified = None
    username = None
    id_user = None
    item_name = None    
    if request.method == 'POST':
        # Handle POST request
        data = request.get_json()
        verified = data.get('verified', False)
        username = data.get('username', False)
        id_user = data.get('id_user', False)
        item_name = data.get('item_name', False)
        place_name = data.get('place_name', False)

        print(verified)
        print(username)
        print(id_user)
        print(item_name)
        print(place_name)
        db.mcq_solved_verified.insert_one({'verified': True,'username':username,'id_user':id_user,'item_name':item_name,'place_name':place_name})


        # Assuming data handling logic here


        return jsonify({'success': True}), 200
    elif request.method == 'GET':
        # doc = collection.find_one({'_id': ObjectId(document_id)})
        doc_id = request.args.get('id_user') 
        place_name = request.args.get('place') 
        # print(doc_id)
        # print(place_name)

        place = db[place_name]
        doc = place.find_one({'_id': ObjectId(doc_id)})     
        # print(doc)

        
        verified_mcq_collection = db['mcq_solved_verified']       
        veri_mcq = verified_mcq_collection.find_one({'id_user': doc_id})  
        print(veri_mcq)
        print('hey')
        # print(current_user._id)


        return render_template('item_detail2.html',doc= doc,veri_mcq=veri_mcq)






if __name__ == '__main__':
    app.run(debug=True, port=5001)
