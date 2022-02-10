# -*- coding: utf-8 -*-

import sys
from datetime import datetime
import tzlocal

from flask import Flask, render_template, make_response, redirect, url_for
from flask_admin import Admin
from flask_apscheduler import APScheduler
from flask_frozen import Freezer
from flask_migrate import Migrate
from flaskext.markdown import Markdown
from sqlalchemy.sql.expression import func


import flask_se_theses
from flask_se_config import SECRET_KEY_THESIS, SECRET_KEY, SQLITE_DATABASE_NAME
from se_models import db, search, init_db, Staff, Users, Thesis, Curriculum, SummerSchool, Posts, DiplomaThemes, recalculate_post_rank
from flask_se_auth import login_manager, register_basic, login_index, password_recovery, user_profile, upload_avatar, \
    logout, vk_callback, google_login, google_callback
from flask_se_news import list_news, get_post, submit_post, post_vote, delete_post
from flask_se_admin import SeAdminModelViewThesis, SeAdminIndexView, SeAdminModelViewUsers, \
    SeAdminModelViewSummerSchool, SeAdminModelViewStaff, SeAdminModelViewNews, SeAdminModelViewDiplomaThemes, \
    SeAdminModelViewReviewDiplomaThemes
from flask_se_scholarships import get_scholarships_1, get_scholarships_2, get_scholarships_3, get_scholarships_4, \
    get_scholarships_5, get_scholarships_6, get_scholarships_7, get_scholarships_8, get_scholarships_9, \
    get_scholarships_10, get_scholarships_11, get_scholarships_12, get_scholarships_13
from flask_se_diplomas import diplomas_index, get_theme, add_user_theme, user_diplomas_index, delete_theme, edit_user_theme


app = Flask(__name__, static_url_path='', static_folder='static', template_folder='templates')

# Flask configs
app.config['APPLICATION_ROOT'] = '/'

# Freezer config
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_DESTINATION'] = '../docs'
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True

# SQLAlchimy config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + SQLITE_DATABASE_NAME
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = SECRET_KEY

# Secret for API
app.config['SECRET_KEY_THESIS'] = SECRET_KEY_THESIS

# Basci auth config
app.config['BASIC_AUTH_USERNAME'] = 'se_staff'
app.config['BASIC_AUTH_PASSWORD'] = app.config['SECRET_KEY_THESIS']


# App add_url_rule
# Login
app.add_url_rule('/login.html', methods=['GET', 'POST'], view_func=login_index)
app.add_url_rule('/register_basic.html', methods=['GET', 'POST'], view_func=register_basic)
app.add_url_rule('/password_recovery.html', methods=['GET', 'POST'], view_func=password_recovery)
app.add_url_rule('/profile.html', methods=['GET', 'POST'], view_func=user_profile)
app.add_url_rule('/upload_avatar', methods=['GET', 'POST'], view_func=upload_avatar)
app.add_url_rule('/logout', methods=['GET'], view_func=logout)
app.add_url_rule('/vk_callback', methods=['GET'], view_func=vk_callback)
app.add_url_rule('/google_login', methods=['GET'], view_func=google_login)
app.add_url_rule('/google_callback', methods=['GET'], view_func=google_callback)


# Theses
app.add_url_rule('/theses.html', view_func=flask_se_theses.theses_search)
app.add_url_rule('/fetch_theses', view_func=flask_se_theses.fetch_theses)
app.add_url_rule('/post_theses', methods=['GET', 'POST'], view_func=flask_se_theses.post_theses)
app.add_url_rule('/theses_tmp.html', view_func=flask_se_theses.theses_tmp)
app.add_url_rule('/theses_delete_tmp', view_func=flask_se_theses.theses_delete_tmp)
app.add_url_rule('/theses_add_tmp', view_func=flask_se_theses.theses_add_tmp)


# News
app.add_url_rule('/news/', view_func=list_news)
app.add_url_rule('/news/index.html', view_func=list_news)
app.add_url_rule('/news/item.html', view_func=get_post)
app.add_url_rule('/news/submit.html', methods=['GET', 'POST'], view_func=submit_post)
app.add_url_rule('/news/post_vote', methods=['GET', 'POST'], view_func=post_vote)
app.add_url_rule('/news/delete', view_func=delete_post)


