from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy 
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:test@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kjhvsdjhfvsjhdvf'


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    hash_pass = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.hash_pass = make_pw_hash(password)

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(2000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner


def get_all_users():
    return User.query.all()

def get_all_posts():
    return Blog.query.all()


@app.before_request
def require_login():
    allowed_routes = ['index', 'blog_posts', 'login', 'register', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/')
def index():
    return render_template('index.html', users=get_all_users(), log_user=session.get('username',''))

@app.route('/login', methods=['POST', 'GET'])
def login():
    login_error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.hash_pass):
            session['username'] = username
            return redirect('/')
        else:
            login_error = "Username or password do not exist"
    return render_template('login.html', login_error=login_error)

@app.route('/register', methods=['POST', 'GET'])
def register():
    # some errors set to blank
    user_error = ''
    password_error = ''
    verify_error = ''
    existing_error = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        existing_user = User.query.filter_by(username=username).first()

        # validation if inputs are blank, between 3 and 20, no spaces, and password and verify do not match
        if len(username) < 3 or len(username) > 20 or not username or ' ' in username:
            username = ''
            user_error = "username must be between 3 and 20 characters"
        if len(password) < 3 or len(password) > 20 or ' ' in password:
            password_error = "password must be between 3 and 20 character"
        if password != verify: 
           verify_error = "password and password verification fields must match"
        if existing_user:
            existing_error = 'Username already exists'

        if not existing_user and not user_error and not password_error and not verify_error:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/')

    # pass errors into template
    return render_template('signup.html', user_error=user_error, password_error=password_error, verify_error=verify_error, existing_error=existing_error)


@app.route('/logout', methods=['GET'])
def logout():
    del session['username']
    return redirect('/')



@app.route('/blog')
def blog_posts():

    if request.args.get('user'):
        author_user = User.query.filter_by(username=request.args.get('user')).first()
        post_list = Blog.query.filter_by(owner=author_user).all()
        return render_template('user.html', blog=post_list, log_user=session.get('username',''))

    if request.args.get('id'):
        post_id = int(request.args.get('id'))
        user_post = Blog.query.get(post_id)
        return render_template('blog.html', blog=user_post, log_user=session.get('username',''))

    else:
        return render_template('user.html', blog=get_all_posts())

@app.route('/newpost', methods=['GET','POST'])
def create_post():

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if title == "":
            flash("title cannot be empty")

        if body == "":
            flash("body cannot be empty")

        owner = User.query.filter_by(username=session['username']).first()
        blog = Blog(title=title, body=body, owner=owner)
        db.session.add(blog)
        db.session.commit()
        return redirect ('/blog'+'?id='+str(blog.id))

    return render_template ('create.html', log_user=session['username'])

if __name__ == '__main__':
    app.run()




 