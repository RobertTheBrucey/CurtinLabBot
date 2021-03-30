class Lab():

    def __init__(self, host, users=-1, ip="0.0.0.0"):
        self.host = host
        self.hostname = host
        self.users = users
        self.ip = ip
        self.load1min = -1.0
        self.load5min = -1.0
        self.load15min = -1.0
    
    def __str__(self):
        return self.users