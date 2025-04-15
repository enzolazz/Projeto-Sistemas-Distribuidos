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
"""The Python implementation of the GRPC helloworld.Greeter client."""

from __future__ import print_function

import logging
import argparse

import grpc
from packages.gRPC import kvs_pb2 as kvs
from packages.gRPC import kvs_pb2_grpc as kvs_grpc


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = kvs_grpc.KeyValueStorerStub(channel)


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
        type=str,
        help="Argumentos do comando separados por ':'. É possivel passar mais de um argumento para cada operação, exceto o snapshot, que só aceita um argumento."
        + " (Insere: 'chave:valor';"
        + " Consulta: 'chave:versao(opicional)';"
        + " Remove: 'chave:versao(opicional)'"
        + " Snapshot: 'versao')",
    )

    args = parser.parse_args()

    logging.basicConfig()
    run()
