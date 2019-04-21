from quart import (Quart, redirect, render_template, request, session, url_for, jsonify)
import asyncio
import json
from ctypes import cdll
from time import sleep
import platform
from time import sleep

import logging

from utils import file_ext
from vcx.api.connection import Connection
from vcx.api.credential_def import CredentialDef
from vcx.api.issuer_credential import IssuerCredential
from vcx.api.proof import Proof
from vcx.api.schema import Schema
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State, ProofState

app = Quart(__name__, static_url_path='/static')
"""
    Global variables that are going to
    be used throughout all the proces of verification
"""
name = ""
sre_connections = {}
credentials = []
payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
payment_plugin.nullpay_init()

"""
    This is the privisional configuration for the SRE entity
    It is mainly for initialization purposes.
"""
provisionConfig = {
  'agency_url':'http://localhost:8080',
  'agency_did':'VsKV7grR1BUE29mG2Fm2kX',
  'agency_verkey':'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
  'wallet_name':'sre_wallet',
  'wallet_key':'123',
  'payment_method': 'null',
  'enterprise_seed':'000000000000000000000000Trustee1'
}

config = None


@app.route("/", methods=["GET"])
async def index():
    
    global name
    global provisionConfig
    global config
    if name == "":
        
        
        # VCX provides agent and wallet to user and returns system config
        print("#1 VCX provides agent and wallet to user and returns system config")
        config = await vcx_agent_provision(json.dumps(provisionConfig))
        config = json.loads(config)
        print(config)
        # Additional info
        config['institution_name'] = 'SRE'
        config['institution_logo_url'] = 'http://robohash.org/234'
        config['genesis_path'] = 'docker.txn'

        # Initialize libvcx with agent and wallet config
        print("#2 Initialize libvcx with agent and wallet config")
        await vcx_init_with_config(json.dumps(config))
        # Create a new schema on the ledger
        print("#3 Create a new schema on the ledger")
        version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
        schema = await Schema.create('pass_uuid', 'degree schema', version, ['name', 'date_of_birth', 'passport_id', 'nationality', 'gender'], 0)
        schema_id = await schema.get_schema_id()
        #4 Create a new credential definition on the ledger
        print("#4 Create a new credential definition on the ledger")
        cred_def = await CredentialDef.create('credef_uuid', 'degree', schema_id, 0)
        cred_def_handle = cred_def.handle
        cred_def_id = await cred_def.get_cred_def_id()
        name = "SRE"
        return await render_template("index_sre.html", name=name)
    else:
        return await render_template("index.html", name=name)

    
@app.route('/new_conn', methods=['POST'])
async def new_conn():


    global sre_connections
    form = await request.form
    curp = form["curp"]
    # Create new connection and return the invite details
    new_conn = await Connection.create(curp)
    await new_conn.connect('{"use_public_did": true}')
    await new_conn.update_state()
    sre_connections[curp] = new_conn
    details = await new_conn.invite_details(False)
    print("**invite details**")
    print(json.dumps(details))
    print("******************")
    return await jsonify({'details' : json.dumps(details)})



@app.route("/connections", methods=["POST", "GET"])
async def connections():
    global name
    if request.method == "POST":
        if request.form["details"] == "":
            error = "Invalido"
            return await render_template('connections.html', error=error, name=name, json_connections=[])
    else:
        json_connections = load_json_connections
        return await render_template('connections.html', name=name, json_connections=[])


@app.route("/offers", methods=["POST", "GET"])
async def offers():

    return await render_template("connections.html")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)
