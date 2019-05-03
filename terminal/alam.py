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

# logging.basicConfig(level=logging.DEBUG) uncomment to get logs

provisionConfig = {
    'agency_url': 'http://localhost:8080',
    'agency_did': 'VsKV7grR1BUE29mG2Fm2kX',
    'agency_verkey': 'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
    'wallet_name': 'user_wallet',
    'wallet_key': '123',
    'payment_method': 'null',
    # 'enterprise_seed': '000000000000000000000000Trustee1'
}

async def main():

    payment_plugin = cdll.LoadLibrary('libnullpay' + file_ext())
    payment_plugin.nullpay_init()

    print("#1 Proporcionar cartera de llaves")
    config = await vcx_agent_provision(json.dumps(provisionConfig))
    config = json.loads(config)
    # Set some additional configuration options specific to alice
    config['institution_name'] = 'alice'
    config['institution_logo_url'] = 'http://robohash.org/456'
    config['genesis_path'] = 'docker.txn'
    with open('alam.json', 'w') as outfile:
        json.dump(json.dumps(config), outfile)
    print("#8 Inicializar VCX Libreria con configuracion de cartera")
    session = await vcx_init_with_config(json.dumps(config))

    print("#9 Ingresar detalles de invitacion")
    details = input('Detalles de invitacion: ')

    print("#10 Convertir string a json y crear conexion")
    jdetails = json.loads(details)
    connection_to_sre = await Connection.create_with_details('sre', json.dumps(jdetails))
    await connection_to_sre.connect('{"use_public_did": true}')
    await connection_to_sre.update_state()

    print("#11 Esperar a que SRE emita oferta de credencial")
    sleep(10)
    offers = await Credential.get_offers(connection_to_sre)

    # Create a credential object from the credential offer
    credential = await Credential.create('credential', offers[0])

    print("#15 Una vez recibida la oferta, responder a la peticion")
    await credential.send_request(connection_to_sre, 0)

    print("#16 Esperar respuesta de SRE y aceptar credencial")
    credential_state = await credential.get_state()
    while credential_state != State.Accepted:
        sleep(2)
        await credential.update_state()
        credential_state = await credential.get_state()

    print("#22 Hacer request de solicitudes de pruebas")
    requests = await DisclosedProof.get_requests(connection_to_sre)

    print("#23 Una vez recibida la solicitud, crear nueva prueba con requisitos")
    proof = await DisclosedProof.create('proof', requests[0])

    print("#24 Consultar cartera por credenciales que satisfagan la informacion requerida")
    credentials = await proof.get_creds()

    # Use the first available credentials to satisfy the proof request
    for attr in credentials['attrs']:
        credentials['attrs'][attr] = {
            'credential': credentials['attrs'][attr][0]
        }
    print(credentials)

    print("#25 Generar la prueba con las credenciales y atributos necesarios")
    await proof.generate_proof(credentials, {})

    print("#26 Enviar prueba de informacion a la SRE")
    await proof.send_proof(connection_to_sre)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
