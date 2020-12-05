from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import math

# from flask_mail import Mail

local_server = True
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

# app.config.update(
#     MAIL_SERVER='smtp.gmail.com',
#     MAIL_PORT=465,
#     MAIL_USE_SSL=True,
#     MAIL_USERNAME=params['gmail_user'],
#     MAIL_PASSWORD=params['gmail_pwd']
# )
# mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

# initializing db
db = SQLAlchemy(app)


class Contacts(db.Model):
    """
    sno, name, phone_num, msg, date, email
    """
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(50), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    tag_line = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    postdate = db.Column(db.String(12), nullable=True)
    postedby = db.Column(db.String(50), nullable=False)


@app.route('/')
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]
    # Calculate total number of pages = total posts / number of post on 1 page
    last = math.ceil(len(posts) / int(params['no_of_posts']))

    # Pagination logic
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1

    page=int(page)

    """
    Slicing - what posts should be available on each page 
    Ex. page 1 :- posts 1 and 2 i.e. posts[0:2]
        page 2 :- posts 3 and 4 i.e. posts[2:4]
    """

    posts = posts[(page-1) * int(params['no_of_posts']): (page-1) * int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # check if user is already logged in
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.filter_by().all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params['admin_user'] and password == params['admin_pwd']:
            # set the session variable
            session['user'] = username
            posts = Posts.query.filter_by().all()
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html', params=params)


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    # if user is logged in and is trying to post
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_tagline = request.form.get('tagline')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_postedby = request.form.get('postedby')
            date = datetime.now()

            if sno == '0':
                post = Posts(title=box_title, tag_line=box_tagline, slug=box_slug, content=box_content, postdate=date,
                             postedby=box_postedby)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                print(post.slug)
                post.title = box_title
                post.tag_line = box_tagline
                post.slug = box_slug
                post.content = box_content
                post.postedby = box_postedby
                post.date = date
                db.session.commit()
                return redirect('/edit/' + sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post, sno=sno)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully!"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        """Add entry to the database"""
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone_num')
        msg = request.form.get('msg')

        entry = Contacts(name=name, phone_num=phone_num, msg=msg, date=datetime.now(), email=email)

        # db.session.add(entry)
        # db.session.commit()
        # mail.send_message("New message from " + name,
        #                   sender=email,
        #                   recipients=[params['gmail_user']],
        #                   body=msg + "\n" + phone_num)

    return render_template('contact.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


app.run(debug=True)
