from flask_sqlalchemy import SQLAlchemy
import os
import socket
from flask import Flask, render_template, request, jsonify, session, url_for, redirect, json
from datetime import timedelta, datetime
from flask_wtf import FlaskForm,RecaptchaField
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
##
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
##
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir+'\dbv1.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdTPogUAAAAAC9SLvgd-dwRPed9vF7Wod-Vtp94'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LdTPogUAAAAAImGDbjnnmtIZlC6fjJAi33GmeuH'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.permanent_session_lifetime = timedelta(seconds=3600)
db = SQLAlchemy(app)



class articleform(FlaskForm):
    recaptcha = RecaptchaField()


class Author(db.Model):
    __tablename__= 'authors'
    id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    articles = db.relationship('Article', backref='author')
    comments = db.relationship('Comment', backref='author')


class Subject(db.Model):
    __tablename__= 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    articles = db.relationship('Article', backref='subject')


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    title = db.Column(db.String(50))
    body = db.Column(db.Text)
    comments = db.relationship('Comment', backref='article')
    time = db.Column(db.DateTime)
    like = db.Column(db.Integer)
    dislike = db.Column(db.Integer)


class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    title = db.Column(db.String(50))
    body = db.Column(db.Text)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    body = db.Column(db.Text)
    time = db.Column(db.DateTime)
    like = db.Column(db.Integer)
    dislike = db.Column(db.Integer)
class IPs(db.Model):
    __tablename__ = 'ip'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(50))
    time = db.Column(db.DateTime)

class LoginForm(FlaskForm):
    author = StringField('author', validators=[InputRequired('A author is required!'),Email(message='Email Format Wrong')])
    subject = StringField('subject', validators=[InputRequired('A subject is required!')])
    title = StringField('title', validators=[InputRequired('A title is required!')])
    body = StringField('body', validators=[InputRequired('A body is required!')])
    file = FileField("File(pdf)", validators=[FileRequired(), FileAllowed(['pdf'])])

class LoginForm2(FlaskForm):
    mail = StringField('mail', validators=[InputRequired(message='Email Required')])
    password = PasswordField('password', validators=[InputRequired(message='passport Required')])


def if_logined():
    mail = session.get('mail')

    if mail is None:
        mail = 'Hello, Stranger'

    return mail


#-----------------------------------------
@app.route('/upload1')
def upload1():
    return render_template('uploads.html')

