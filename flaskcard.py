# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flaskext.mysql import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user , logout_user , current_user , login_required
from contextlib import closing # helps initialize a database so we don't have to hardcode
from models import *

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'development key'
app.config['USERNAME'] = 'admin'
app.config['PASSWORD'] = 'default'
# app.config['MYSQL_DATABASE_USER'] = 'root'
# app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
# app.config['MYSQL_DATABASE_DB'] = 'EmpData'
# app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flaskcard.db'

db.init_app(app)
lm = LoginManager()
lm.init_app(app)


def get_current_user():
    if g.user is None:
        return None
    return User.query.filter_by(id=current_user.get_id()).first()

@app.before_request
def before_request():
    """
    Ensure that the requests you make are associated with a user (for the most part)
    """
    g.user = current_user

@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    # Ensure unique usernames!
    if User.query.filter_by(username=request.form['username']).first() is not None:
        flash('That username is already taken')
        return redirect(url_for('register'))

    new_user = User(request.form['username'],request.form['password'])
    db.session.add(new_user)
    db.session.commit()
    flash('User registered!')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    err = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        registered_user = User.query.filter_by(username=username,password=password).first()
        if registered_user is None:
            flash('Username or Password is invalid' , 'error')
            return redirect(url_for('login'))
        login_user(registered_user)
        flash('You\'re logged in')
        return redirect(request.args.get('next') or url_for('show_semesters'))
    return render_template('login.html', error=err)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You logged out')
    return redirect(url_for('login'))

@app.before_first_request
def initialize_database():
    db.create_all()

@app.route('/')
@login_required
def show_semesters():
    """
    Show semesters for the logged-in user
    """
    user = User.query.filter_by(id=current_user.get_id()).first()
    if user is None:
        return redirect(url_for('login'))
    semesters = [semester for semester in user.semesters]
    return render_template('overview.html', semesters=semesters)

@app.route('/add_semester', methods=['POST'])
@login_required
def add_semester():
    # TODO: separate form validation and object creation
    semester = Semester(request.form['season'],request.form['year'],current_user.get_id())
    db.session.add(semester)
    db.session.commit()
    flash('Semester has been added!')
    return redirect(url_for('show_semesters'))


@app.route('/semester')
@login_required
def semester():
    try:
        season = request.args.get('season')
        year = request.args.get('year')
    except:
        flash('Semester does not exist in the database')
        return redirect(url_for('show_semesters'))
    # TODO: show courses that exist for that semester
    semester = Semester.query.filter_by(season=season,year=year,user_id=get_current_user().id).first()
    if semester is None:
        flash('Could not find a semester associated with %s %s for %s' % (season,year,get_current_user().id))
        return redirect(url_for('show_semesters'))
    courses = [course for course in semester.courses]
    return render_template('semester.html', courses=courses,season=season,year=year,semester=semester)


@app.route('/semester/add_course', methods=['POST'])
@login_required
def add_course():
    name = request.form['name']
    instructor = request.form['instructor']
    semester_id = request.form['semester_id']
    new_course = Course(name,instructor,semester_id)

    db.session.add(new_course)
    db.session.commit()
    flash('Course added!')
    year = request.form['year']
    season = request.form['season']
    return redirect(url_for('semester', season=season, year=year))

@app.route('/course/<course_id>')
@login_required
def course(course_id):
    course = Course.query.filter_by(id=course_id).first()
    if course is None:
        return redirect(url_for('semester',year=request.form['year'],season=request.form['season']))
    semester = Semester.query.filter_by(id=course.semester_id).first()
    context = {
        'course' : course,
        'semester' : semester,
        'assignments' : [assignment for assignment in course.assignments]
    }
    return render_template('course.html',**context)

@app.route('/course/<course_id>/add_grade', methods=['POST'])
@login_required
def add_grade(course_id):
    course = Course.query.filter_by(id=course_id).first()
    semester = Semester.query.filter_by(id=course.semester_id).first()
    assignment = Assignment(request.form['title'],
                            request.form['points_earned'],
                            request.form['total_points'],
                            course_id,
                            category=request.form['category'])
    db.session.add(assignment)
    db.session.commit()
    return redirect(url_for('course', course_id=course_id, semester_id=course.semester_id))

@app.route('/course/assignments/<assignment_id>'), methods=['GET']
def assignment(assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).first()
    if assignment is None:

        flash('Assignment does not exist in our database!')
        return redirect(url_for('course',course_id=))
    course = Course.query.filter_by(id=assignment.course_id).first()
    return render_template('assignment.html',{assignment : assignment,
                                                course : course})
# running the app by itself from command line
if __name__ == "__main__":
    app.run()
