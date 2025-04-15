from packages.gRPC import kvs_pb2 as kvs
from collections import defaultdict


class Armazenamento:
    def __init__(self):
        self.tabela = defaultdict(list)
        self.versoes = defaultdict(int)

    def insere(self, request):
        chave, valor = request.chave, request.valor

        if (
            not isinstance(chave, str)
            or len(chave) < 3
            or not isinstance(valor, str)
            or len(valor) < 3
        ):
            return kvs.Versao(versao=-1)

        if chave not in self.tabela:
            self.versoes[chave] += 1
        else:
            self.versoes[chave] += 1

        self.tabela[chave].append((valor, self.versoes[chave]))

        return kvs.Versao(versao=self.versoes[chave])

    def consulta(self, request):
        chave, versao = request.chave, request.versao

        if chave not in self.tabela:
            return kvs.Tupla()

        if versao == 0:
            _, versao = max(self.tabela[chave], key=lambda x: x[1])

        for valor, _versao in reversed(self.tabela[chave]):
            if _versao <= versao:
                return kvs.Tupla(chave=chave, valor=valor, versao=_versao)

        return kvs.Tupla()

    def remove(self, request):
        chave, versao = request.chave, request.versao

        if not isinstance(chave, str) or len(chave) < 3 or chave not in self.tabela:
            return kvs.Versao(versao=-1)

        if versao == 0:
            del self.tabela[chave]
            return kvs.Versao()

        if not isinstance(versao, int):
            return kvs.Versao(versao=-1)

        for valor, _versao in self.tabela[chave]:
            if _versao == versao:
                self.tabela[chave].remove((valor, _versao))

                return kvs.Versao(versao=_versao)

        return kvs.Versao(versao=-1)

    def snapshot(self, request):
        versao = request.versao

        if not isinstance(versao, int):
            return

        for chave in self.tabela:
            versao_consulta = versao if versao > 0 else 0
            tupla = self.consulta(kvs.ChaveVersao(chave=chave, versao=versao_consulta))
            if tupla.chave:
                yield tupla
