# coding utf-8

class Holder:
    
    def __init__(self, config, name):
        self.config = config
        self.name = name
        self.connection = {}
        self.offers = []
        self.requests = []
        self.credentials = []

class Issuer(Holder):

    def __init__(self, conf, name, schema_conf, cd_conf, cred_iss):
        super().__init__(conf, name)
        self.schema = schema_conf
        self.cred_def = cd_conf
        self.cred_iss = cred_iss
        self.proofs = []
