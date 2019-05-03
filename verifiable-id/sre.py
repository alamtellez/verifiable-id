from quart import (Quart, redirect, render_template, request, session, url_for, jsonify)
import asyncio
import json
from ctypes import cdll
from time import sleep
import platform
from time import sleep
from models import Issuer

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

def init_sre():

    print("#1 Cargar configuracion inicial")
    with open('sre.json') as conf:
        config = json.load(conf)
    with open('schema.json') as conf:
        schema_config = json.load(conf)
    with open('cred_def.json') as conf:
        cred_def_config = json.load(conf)
    with open('cred_iss.json') as conf:
        cred_iss_config = json.load(conf)
    model = Issuer(config, None, schema_config, cred_def_config, cred_iss_config)
    return model

    
sre_model = init_sre()

@app.route("/", methods=["GET"])
async def index():
    
    global sre_model
    if sre_model.name == None:
        
        
        # VCX provides agent and wallet to user and returns system config
        # print("#1 VCX provides agent and wallet to user and returns system config")
        # config = await vcx_agent_provision(json.dumps(provisionConfig))
        # config = json.loads(config)
        # print(config)
        # # Additional info
        # config['institution_name'] = 'SRE'
        # config['institution_logo_url'] = 'http://robohash.org/234'
        # config['genesis_path'] = 'docker.txn'

        # print("#1 Cargar configuracion inicial")
        # with open('sre.json') as conf:
        #     config = json.load(conf)
        # config = json.loads(config)
        print("#2 Inicializar VCX Libreria con configuracion de cartera")
        session = await vcx_init_with_config(json.dumps(sre_model.config))
        # Create a new schema on the ledger
        print("#3 Load already created schema on the ledger")
        # with open('schema.json') as conf:
        #     schema_config = json.load(conf)
        # # schema_config = json.loads(config)
        schema = await Schema.deserialize(sre_model.schema)
        schema_id = await schema.get_schema_id()
        #4 Create a new credential definition on the ledger
        # print("#4 Create a new credential definition on the ledger")
        # cred_def = await CredentialDef.create('credef_uuid', 'degree', schema_id, 0)
        # cred_def_handle = cred_def.handle
        # cred_def_id = await cred_def.get_cred_def_id()
        # print("#4 Cargar definicion de credencial ya hecha en el ledger")
        # with open('cred_def.json') as conf:
        #     cred_def_config = json.load(conf)
        # cred_def_config = json.loads(config)
        cred_def = await CredentialDef.deserialize(sre_model.cred_def)
        cred_def_id = await cred_def.get_cred_def_id()

        sre_model.name = "SRE"
        return await render_template("index_sre.html", name=sre_model.name)
    else:
        return await render_template("index_sre.html", name=sre_model.name)

    
@app.route('/new_conn', methods=['POST'])
async def new_conn():
    global sre_model
    if request.method == "POST":
        
        form = await request.form
        curp = form["curp"]
        # Create new connection and return the invite details
        new_conn = await Connection.create(curp)
        print("Creo")
        await new_conn.connect('{"use_public_did": true}')
        await new_conn.update_state()
        sre_model.connection = new_conn
        details = await new_conn.invite_details(False)
        print("**invite details**")
        print(json.dumps(details))
        print("******************")
        return await redirect(url_for('connections'))


@app.route('/offer_credential', methods=['POST'])
async def offer_credential():
    global sre_model
    if request.method == "POST":
        
        form = await request.form
        curp = form["curp"]
        print("#4 Load already created Credential Issuer")
        credential = await IssuerCredential.deserialize(sre_model.cred_iss)
        await credential.send_offer(sre_model.connection[curp])
        await credential.update_state()
        return await redirect(url_for('connections'))



@app.route("/connections", methods=["POST", "GET"])
async def connections():
    global sre_model
    if request.method == "POST":
        form = await request.form
        curp = form["curp"]
        credential = await IssuerCredential.deserialize(sre_model.cred_iss)
        await credential.send_offer(sre_model.connection[curp])
        await credential.update_state()
        return await redirect(url_for('offers'))
    else:
        pendiente = None
        aceptada = None
        for key, value in sre_model.connection:
            curp = key
            connection_state = await sre_model.value.get_state()
            if connection_state != State.Accepted:
                pendiente = True
            else:
                aceptada = True
        return await render_template('sre_connections.html', pendiente=pendiente, aceptada=aceptada, curp=curp)


@app.route("/offers", methods=["POST", "GET"])
async def offers():
    global sre_model
    if request.method == "POST":
        form = await request.form
        curp = form["curp"]
        credential = await IssuerCredential.deserialize(sre_model.cred_iss)
        await credential.send_credential(sre_model.connection[curp])
        await credential.update_state()
        return await redirect(url_for('offers'))
    else:
        pendiente = None
        aceptada = None
        curp = list(sre_model.connection.keys())[0]
        credential = await IssuerCredential.deserialize(sre_model.cred_iss)
        credential_state = await credential.get_state()
        if credential_state != State.RequestReceived:
            pendiente = True
        else:
            aceptada = True
        return await render_template('sre_offers.html', pendiente=pendiente, aceptada=aceptada, curp=sre_model)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)
