# COMPUTATIONAL THINKING USING PYTHON

---

## SPRINT \[4\] — REPORT

**24 DE MAIO DE 2026**

---

**Turma 1TDSPR**

RM 568542 — Hugo Souza de Jesus

RM 566815 — Lucas Campanhã dos Santos

RM 567010 — Lucas Marcelino Pompeu

**LINK PARA O VÍDEO NO YOUTUBE:** *a definir*

---

&nbsp;

---

# SUMÁRIO

**INTRODUÇÃO** .............................................................. 3

**OBJETIVOS** .................................................................. 4
- Objetivo Geral ................................................................ 4
- Objetivos Específicos ....................................................... 4

**JUSTIFICATIVA** ............................................................ 5

**ARQUITETURA DO SISTEMA** ......................................... 6
- Estrutura de Arquivos ...................................................... 6
- Responsabilidades dos Módulos ......................................... 7

**INTEGRAÇÃO COM ORACLE DATABASE** ......................... 10
- Conexão e Credenciais .................................................... 10
- Estratégia de Persistência (carregar/salvar) ........................ 11
- Setup das Tabelas (Oracle_Scripts.sql) .............................. 12

**MODELO DE DADOS** ..................................................... 13
- Entidades e Campos ........................................................ 13
- Relacionamentos ........................................................... 15

**SISTEMA DE PERMISSÕES** ........................................... 16

**DESCRIÇÃO DAS FUNCIONALIDADES** ............................ 17
- Módulo de Acesso Público ................................................ 17
- Painel do Colaborador ..................................................... 18
- Painel do Dentista .......................................................... 20

**CONSUMO DE API EXTERNA — VIACEP** ........................ 22

**RELATÓRIOS COM FILTROS E EXPORTAÇÃO JSON** ........ 23
- Pacientes por dentista (com filtro de UF) ........................... 23
- Atendimentos por status e período .................................... 24
- Notificações a partir de uma data ..................................... 25

**ESTRUTURAS DE PROGRAMAÇÃO UTILIZADAS** .............. 26
- CRUD sobre Oracle ......................................................... 26
- Funções com Parâmetros e Retorno ................................... 27
- Listas e Dicionários ........................................................ 28
- Validação de Entradas e Tratamento de Exceções .................. 29

**ATENDIMENTO AOS REQUISITOS DA RUBRICA** ............. 30

**COMO EXECUTAR** ....................................................... 31

**CONCLUSÃO** .............................................................. 32

---

&nbsp;

---

# INTRODUÇÃO

Este documento descreve a **Sprint 4** do projeto *Tech do Bem*, realizado na disciplina **Computational Thinking Using Python** do curso de Tecnologia em Desenvolvimento de Software da FIAP, turma **1TDSPR**.

O objetivo da Sprint 4, conforme o briefing da disciplina, é **integrar o sistema desenvolvido na Sprint 3 com um banco de dados Oracle**, substituindo a persistência em arquivos JSON por uma camada relacional real. Além disso, esta sprint adiciona:

- **Consumo de uma API pública externa** (ViaCEP) para autopreenchimento de endereço durante o cadastro de pacientes.
- **Relatórios com filtros** (SELECT/WHERE) e **exportação de resultados em JSON**, contemplando o requisito de "duas ou mais consultas filtradas" do rubric.
- **Scripts DDL** para criação das tabelas, sequências e constraints no Oracle Database da FIAP.

A solução mantém a arquitetura modular da Sprint 3 — separação de responsabilidades em `storage`, `auth`, `crud`, `utils` e painéis específicos por perfil de usuário — e amplia o modelo de dados para incluir endereço geocodificado do paciente (CEP, logradouro, bairro, cidade, UF). O resultado é um sistema CLI completo, com persistência real, integração externa e geração de relatórios operacionais.

---

&nbsp;

---

# OBJETIVOS

## Objetivo Geral

Integrar o sistema CLI da *Turma do Bem* com um banco de dados Oracle, evoluindo a camada de persistência de arquivos JSON para uma estrutura relacional com tabelas, sequências e constraints. Adicionalmente, demonstrar o consumo de uma API pública externa e a geração de relatórios filtrados exportáveis em JSON.

## Objetivos Específicos

- **Implementar a camada de conexão com Oracle** utilizando a biblioteca `oracledb`, expondo um *context manager* que garante `commit`/`rollback` automáticos e fechamento adequado de recursos.
- **Reescrever `storage.py`** para sincronizar a lista em memória com a tabela correspondente no banco, aplicando `INSERT`, `UPDATE` e `DELETE` conforme o diff entre o estado atual da lista e o banco.
- **Criar o script DDL `Oracle_Scripts.sql`** com `DROP` idempotente (PL/SQL), `CREATE TABLE` para 8 entidades, sequências, *primary keys*, *foreign keys*, *unique constraints* e *check constraints*.
- **Adicionar o módulo `api_externa.py`** consumindo o ViaCEP (HTTPS, biblioteca padrão `urllib`) com validação de CEP, tratamento de erros de rede e formatação dos dados retornados.
- **Estender a entidade Paciente** com os campos `cep`, `logradouro`, `bairro`, `cidade`, `uf`, integrando o cadastro com a busca automática via ViaCEP.
- **Criar o módulo `relatorios.py`** com **3 relatórios** baseados em SELECT/WHERE, oferecendo opção de exportação dos resultados para arquivos `.json` na pasta `exports/`.
- **Manter o CRUD completo** das entidades Colaborador, Dentista, Paciente, Campanha, Atendimento, Notificação, Anotação e Solicitação, agora persistido em Oracle.
- **Preservar todas as validações de entrada e tratamento de exceções** da Sprint 3, adicionando captura específica para `oracledb.DatabaseError`.
- **Documentar o passo a passo de execução** incluindo conexão à VPN/rede da FIAP, instalação do `oracledb` e execução do script `_setup_db.py` para criação inicial das tabelas.

---

&nbsp;

---

# JUSTIFICATIVA

Sistemas de gestão para organizações do terceiro setor frequentemente esbarram nas mesmas limitações: persistência frágil em arquivos locais, ausência de integrações com serviços externos e dificuldade para extrair informação consolidada dos dados operacionais. A Sprint 3 do projeto *Tech do Bem* endereçou a primeira camada do problema (CRUD + JSON), mas deixava em aberto duas questões críticas: como garantir integridade referencial e como gerar visões agregadas dos dados.

