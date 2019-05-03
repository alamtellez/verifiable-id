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
from vcx.api.proof import Proof
from vcx.api.utils import vcx_agent_provision
from vcx.api.vcx_init import vcx_init_with_config
from vcx.state import State, ProofState

# logging.basicConfig(level=logging.DEBUG) uncomment to get logs

provisionConfig = {
    'agency_url': 'http://localhost:8080',
    'agency_did': 'VsKV7grR1BUE29mG2Fm2kX',
    'agency_verkey': 'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
    'wallet_name': 'bank_wallet',
    'wallet_key': '123',
    'payment_method': 'null',
    'enterprise_seed': '000000000000000000000000Trustee1'
}

async def main():

    payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
    payment_plugin.nullpay_init()
    print("Iniciando Banco...")
    print("..................")
    print("#1 Proporcionar cartera de llaves")
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    # Set some additional configuration options specific to alice
    config['institution_name'] = 'banco'
    config['institution_logo_url'] = 'http://robohash.org/456'
    config['genesis_path'] = 'docker.txn'
    with open('banco.json', 'w') as outfile:
        json.dump(json.dumps(config), outfile)
    print("#8 Inicializar VCX Libreria con configuracion de cartera")
    session = await vcx_init_with_config(json.dumps(config))

    print("#5 Banco crea nueva conexion para Alam y enviar invitacion")
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

    with open('sre.json', 'r') as s_c:
        sre_conf = json.load(s_c)
    proof_attrs = [
        {'name': 'name', 'restrictions': [{'issuer_did': sre_conf['institution_did']}]},
        {'name': 'date_of_birth', 'restrictions': [{'issuer_did': sre_conf['institution_did']}]},
        {'name': 'nationality', 'restrictions': [{'issuer_did': sre_conf['institution_did']}]}
    ]
    print("\n\n Atributos solicitados:\n")
    for el in proof_attrs:
        print(el["name"])

    print("#19 Crear solicitud de prueba de informacion:")
    print("Solicita - Nombre, fecha de nacimiento y nacionalidad")
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
    info = await proof.get_proof(connection_to_alam)
    
    print("#28 Validando prueba...")
    if proof.proof_state == ProofState.Verified:
        print("Prueba verificada")
    else:
        print("Informacion invalida")
    attrs = info["requested_proof"]["revealed_attrs"]
    print("\n\n Atributos revelados:\n")
    for key, value in attrs.items():
        print(key, value["raw"])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