@app.route('/upload',methods=['POST'])
def upload():
    target= os.path.join(APP_ROOT, 'folder/')
    print(target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        destination = "/".join([target,filename])
        print(destination)
        file.save(destination)
        return redirect(url_for('index'))

#-----------------------------------------

@app.route('/')
def index():

    subjects = Subject.query.all()
    post = Article.query.order_by(Article.time.desc()).all()
    testss = socket.gethostbyname(socket.getfqdn())
    print(testss)
    ips = IPs(ip=testss, time=datetime.now())
    db.session.add(ips)
    db.session.commit()


    return render_template('index.html', mail=if_logined(), subjects=subjects,post=post)




@app.route('/articles/<subject_id>', methods=['GET', 'POST'])
def get_articles(subject_id):
    page = request.args.get('page', 1, type=int)
    pagination = Article.query.filter(Article.subject_id == subject_id).order_by(Article.time.desc()).paginate(page, per_page=5, error_out=False)

    articles = pagination.items
    return render_template('articles.html', articles=articles, pagination=pagination, mail=if_logined(),
                           subject_id=subject_id)


@app.route('/article/<article_id>')
def get_article(article_id):
    commentss = Comment.query.order_by(Comment.time.desc()).all()
    article = Article.query.filter(Article.id == article_id).first()



    return render_template('article.html', article=article, commentss=commentss, Tool=Tool)



@app.before_request
def before_action():
    app.logger.debug('-------------------------------------------------request.path:' + request.path + '-------------------------------------------------------------------')

    if not request.path.startswith('/static') and not request.path == '/login':
        session['newurl'] = request.path

    if 'mail' not in session:
        if  request.path == '/admin':
            return redirect('/login')

    print(session.get('2'))


@app.after_request
def ip_count(response):
    if request.path.startswith('/article/'):
        article_id = request.path[request.path.rfind('/article/', 1):]
        print(article_id)
        session[article_id] = 66666;
    return response

@app.route('/login', methods=['POST', 'GET'])
def login():
    login = LoginForm2()
    mail = session.get('mail')
    if mail is not None:
        return redirect(url_for('index'))

    admin = format(login.mail.data)
    adminpw = format(login.password.data)

    if request.method == 'POST':
        if admin == 'admin@qq.com':

            if adminpw == '123456':
                session['mail'] = format(login.mail.data)
                newurl = session['newurl']
                session.pop('newurl', None)
            else:
                return render_template('login.html', login=login)
        else:
            return render_template('login.html', login=login)

        return redirect(newurl)
    else:
        return render_template('login.html',login=login)


@app.route('/test_get', methods=['POST', 'GET'])
def test_get():
    app.logger.debug('======================================================')
    session.pop('mail')

    name = request.args.get('name')
    age = int(request.args.get('age'))

    if name == 'kikay' and age == 18:
        return jsonify({'result': 'ok'})
    else:
        return jsonify({'result': 'error'})


@app.route('/mystring')
def mystring():
    app.logger.debug('======================================================')
    return 'my string'

#-------------------------------------------------------------------------------------------------------

@app.route('/post/<int:post_id>')
def post(post_id):
    post=Article.query.filter_by(id=post_id).one()
    return render_template('article.html',post=post)




@app.route('/addposting', methods=['POST','GET'])

def addposting():
    addposting = LoginForm()



    if addposting.validate_on_submit():

        target = os.path.join(APP_ROOT, 'folder/')
        print(target)

        if not os.path.isdir(target):
            os.mkdir(target)

        for file in request.files.getlist("file"):
            print(file)
            filename = file.filename
            destination = "/".join([target, filename])
            print(destination)
            file.save(destination)

        authors = format(addposting.author.data)
        subject = format(addposting.subject.data)
        title = format(addposting.title.data)
        body = format(addposting.body.data)

        if authors == 'admin@qq.com':
            authors = 2
        else:
            authors = 1

        if subject == 'Math':
            subject = 1
        elif subject == 'History':
            subject = 2
        else:
            subject = 3

        article = Article(author_id=authors, subject_id=subject, title=title, body=body, time=datetime.now(),like=0,dislike=0)
        db.session.add(article)
        db.session.commit()

        return redirect(url_for('index'))
    return render_template('posting.html', addposting=addposting)


@app.route('/commenting', methods=['POST', 'GET'])
def commenting():
    author = request.form['author']
    body = request.form['comment']
    articleid = request.form['articleids']
    likedis = request.form['liked']
    test1 = Article.query.filter_by(id=articleid).first()

    if likedis == '1':
        test1.like += 1
        db.session.commit()

    else :
        test1.dislike += 1
        db.session.commit()


    if author == 'admin@qq.com':
        author = 2
    elif author == 'anton@qq.com':
        author = 1
    else:
       author = 3



    comments = Comment(author_id=author, body=body,article_id=articleid, time=datetime.now(), like=0,dislike=0)
    db.session.add(comments)
    db.session.commit()
    return redirect(url_for('index'))



@app.route('/admin')
def admin():

    author=Author.query.all()
    comen = Comment.query.all()
    art = Article.query.all()

    mail = session.get('mail')
    if mail is None:
     return render_template('login.html')
    else:
     return render_template('admin.html',mail=if_logined(),author=author,art=art,comen=comen)

@app.route('/donation')
def donation():

    return render_template('donation.html')

@app.route('/delete/article/<int:article_id>', methods=['POST', 'GET'])
def delete_article(article_id):
    article = Article.query.filter(Article.id == article_id).first()

    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/comment/<int:comment_id>', methods=['POST', 'GET'])
def delete_comment(comment_id):
    comments = Comment.query.filter(Comment.id == comment_id).first()

    db.session.delete(comments)
    db.session.commit()
    return redirect(url_for('index'))

#-------------------------------------------------------------------------email filter
class Tool:

    @staticmethod
    def email_display_filter(email):
        pre = email[:email.rfind('@')]
        display = pre[:len(pre) // 2]
        suf = email[email.rfind('@') + 1:]

        for i in range(len(pre[len(pre) // 2:])):
            display += '*'

        return display + suf


#-----------------------------------------------------------------------------------------------------
@app.route('/home')
def home():
    return render_template('home.html', mail=session['mail'])



@app.route('/post_article', methods=['POST', 'GET'])
def post_article():
    title = request.args.get('title')
    body = request.args.get('body')

    article = Article(author_id=1, subject_id=1, title=title, body=body, time=datetime.now().date())
    db.session.add(article)
    return jsonify({'result': 'ok'})


@app.route('/edit')
def edit():
    return render_template('edit.html', mail=if_logined())



@app.route('/api/auth', methods=['POST', 'GET'])
def auth():

    return jsonify({"result": "ojbk"})



if __name__ == '__main__':
    app.run(debug=True)











