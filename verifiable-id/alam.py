from flask import (Flask, redirect, render_template, request, session, url_for)
import asyncio
import json
from ctypes import cdll
from time import sleep
import platform

import logging

from utils import file_ext
from vcx.api.connection import Connection
from vcx.api.credential import Credential
from vcx.api.disclosed_proof import DisclosedProof
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State

app = Flask(__name__, static_url_path='/static')

name = ""
alice_connections = []
credentials = []
payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
payment_plugin.nullpay_init()

provisionConfig = {
    'agency_url': 'http://localhost:8080',
    'agency_did': 'VsKV7grR1BUE29mG2Fm2kX',
    'agency_verkey': 'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
    'wallet_name': 'alice_wallet',
    'wallet_key': '123',
    'payment_method': 'null',
    'enterprise_seed': '000000000000000000000000Trustee1'
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
    if request.method == "POST":
        res = request.form["name"]
        if res == "":
            return render_template("index.html", name=None, error="Elige un nombre")
        else:
            name = res
            global provisionConfig
            provisionConfig['wallet_name'] = "{}{}".format(name, "_wallet")
            config = await vcx_agent_provision(json.dumps(provisionConfig))
            global config
            config = json.loads(config)
            # Set some additional configuration options specific to alice
            config['institution_name'] = name
            config['institution_logo_url'] = 'http://robohash.org/456'
            config['genesis_path'] = 'docker.txn'
            await vcx_init_with_config(json.dumps(config))

            return render_template("index.html", name=name)

    else:
        if name == "":
            return render_template("index.html", name=None)
        else:
            return render_template("index.html", name=name)

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
