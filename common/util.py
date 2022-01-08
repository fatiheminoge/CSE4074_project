def check_user_by_client_address(users, client_address):
    user = next((x for x in users if x.client_address == client_address), None)
    return user


def check_user(users, username):
    user = next((x for x in users if x.username == username), None)
    return user


def check_password(user, password: str):
    return user.password == password

def remove_user_by_username(users, username):
    for user in users:
        if user.username == username:
            users.remove(user)
            break
