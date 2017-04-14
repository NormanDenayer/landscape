from landscape import models, login_manager


@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))
