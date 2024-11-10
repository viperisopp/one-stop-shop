import pymongo
from datetime import datetime
from flask import Flask,render_template,request,redirect
from bson.objectid import ObjectId
from flask import flash
import random
from passlib.hash import sha256_crypt
import os
from dotenv import load_dotenv

app = Flask(__name__, template_folder='../templates')

#app = Flask("one_stop_shop")
app.config['SECRET_KEY'] = 'safe^&*hdgahksdg'
load_dotenv()

client = pymongo.MongoClient(os.getenv('MONGO_URI'))
db = client.one_stop_shop

session = {}
collection = db.accounts
collection2 = db.stock
collection3 = db.cart

@app.route('/',methods = ["GET","POST"])
def index():
    stores = collection.find()
    return "render_template(index.html,stores=stores)"
#     if request.method == "GET":
#         if session:
#             del session['email']
# #        collection3.delete_many({})
# #        collection3.insert_one({})
#         stores = collection.find()
#         print(stores)
#         return render_template("index.html",stores=stores)
#     if request.method == "POST":
#         if 'cont_shop' in request.form:
#             if session:
#                 del session['email']
#             stores = collection.find()
#             return render_template("index.html",stores=stores)
#         else:
#             if session:
#                 del session['email']
#             collection3.delete_many({})
#             collection3.insert_one({})
#             stores = collection.find()
#             flash('Checkout Successful!')
#             return render_template("index.html",stores=stores)
    
@app.route('/register', methods = ["POST"])
def new_shop():
    d={}
    if request.form['shop_name']:
        d["shop_name"] = request.form['shop_name']
    else:
        flash("you must submit an entry for all the forms")
        return redirect('/')
    if request.form['owner_name']:
        d["owner_name"] = request.form['owner_name']
    else:
        flash("you must submit an entry for all the forms")
        return redirect('/')
    if request.form['email'] and not collection.find_one({"email":request.form['email']}):
        d["email"] = request.form['email']
    else:
        flash("you must submit an entry for all the forms")
        return redirect('/')
    if request.form['contact'] and not collection.find_one({"contact":request.form['contact']}):
        d["contact"] = request.form['contact']
    else:
        flash("you must submit an entry for all the forms")
        return redirect('/')
    if request.form['password']:
        d["password"] = sha256_crypt.hash(request.form['password'])
    else:
        flash("you must submit an entry for all the forms")
        return redirect('/')
    
    collection.insert_one(d)
    flash("store created!")

    return redirect("/")

@app.route('/login', methods = ['POST'])
def shop_login():
    d = {}
    d['email'] = request.form['email']
    d['password'] = request.form['password']
    if collection.find_one({"email":d['email']}):
        if sha256_crypt.verify(d['password'],collection.find_one({"email":d['email']})['password']):
            session['email'] = d['email']
            return redirect('/home')
    flash('The email or password your entered is incorrect')
    return redirect('/')


@app.route('/home',methods = {'GET','POST'})
def home():
    if request.method=="GET":
        products = collection2.find({'identity':session['email']})
        return render_template('shop_home.html',products=products)

@app.route('/logout',methods = ['POST'])
def logout():
    del session['email']
    return redirect('/')

@app.route('/product',methods = ['POST'])
def addprod():
    d = {}
    d['name'] = request.form['product_name']
    d['description'] = request.form['product_description']
    d['price'] = request.form['product_price']
    d['stock'] = int(request.form['amt_stock'])
    d['image'] = request.form['image_link']
    d['identity'] = session['email']
    collection2.insert_one(d)
    flash('successful entry!')
    return redirect('/home')

@app.route('/addstock/<product_id>',methods= ["POST"])
def addstock(product_id):
    if request.form['stockadder']:
        collection2.update_one({'_id':ObjectId(product_id)},{'$inc':{'stock':int(request.form['stockadder'])}})
    return redirect('/home')


@app.route('/shop/<email>',methods=['GET',"POST"])
def display_shop(email):
    if request.method == "GET":
        stores = collection.find()
        products = collection2.find({'identity':email})
        return render_template('index.html',products=products,stores=stores)
    elif request.method == "POST":
        if 'add_to_cart' in request.form:
            id = ObjectId(request.form['add_to_cart'])
            email = collection2.find_one({"_id":id})["identity"]
            if request.form['stocktocart'] == '':
                flash('please select a quantity')
                return redirect('/shop/'+email)
            collection2.update_one({'_id':id},{'$inc':{'stock':-1*int(request.form['stocktocart'])}})
            product = collection2.find_one({'_id':id})
            product_to_add = {}
            product_to_add['name'] = product['name']
            product_to_add['quantity'] = int(request.form['stocktocart'])
            product_to_add['price'] = product['price']
            collection3.update_one({"_id":collection3.find_one({})["_id"]}, {"$push":{'cart':product_to_add}})
            return redirect('/shop/'+email)
        else:
            stores = collection.find()
            products = collection2.find({'identity':email})
            return render_template('index.html',products=products,stores=stores)


@app.route('/checkout',methods=['GET',"POST"])
def checkout_screen():
    if request.method == "GET":
        if "cart" in collection3.find_one():
            items = collection3.find_one()["cart"]
        else:
            flash("You must buy something before checking out")
            return redirect("/")
        cart = []
        for n in items:
            found = False
            for i in cart:
                if n["name"] == i["name"]:
                    i['quantity'] += n['quantity']
                    found = True
            if found == False:
                cart.append(n)
        
        total = 0
        for n in cart:
            total += int(n['price']) * n['quantity']
        return render_template('checkout.html',cart=cart,total=total)




if __name__ == '__main__': 
    app.run()