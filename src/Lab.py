class Lab():

    def __init__(self, host, users=-1, ip="0.0.0.0"):
        self.hostname = host
        self.users = users
        self.ip = ip
    
    def __str__(self):
        return self.users