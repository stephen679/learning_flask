from sqlalchemy import Column, Integer, String, Table, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    semesters = db.relationship('Semester', backref='person',lazy='dynamic')

    def __init__(self, username="", password=""):
        self.username = username
        self.password = password

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        """
        Flask-Login id's require unicode strings!
        """
        return unicode(self.id)

    def __repr__(self):
        return '<User: %r (%r %r)>' % (self.username,self.first_name, self.last_name)

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(String(10))
    year = db.Column(Integer)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id')) # attached to a user model
    courses = db.relationship('Course', backref='semester',lazy='dynamic') # one-to-many, Semester* to courses

    def __init__(self,season="WINTER",year=2016,user_id=-1):
        self.season = season
        self.year = year
        self.user_id = user_id

    def __repr__(self):
        return '<Semester: %r %r>' % (self.season,self.year)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester_id = db.Column(db.Integer,db.ForeignKey('semester.id'))
    name = db.Column(db.String(128))
    instructor = db.Column(db.String(128))
    categories = db.relationship('Category', backref='course',lazy='dynamic')

    def __init__(self, name="", instructor="",semester_id=-1,categories=None):
        self.semester_id = semester_id
        self.name = name
        self.instructor = instructor
        if categories is not None:
            self.categories = categories

    def __repr__(self):
        return '<Course: %r, Taught by: %r>' % (self.name, self.instructor)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128),primary_key=False)
    earned_points = db.Column(db.Integer)
    total_points = db.Column(db.Integer)
    description = (db.Column(db.String(128)))
    category_id = db.Column(db.Integer,db.ForeignKey('category.id'))

    def __init__(self,name="",earned_points=0.0,total_points=0.0,category_id=-1,description=None):
        self.name = name
        self.earned_points = earned_points
        self.total_points = total_points
        self.category_id = category_id
        if description is not None:
            self.description = description

    def __repr__(self):
        return '<Assignment: %r, %r/%r point>' % \
                                    (self.name, self.earned_points,self.total_points)

class Category(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(128))
    weight = db.Column(db.Float) # 0.0 < weight <= 1.0
    assignments = db.relationship('Assignment', backref='person', lazy='dynamic')
    course_id = db.Column(db.Integer,db.ForeignKey('course.id'))

    def __init__(self, name="", weight=0.0,course_id=-1):
        self.name = name
        self.weight = weight
        self.course_id = course_id

    def compute_average(self):
        return self.compute_raw_earned()*1.0/self.compute_raw_total()*self.weight

    def compute_raw_earned(self):
        return reduce(lambda total,assignment: total + assignment.earned_points,self.assignments,0)

    def compute_raw_total(self):
        return reduce(lambda total, assignment: total + assignment.total_points,self.assignments,0)
