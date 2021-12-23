from user import User


def parse_msg():
    pass


def check_user_by_client_address(users, client_address):
    user = next((x for x in users if x.client_address == client_address), None)
    return user


def check_user(users: list, username: str):
    user = next((x for x in users if x.username == username), None)
    return user


def check_password(user: User, password: str):
    return user.password == password
