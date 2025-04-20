from packages.gRPC import kvs_pb2 as kvs
from collections import defaultdict
import threading


class Armazenamento:
    def __init__(self):
        self.tabela = defaultdict(list)
        self.versoes = defaultdict(int)
        self._lock = threading.RLock()

    def __call__(self):
        with self._lock:
            return self.tabela, self.versoes

    def insere(self, request) -> kvs.Versao:
        with self._lock:
            chave, valor = request.chave, request.valor

            if (
                not isinstance(chave, str)
                or len(chave) < 3
                or not isinstance(valor, str)
                or len(valor) < 3
            ):
                return kvs.Versao(versao=-1)

            self.versoes[chave] += 1

            self.tabela[chave].append((valor, self.versoes[chave]))

            return kvs.Versao(versao=self.versoes[chave])

    def consulta(self, request):
        with self._lock:
            chave, versao = request.chave, request.versao

            if chave not in self.tabela:
                return kvs.Tupla()

            if versao <= 0:
                versao = self.versoes[chave]

            for valor, ver in reversed(self.tabela[chave]):
                if ver <= versao:
                    return kvs.Tupla(chave=chave, valor=valor, versao=ver)

            return kvs.Tupla()

    def remove(self, request):
        with self._lock:
            chave, versao = request.chave, request.versao

            if not isinstance(chave, str) or len(chave) < 3 or chave not in self.tabela:
                return kvs.Versao(versao=-1)

            if versao == 0:
                del self.tabela[chave]
                return kvs.Versao()

            if not isinstance(versao, int):
                return kvs.Versao(versao=-1)

            for valor, ver in self.tabela[chave]:
                if ver == versao:
                    self.tabela[chave].remove((valor, ver))

                    return kvs.Versao(versao=ver)

            return kvs.Versao(versao=-1)

    def snapshot(self, request):
        with self._lock:
            versao = request.versao
            resultado = []

            if not isinstance(versao, int):
                return

            for chave in self.tabela:
                ver = versao if versao > 0 else 0
                tupla = self.consulta(kvs.ChaveVersao(chave=chave, versao=ver))
                if tupla.chave:
                    resultado.append(tupla)

        for tupla in resultado:
            yield tupla

    def atualizar(self, tabela, versoes):
        with self._lock:
            self.tabela = defaultdict(list, tabela)
            self.versoes = defaultdict(int, versoes)
