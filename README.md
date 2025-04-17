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
- **protoletariat**: para otimizar e consertar os imports gerados pelo protoc.
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

As tabelas hashs foram implementadas no [`src/packages/armazenamento`](./src/packages/armazenamento.py). A implementeção é baseada em dicionários utilizando o pacote `defaultdict` do Python. As tabelas hash são armazenadas nos dicionários com as `keys` sendo as chaves passadas pelo cliente e os `values` sendo uma tupla (valor, versao) com o valor passado pelo cliente e sua respectiva versão dentro de cada chave. As tabelas hash são armazenadas em um dicionário chamado `tabelas` e cada chave também tem um dicionário chamado `versoes` que armazena as versões de cada chave em inteiros. O `Armazenamento` possui métodos de inserção, remoção e consulta de chaves, além do método snapshot que retorna um conjunto de tuplas com versões menores ou iguais a versão passada.

## Descrição das dificuldades

As dificuldades vieram na organização do código, ao tentar transformar gerado pelo `grpc_tools.protoc` em pacotes globais do projeto. A geração dos códigos é acompanhada de imports relativos, o que torna a importação dos pacotes gerados um pouco confusa. Para resolver isso, foi utilizado o pacote `protoletariat` para otimizar e consertar os imports gerados pelo `protoc`. O pacote `protoletariat` é um pacote de terceiros que foi instalado via pip nas dependências do projeto. As chamadas dos pacotes acontecem no arquivo [`compile.sh`](./compile.sh) na funcao `generate_gRPC`. De resto, as implementações foram tranquilas e não trouxeram muitas dificuldades.
