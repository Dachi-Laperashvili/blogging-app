from flask import render_template, redirect, flash, request, jsonify
from forms import SignUp, Login, AddBlog, EditBlog, EditUser, AddComment
from slugify import slugify
from extensions import app, db
from models import User, Blog, Comment, Notification
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import desc
from os import path
import uuid


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    if form.validate_on_submit():
        user_found = False

        user = User.query.filter(User.email == form.email.data).first()
        if user:
            user_found = True
            if user.check_password(form.password.data):
                login_user(user)
                return redirect("/")
            else:
                flash("Incorrect password", category="danger")
        if not user_found:
            flash("User with that email doesn't exist", category="danger")
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUp()

    if form.validate_on_submit():
        new_user = User(first_name=form.name.data,
                        last_name=form.surname.data,
                        email=form.email.data,
                        password=form.password.data,
                        birthday=form.birthday.data)

        existing_user = User.query.filter(User.email == form.email.data).first()
        if existing_user:
            flash("User with that email already exists")
        else:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash("Congratulations, your account has been successfully created.", category="success")
            return redirect("/")
    print(form.errors)

    return render_template("signup.html", form=form)


@app.route('/')
def home():
    blogs = Blog.query.order_by(Blog.likes.desc()).paginate(per_page=6)
    return render_template("index.html", blogs=blogs)


@app.route("/dashboard/<int:page_id>")
def page(page_id):
    blogs = Blog.query.order_by(Blog.date.desc()).paginate(per_page=6, page=page_id)
    return render_template("dashboard.html", blogs=blogs, page_id=page_id)


@app.route('/add-post', methods=['GET', 'POST'])
@login_required
def create():
    form = AddBlog()
    if form.validate_on_submit():
        random_name = str(uuid.uuid4())

        form.img.data.save((path.join(app.root_path, 'static/images', random_name)))
        new_blog = Blog(title=form.title.data, slug=slugify(form.slug.data),
                        content=form.content.data, user_id=current_user.id, image=random_name)

        existing_blog = Blog.query.filter(Blog.slug == new_blog.slug).first()
        if existing_blog:
            flash("Blog with that slug already exists!")
        else:
            db.session.add(new_blog)
            db.session.commit()
            return redirect("/")
    return render_template("add_blog.html", form=form)


@app.route('/home/<blog_slug>', methods=['GET', 'POST'])
def view_blog(blog_slug):
    blog = Blog.query.filter(Blog.slug == blog_slug).first()
    form = AddComment()
    comments = Comment.query.filter(Comment.blog_id == blog.id, Comment.parent_id.is_(None)).all()
    if blog:
        post = blog

        if form.validate_on_submit():
            new_comment = Comment(comment=form.message.data, blog_id=blog.id, user_id=current_user.id)
            new_notification = Notification(content=current_user.username + " commented on your blog:'" + blog.title + ".'",
                                            to_user_id=blog.user_id, from_user_id=current_user.id,blog_id=blog.id)
            db.session.add(new_comment)
            db.session.add(new_notification)
            db.session.commit()
            return redirect(f"/home/{blog_slug}")
    else:
        flash("Blog with that slug doesn't exist", category="danger")
        return redirect("/")
    return render_template("blog.html", post=post, form=form, comments=comments)


@app.route('/delete/<blog_slug>')
@login_required
def delete_blog(blog_slug):
    blog = Blog.query.filter(Blog.slug == blog_slug).first()
    if blog and blog.user_id == current_user.id or current_user.role == "admin":
        db.session.delete(blog)
        db.session.commit()
        flash("Blog Has Been Deleted!", category="warning")
    else:
        flash("You should be creator of the blog to delete it!", category="danger")
    return redirect("/")


@app.route('/edit/<blog_slug>', methods=['GET', 'POST'])
@login_required
def edit_blog(blog_slug):
    blog = Blog.query.filter(Blog.slug == blog_slug).first()
    form = EditBlog()
    if not blog:
        flash("Blog with that slug doesn't exist!", category="danger")
        return redirect("/")

    if blog.user_id == current_user.id:
        if form.validate_on_submit():
            blog.title = form.title.data
            blog.slug = form.slug.data
            blog.content = form.content.data

            if form.img.data:
                random_name = str(uuid.uuid4())
                blog.image = random_name
                form.img.data.save((path.join(app.root_path, 'static/images', random_name)))
            db.session.add(blog)
            db.session.commit()
            return redirect('/')
        form.title.data = blog.title
        form.slug.data = blog.slug
        form.content.data = blog.content
        return render_template("edit_blog.html", form=form)
    else:
        flash("You should be creator of the blog to edit it!", category="danger")
        return redirect("/")


@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    form = EditUser()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.birthday = form.birthday.data

        if form.password.data:
            current_user.password = generate_password_hash(form.password.data)
        if form.img.data:
            random_name = str(uuid.uuid4())
            current_user.picture = random_name
            form.img.data.save((path.join(app.root_path, 'static/pfp', random_name)))
        db.session.add(current_user)
        db.session.commit()
        return redirect("/profile")

    form.username.data = current_user.username
    form.email.data = current_user.email
    form.birthday.data = current_user.birthday

    return render_template("account.html", form=form)


