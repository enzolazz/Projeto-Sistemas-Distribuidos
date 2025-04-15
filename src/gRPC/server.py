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

from concurrent import futures
import logging

import grpc
from packages.gRPC import kvs_pb2 as kvs
from packages.gRPC import kvs_pb2_grpc as kvs_grpc
from packages.armazenamento import Armazenamento


class KeyValueStorer(kvs_grpc.KeyValueStorerServicer):
    def __init__(self):
        self.hash = Armazenamento()

    def Insere(self, request, context):
        print(
            "Received insert request.", "chave:", request.chave, "valor:", request.valor
        )

        result = self.hash.insere(
            kvs.ChaveValor(chave=request.chave, valor=request.valor)
        )

        print("Insert result:", result.versao)

        return result

    def Consulta(self, request, context):
        print("Received select request.")

        return self.hash.consulta(
            kvs.ChaveVersao(chave=request.chave, versao=request.versao)
        )

    def Remove(self, request, context):
        print("Received delete request.")

        return self.hash.remove(
            kvs.ChaveVersao(chave=request.chave, versao=request.versao)
        )

    def Snapshot(self, request, context):
        print("Received snapshot request.")

        return self.hash.snapshot(kvs.Versao(versao=request.versao))


def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvs_grpc.add_KeyValueStorerServicer_to_server(KeyValueStorer(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()