# Scholarships
app.add_url_rule('/scholarships/1.html', view_func=get_scholarships_1)
app.add_url_rule('/scholarships/2.html', view_func=get_scholarships_2)
app.add_url_rule('/scholarships/3.html', view_func=get_scholarships_3)
app.add_url_rule('/scholarships/4.html', view_func=get_scholarships_4)
app.add_url_rule('/scholarships/5.html', view_func=get_scholarships_5)
app.add_url_rule('/scholarships/6.html', view_func=get_scholarships_6)
app.add_url_rule('/scholarships/7.html', view_func=get_scholarships_7)
app.add_url_rule('/scholarships/8.html', view_func=get_scholarships_8)
app.add_url_rule('/scholarships/9.html', view_func=get_scholarships_9)
app.add_url_rule('/scholarships/10.html', view_func=get_scholarships_10)
app.add_url_rule('/scholarships/11.html', view_func=get_scholarships_11)
app.add_url_rule('/scholarships/12.html', view_func=get_scholarships_12)
app.add_url_rule('/scholarships/13.html', view_func=get_scholarships_13)


# Diplomas
app.add_url_rule('/diplomas/index.html', view_func=diplomas_index)
app.add_url_rule('/diplomas/theme.html', view_func=get_theme)
app.add_url_rule('/diplomas/add_theme.html', methods=['GET', 'POST'], view_func=add_user_theme)
app.add_url_rule('/diplomas/user_themes.html', view_func=user_diplomas_index)
app.add_url_rule('/diplomas/delete_theme.html', view_func=delete_theme)
app.add_url_rule('/diplomas/edit_theme.html', methods=['GET', 'POST'], view_func=edit_user_theme)


# Init Database
db.app = app
db.init_app(app)

app.config['MSEARCH_BACKEND'] = 'whoosh'
app.config['MSEARCH_ENABLE'] = True
search.init_app(app)
search.create_index(Thesis, update=True)
search.create_index(Users, update=True)

# Init Migrate
migrate = Migrate(app, db, render_as_batch=True)

app.logger.error('SECRET_KEY_THESIS: %s', str(app.config['SECRET_KEY_THESIS']))

# Init Freezer
freezer = Freezer(app)

# Init Sitemap
zero_days_ago = (datetime.now()).date().isoformat()

# Init LoginManager
login_manager.init_app(app)

# Init markdown
Markdown(app)


# Init APScheduler
app.config['SCHEDULER_TIMEZONE'] = 'UTC'
scheduler = APScheduler()
scheduler.add_job(id='RecalculatePostRank', func=recalculate_post_rank, trigger="interval", seconds=3600)
scheduler.start()

# Init Flask-admin
admin = Admin(app, index_view=SeAdminIndexView(), template_mode='bootstrap4')
# Add views to the Flask-admin
admin.add_view(SeAdminModelViewUsers(Users, db.session))
admin.add_view(SeAdminModelViewStaff(Staff, db.session))
admin.add_view(SeAdminModelViewThesis(Thesis, db.session))
admin.add_view(SeAdminModelViewSummerSchool(SummerSchool, db.session))
admin.add_view(SeAdminModelViewNews(Posts, db.session))
admin.add_view(SeAdminModelViewDiplomaThemes(DiplomaThemes, db.session, endpoint="diplomathemes"))
admin.add_view(SeAdminModelViewReviewDiplomaThemes(DiplomaThemes, db.session, endpoint="reviewdiplomathemes", name="Review DiplomaThemes"))




# Flask routes goes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/index.html')
def index_html():
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.route('/404.html')
def status_404():
    return render_template('404.html')


@app.route('/contacts.html')
def contacts():
    return render_template('contacts.html')


@app.route('/students/index.html')
def students():
    return render_template('students.html')


@app.route('/students/scholarships.html')
def scholarships():
    return render_template('students_scholarships.html')


@app.route('/bachelor/application.html')
def bachelor_application():
    return render_template('bachelor_application.html')


