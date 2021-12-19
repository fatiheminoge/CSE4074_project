from user import User

def parse_msg():
    pass

def check_user(users : list, user_name : str):
    user = next((x for x in users if x.user_name == user_name), None)
    return user

def check_password(user : User, password : str):
    return user.password == password

def check_user_fromip(users : list, ipaddr):
    user = next((x for x in users if x.ipaddr == ipaddr), None)
    return user