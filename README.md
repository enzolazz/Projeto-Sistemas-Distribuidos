# Projeto da disciplina GBC074 - 2024/2 (Sistemas Distribuídos)

## Professor

- Prof. Dr. Paulo Rodolfo da Silva Leite Coelho

## Integrantes

- Enzo Lazzarini Amorim
- João Lucas Pontes Freitas

## Dependências

- Ambiente Linux (Linux shell + utilitários básicos: /bin/sh, bash, mkdir, etc.).
- Python (3.7 a 3.12 por suporte do pacote `paho-mqtt`) e pip.

## Detalhes de instalação

Foi utilizada a linguagem **Python 3.12.0** no desenvolvimento do projeto.
Foram utilizados os seguintes pacotes principais:

- **grpcio**: para comunicação gRPC entre cliente e servidor.
- **grpcio-tools**: geração de código Python a partir de arquivos `.proto`.
- **paho-mqtt**: para comunicação entre servidores via protocolo MQTT.
- **protobuf**: manipulação de mensagens Protobuf.
- **protoletariat**: para otimizar e consertar os imports gerados pelo protobuf.
- **argparse**: parsing de argumentos de linha de comando.
- **logging**: geração de logs para depuração e acompanhamento.

Outras dependências auxiliares podem ser consultadas no arquivo [`requirements.txt`](./requirements.txt).

## Instruções de compilação

- Clone o repositório:

```bash
git clone https://github.com/enzolazz/Projeto-Sistemas-Distribuidos.git
```

- Entre na pasta do projeto:

```bash
cd Projeto-Sistemas-Distribuidos
```

- Execute o script para compilar o projeto:

```bash
./compile.sh
```

<details>
    <summary>Limpar o projeto (se necessário)</summary>

Execute o script com argumento `clean`:

```bash
./compile.sh clean
```

</details>

<details>
  <summary>Verificar dependências (se necessário)</summary>

Execute o script com argumento `requirements`:

```bash
./compile.sh requirements
```

</details>

Se tudo ocorreu bem, as dependências necessárias para o projeto estarão instaladas e os arquivos gerados pelo pacote do gRPC estarão na pasta [`src/packages/gRPC`](./src/packages/gRPC/).

## Uso do servidor

O servidor está inteiramente implementado no arquivo [`src/server.py`](./src/server.py), que cria uma classe `KVS` herdando o `KVSServicer` dos arquivos gerados pelo gRPC. O servidor é iniciado na porta `50051` por padrão, mas recebe como argumento a porta desejada via -p ou --port. O servidor pode ser iniciado com o seguinte comando:

```bash
./server.py -p <PORT>
```

ou

```bash
./server.py --port <PORT>
```

## Organização dos dados

As tabelas hashs foram implementadas no [`src/packages/armazenamento`](./src/packages/armazenamento.py).
