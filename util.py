def parse_msg():
    pass

def find_user(users : list, user_name : str):
    user = next((x for x in users if x.user_name == user_name), None)
    return user
