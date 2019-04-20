from quart import (Quart, redirect, render_template, request, session, url_for)
import asyncio
import json
import random
from ctypes import cdll
from time import sleep
import platform

import logging

from demo_utils import file_ext
from vcx.api.connection import Connection
from vcx.api.credential_def import CredentialDef
from vcx.api.issuer_credential import IssuerCredential
from vcx.api.proof import Proof
from vcx.api.schema import Schema
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State, ProofState

app = Quart(__name__, static_url_path='/static')

name = "SRE"
sre_connections = []
credentials = []
payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
payment_plugin.nullpay_init()

provisionConfig = {
  'agency_url':'http://localhost:8080',
  'agency_did':'VsKV7grR1BUE29mG2Fm2kX',
  'agency_verkey':'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
  'wallet_name':'faber_wallet',
  'wallet_key':'123',
  'payment_method': 'null',
  'enterprise_seed':'000000000000000000000000Trustee1'
}
config = None

def load_json_connections():
    global alice_connections
    res = []
    for conn in alice_connections:
        j_conn = conn.serialize()
        res.append(j_conn)

    return res

@app.route("/", methods=["POST", "GET"])
def index():
    global name
    global provisionConfig
    global config
    provisionConfig['wallet_name'] = "{}{}".format(name, "_wallet")
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    # Set some additional configuration options specific to faber
    config['institution_name'] = 'SRE'
    config['institution_logo_url'] = 'http://robohash.org/234'
    config['genesis_path'] = 'docker.txn'

    print("#2 Initialize libvcx with new configuration")
    await vcx_init_with_config(json.dumps(config))

    # print("#3 Create a new schema on the ledger")
    # version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    # schema = await Schema.create('schema_uuid', 'degree schema', version, ['name', 'date_of_birth', 'passport_id', 'nationality', 'gender'], 0)
    # schema_id = await schema.get_schema_id()
    #
    # print("#4 Create a new credential definition on the ledger")
    # cred_def = await CredentialDef.create('credef_uuid', 'degree', schema_id, 0)
    # cred_def_handle = cred_def.handle
    # cred_def_id = await cred_def.get_cred_def_id()

    print("#5 Create a connection to alice and print out the invite details")
    connection_to_alice = await Connection.create('alice')
    await connection_to_alice.connect('{"use_public_did": true}')
    await connection_to_alice.update_state()
    details = await connection_to_alice.invite_details(False)
    print("**invite details**")
    print(json.dumps(details))
    print("******************")
    return render_template("index.html", name=name, details=json.dumps(details), did=config['institution_did'])

@app.route("/connections", methods=["POST", "GET"])
def connections():
    global name
    if request.method == "POST":
        if request.form["details"] == "":
            error = "Invalido"
            return render_template('connections.html', error=error, name=name, json_connections=[])
        else:
            invite = request.form["details"]
            jdetails = json.loads(details)
            new_connection = await Connection.create_with_details('faber', json.dumps(jdetails))
            await new_connection.connect('{"use_public_did": true}')
            await new_connection.update_state()
            global alice_connections
            alice_connections.append(new_connection)
            json_connections= load_json_connections()
            return render_template("connections.html", json_connections=json_connections, name=name)
    else:
        json_connections = load_json_connections
        return render_template('connections.html', name=name, json_connections=[])

@app.route("/offers", methods=["POST", "GET"])
def offers():
    pass





    return render_template("connections.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)
