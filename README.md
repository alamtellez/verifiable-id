# verifiable-id
Este proyecto presenta la prueba de concepto de un sistema de identificacion descentralizado con credenciales verificables
comoproyecto de investigacion para la materia de Proyecto Integrador para el Desarrollo de Soluciones Empresariales
realizado por [Arturo Alam Tellez Villagomez](https://github.com/atellez08)

# By Alam

# Instrucciones de instalacion

### Nota
El proceso de instalacion es largo y tomara 1+ horas, ademas de que al ser un proyecto en estado de
incubacion, puede presentar errores, sin embargo el proceso ideal seria el siguiente

Este proyecto como muchos de hyperledger esta montado en una infraestructua de contenedores
por lo que es necesario la instalacion de docker en primer lugar
siguiendo las instrucciones para el SO de eleccion (se recomienda Ubuntu para mayor facilidad) [here](https://docs.docker.com/install/linux/docker-ce/ubuntu/)

Una vez instalado docker, se procesde a realizar la instalacion de Libindy
esta libreria contiene las funciones para interactuar con el ledger

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
    sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial {release channel}"
    sudo apt-get update
    sudo apt-get install -y libindy

Se debe construir la imagen de los requerimientos del sistema en los contenedores
para ello se debe descargar el repositorio que contiene las instrucciones:

    git clone git@github.com:hyperledger/indy-sdk.git

Ingresar a la carpeta indy-sdk/

    cd indy-sdk/

Desde ahi dentro se construiran los contenedores necesarios para dar vida al blockchain

    docker build -f ci/indy-pool.dockerfile -t indy_pool .

Esta parte del proceso es bastante tardada, entre 20 y 30 minutos ya que requiere la descarga e instalacion de muchas dependencias

Indy ofrece wrappers para diferentes lenguajes, en esta ocasion se selecciono Python para el desarrolo del proyecto, por ello se debe instalar las dependencias necesarias para poder utilizar Libindy con la interfaz dada: (Como recomendacion se proporne el uso de virtual environments de python para mantener las versiones de librerias y dependencias
aisladas y especificas para el desarrollo del proyecto)

    pip install python3-indy

A continuacion procederemos a la instalacion de VCX, la cual es una libreria que provee de herramientas de alto nivel sobre Libindy
para el desarrollo de aplicaciones, sin embargo se encuentra en etapa experimental por lo que no se garantiza su funcionamiento

    pip install python3-wrapper-vcx

Hasta este punto ya se encuentra el sistema con las dependencias necesarias para correr, sin embargo
VCX requiere de un agente en la nube para la comunicacion entre entidades por lo que se debe instalar

    cd vcx/dummy-cloud-agent/
    cargo run config/sample-config.json

El ultimo comando instalara y desplegara el agente en la nube y lo dejara corriendo, esto permitira que se lleve a acabo la comunicacion entre agentes de las diferentes partes del proceso de identidad

Y una libreria para el uso de pagos (aunque en esta prueba de concepto, no se utilizara, debe estar instalada)

    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
    sudo add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial master"
    sudo apt-get update
    sudo apt-get install -y libnullpay

Una vez concluido el proceso podremos correr la imagen construida que correra en nodos locales en `127.0.0.1` o `localhost`

    docker run -itd -p 9701-9708:9701-9708 indy_pool

Podemos verificar que la imagen este corriendo con el comando

    docker container list

Asi tendremos nuestro ambiente de desarrollo listo para correr la prueba de concepto, para ello se necesita clonar este repositorio

## Prueba en terminal

La prueba de concepto fue desarrollada como un script en terminal que establece los pasos descritos en el texto del trabajo de investigacion para la emision y verificacion de credenciales (es necesario tener minimo python 3.6)

    python sre.py

Dejar que se ejecute y cuando se presentan los detalles de la invitacion para establecer la comunicacion, se debera ejecutar el script

    python alam.py

Y copiar los detalles de la invitacion, a partir de ahi se podra ver el progreso de la aplicacion


## Hyperledger Indy
