from concurrent import futures
import logging
import argparse
import json
import uuid
import grpc
import paho.mqtt.client as mqtt

from packages.gRPC import kvs_pb2 as kvs
from packages.gRPC import kvs_pb2_grpc as kvs_grpc
from packages.armazenamento import Armazenamento


class KVS(kvs_grpc.KVSServicer):
    def __init__(self, port: str):
        # Inicializa o hash de armazenamento
        try:
            self.hash = Armazenamento()

        except Exception as e:
            logging.error(f"Falha ao inicializar hash: {e}")
            # Se não puder inicializar o hash, servidor não pode funcionar.
            raise

        # Gera um ID único de servidor
        self.id_servidor = str(uuid.uuid4()) + f"-{port}"
        self.atualizando = False

        # Configura o cliente MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect

        # Tenta conectar ao broker MQTT.
        # Não pode falhar para a aplicação continuar. Se falhar, encerra o processo.
        try:
            self.mqtt_client.connect("localhost", 1883, 60)

        except ConnectionRefusedError:
            logging.error(
                "Erro ao conectar ao broker MQTT. Verifique se o broker está ativo."
            )

        except Exception as e:
            logging.error(f"Erro inesperado ao conectar ao broker MQTT: {e}")

        # Inicia o loop de rede em thread separada
        self.mqtt_client.loop_start()

    def publish_comando(self, comando, request):
        """
        Publica um comando no tópico 'kvs/comandos'.
        Tratamento: captura qualquer erro de serialização ou publicação.
        """

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

            # QoS=1 para garantir entrega pelo menos uma vez
            result = self.mqtt_client.publish("kvs/comandos", json.dumps(data), qos=1)

            # Verifica retorno para possíveis erros de rede
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logging.error(f"MQTT publish falhou com código {result.rc}")

        except Exception as e:
            logging.error(f"Erro ao publicar comando: {e}, com requisicao: {request}")

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        """
        Callback de conexão MQTT.
        Tratamento: reage a códigos de falha e retorna para reconnect.
        """

        if reason_code == 0:
            logging.info("Conectado ao broker MQTT com sucesso.")

        # Se falhar, lança exceção
        else:
            logging.error(f"Erro ao conectar ao broker MQTT. Código: {reason_code}")
            raise ConnectionRefusedError("Erro ao conectar ao broker MQTT.")

        # Inscreve-se nos tópicos necessários
        client.subscribe("kvs/comandos")
        client.subscribe("kvs/atualizar/pedido")
        client.subscribe(f"kvs/atualizar/resposta/{self.id_servidor}")

        # Solicita atualização ao entrar na rede
        client.publish(
            "kvs/atualizar/pedido",
            json.dumps({"remetente": self.id_servidor}),
            qos=1,
        )

    def on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        """
        Callback de desconexão MQTT.
        Tentamos reconnect em falhas não intencionais.
        """

        # Se desconectado intencionalmente, não tenta reconectar
        if reason_code == 0:
            logging.info("Desconectado do broker MQTT com sucesso.")

        # Se desconectado por erro, tenta reconectar e encerrar se falhar
        else:
            logging.error(f"MQTT desconectado ({reason_code}); tentando reconectar…")
            try:
                client.reconnect()

            except Exception:
                logging.exception("Falha ao reconectar; encerrando.")
                exit(1)

    def on_message(self, client, userdata, message):
        """
        Callback de mensagem MQTT.
        Tratamento: valida JSON, filtra mensagens próprias e executa comandos.
        """

        try:
            payload = json.loads(message.payload.decode())

        except json.JSONDecodeError:
            logging.error(
                f"Erro ao decodificar JSON recebido no tópico {message.topic}: "
                f"{message.payload!r}"
            )
            return

        # Ignora mensagens originadas por este servidor
        if payload.get("remetente") == self.id_servidor:
            return

        logging.info(
            f"Mensagem recebida: "
            f"Tópico={message.topic}, Remetente={payload.get('remetente')}"
        )

        try:
            # Dispara ação conforme tópico
            if message.topic == "kvs/comandos":
                cmd = payload.get("comando")

                if cmd == "insere":
                    cv = kvs.ChaveValor(
                        chave=str(payload.get("chave")), valor=str(payload.get("valor"))
                    )
                    self.hash.insere(cv)

                elif cmd == "remove":
                    cv = kvs.ChaveVersao(
                        chave=str(payload.get("chave")),
                        versao=int(payload.get("versao")),
                    )
                    self.hash.remove(cv)

            elif message.topic == "kvs/atualizar/pedido":
                # Envia snapshot + versões
                client.publish(
                    f"kvs/atualizar/resposta/{payload.get('remetente')}",
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

                logging.info("Atualizando dados locais com snapshot recebido…")
                self.hash.atualizar(payload.get("tabela"), payload.get("versoes"))
                client.unsubscribe(message.topic)
                self.atualizando = True

        except Exception as e:
            # Qualquer falha na aplicação do comando é registrada
            logging.error(f"Erro ao processar mensagem MQTT: {e}")

    # --- Métodos gRPC ---
    def Insere(self, request, context):
        """
        Inserção simples via gRPC. Em caso de falha no armazenamento,
        aborta a chamada com status INTERNAL.
        """

        logging.info(
            "Operacao de `inserir` recebida.",
            f"chave: {request.chave}",
            f"valor: {request.valor}",
        )

        try:
            cv = kvs.ChaveValor(chave=request.chave, valor=request.valor)
            self.publish_comando("insere", request)

            return self.hash.insere(cv)

        except Exception as e:
            logging.error(f"Erro em Insere(): {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Falha ao inserir: {e}")

    def InsereVarias(self, request_iterator, context):
        """
        Inserção em stream. Se um item falhar, aborta o stream.
        """

        logging.info("Operacao de `insere-varias` recebida. Requisicoes:\n")

        for request in request_iterator:
            try:
                logging.info(f"chave: {request.chave}", f"versao: {request.valor}")
                cv = kvs.ChaveValor(chave=request.chave, valor=request.valor)
                self.publish_comando("insere", request)

                yield self.hash.insere(cv)

            except Exception as e:
                logging.error(f"Erro em InsereVarias(): {e}")
                context.abort(grpc.StatusCode.INTERNAL, f"Falha ao inserir várias: {e}")

    def ConsultaVarias(self, request_iterator, context):
        """
        Consulta em stream. Cada falha aborta o stream.
        """

        for request in request_iterator:
            try:
                logging.info(f"chave: {request.chave}", f"versao: {request.versao}")
                cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)

                yield self.hash.consulta(cv)

            except Exception as e:
                logging.error(f"Erro em ConsultaVarias(): {e}")
                context.abort(
                    grpc.StatusCode.INTERNAL, f"Falha ao consultar várias: {e}"
                )

    def RemoveVarias(self, request_iterator, context):
        """
        Remoção em stream. Cada falha aborta o stream.
        """

        logging.info("Operacao de `remove-varias` recebida. Requisicoes:\n")

        for request in request_iterator:
            try:
                logging.info(f"chave: {request.chave}", f"versao: {request.versao}")
                cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)
                self.publish_comando("remove", request)

                yield self.hash.remove(cv)

            except Exception as e:
                logging.error(f"Erro em RemoveVarias(): {e}")
                context.abort(grpc.StatusCode.INTERNAL, f"Falha ao remover várias: {e}")

    def Consulta(self, request, context):
        """
        Consulta única. Em caso de erro no armazenamento, aborta com INTERNAL.
        """

        logging.info(
            "Operacao de `consulta` recebida.",
            f"chave: {request.chave}",
            f"versao: {request.versao}",
        )

        try:
            cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)
            return self.hash.consulta(cv)

        except Exception as e:
            logging.error(f"Erro em Consulta(): {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Falha ao consultar: {e}")

    def Remove(self, request, context):
        """
        Remoção única. Em caso de erro, aborta o call.
        """

        logging.info(
            "Operacao de `remove` recebida.",
            f"chave: {request.chave}",
            f"versao: {request.versao}",
        )

        try:
            cv = kvs.ChaveVersao(chave=request.chave, versao=request.versao)
            self.publish_comando("remove", request)
            return self.hash.remove(cv)

        except Exception as e:
            logging.error(f"Erro em Remove(): {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Falha ao remover: {e}")

    def Snapshot(self, request, context):
        """
        Retorna snapshot. Caso falhe, aborta.
        """

        logging.info(
            "Operacao de `snapshot` recebida.",
            f"versao: {request.versao}",
        )

        try:
            return self.hash.snapshot(kvs.Versao(versao=request.versao))

        except Exception as e:
            logging.error(f"Erro em Snapshot(): {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Falha ao gerar snapshot: {e}")


def serve(PORT: str):
    """
    Inicializa o servidor gRPC. Erros em add_insecure_port ou start são críticos.
    """

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kvs_grpc.add_KVSServicer_to_server(KVS(PORT), server)
    bind_result = server.add_insecure_port("[::]:" + PORT)

    if bind_result == 0:
        logging.error(f"Não foi possível vincular porta {PORT}")
        raise RuntimeError(f"Bind na porta {PORT} falhou")

    server.start()
    print(f"Server started, listening on {PORT}")
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

    try:
        serve(str(args.port))

    except Exception as e:
        logging.exception(f"Falha ao iniciar o servidor: {e}")
        exit(1)
