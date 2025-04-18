from concurrent import futures
import logging, argparse, json, uuid
import grpc
import paho.mqtt.client as mqtt

from packages.gRPC import kvs_pb2 as kvs
from packages.gRPC import kvs_pb2_grpc as kvs_grpc
from packages.armazenamento import Armazenamento


class KVS(kvs_grpc.KVSServicer):
    def __init__(self, port: str):
        self.hash = Armazenamento()
        self.id_servidor = str(uuid.uuid4()) + f"-{port}"
        self.atualizando = False

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        try:
            self.mqtt_client.connect("localhost", 1883, 60)
        except ConnectionRefusedError:
            logging.error(
                "Erro ao conectar ao broker MQTT. Verifique se o broker está ativo."
            )
            exit(1)
        except Exception as e:
            logging.error(f"Erro inesperado ao conectar ao broker MQTT: {e}")
            exit(1)

        self.mqtt_client.loop_start()

    def publish_comando(self, comando, request):
        try:
            data = {
                "remetente": self.id_servidor,
                "comando": comando,
                "chave": request.chave,
            }

            if comando == "insere":
                data["valor"] = request.valor

            elif comando == "remove":
                data["versao"] = request.versao

            self.mqtt_client.publish("kvs/comandos", json.dumps(data), qos=1)

        except Exception as e:
            logging.error(f"Erro ao publicar comando: {e}, com requisicao: {request}")

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logging.info("Conectado ao broker MQTT com sucesso.")

        if reason_code > 0:
            logging.error(f"Erro ao conectar ao broker MQTT. Código: {reason_code}")
            raise ConnectionRefusedError("Erro ao conectar ao broker MQTT.")

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
            qos=1,
        )

    def on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logging.info("Disconectado ao broker MQTT com sucesso.")

        if reason_code > 0:
            logging.error("MQTT desconectado (%s); tentando reconectar…", reason_code)
            try:
                client.reconnect()
            except Exception:
                logging.exception("Falha ao reconectar; encerrando.")
                exit(1)

    def on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())

        except json.JSONDecodeError:
            logging.error(
                f"Erro ao decodificar a mensagem, recebida via MQTT no tópico {message.topic}:\n\
                {message.payload.decode()}"
            )
            return

        if payload.get("remetente") == self.id_servidor:
            return

        logging.info(
            f"Mensagem recebida.\
                Tópico: {message.topic};\
                Remetente: {payload.get("remetente")}\
                {f"Comando: {payload.get("comando")}" if message.topic == "kvs/comandos" else ""}"
        )

        if message.topic == "kvs/comandos":
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

        elif message.topic == "kvs/atualizar/pedido":
            client.publish(
                f"kvs/atualizar/resposta/{payload.get("remetente")}",
                json.dumps(
                    {
                        "remetente": self.id_servidor,
                        "tabela": self.hash()[0],
                        "versoes": self.hash()[1],
                    }
                ),
                qos=1,
            )

        elif message.topic == f"kvs/atualizar/resposta/{self.id_servidor}":
            if self.atualizando:
                return

            logging.info("Atualizando os dados...")
            self.hash.atualizar(payload.get("tabela"), payload.get("versoes"))

            client.unsubscribe(message.topic)
            self.atualizando = True

    def Insere(self, request, context):
        logging.info(
            "Operacao de `inserir` recebida.",
            f"chave: {request.chave}",
            f"valor: {request.valor}",
        )

        cv = kvs.ChaveValor(chave=request.chave, valor=request.valor)

        self.publish_comando("insere", request)

        return self.hash.insere(cv)

    def InsereVarias(self, request_iterator, context):
        logging.info("Operacao de `insere-varias` recebida. Requisicoes:\n")

        for request in request_iterator:
            cv = kvs.ChaveValor(chave=request.chave, valor=request.valor)

            logging.info(f"chave: {request.chave}", f"versao: {request.valor}")
            self.publish_comando("insere", request)

            yield self.hash.insere(cv)

    def ConsultaVarias(self, request_iterator, context):
        logging.info("Operacao de `consulta-varias` recebida. Requisicoes:\n")

        for request in request_iterator:
            cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

            logging.info(f"chave: {request.chave}", f"versao: {request.versao}")

            yield self.hash.consulta(cv)

    def RemoveVarias(self, request_iterator, context):
        logging.info("Operacao de `remove-varias` recebida. Requisicoes:\n")

        for request in request_iterator:
            cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

            logging.info(f"chave: {request.chave}", f"versao: {request.versao}")
            self.publish_comando("remove", request)

            yield self.hash.remove(cv)

    def Consulta(self, request, context):
        logging.info(
            "Operacao de `consulta` recebida.",
            f"chave: {request.chave}",
            f"versao: {request.versao}",
        )

        cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

        return self.hash.consulta(cv)

    def Remove(self, request, context):
        logging.info(
            "Operacao de `remove` recebida.",
            f"chave: {request.chave}",
            f"versao: {request.versao}",
        )

        cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

        self.publish_comando("remove", request)

        return self.hash.remove(cv)

    def Snapshot(self, request, context):
        logging.info(
            "Operacao de `snapshot` recebida.",
            f"versao: {request.versao}",
        )

        return self.hash.snapshot(kvs.Versao(versao=request.versao))


def serve(PORT: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvs_grpc.add_KVSServicer_to_server(KVS(PORT), server)
    bind_result = server.add_insecure_port("[::]:" + PORT)
    server.start()
    print(f"Server started, listening on {bind_result}")
    server.wait_for_termination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Servidor gRPC. Recebe comandos do cliente via gRPC e executa operações no armazenamento."
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        required=True,
        help="Porta a ser utilizada pelo servidor",
    )

    args = parser.parse_args()

    logging.basicConfig()

    serve(str(args.port))
