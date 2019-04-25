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

# logging.basicConfig(level=logging.DEBUG) uncomment to get logs

# 'agency_url': URL of the agency
# 'agency_did':  public DID of the agency
# 'agency_verkey': public verkey of the agency
# 'wallet_name': name for newly created encrypted wallet
# 'wallet_key': encryption key for encoding wallet
# 'payment_method': method that will be used for payments
provisionConfig = {
  'agency_url':'http://localhost:8080',
  'agency_did':'VsKV7grR1BUE29mG2Fm2kX',
  'agency_verkey':'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
  'wallet_name':'sre_wallet',
  'wallet_key':'123',
  'payment_method': 'null',
  'enterprise_seed':'000000000000000000000000Trustee1'
}


async def main():

    payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
    payment_plugin.nullpay_init()

    print("#1 Provision an agent and wallet, get back configuration details")
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    # Set some additional configuration options specific to faber
    config['institution_name'] = 'Faber'
    config['institution_logo_url'] = 'http://robohash.org/234'
    config['genesis_path'] = 'docker.txn'
    print(config)
    with open('faber.json', 'w') as outfile:
        json.dump(config, outfile)
    # Hope it works
    print("#2 Initialize libvcx with new configuration")
    session = await vcx_init_with_config(json.dumps(config))

    print("#3 Create a new schema on the ledger")
    version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    schema = await Schema.create('passport_1', 'degree schema', version, ['name', 'date_of_birth', 'passport_id', 'nationality', 'gender'], 0)
    schema_id = await schema.get_schema_id()
    with open('schema.json', 'w') as out_sch:
        json.dump(schema.serialize(), out_sch)

    print("#4 Create a new credential definition on the ledger")
    cred_def = await CredentialDef.create('credef_uuid', 'degree', schema_id, 0)
    cred_def_handle = cred_def.handle
    cred_def_id = await cred_def.get_cred_def_id()
    with open('cred_def.json', 'w') as out_cred_def:
        json.dump(cred_def.serialize(), out_cred_def)

    print("#5 Create a connection to alam and print out the invite details")
    connection_to_alam = await Connection.create('alam')
    await connection_to_alam.connect('{"use_public_did": true}')
    await connection_to_alam.update_state()
    details = await connection_to_alam.invite_details(False)
    print("**invite details**")
    print(json.dumps(details))
    print("******************")

    print("#6 Poll agency and wait for alam to accept the invitation (start alam.py now)")
    connection_state = await connection_to_alam.get_state()
    while connection_state != State.Accepted:
        sleep(2)
        await connection_to_alam.update_state()
        connection_state = await connection_to_alam.get_state()

    schema_attrs = {
        'name': 'Alam',
        'date_of_birth': format("%d-%d-%d" % (random.randint(1,30),random.randint(1,12),random.randint(1960,2019))),
        'passport_id': format("G%d%d%d" % (random.randint(1, 99), random.randint(20, 50), random.randint(10, 15))),
        'nationality': 'mexicana',
        'gender': 'M',
    }

    print("#12 Create an IssuerCredential object using the schema and credential definition")
    credential = await IssuerCredential.create('alam_pass', schema_attrs, cred_def_handle, 'passport', '0')
    with open('cred_iss.json', 'w') as out_cred_iss:
        json.dump(credential.serialize(), out_cred_iss)
    print("#13 Issue credential offer to alam")
    await credential.send_offer(connection_to_alam)
    await credential.update_state()

    print("#14 Poll agency and wait for alam to send a credential request")
    credential_state = await credential.get_state()
    while credential_state != State.RequestReceived:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    print("#17 Issue credential to alam")
    await credential.send_credential(connection_to_alam)

    print("#18 Wait for alam to accept credential")
    await credential.update_state()
    credential_state = await credential.get_state()
    while credential_state != State.Accepted:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    proof_attrs = [
        {'name': 'name', 'restrictions': [{'issuer_did': config['institution_did']}]},
        {'name': 'date_of_birth', 'restrictions': [{'issuer_did': config['institution_did']}]},
        {'name': 'gender', 'restrictions': [{'issuer_did': config['institution_did']}]}
    ]

    print("#19 Create a Proof object")
    proof = await Proof.create('proof_uuid', 'proof_from_alam', proof_attrs, {})

    print("#20 Request proof of degree from alam")
    await proof.request_proof(connection_to_alam)

    print("#21 Poll agency and wait for alam to provide proof")
    proof_state = await proof.get_state()
    while proof_state != State.Accepted:
        sleep(2)
        await proof.update_state()
        proof_state = await proof.get_state()

    print("#27 Process the proof provided by alam")
    await proof.get_proof(connection_to_alam)

    print("#28 Check if proof is valid")
    if proof.proof_state == ProofState.Verified:
        print("proof is verified!!")
    else:
        print("could not verify proof :(")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
