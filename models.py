class User:
    def __init__(self, login: str, hashpass: str):
        self.login = login
        self.hashpass = hashpass
        self.authorized = False