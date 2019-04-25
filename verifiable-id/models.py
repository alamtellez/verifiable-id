# coding utf-8

class Holder:
    
    def __init__(self, provConfig, config):
        self.provConfig = provConfig
        self.config = config
        self.connections = []
        self.offers = []
        self.requests = []
        self.credentials []

class Issuer(Holder):

    def __init__(self, prov, conf):
        super().__init__(prov, conf)
        self.schema = None
        self.cred_def = None
        self.cred_iss = None
        self.proofs = []