A Sprint 4 ataca exatamente esses dois pontos. A migração para **Oracle Database** introduz constraints declarativas — *foreign keys*, *unique constraints* e *check constraints* — que garantem, no nível do banco, que estados inválidos do sistema (um atendimento órfão, um dentista com CRO duplicado, um cargo fora da lista permitida) sejam **impossíveis** de persistir, independentemente de quem está consumindo o banco. A camada Python continua validando entradas, mas o banco passa a ser uma rede de segurança adicional.

A inclusão da **API ViaCEP** demonstra como uma integração simples com um serviço público elimina retrabalho operacional: o colaborador digita um CEP e o sistema preenche logradouro, bairro, cidade e UF automaticamente. Em uma ONG com voluntários rotativos e cadastros frequentes, isso reduz erros de digitação e padroniza a forma como endereços são armazenados — pré-requisito para análises geográficas futuras (a visão de "pacientes por bairro" no front-end web depende justamente dessa padronização).

Os **relatórios com SELECT/WHERE e exportação JSON** atendem a uma demanda operacional concreta: o coordenador da ONG precisa frequentemente extrair listas filtradas (atendimentos do mês, pacientes de um dentista específico, histórico de comunicações) para uso fora do sistema — relatórios mensais, prestação de contas, integração com planilhas. A exportação em JSON é o ponto de entrada para essas integrações sem exigir acesso direto ao banco.

Tecnicamente, a Sprint 4 também demonstra um padrão importante de programação: **isolar a complexidade da camada de dados em um único módulo (`storage.py`)** com uma API mínima (`carregar`, `salvar`, `proximo_id`). Os demais módulos — `crud`, `painel_colaborador`, `painel_dentista`, `auth` — **não foram alterados** em sua lógica de negócio. A migração de JSON para Oracle ficou contida em três arquivos novos (`database.py`, `_setup_db.py`, `Oracle_Scripts.sql`) e na reescrita interna de `storage.py`, sem propagar dependências do banco para o resto do sistema.

---

&nbsp;

---

# ARQUITETURA DO SISTEMA

## Estrutura de Arquivos

```
Python - Sprint 4/
│
├── main.py                       # Ponto de entrada e menu público
├── _setup_db.py                  # Executa Oracle_Scripts.sql na primeira vez
├── Oracle_Scripts.sql            # DDL: DROP + CREATE TABLE + sequências
├── Scripts_Oracle.txt            # Cópia .txt do .sql (formato exigido pelo rubric)
├── requirements.txt              # oracledb>=2.0.0
├── sprint-4.txt                  # RMs + link do vídeo
├── Documentacao_Sprint4.md       # Este documento
│
├── exports/                      # Saída dos relatórios em JSON (criada em runtime)
│
└── modules/
    ├── database.py               # Conexão Oracle + context manager
    ├── storage.py                # Sincronização lista ↔ tabela (INSERT/UPDATE/DELETE)
    ├── api_externa.py            # Cliente ViaCEP (urllib + json)
    ├── relatorios.py             # 3 relatórios SELECT/WHERE + export JSON
    ├── utils.py                  # Entrada segura, validações, formatação
    ├── auth.py                   # Login, troca de senha, solicitações, permissões
    ├── crud.py                   # CRUD: todas as entidades (chama api_externa no cadastro)
    ├── painel_colaborador.py     # Dashboard do Colaborador (inclui relatórios)
    └── painel_dentista.py        # Dashboard do Dentista
```

Os arquivos `_setup_db.py` e `Oracle_Scripts.sql` precisam ser executados **uma vez** antes do primeiro uso, para criar as tabelas no banco. Após isso, qualquer execução de `main.py` reutiliza as tabelas existentes — apenas o usuário `ADMIN` é recriado em memória pela função `_seed_admin()` se ainda não existir na tabela `tdb_colaboradores`.

---

## Responsabilidades dos Módulos

### `main.py` — Ponto de Entrada

Inalterado em estrutura desde a Sprint 3, apenas com captura adicional de `oracledb.DatabaseError`:

1. Chama `storage.inicializar()` que testa a conexão Oracle.
2. Garante o usuário `ADMIN` via `_seed_admin()`.
3. Exibe o **menu público** (login / solicitar cadastro / sair).
4. Roteia o usuário autenticado para `menu_colaborador` ou `menu_dentista`.
5. Captura erros de banco no nível mais externo, exibindo mensagem amigável.

---

### `modules/database.py` — Camada de Conexão Oracle (NOVO)

Centraliza tudo que envolve a biblioteca `oracledb`:

| Símbolo | Descrição |
|---|---|
| `HOST`, `PORT`, `SID`, `USUARIO`, `SENHA` | Constantes com as credenciais do banco da FIAP |
| `DSN` | Construído com `oracledb.makedsn(HOST, PORT, sid=SID)` |
| `conectar()` | Abre uma conexão simples |
| `cursor()` | **Context manager** que abre conexão + cursor, faz `commit` em sucesso, `rollback` em exceção e fecha tudo no `finally` |
| `testar_conexao()` | Executa `SELECT 1 FROM DUAL` e devolve `True`/`False` |

O context manager `cursor()` é o ponto único de acesso ao banco: qualquer função que precise ler ou escrever usa `with database.cursor() as cur:` e ganha automaticamente o tratamento transacional correto.

---

### `modules/storage.py` — Camada de Persistência (REESCRITO)

Preserva a **assinatura pública** da Sprint 3 (`carregar`, `salvar`, `proximo_id`, `inicializar`) mas substitui o backend de JSON por Oracle. Internamente:

- `SCHEMAS` é um dicionário que mapeia cada entidade (`"colaboradores"`, `"dentistas"`, etc.) para a tabela correspondente e a lista de colunas. Colunas que armazenam estruturas complexas (`exames`, `dados`) são marcadas como `json_cols` e serializadas com `json.dumps`/`json.loads` na fronteira.
- `carregar(entidade)` faz `SELECT ... ORDER BY id` e devolve uma lista de dicionários, exatamente como antes.
- `salvar(entidade, lista)` aplica uma estratégia de **diff e sync**: compara IDs da lista com os IDs presentes no banco e executa `INSERT` (novos), `UPDATE` (existentes) ou `DELETE` (sumidos). Isso preserva a semântica "carrega tudo, modifica em memória, salva tudo" da Sprint 3 — nenhum chamador precisou ser reescrito.
- `proximo_id(lista)` continua calculando `max(ids) + 1`. As sequências do Oracle existem por questão de boa prática, mas o controle do ID continua na aplicação para manter compatibilidade com o código herdado.

