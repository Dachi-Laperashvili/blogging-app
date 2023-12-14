from flask_wtf import FlaskForm
from wtforms.fields import StringField, EmailField, PasswordField, SubmitField, DateField, TextAreaField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired, Email, length, equal_to


class SignUp(FlaskForm):
    name = StringField("First Name", validators=[DataRequired()])
    surname = StringField("Last Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), length(min=8, max=64)])
    repeat_password = PasswordField("Repeat Password", validators=[DataRequired(), equal_to("password", "passwords "
                                                                                                        "don't match")])
    birthday = DateField("Birthday", validators=[DataRequired()])

    register = SubmitField("Sign Up")


class Login(FlaskForm):
    email = EmailField("Enter Your Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Enter Your Password", validators=[DataRequired()])

    login = SubmitField("Login")


class AddBlog(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    img = FileField(validators=[FileRequired()])
    content = TextAreaField("Content", validators=[DataRequired()])

    submit = SubmitField("Submit", validators=[DataRequired()])


class EditBlog(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    img = FileField()
    content = TextAreaField("Content", validators=[DataRequired()])
    submit = SubmitField("Submit")


class EditUser(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password")
    img = FileField()
    birthday = DateField("Birthday", validators=[DataRequired()])

    update = SubmitField("Update")


class AddComment(FlaskForm):
    message = StringField("Write a public comment...", validators=[DataRequired()])

    comment = SubmitField("Comment")
