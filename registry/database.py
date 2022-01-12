from common.error import *
from configparser import ConfigParser
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy import Column, String, Date, Integer, Boolean, ARRAY, TIMESTAMP, and_
from sqlalchemy.sql.schema import MetaData, Table
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.exc import IntegrityError
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))


def config(filename='registry/database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            'Section {0} not found in the {1} file'.format(section, filename))

    return db


def get_engine(user, password, host, port, database):
    url = f'postgresql://{user}:{password}@{host}:{port}/{database}'
    if not database_exists(url):
        create_database(url)
    engine = create_engine(url)
    return engine


params = config()
engine = get_engine(**params)
inspector = inspect(engine)
meta = MetaData(engine)
user_table = Table(
    'users', meta,
    Column('username', String, primary_key=True),
    Column('password', String),
    Column('address', ARRAY(String)),
    Column('last_active', TIMESTAMP),
    Column('chatport', Integer),
    Column('busy', Boolean, default=False),
    Column('thread_active', Boolean, default=False),
    Column('port', Integer),
    Column('online', Boolean, default=False)

)


class Database:
    def __init__(self):
        self.conn = engine.connect()
        if not inspector.has_table('users'):
            user_table.create()

    def search(self, username):
        try:
            select_statement = user_table.select().where(user_table.c.username == username)
            user = self.conn.execute(select_statement).fetchone()
            return dict(user)
        except Exception as e:
            print(e)

    def register(self, **args):
        try:
            select_statement = user_table.select().where(user_table.c.username == args['username'])
            user = self.conn.execute(select_statement).fetchone()
            if user is None:
                insert_statement = user_table.insert().values(**args)
                self.conn.execute(insert_statement)
            else:
                raise Exception
        except Exception:
            raise UserAlreadyExistsException

    def login(self, username, password, address, chatport):
        select_statement = user_table.select().where(user_table.c.username == username)
        user = self.conn.execute(select_statement).fetchone()
        if user is not None:
            user = dict(user)
            if user['password'] == password:
                update_statement = user_table.update().where(user_table.c.username == username).values(
                    address=address, last_active=datetime.now(), chatport=chatport, online=True)
                self.conn.execute(update_statement)

                select_statement = user_table.select().where(user_table.c.username == username)
                user = dict(self.conn.execute(select_statement).fetchone())
                user['last_active'] = datetime.now()
                return user
            else:
                raise WrongPasswordException
        else:
            raise UserNotExistsException

    def logout(self, username):
        select_statement = user_table.select().where(user_table.c.username == username)
        user = self.conn.execute(select_statement).fetchone()
        if user is not None:
            user = dict(user)
            if user['online'] == True:
                update_statement = user_table.update().where(
                    user_table.c.username == username).values(online=False)
                self.conn.execute(update_statement)
            else:
                raise UserIsNotLoggedInException
        else:
            raise UserNotExistsException

    def chat_address(self, username):
        select_statement = user_table.select().where(
            and_(user_table.c.username == username, user_table.c.online == True))
        user = self.conn.execute(select_statement).fetchone()
        if user is not None:
            user = dict(user)
            return (user['address'][0], int(user['chatport']))
        else:
            raise UserNotExistsException

    def update_field(self, username, **args):
        select_statement = user_table.select().where(user_table.c.username == username)
        user = self.conn.execute(select_statement).fetchone()
        if user is not None:
            update_statement = user_table.update().where(
                user_table.c.username == username).values(**args)
            self.conn.execute(update_statement)

    def search_all_peers(self):
        select_statement = user_table.select().where(user_table.c.online == True)
        users = self.conn.execute(select_statement).fetchall()
        ls = []
        for user in users:
            user = dict(user)
            ls.append(user['address'][0], int(user['chatport']))
        return ls
        
    def search_all_peers2(self,usernames):
        select_statement = user_table.select().where(user_table.c.online == True)
        users = self.conn.execute(select_statement).fetchall()
        ls = []
        for user in users:
            user = dict(user)
            username = user['username']
            if username in usernames and user['online'] == True:
                ls.append({'chat_address':(user['address'][0], int(user['chatport'])),'username':user['username'] })
        return ls        

    def set_offline(self):
        update_statement = user_table.update().where(user_table.c.online == True).values(
            online=False
        )
        self.conn.execute(update_statement)