@app.route('/bachelor/programming-technology.html')
def bachelor_programming_technology():

    curricula1 = Curriculum.query.filter(Curriculum.course_id==1).filter(Curriculum.study_year==1).order_by(Curriculum.type).all()
    curricula2 = Curriculum.query.filter(Curriculum.course_id==1).filter(Curriculum.study_year==2).order_by(Curriculum.type).all()
    curricula3 = Curriculum.query.filter(Curriculum.course_id==1).filter(Curriculum.study_year == 3).order_by(Curriculum.type).all()
    curricula4 = Curriculum.query.filter(Curriculum.course_id==1).filter(Curriculum.study_year == 4).order_by(Curriculum.type).all()

    return render_template('bachelor_programming-technology.html', curricula1=curricula1, curricula2=curricula2,
                           curricula3=curricula3, curricula4=curricula4)


@app.route('/bachelor/software-engineering.html')
def bachelor_software_engineering():

    curricula1 = Curriculum.query.filter(Curriculum.course_id==2).filter(Curriculum.study_year==1).order_by(Curriculum.type).all()
    curricula2 = Curriculum.query.filter(Curriculum.course_id==2).filter(Curriculum.study_year==2).order_by(Curriculum.type).all()
    curricula3 = Curriculum.query.filter(Curriculum.course_id==2).filter(Curriculum.study_year == 3).order_by(Curriculum.type).all()
    curricula4 = Curriculum.query.filter(Curriculum.course_id==2).filter(Curriculum.study_year == 4).order_by(Curriculum.type).all()

    return render_template('bachelor_software-engineering.html', curricula1=curricula1, curricula2=curricula2,
                           curricula3=curricula3, curricula4=curricula4)


@app.route('/master/information-systems-administration.html')
def master_information_systems_administration():
    return render_template('master_information-systems-administration.html')


@app.route('/master/software-engineering.html')
def master_software_engineering():
    return render_template('master_software-engineering.html')


@app.route('/department/staff.html')
def department_staff():
    records = Staff.query.filter_by(still_working=True).all()
    staff = []

    # TODO: no need loop
    for s in records:
        position = s.position
        if s.science_degree:
            position = position + ", " + s.science_degree

        staff.append({'name': s.user, 'position': position, 'contacts': s.official_email,
                      'avatar': s.user.avatar_uri, 'id': s.id})

    return render_template('department_staff.html', staff = staff)


@app.route('/bachelor/admission.html')
def bachelor_admission():

    students = []

    records = Thesis.query.filter_by(recomended=True)
    if records.count():
        theses = records.order_by(func.random()).limit(4).all()
    else:
        theses = []
    staff = Staff.query.filter_by(still_working=True).limit(6).all()
    return render_template('bachelor_admission.html', students = students, theses=theses, staff=staff)


@app.route('/frequently-asked-questions.html')
def frequently_asked_questions():
    return render_template('frequently_asked_questions.html')


@app.route('/nooffer.html')
def nooffer():
    return render_template('nooffer.html')


@app.route('/summer_school_2021.html')
def summer_school():

    projects = SummerSchool.query.filter_by(year=2021).all()
    return render_template('summer_school.html', projects=projects)


@app.route('/sitemap.xml', methods=['GET'])
@app.route('/Sitemap.xml', methods=['GET'])
def sitemap():

    """Generate sitemap.xml. Makes a list of urls and date modified."""
    pages = []
    skip_pages = ['/nooffer.html', '/fetch_theses', '/Sitemap.xml', '/sitemap.xml', '/404.html', '/post_theses',
                  '/theses_tmp.html', '/theses_delete_tmp', '/theses_add_tmp', '/google_callback', '/vk_callback']

    # static pages
    for rule in app.url_map.iter_rules():

        if rule.rule in skip_pages:
            continue

        # Skip admin URL
        if 'admin/' in rule.rule:
            continue

        if "GET" in rule.methods and len(rule.arguments) == 0:
            pages.append(
                ["https://se.math.spbu.ru" + str(rule.rule), zero_days_ago]
            )

    sitemap_xml = render_template('sitemap_template.xml', pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "build":
            freezer.freeze()
        elif sys.argv[1] == "init":
            init_db()
    else:
        app.run(port=5000)
