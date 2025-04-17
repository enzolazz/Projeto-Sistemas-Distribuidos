from concurrent import futures
import logging, argparse, json, uuid
import grpc
import paho.mqtt.client as mqtt

from packages.gRPC import kvs_pb2 as kvs
from packages.gRPC import kvs_pb2_grpc as kvs_grpc
from packages.armazenamento import Armazenamento


class KVS(kvs_grpc.KVSServicer):
    def __init__(self, server_id):
        self.hash = Armazenamento()
        self.id_servidor = server_id
        self.atualizando = False

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.mqtt_client.connect("localhost", 1883, 60)
        self.mqtt_client.loop_start()

    def publish_comando(self, comando, request):
        data = {
            "remetente": self.id_servidor,
            "comando": comando,
            "chave": request.chave,
        }

        if comando == "insere":
            data["valor"] = request.valor
        elif comando == "remove":
            data["versao"] = request.versao

        self.mqtt_client.publish("kvs/comandos", json.dumps(data))

    def on_connect(self, client, userdata, flags, rc):
        print("Conectado ao broker MQTT com resultado: " + str(rc))
        client.subscribe("kvs/comandos")
        client.subscribe("kvs/atualizar/pedido")
        client.subscribe(f"kvs/atualizar/resposta/{self.id_servidor}")

        client.publish(
            "kvs/atualizar/pedido",
            json.dumps(
                {
                    "remetente": self.id_servidor,
                }
            ),
        )

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())

        if payload.get("remetente") == self.id_servidor:
            return

        print(
            f"Mensagem recebida.\
                Tópico: {msg.topic};\
                Remetente: {payload.get("remetente")}\
                {f"Comando: {payload.get("comando")}" if msg.topic == "kvs/comandos" else ""}"
        )

        if msg.topic == "kvs/comandos":
            if payload.get("comando") == "insere":
                cv = kvs.ChaveValor(
                    chave=str(payload.get("chave")), valor=str(payload.get("valor"))
                )

                self.hash.insere(cv)
            elif payload.get("comando") == "remove":
                cv = kvs.ChaveVersao(
                    chave=str(payload.get("chave")), versao=int(payload.get("versao"))
                )

                self.hash.remove(cv)
        elif msg.topic == "kvs/atualizar/pedido":
            client.publish(
                f"kvs/atualizar/resposta/{payload.get("remetente")}",
                json.dumps(
                    {
                        "remetente": self.id_servidor,
                        "tabela": self.hash()[0],
                        "versoes": self.hash()[1],
                    }
                ),
            )
        elif msg.topic == f"kvs/atualizar/resposta/{self.id_servidor}":
            if self.atualizando:
                return

            print("Atualizando os dados...")
            self.hash.atualizar(payload.get("tabela"), payload.get("versoes"))

            client.unsubscribe(msg.topic)
            self.atualizando = True

    def Insere(self, request, context):
        print(
            "Received insert request.", "chave:", request.chave, "valor:", request.valor
        )

        cv = kvs.ChaveValor(chave=request.chave, valor=request.valor)

        self.publish_comando("insere", request)

        return self.hash.insere(cv)

    def InsereVarias(self, request_iterator, context):
        print("Received batch insert.", request_iterator, sep="\n")

        for request in request_iterator:
            self.publish_comando("insere", request)

            cv = kvs.ChaveValor(chave=request.chave, valor=request.valor)

            yield self.hash.insere(cv)

    def ConsultaVarias(self, request_iterator, context):
        print("Received batch select.", request_iterator, sep="\n")

        for request in request_iterator:
            cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

            yield self.hash.consulta(cv)

    def RemoveVarias(self, request_iterator, context):
        print("Received batch delete.", request_iterator, sep="\n")

        for request in request_iterator:
            self.publish_comando("remove", request)

            cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

            yield self.hash.remove(cv)

    def Consulta(self, request, context):
        print("Received select request.", request)

        cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

        return self.hash.consulta(cv)

    def Remove(self, request, context):
        print("Received delete request.")

        cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

        self.publish_comando("insere", request)

        return self.hash.remove(cv)

    def Snapshot(self, request, context):
        print("Received snapshot request.")

        return self.hash.snapshot(kvs.Versao(versao=request.versao))


def serve(PORT: str):
    port = PORT
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvs_grpc.add_KVSServicer_to_server(KVS("server-" + PORT), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Servidor gRPC. Recebe comandos do cliente via gRPC e executa operações no armazenamento."
    )

    parser.add_argument(
        "-p", type=str, default="50051", help="Porta a ser utilizada pelo servidor"
    )

    args = parser.parse_args()

    logging.basicConfig()
    serve(str(args.p))
