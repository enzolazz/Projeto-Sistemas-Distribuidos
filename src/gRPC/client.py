# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import logging
import argparse
import sys

import grpc
from packages.gRPC import kvs_pb2 as kvs
from packages.gRPC import kvs_pb2_grpc as kvs_grpc


def run(comando, argumentos):
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = kvs_grpc.KeyValueStorerStub(channel)

        resposta = kvs.Tupla()
        match comando:
            case "insere":
                if len(argumentos) == 1:
                    chave, valor = argumentos[0].split(":")
                    print(chave, valor)

                    resposta = stub.Insere(kvs.ChaveValor(chave=chave, valor=valor))
            case "consulta":
                if len(argumentos) == 1:
                    cmd = argumentos[0].split(":")
                    chave = cmd[0]
                    versao = int(cmd[1]) if len(cmd) > 1 else 0

                    print(chave, versao)

                    resposta = stub.Consulta(
                        kvs.ChaveVersao(chave=chave, versao=versao)
                    )
            case "remove":
                if len(argumentos) == 1:
                    cmd = argumentos[0].split(":")
                    chave = cmd[0]
                    versao = int(cmd[1]) if len(cmd) > 1 else 0

                    resposta = stub.Remove(kvs.ChaveVersao(chave=chave, versao=versao))
            case "snapshot":
                resposta = stub.Snapshot(kvs.Versao(versao=argumentos[0]))
            case _:
                print(
                    "Comando inválido. Os comandos válidos são: insere, consulta, remove e snapshot."
                )
                sys.exit(1)

        if not resposta.versao:
            print("Falha em algum momento da comunicacao")
        else:
            print("Resposta do servidor:", str(resposta), sep="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cliente gRPC. Envia comandos para o servidor com seus respectivos argumentos."
    )

    parser.add_argument(
        "comando", type=str, help="Comando a ser realizado pelo servidor"
    )

    parser.add_argument(
        "argumentos",
        nargs="+",
        help="Argumentos do comando separados por ':'. É possivel passar mais de um argumento para cada operação, exceto o snapshot, que só aceita um argumento."
        + " (Insere: 'chave:valor';"
        + " Consulta: 'chave:versao(opicional)';"
        + " Remove: 'chave:versao(opicional)'"
        + " Snapshot: 'versao')",
    )

    args = parser.parse_args()

    logging.basicConfig()
    run(args.comando, args.argumentos)
