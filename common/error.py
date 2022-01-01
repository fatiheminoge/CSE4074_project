class WrongPasswordException(Exception):
    """Raised in case of wrong password"""
    
class UserNotExistsException(Exception):
    """Raised if the user is not exists"""
    
class UserAlreadyExistsException(Exception):
    """Raised if the user with same username already exists"""
    
class UserIsNotLoggedInException(Exception):
    """Raised if the user is not logged in"""