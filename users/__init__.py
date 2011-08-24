# -*- coding: utf-8 -*-

from main import login_page, login_manager, admin_required

from base import app

# secret key, necessary for sessions, and sessions are
# in turn necessary for users to login
app.secret_key = '9af"]ßÄ!_°$2ha€42~µ…010'

login_manager.setup_app(app)

app.register_blueprint(login_page, url_prefix="/users")

