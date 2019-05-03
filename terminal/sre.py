import asyncio
import json
import random
from ctypes import cdll
from time import sleep
import platform

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
    doc_version = 1.3
    """
        This section is to initialize the credentials and wallet
    """
    payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
    payment_plugin.nullpay_init()
    # 1 Provision an agent and wallet, get back configuration details
    print("#1 Proporcionar cartera de llaves")
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    # print("#2 Extra configuration for SRE")
    # 2 Extra configuration for SRE
    config['institution_name'] = 'SRE'
    config['institution_logo_url'] = 'http://robohash.org/234'
    config['genesis_path'] = 'docker.txn'
    # print(config)
    with open('sre.json', 'w') as outfile:
        json.dump(config, outfile)


    """
        Open serialized config to restore session
    """
    # print("#1 Cargar configuracion inicial")
    # with open('sre.json') as conf:
    #     config = json.load(conf)
    # config = json.loads(config)
    print("#2 Inicializar VCX Libreria con configuracion de cartera")
    session = await vcx_init_with_config(json.dumps(config))
    
    
    """
        Here we create a new schema for the structure of credentials
    """
    print("#3 Crear un nuevo Schema en el ledger")
    version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    schema = await Schema.create('passport_' + str(doc_version), 'schema_pass_'+ str(doc_version), version, ['name', 'date_of_birth', 'passport_id', 'nationality', 'gender'], 0)
    schema_id = await schema.get_schema_id()
    with open('schema.json', 'w') as out_sch:
        json.dump(await schema.serialize(), out_sch)
    
    
    """
        Load already created schema
    """
    # print("#3 Load already created schema on the ledger")
    # with open('schema.json') as conf:
    #     schema_config = json.load(conf)
    # # schema_config = json.loads(config)
    # schema = await Schema.deserialize(schema_config)
    # schema_id = await schema.get_schema_id()

    """
        Here we create a new credential_definition
    """
    print("#4 Crear un nuevo Credential Definition para establecerse como emisor de credenciales")
    cred_def = await CredentialDef.create('credef_pass_'+ str(doc_version), 'passport_cred_' + str(doc_version), schema_id, 0)
    cred_def_handle = cred_def.handle
    cred_def_id = await cred_def.get_cred_def_id()
    with open('cred_def.json', 'w') as out_cred_def:
        json.dump(await cred_def.serialize(), out_cred_def)


    """
        Load already created credentiad_definition
    """
    # print("#4 Cargar definicion de credencial ya hecha en el ledger")
    # with open('cred_def.json') as conf:
    #     cred_def_config = json.load(conf)
    # # cred_def_config = json.loads(config)
    # cred_def = await CredentialDef.deserialize(cred_def_config)
    # cred_def_id = await cred_def.get_cred_def_id()

    """
        New invitation details
    """
    print("#5 Crear nueva conexion para Alam y enviar invitacion")
    connection_to_alam = await Connection.create('other')
    await connection_to_alam.connect('{"use_public_did": true}')
    await connection_to_alam.update_state()
    details = await connection_to_alam.invite_details(False)
    print("**invite details**")
    print(json.dumps(details))
    print("******************")

    print("#6 Esperar a que Alam acepte la invitacion")
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


    """
        Start to create a credential issuer
    """
    print("#12 Crear objeto de emision de credencial utilizando un CredDef y un Schema especificos")
    print("Con la informacion de Alam", schema_attrs)
    credential = await IssuerCredential.create('alam_pass', schema_attrs, cred_def_handle, 'passport'+ str(doc_version), '0')
    with open('cred_iss.json', 'w') as out_cred_iss:
        json.dump(await credential.serialize(), out_cred_iss)


    """
        Load Credential Issuer
    """
    # print("#4 Load already created Credential Issuer")
    # with open('cred_iss.json') as conf:
    #     cred_iss_config = json.load(conf)
    # cred_iss_config = json.loads(config)
    # credential = await IssuerCredential.deserialize(cred_iss_config)


    print("#13 Emitir oferta de credencial a Alam")
    await credential.send_offer(connection_to_alam)
    await credential.update_state()

    print("#14 Esperar respuesta satisfactoria")
    credential_state = await credential.get_state()
    while credential_state != State.RequestReceived:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    print("#17 Emitir credencial a Alam")
    await credential.send_credential(connection_to_alam)

    print("#18 Esperar a que Alam reciba credencial y responda de confirmacion")
    await credential.update_state()
    credential_state = await credential.get_state()
    while credential_state != State.Accepted:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    proof_attrs = [
        {'name': 'name', 'restrictions': [{'issuer_did': config['institution_did']}]},
        {'name': 'date_of_birth', 'restrictions': [{'issuer_did': config['institution_did']}]},
        {'name': 'nationality', 'restrictions': [{'issuer_did': config['institution_did']}]}
    ]

    print("#19 Crear solicitud de prueba de informacion")
    print("En este caso hacemos una solicitud de documentos pero tienen que estar firmados exclusivamente por la SRE")
    proof = await Proof.create('proof_uuid', 'proof_from_alam', proof_attrs, {})

    print("#20 Enviar solicitud de informacion")
    await proof.request_proof(connection_to_alam)

    print("#21 Esperar respuesta de Alam")
    proof_state = await proof.get_state()
    while proof_state != State.Accepted:
        sleep(2)
        await proof.update_state()
        proof_state = await proof.get_state()

    print("#27 Procesar la prueba, comprobar firma digital del emisor, secreto maestro de Alam e informacion valida")
    await proof.get_proof(connection_to_alam)

    print("#28 Validando prueba...")
    if proof.proof_state == ProofState.Verified:
        print("Prueba verificada")
    else:
        print("Informacion invalida")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