---

### `modules/api_externa.py` — Cliente ViaCEP (NOVO)

Módulo dedicado ao consumo da API pública [ViaCEP](https://viacep.com.br). Implementado com a **biblioteca padrão** (`urllib.request` + `json` + `re`), sem dependências externas:

| Função | Descrição |
|---|---|
| `_normalizar_cep(cep)` | Remove caracteres não numéricos e valida que sobram 8 dígitos |
| `buscar_endereco(cep)` | Faz a requisição HTTPS, trata `URLError`/`TimeoutError`/JSON inválido, devolve `{cep, logradouro, bairro, cidade, uf}` ou `None` |
| `coletar_endereco_interativo(prompt)` | Pergunta o CEP ao usuário, chama `buscar_endereco`, devolve dict pronto pra ser mesclado no registro |

O timeout é fixado em 5 segundos. Em caso de falha de rede, CEP inválido ou CEP não encontrado, o sistema imprime uma mensagem amigável e prossegue com os campos vazios, permitindo o cadastro manual.

---

### `modules/relatorios.py` — Relatórios Filtrados (NOVO)

Implementa o requisito da Sprint 4 de **duas ou mais consultas filtradas com exportação em JSON**. Foram criados **três relatórios**, todos acessíveis a partir do painel do Colaborador (cargo Auxiliar ou superior):

| Relatório | Filtros (WHERE) | JOINs |
|---|---|---|
| Pacientes por dentista | `id_dentista = :id_dent` (obrigatório) + `UPPER(uf) = :uf` (opcional) | INNER JOIN tdb_dentistas |
| Atendimentos por status e período | `data BETWEEN :inicio AND :fim` + `status = :status` (opcional) | INNER JOIN paciente + dentista + LEFT JOIN campanha |
| Notificações a partir de uma data | `SUBSTR(data_envio, 1, 10) >= :inicio` | LEFT JOIN colaborador + dentista |

Em todos os relatórios o fluxo é o mesmo:
1. Pergunta os filtros ao usuário (com validação via `utils`).
2. Executa SELECT com `binds` parametrizados (à prova de SQL injection).
3. Exibe o resultado formatado na tela.
4. Pergunta `"Exportar resultado para JSON? (S/N)"`. Se sim, escreve `exports/<prefixo>_<timestamp>.json`.

A função interna `_exportar_json` cria a pasta `exports/` se necessário e usa `json.dump(..., default=str)` para lidar com objetos `Date`/`Decimal` que o Oracle eventualmente retorna.

---

### `modules/utils.py` — Utilitários de Interface

Idêntico em estrutura à Sprint 3, com adições para a Sprint 4:

| Função | Descrição |
|---|---|
| `input_texto(prompt, obrigatorio)` | Lê texto, com validação de campo obrigatório |
| `input_inteiro(prompt, minimo, maximo)` | Lê inteiro com validação de intervalo |
| `input_data(prompt)` | Lê data `DD/MM/AAAA` e devolve ISO `AAAA-MM-DD` |
| `input_cpf(prompt, obrigatorio)` | Valida formato `XXX.XXX.XXX-XX` |
| `input_cro(prompt)` | Valida formato `XXXXXX-UF` |
| `input_senha(prompt)` | Usa `getpass.getpass` para esconder a digitação |
| `confirmar(prompt)` | Loop S/N |
| `cabecalho`, `separador`, `pausar` | Apresentação da tela |
| `formatar_data`, `data_hoje_iso`, `datetime_agora_iso` | Conversão de datas |

---

### `modules/auth.py` — Autenticação e Permissões

Inalterado em lógica. Continua oferecendo `fazer_login`, `trocar_senha`, `submeter_solicitacao`, `tem_permissao`. Como `storage.carregar` agora vai ao Oracle, qualquer chamada ao `auth` automaticamente consulta o banco — sem necessidade de mudanças no módulo.

A hierarquia de cargos permanece:

| Cargo | Nível |
|---|---|
| Estagiário | 1 |
| Auxiliar | 2 |
| Coordenador | 3 |
| Administrador | 4 |

---

### `modules/crud.py` — Operações de CRUD

Mantém o conjunto de operações de Create/Read/Update/Delete para todas as entidades. A diferença em relação à Sprint 3 está no **cadastro de paciente** e na **edição de paciente**: ambos agora chamam `api_externa.coletar_endereco_interativo()` para preencher CEP, logradouro, bairro, cidade e UF a partir do ViaCEP.

Todos os fluxos continuam recebendo `usuario_logado` para validar permissões via `auth.tem_permissao` antes de qualquer escrita.

---

### `modules/painel_colaborador.py` e `modules/painel_dentista.py`

Estrutura preservada da Sprint 3. O painel do Colaborador ganhou uma nova opção de menu — **Relatórios** — que invoca `relatorios.menu_relatorios(usuario_logado)`.

---

&nbsp;

---

# INTEGRAÇÃO COM ORACLE DATABASE

## Conexão e Credenciais

A conexão é configurada em `modules/database.py` com as credenciais do banco didático da FIAP:

```python
HOST = "oracle.fiap.com.br"
PORT = 1521
SID = "orcl"
USUARIO = "RM567010"
SENHA = "<senha do RM>"

DSN = oracledb.makedsn(HOST, PORT, sid=SID)
```

A string DSN é o equivalente da string JDBC `jdbc:oracle:thin:@oracle.fiap.com.br:1521:orcl`. O usuário/senha devem estar conectados à **rede ou VPN da FIAP** para que o host `oracle.fiap.com.br` seja resolvível.

A função `database.cursor()` é o **único** ponto onde transações são abertas:

```python
@contextmanager
def cursor():
    conexao = conectar()
    cur = conexao.cursor()
    try:
        yield cur
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cur.close()
        conexao.close()
```

Esse padrão garante que qualquer chamada à camada de dados:
- Use `commit` automaticamente em caso de sucesso.
- Faça `rollback` em caso de qualquer exceção, preservando a integridade.
- Sempre feche cursor e conexão, mesmo em caso de erro inesperado.

---

## Estratégia de Persistência (carregar/salvar)

O `storage.py` preserva o contrato da Sprint 3 — chamadas continuam sendo `storage.carregar("pacientes")` e `storage.salvar("pacientes", lista)`. A diferença é o que acontece dentro de `salvar()`:

```python
def salvar(entidade: str, dados: list[dict]) -> None:
    schema = SCHEMAS[entidade]
    tabela = schema["table"]
    cols = schema["cols"]

    with database.cursor() as cur:
        cur.execute(f"SELECT id FROM {tabela}")
        ids_existentes = {linha[0] for linha in cur.fetchall()}
        ids_novos = {item["id"] for item in dados}

        for id_removido in ids_existentes - ids_novos:
            cur.execute(f"DELETE FROM {tabela} WHERE id = :id", {"id": id_removido})

        for item in dados:
            binds = {c: _to_db(c, item.get(c), schema) for c in cols}
            if item["id"] in ids_existentes:
                cur.execute(sql_update, binds)
            else:
                cur.execute(sql_insert, binds)
```

A vantagem dessa estratégia é que o resto do código (`crud.py`, `painel_*`) continua escrevendo no padrão **"carrega tudo, modifica em memória, salva tudo"** — exatamente como na Sprint 3 — sem perceber que por trás existe um banco relacional. Toda a complexidade de diff/sync fica encapsulada em uma única função.

---

## Setup das Tabelas (Oracle_Scripts.sql)

O arquivo `Oracle_Scripts.sql` é a fonte canônica do schema. Estrutura:

1. **Blocos PL/SQL de DROP idempotente** — usam `BEGIN EXECUTE IMMEDIATE 'DROP...'; EXCEPTION WHEN OTHERS THEN NULL; END;` para evitar erro caso a tabela ainda não exista.
2. **8 tabelas** com PKs, FKs, UNIQUEs e CHECKs declaradas no `CREATE TABLE`.
3. **8 sequências** (`seq_tdb_*`) reservadas para uso futuro.
4. `COMMIT` final.

Para executar contra o banco da FIAP, basta rodar:

```bash
python3 _setup_db.py
```

O script `_setup_db.py` faz o parse cuidadoso do arquivo SQL — separando blocos PL/SQL (terminados em `/` numa linha isolada) de statements DDL/DML comuns (terminados em `;`) — e executa cada um via `cur.execute`, reportando sucesso/falha individualmente.

---

&nbsp;

---

# MODELO DE DADOS

## Entidades e Campos

### `tdb_colaboradores`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `nome` | VARCHAR2(100) | NOT NULL |
| `cpf` | VARCHAR2(14) | — |
| `email` | VARCHAR2(100) | NOT NULL, UNIQUE |
| `senha` | VARCHAR2(100) | NOT NULL |
| `cargo` | VARCHAR2(30) | NOT NULL, CHECK IN ('Estagiário','Auxiliar','Coordenador','Administrador') |
| `disponibilidade` | NUMBER(1) | DEFAULT 1, CHECK IN (0,1) |

### `tdb_dentistas`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `nome` | VARCHAR2(100) | NOT NULL |
| `cpf` | VARCHAR2(14) | — |
| `email` | VARCHAR2(100) | NOT NULL, UNIQUE |
| `senha` | VARCHAR2(100) | NOT NULL |
| `cro` | VARCHAR2(10) | NOT NULL, UNIQUE |
| `especialidade` | VARCHAR2(100) | — |
| `disponibilidade` | NUMBER(1) | DEFAULT 1, CHECK IN (0,1) |
| `id_colaborador` | NUMBER(10) | FK → tdb_colaboradores(id) |

### `tdb_pacientes` — *com endereço (novo na Sprint 4)*

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `nome` | VARCHAR2(100) | NOT NULL |
| `cpf` | VARCHAR2(14) | — |
| `data_nasc` | VARCHAR2(10) | — |
| `telefone` | VARCHAR2(20) | — |
| `email` | VARCHAR2(100) | — |
| `id_dentista` | NUMBER(10) | FK → tdb_dentistas(id) |
| `cep` | VARCHAR2(9) | — *(preenchido via ViaCEP)* |
| `logradouro` | VARCHAR2(200) | — |
| `bairro` | VARCHAR2(100) | — |
| `cidade` | VARCHAR2(100) | — |
| `uf` | VARCHAR2(2) | — |

### `tdb_campanhas`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `nome` | VARCHAR2(100) | NOT NULL |
| `local` | VARCHAR2(200) | NOT NULL |
| `data_inicio` | VARCHAR2(10) | NOT NULL |
| `data_fim` | VARCHAR2(10) | NOT NULL, CHECK (data_fim >= data_inicio) |
| `id_colaborador` | NUMBER(10) | FK → tdb_colaboradores(id) |

### `tdb_atendimentos`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `id_paciente` | NUMBER(10) | NOT NULL, FK → tdb_pacientes(id) |
| `id_dentista` | NUMBER(10) | NOT NULL, FK → tdb_dentistas(id) |
| `id_campanha` | NUMBER(10) | FK → tdb_campanhas(id) |
| `data` | VARCHAR2(10) | NOT NULL |
| `tipo` | VARCHAR2(40) | NOT NULL |
| `status` | VARCHAR2(20) | NOT NULL, CHECK IN ('agendado','realizado','cancelado') |
| `observacoes` | VARCHAR2(1000) | — |
| `exames` | VARCHAR2(4000) | — *(JSON serializado pelo storage)* |

### `tdb_notificacoes`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `mensagem` | VARCHAR2(1000) | NOT NULL |
| `data_envio` | VARCHAR2(20) | NOT NULL |
| `status_envio` | VARCHAR2(20) | NOT NULL |
| `canal` | VARCHAR2(20) | NOT NULL, CHECK IN ('email','sms','push') |
| `id_colaborador` | NUMBER(10) | FK → tdb_colaboradores(id) |
| `id_dentista` | NUMBER(10) | FK → tdb_dentistas(id) |

### `tdb_anotacoes`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `texto` | VARCHAR2(1000) | NOT NULL |
| `data` | VARCHAR2(20) | NOT NULL |
| `autor_id` | NUMBER(10) | NOT NULL |
| `autor_tipo` | VARCHAR2(20) | NOT NULL, CHECK IN ('colaborador','dentista') |
| `sobre_id` | NUMBER(10) | NOT NULL |
| `sobre_tipo` | VARCHAR2(20) | NOT NULL, CHECK IN ('paciente','dentista') |

### `tdb_solicitacoes`

| Coluna | Tipo | Constraint |
|---|---|---|
| `id` | NUMBER(10) | PK |
| `tipo` | VARCHAR2(30) | NOT NULL, CHECK IN ('dentista','colaborador','alteracao_paciente') |
| `dados` | VARCHAR2(4000) | NOT NULL *(JSON serializado)* |
| `status` | VARCHAR2(20) | NOT NULL, CHECK IN ('pendente','aprovado','recusado') |
| `data` | VARCHAR2(20) | NOT NULL |

---

## Relacionamentos

```
tdb_colaboradores ──< tdb_dentistas ──< tdb_pacientes ──< tdb_atendimentos
        │                  │                 │
        │                  │                 └──< tdb_anotacoes (sobre_tipo='paciente')
        │                  └──< tdb_anotacoes (sobre_tipo='dentista')
        │
        ├──< tdb_campanhas ──< tdb_atendimentos
        │
        └──< tdb_notificacoes >── tdb_dentistas
```

A hierarquia central permanece **Colaborador → Dentista → Paciente**. As entidades polimórficas (`tdb_anotacoes`, `tdb_solicitacoes`) usam colunas discriminadoras (`autor_tipo`, `sobre_tipo`, `tipo`) com check constraint para restringir os valores permitidos.

---

&nbsp;

---

# SISTEMA DE PERMISSÕES

O controle de acesso continua sendo implementado pela função `tem_permissao(colaborador, nivel_minimo)` em `auth.py`, com a mesma hierarquia da Sprint 3 e a adição da permissão para acessar Relatórios:

| Ação | Estagiário (1) | Auxiliar (2) | Coordenador (3) | Administrador (4) | Dentista |
|---|:---:|:---:|:---:|:---:|:---:|
| Visualizar dentistas | ✓ | ✓ | ✓ | ✓ | — |
| Visualizar pacientes | ✓ | ✓ | ✓ | ✓ | — |
| Cadastrar paciente | — | ✓ | ✓ | ✓ | — |
| Editar paciente | — | ✓ | ✓ | ✓ | Solicitação |
| Excluir paciente | — | — | ✓ | ✓ | — |
| Cadastrar dentista | — | — | — | ✓ | — |
| Editar dentista | — | ✓ | ✓ | ✓ | — |
| Excluir dentista | — | — | — | ✓ | — |
| Cadastrar colaborador | — | — | — | ✓ | — |
| Editar colaborador | — | — | ✓ | ✓ | — |
| Excluir colaborador | — | — | — | ✓ | — |
| Aprovar solicitações | — | — | ✓ | ✓ | — |
| **Acessar Relatórios** | — | ✓ | ✓ | ✓ | — |
| Alterar senha alheia | — | — | — | ✓ | — |
| Alterar própria senha | ✓ | ✓ | ✓ | ✓ | ✓ |
| Registrar atendimento | — | — | — | — | ✓ |
| Solicitar exame | — | — | — | — | ✓ |
| Enviar notificação | ✓ | ✓ | ✓ | ✓ | ✓ |
| Criar anotações | ✓ | ✓ | ✓ | ✓ | ✓ |

---

&nbsp;

---

# DESCRIÇÃO DAS FUNCIONALIDADES

## Módulo de Acesso Público

Idêntico à Sprint 3:

### Fazer Login

E-mail (ou `ADMIN`) + senha. Busca em `tdb_colaboradores` e `tdb_dentistas`. Em caso de sucesso, redireciona para o painel correspondente.

> **Credenciais padrão do administrador:**
> - Usuário: `ADMIN`
> - Senha: `ADMIN`

### Solicitar Cadastro

Permite que qualquer pessoa submeta uma solicitação de cadastro como Dentista ou Colaborador, salva em `tdb_solicitacoes` com `status = 'pendente'`. Coordenadores e Administradores podem aprovar/recusar após o login.

---

## Painel do Colaborador

### [1] Ver Meus Dentistas

Exibe resumo operacional dos dentistas vinculados ao colaborador logado, com contagem de pacientes, atendimentos realizados/agendados/cancelados.

### [2] Notificações Não Lidas

Lista as notificações não lidas em ordem decrescente. Ao sair da tela, todas são marcadas como lidas (UPDATE no banco).

### [3] Enviar Notificação a Dentista

Mensagem direta para um dentista vinculado. Insere registro em `tdb_notificacoes` com `canal = 'email'` e `status_envio = 'enviado'`.

### [4] Anotações sobre Dentistas

Submenu para ver ou adicionar anotações (sobre_tipo='dentista'). Anotações são compartilhadas entre todos os colaboradores.

### [5] Gestão de Cadastros

Submenu de CRUD adaptado por cargo (Estagiário sem acesso, Auxiliar/Coordenador/Administrador com privilégios crescentes). Ver tabela de permissões.

### [6] Relatórios *(novo na Sprint 4)*

Submenu com três relatórios SELECT/WHERE e exportação JSON. Ver seção [Relatórios com Filtros](#relatórios-com-filtros-e-exportação-json).

### [7] Alterar Senha

Troca a própria senha. Administrador pode trocar senhas de outros usuários.

### [0] Logout

Retorna ao menu público.

---

## Painel do Dentista

### [1] Ver Meus Pacientes

Ficha de cada paciente vinculado ao dentista logado, com próximo atendimento agendado, último atendimento realizado e indicador de exames pendentes.

### [2] Registrar Atendimento (Fase 1) e [2a] Atualizar Atendimento (Fase 2)

Ciclo em duas fases (pré-atendimento e pós-atendimento) com geração automática de notificação para o colaborador responsável.

### [3] Solicitar Exame / Registrar Resultado

Gerencia exames vinculados a atendimentos. Exames são persistidos como JSON dentro da coluna `tdb_atendimentos.exames`.

### [4] Notificações Não Lidas

Listagem cronológica decrescente das notificações recebidas.

### [5] Enviar Notificação a Paciente

Mensagem direta para qualquer um dos pacientes do dentista.

### [6] Anotações sobre Pacientes

Submenu de ver/adicionar anotações sobre pacientes do dentista. Visível também pelo colaborador responsável.

### [7] Solicitar Alteração de Cadastro de Paciente

Cria registro em `tdb_solicitacoes` com `tipo = 'alteracao_paciente'` para aprovação posterior.

### [8] Alterar Senha

Troca a própria senha.

### [0] Logout

Retorna ao menu público.

---

&nbsp;

---

# CONSUMO DE API EXTERNA — VIACEP

O módulo `modules/api_externa.py` consome o serviço público brasileiro [ViaCEP](https://viacep.com.br), gratuito e sem necessidade de chave de API. A integração é usada no cadastro e na edição de pacientes.

**Fluxo no cadastro de paciente:**

1. O colaborador chega no campo CEP do formulário.
2. Digita o CEP (com ou sem hífen, com ou sem espaços — o sistema normaliza).
3. Pressiona Enter.
4. O sistema chama `buscar_endereco(cep)`, que:
   - Normaliza o CEP para 8 dígitos.
   - Constrói a URL `https://viacep.com.br/ws/{cep}/json/`.
   - Faz a requisição via `urllib.request.urlopen` com timeout de 5 segundos.
   - Parseia o JSON de resposta.
   - Trata `URLError` (rede caiu), `ValueError`/`TimeoutError` (resposta corrompida) e o campo `erro: true` (CEP não encontrado na base).
5. Em sucesso, mostra o endereço encontrado e devolve um dict com `{cep, logradouro, bairro, cidade, uf}` que é mesclado no registro do paciente.
6. Em falha, devolve dict vazio (com strings vazias) e segue o cadastro — o operador pode preencher manualmente.

**Trecho relevante:**

```python
def buscar_endereco(cep: str) -> dict | None:
    normalizado = _normalizar_cep(cep)
    if not normalizado:
        print("  [API] CEP inválido (use 8 dígitos).")
        return None

    url = URL_BASE.format(cep=normalizado)
    try:
        with request.urlopen(url, timeout=TIMEOUT_SEG) as resposta:
            payload = json.loads(resposta.read().decode("utf-8"))
    except error.URLError as exc:
        print(f"  [API] Falha de rede ao consultar ViaCEP: {exc.reason}")
        return None
    except (ValueError, TimeoutError) as exc:
        print(f"  [API] Resposta inválida do ViaCEP: {exc}")
        return None

    if payload.get("erro"):
        print("  [API] CEP não encontrado na base do ViaCEP.")
        return None

    return {
        "cep": payload.get("cep") or _formatar_cep(normalizado),
        "logradouro": payload.get("logradouro") or "",
        "bairro": payload.get("bairro") or "",
        "cidade": payload.get("localidade") or "",
        "uf": payload.get("uf") or "",
    }
```

O ViaCEP foi escolhido por três razões: (a) é mantido por uma empresa brasileira com SLA público e taxa de disponibilidade próxima de 100%; (b) não exige autenticação ou chave de API; (c) cobre 100% dos CEPs do Brasil, com retorno padronizado em JSON.

---

&nbsp;

---

# RELATÓRIOS COM FILTROS E EXPORTAÇÃO JSON

O módulo `modules/relatorios.py` implementa três relatórios baseados em SELECT/WHERE no Oracle, com opção de exportar os resultados em arquivos JSON. O menu fica acessível em **Painel do Colaborador → [6] Relatórios**, com restrição para cargo Auxiliar ou superior.

## Pacientes por dentista (com filtro de UF)

**SQL:**

```sql
SELECT p.id, p.nome, p.cpf, p.data_nasc, p.telefone, p.email,
       p.cidade, p.uf, d.nome AS dentista_nome, d.cro
FROM tdb_pacientes p
INNER JOIN tdb_dentistas d ON d.id = p.id_dentista
WHERE p.id_dentista = :id_dent
  [AND UPPER(p.uf) = :uf]            -- opcional
ORDER BY p.nome
```

**Filtros pedidos ao usuário:** ID do dentista (obrigatório), UF (opcional).
**Use case:** o colaborador quer ver todos os pacientes que estão sob responsabilidade de um determinado dentista, opcionalmente filtrando por UF para uma campanha estadual.

## Atendimentos por status e período

**SQL:**

```sql
SELECT a.id, a.data, a.tipo, a.status, a.observacoes,
       p.nome AS paciente, d.nome AS dentista, c.nome AS campanha
FROM tdb_atendimentos a
INNER JOIN tdb_pacientes p ON p.id = a.id_paciente
INNER JOIN tdb_dentistas d ON d.id = a.id_dentista
LEFT  JOIN tdb_campanhas c ON c.id = a.id_campanha
WHERE a.data BETWEEN :data_inicio AND :data_fim
  [AND a.status = :status]           -- opcional
ORDER BY a.data
```

**Filtros pedidos:** status (1=agendado, 2=realizado, 3=cancelado, 4=todos), data inicial, data final.
**Use case:** relatório mensal de atendimentos da ONG — quantos foram realizados, quantos foram cancelados, e em qual campanha cada um foi feito.

## Notificações a partir de uma data

**SQL:**

```sql
SELECT n.id, n.data_envio, n.canal, n.mensagem,
       c.nome AS colaborador, d.nome AS dentista
FROM tdb_notificacoes n
LEFT JOIN tdb_colaboradores c ON c.id = n.id_colaborador
LEFT JOIN tdb_dentistas    d ON d.id = n.id_dentista
WHERE SUBSTR(n.data_envio, 1, 10) >= :data_inicio
ORDER BY n.data_envio DESC
```

**Filtro:** data inicial.
**Use case:** auditoria das comunicações enviadas pelo sistema a partir de uma data — útil para verificar o histórico de avisos em casos de reclamação ou prestação de contas.

---

## Exportação em JSON

Em qualquer relatório, após exibir os resultados em tela, o sistema pergunta:

```
  Exportar resultado para JSON? (S/N):
```

Se **S**, o helper `_exportar_json` é invocado:

```python
def _exportar_json(dados: list[dict], prefixo: str) -> str:
    os.makedirs(PASTA_EXPORT, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome = f"{prefixo}_{carimbo}.json"
    caminho = os.path.join(PASTA_EXPORT, nome)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2, default=str)
    return caminho
```

O arquivo é gravado em `exports/<prefixo>_<YYYYMMDD_HHMMSS>.json`, com codificação UTF-8 (preserva acentos), `indent=2` (legível) e `default=str` (converte objetos `Date`/`Decimal` automaticamente). O caminho do arquivo gerado é exibido para o usuário.

---

&nbsp;

---

# ESTRUTURAS DE PROGRAMAÇÃO UTILIZADAS

## CRUD sobre Oracle

As operações de Create / Read / Update / Delete continuam expressas no estilo da Sprint 3 — *carrega tudo, modifica em memória, salva tudo* — mas agora são traduzidas em SQL pela camada `storage`:

### Read

```python
def carregar(entidade: str) -> list[dict]:
    schema = SCHEMAS[entidade]
    cols_sql = ", ".join(schema["cols"])
    sql = f"SELECT {cols_sql} FROM {schema['table']} ORDER BY id"
    with database.cursor() as cur:
        cur.execute(sql)
        linhas = cur.fetchall()
    return [_linha_para_dict(l, schema) for l in linhas]
```

### Create + Update + Delete (sincronização)

```python
def salvar(entidade: str, dados: list[dict]) -> None:
    schema = SCHEMAS[entidade]
    with database.cursor() as cur:
        cur.execute(f"SELECT id FROM {schema['table']}")
        ids_existentes = {linha[0] for linha in cur.fetchall()}
        ids_novos = {item["id"] for item in dados}

        for id_removido in ids_existentes - ids_novos:
            cur.execute(sql_delete, {"id": id_removido})

        for item in dados:
            binds = {c: _to_db(c, item.get(c), schema) for c in cols}
            if item["id"] in ids_existentes:
                cur.execute(sql_update, binds)
            else:
                cur.execute(sql_insert, binds)
```

---

## Funções com Parâmetros e Retorno

Toda a lógica continua organizada em funções pequenas, com parâmetros explícitos e valores de retorno tipados:

```python
def buscar_endereco(cep: str) -> dict | None:
    ...

def tem_permissao(colaborador: dict, nivel_minimo: int) -> bool:
    return nivel_colaborador(colaborador) >= nivel_minimo

def _exportar_json(dados: list[dict], prefixo: str) -> str:
    ...
```

---

## Listas e Dicionários

A representação em memória continua sendo listas de dicionários — mesmo após a migração para Oracle. As funções de leitura do banco devolvem as mesmas estruturas que antes vinham de `json.load`:

```python
pacientes = storage.carregar("pacientes")
# Equivalente a Sprint 3, mas agora vem do Oracle:
# [
#   {"id": 1, "nome": "...", "cep": "01310100", "bairro": "Bela Vista", ...},
#   {"id": 2, "nome": "...", "cep": None, "bairro": None, ...},
# ]

# Filtros, ordenação e buscas continuam usando idioms de Python puro
meus = [p for p in pacientes if p["id_dentista"] == dentista["id"]]
alvo = next((p for p in pacientes if p["id"] == uid), None)
```

---

## Validação de Entradas e Tratamento de Exceções

Continuam todas as validações do Sprint 3 (`input_inteiro`, `input_data`, `input_cpf`, `input_cro`, `input_texto`) com `try/except` em torno das conversões. Adicionalmente, na Sprint 4 foi adicionada:

### Captura de erros do banco

```python
# main.py
try:
    if opcao == 1:
        resultado = fazer_login()
        ...
except oracledb.DatabaseError as exc:
    print(f"\n  [ERRO] Falha de banco de dados: {exc}")
    utils.pausar()
```

### Captura de erros de rede na API externa

```python
try:
    with request.urlopen(url, timeout=TIMEOUT_SEG) as resposta:
        payload = json.loads(resposta.read().decode("utf-8"))
except error.URLError as exc:
    print(f"  [API] Falha de rede ao consultar ViaCEP: {exc.reason}")
    return None
except (ValueError, TimeoutError) as exc:
    print(f"  [API] Resposta inválida do ViaCEP: {exc}")
    return None
```

### Transações com rollback automático

```python
@contextmanager
def cursor():
    conexao = conectar()
    cur = conexao.cursor()
    try:
        yield cur
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cur.close()
        conexao.close()
```

---

&nbsp;

---

# ATENDIMENTO AOS REQUISITOS DA RUBRICA

Mapeamento direto entre os requisitos da Sprint 4 (Computational Thinking Using Python) e onde cada um é atendido no código:

| Requisito (pontos) | Onde está atendido |
|---|---|
| **CRUD com inserção, alteração, exclusão e consulta** (15 pts) | `modules/crud.py` (CRUD de Colaborador, Dentista, Paciente, Campanha, Solicitação) + `modules/storage.py.salvar()` que executa INSERT/UPDATE/DELETE no Oracle |
| **Estrutura de menus e submenus para acesso ao CRUD** (5 pts) | `main.py` (menu público) → `modules/painel_colaborador.py` e `modules/painel_dentista.py` (menus de cada perfil) → submenus em `crud.py` (gerenciar dentistas, pacientes, colaboradores, solicitações) |
| **Validações de entrada e tratamento de exceções com try/except** (10 pts) | `modules/utils.py` (input_inteiro, input_data, input_cpf, input_cro com loops + try/except) + `main.py` (captura `oracledb.DatabaseError`) + `relatorios.py` (idem) + `api_externa.py` (captura `URLError`, `ValueError`, `TimeoutError`) |
| **Pelo menos 2 consultas no banco com filtros (SELECT/WHERE) + exportação JSON** (15 pts) | `modules/relatorios.py` — **3 relatórios** com SELECT/WHERE, opção `S/N` para exportar resultado em `exports/<nome>_<timestamp>.json` |
| **Consumo de uma API externa pública** (10 pts) | `modules/api_externa.py` — cliente HTTPS para [ViaCEP](https://viacep.com.br), integrado ao cadastro/edição de paciente em `crud.py` |
| **Organizar o código fonte em funções** (5 pts) | Todo o código está em funções com parâmetros nomeados, type hints e retorno tipado — `auth.py`, `crud.py`, `storage.py`, `utils.py`, `relatorios.py`, `api_externa.py` |
| **Usabilidade e boas práticas** (10 pts) | Cabeçalhos consistentes (`utils.cabecalho`), confirmações (`utils.confirmar`), getpass para senhas, mensagens de erro amigáveis, separação clara entre camadas, type hints, encapsulamento da conexão Oracle em context manager |

**Entregáveis adicionais:**
- `Oracle_Scripts.sql` e `Scripts_Oracle.txt` — scripts DDL para criar as tabelas no Oracle (atende ao item "Arquivo TXT com scripts necessários para criação das tabelas em banco de dados Oracle" da entrega).
- `sprint-4.txt` — Nomes e RMs dos integrantes + link do vídeo no YouTube.

---

&nbsp;

---

# COMO EXECUTAR

## Pré-requisitos

- **Python 3.9** ou superior
- **Biblioteca `oracledb`** — instalável via `pip`
- **Acesso ao banco da FIAP** — você precisa estar conectado à rede interna ou à VPN para que o host `oracle.fiap.com.br` seja alcançável

## Passo a Passo

### 1. Instalar dependências

```bash
cd "Python - Sprint 4"
pip install -r requirements.txt
```

`requirements.txt` contém apenas:
```
oracledb>=2.0.0
```

### 2. Conectar à rede da FIAP

Verifique que `oracle.fiap.com.br` é alcançável:

```bash
ping -c 2 oracle.fiap.com.br
```

Se você está fora do campus, conecte-se à **VPN da FIAP** antes de prosseguir.

### 3. Criar as tabelas no Oracle

Execute o script de setup uma única vez:

```bash
python3 _setup_db.py
```

Saída esperada (resumida):
```
Parsed 28 statements de Oracle_Scripts.sql

  [01] OK     BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_atendimentos...
  [02] OK     BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_notificacoes...
  ...
  [17] OK     CREATE TABLE tdb_colaboradores
  ...
  [25] OK     CREATE SEQUENCE seq_tdb_colaboradores
  ...

Resumo: 28 sucesso(s), 0 falha(s).
```

> **Importante:** o script `Oracle_Scripts.sql` é **idempotente** — ele começa fazendo `DROP TABLE ... CASCADE CONSTRAINTS` para todas as tabelas, então pode ser rodado quantas vezes for necessário sem deixar lixo no banco. Atenção: rodar de novo **apaga todos os dados** existentes.

### 4. Rodar a aplicação

```bash
python3 main.py
```

Na primeira execução, o sistema confirma a conexão com o banco e insere o usuário `ADMIN` em `tdb_colaboradores` se ele ainda não existir.

## Credenciais Iniciais

| Campo | Valor |
|---|---|
| Usuário | `ADMIN` |
| Senha | `ADMIN` |

> Recomenda-se alterar a senha do administrador no primeiro acesso pelo menu **Alterar Senha** do painel do colaborador.

## Fluxo Recomendado para Demonstração

1. **Login** com `ADMIN / ADMIN`.
2. **Gestão de Cadastros → Gerenciar Colaboradores** → cadastrar um Coordenador.
3. **Gestão de Cadastros → Gerenciar Dentistas** → cadastrar um dentista vinculado ao colaborador.
4. **Gestão de Cadastros → Gerenciar Pacientes** → cadastrar um paciente; quando o sistema pedir o CEP, digite `01310-100` (Av. Paulista — Bela Vista) e observe o ViaCEP preencher logradouro, bairro, cidade e UF automaticamente.
5. **Logout** e fazer login com o dentista recém-criado.
6. **Registrar Atendimento** para o paciente criado — verifique a notificação automática gerada para o colaborador.
7. **Logout** e voltar para o colaborador.
8. **Notificações Não Lidas** — confirmar a notificação do dentista.
9. **Relatórios** → escolher *"Atendimentos por status e período"* → filtros amplos → quando o resultado aparecer, escolher **S** na pergunta de exportação. Verifique o arquivo gerado em `exports/`.

---

&nbsp;

---

# CONCLUSÃO

A Sprint 4 conclui o ciclo do projeto Python ao integrar o sistema CLI com um banco de dados real (Oracle), uma API externa pública (ViaCEP) e relatórios operacionais com exportação em formato consumível por outras ferramentas (JSON).

Do ponto de vista técnico, a migração de JSON para Oracle foi feita preservando o contrato do `storage.py` — o que evidencia o valor de uma **API estável entre camadas**: nenhum módulo de negócio (`crud.py`, painéis, `auth.py`) precisou ser alterado. A complexidade do banco fica encapsulada em três arquivos novos (`database.py`, `_setup_db.py`, `Oracle_Scripts.sql`) e na reescrita interna de `storage.py`. Este é um padrão de design que se replica em sistemas reais quando uma equipe troca o ORM, o tipo de banco ou o provedor de cache.

O consumo da API ViaCEP demonstra como integrar serviços públicos com a biblioteca padrão da linguagem (sem dependências adicionais), e como tratar de forma robusta as três classes de falha que toda chamada de rede pode ter: indisponibilidade, resposta corrompida e resposta semântica de erro (CEP inexistente).

Os relatórios atendem ao requisito acadêmico e também a uma necessidade real da ONG: prestação de contas, auditoria de comunicações e relatórios mensais de atendimento. A exportação em JSON converte o sistema em **fornecedor de dados** para outras ferramentas — pode alimentar planilhas, BI ou os outros componentes da arquitetura do projeto (back-end Java, front-end web, ML preditivo).

Em conjunto, a Sprint 4 fecha o protótipo Python como demonstração completa dos pilares da disciplina: estruturas de dados, controle de fluxo, validação, modularização, persistência relacional, integração externa e geração de relatórios — todos exercidos sobre um problema real, com regras de negócio coerentes.

&nbsp;

---

> *O privilégio de poder mudar vidas, a compaixão como valor.*
> *A tecnologia para impulsionar — isso é Turma do Bem, isso é Tech do Bem.*

---