@app.route('/my_blogs')
@login_required
def my_blogs():
    user_blogs = Blog.query.filter_by(user_id=current_user.id).order_by(Blog.date.desc()).all()
    return render_template("my_blogs.html", user_blogs=user_blogs)


@app.route('/like/<slug>', methods=['POST'])
@login_required
def like_unlike(slug):
    blog = Blog.query.filter_by(slug=slug).first()
    if blog:
        if request.method == 'POST':
            is_liked = request.form.get('is_liked')
            print(is_liked)
            if is_liked != "true" and current_user not in blog.liked_by:
                blog.add_like(current_user)
                if blog.user_id != current_user.id:
                    existing_notification = Notification.query.filter_by(
                        content=current_user.username + " liked your post:'" + blog.title + ".'",
                        to_user_id=blog.user_id, from_user_id=current_user.id, blog_id=blog.id
                    ).first()

                    if not existing_notification:
                        new_notification = Notification(content=current_user.username + " liked your post:'" +
                                                        blog.title + ".'",
                                                        to_user_id=blog.user_id, from_user_id=current_user.id,
                                                        blog_id=blog.id)
                        db.session.add(new_notification)
                        db.session.commit()
            else:
                blog.remove_like(current_user)
            return jsonify({"likes": blog.likes, 'liked': current_user in blog.liked_by})
    return jsonify({'error': 'Invalid Request'})


@app.route('/home/<blog_slug>/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(blog_slug, comment_id):
    comment = Comment.query.get(comment_id)
    if comment and comment.user_id == current_user.id or current_user.role == "admin":
        db.session.delete(comment)
        db.session.commit()
        if comment.replies:
            for reply_comment in comment.replies:
                db.session.delete(reply_comment)
                db.session.commit()
    return redirect(f"/home/{blog_slug}")


@app.route('/search/<int:page_id>')
def search(page_id=1):
    name = request.args['search']
    blogs = Blog.query.filter(Blog.title.ilike(f"%{name}%")).paginate(per_page=6, page=page_id)
    return render_template("results.html", blogs=blogs, page_id=page_id)


@app.route('/home/<slug>/reply', methods=['POST'])
@login_required
def reply(slug):
    blog = Blog.query.filter_by(slug=slug).first()
    parent_id = request.form.get('parent_id')
    comment = Comment.query.get(parent_id)
    parent_user = request.form.get('parent_user')
    reply_id = request.form.get('reply_id')
    reply_user = request.form.get('reply_user')
    message = request.form.get('message')

    if parent_id and message:
        new_comment = Comment(comment=message, blog_id=blog.id, user_id=current_user.id, parent_id=parent_id)
        if parent_user != current_user:
            new_notification = Notification(content=current_user.username + " replied to your comment:'" +
                                            comment.comment + ".'",
                                            to_user_id=parent_user, from_user_id=current_user.id, comment_id=parent_id)
            db.session.add(new_notification)
        db.session.add(new_comment)
        db.session.commit()

    if reply_id and reply_user != current_user.id:
        new_notification = Notification(content=current_user.username + " replied to your comment.",
                                        to_user_id=reply_user, from_user_id=current_user.id, comment_id=reply_id)
        db.session.add(new_notification)
        db.session.commit()
    return redirect(f"/home/{slug}")


@app.route('/get-notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = (Notification.query.filter_by(to_user_id=current_user.id)
                     .order_by(desc(Notification.timestamp)).all())
    unread_count = Notification.query.filter_by(to_user_id=current_user.id, read_status=False).count()

    formatted_notification = [{'content': notification.content,
                               'id': notification.id,
                               'timestamp': notification.timestamp.strftime("%d %b %Y %H:%M"),
                               'user_picture': notification.from_user.picture,
                               'read_status': notification.read_status}
                              for notification in notifications]

    return jsonify({'notifications': formatted_notification, 'unread_count': unread_count})


@app.route('/mark-read', methods=['POST'])
def mark_read():
    notification_id = request.json.get('notification_id')
    notification = Notification.query.get(notification_id)
    notifications = (Notification.query.filter_by(to_user_id=current_user.id)
                     .order_by(desc(Notification.timestamp)).all())
    unread_count = Notification.query.filter_by(to_user_id=current_user.id, read_status=False).count()

    formatted_notification = [{'content': notification.content,
                               'id': notification.id,
                               'timestamp': notification.timestamp.strftime("%d %b %Y %H:%M"),
                               'user_picture': notification.from_user.picture,
                               'read_status': notification.read_status}
                              for notification in notifications]
    if notification and notification.to_user_id == current_user.id:
        notification.read_status = True
        db.session.commit()
        return jsonify({'message': 'Notification marked as read!',
                        'notifications': formatted_notification, 'unread_count': unread_count})
    return jsonify({'message': 'Notification not found or unauthorized',
                    'notifications': formatted_notification, 'unread_count': unread_count})
