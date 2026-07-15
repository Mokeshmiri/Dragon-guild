from flask_login import UserMixin


# represents a logged-in user for flask-login
class User(UserMixin):
    # stores the user information needed by the session
    def __init__(self, id, email, role):
        self.id = str(id)
        self.email = email
        self.role = role
