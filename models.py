from datetime import datetime

from extensions import db, app, login_manager
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    birthday = db.Column(db.Date)
    role = db.Column(db.String)
    picture = db.Column(db.String)

    def __init__(self, first_name, last_name, email, password, birthday,
                 role="guest", picture="default.jpg"):
        self.username = first_name + " " + last_name
        self.email = email
        self.password = generate_password_hash(password)
        self.birthday = birthday
        self.role = role
        self.picture = picture

    def check_password(self, password):
        return check_password_hash(self.password, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    slug = db.Column(db.String, unique=True)
    image = db.Column(db.String)
    content = db.Column(db.String)
    date = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='blogs')
    likes = db.Column(db.Integer, default=0)
    liked_by = db.relationship('User', backref='liked_blogs')

    def __init__(self, title, slug, content, image, user_id):
        self.title = title
        self.slug = slug
        self.content = content
        self.user_id = user_id
        self.image = image

    def add_like(self):
        if current_user not in self.liked_by:
            self.liked_by.append(current_user)
            self.likes += 1
            db.session.commit()

    def remove_like(self):
        if current_user in self.liked_by:
            self.liked_by.remove(current_user)
            self.likes -= 1
            db.session.commit()


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String)
    date = db.Column(db.DateTime, default=datetime.now)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    blog = db.relationship('Blog', backref='comments')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User')

    def __init__(self, comment, blog_id, user_id):
        self.comment = comment
        self.blog_id = blog_id
        self.user_id = user_id


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
