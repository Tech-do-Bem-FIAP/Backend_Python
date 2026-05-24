-- ═══════════════════════════════════════════════════════════════════
-- Tech do Bem — Sistema de Gestão Odontológica
-- Sprint 4 | Computational Thinking Using Python | FIAP 1TDSPR
--
-- RM568542 - Hugo Souza de Jesus
-- RM566815 - Lucas Campanhã dos Santos
-- RM567010 - Lucas Marcelino Pompeu
-- ═══════════════════════════════════════════════════════════════════


-- ─── Apagando sequências e tabelas anteriores (idempotente) ─────────
-- Os blocos PL/SQL evitam erros caso o objeto ainda não exista.

BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_atendimentos  CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_notificacoes  CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_anotacoes     CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_solicitacoes  CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_pacientes     CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_campanhas     CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_dentistas     CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE tdb_colaboradores CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_colaboradores'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_dentistas';     EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_pacientes';     EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_campanhas';     EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_atendimentos';  EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_notificacoes';  EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_anotacoes';     EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE seq_tdb_solicitacoes';  EXCEPTION WHEN OTHERS THEN NULL; END;
/


-- ─── Criando as tabelas ─────────────────────────────────────────────

CREATE TABLE tdb_colaboradores (
    id              NUMBER(10)    NOT NULL,
    nome            VARCHAR2(100) NOT NULL,
    cpf             VARCHAR2(14),
    email           VARCHAR2(100) NOT NULL,
    senha           VARCHAR2(100) NOT NULL,
    cargo           VARCHAR2(30)  NOT NULL,
    disponibilidade NUMBER(1)     DEFAULT 1 NOT NULL,
    CONSTRAINT pk_tdb_colaboradores      PRIMARY KEY (id),
    CONSTRAINT uk_tdb_colaboradores_mail UNIQUE (email),
    CONSTRAINT ck_tdb_colab_cargo        CHECK (cargo IN ('Estagiário', 'Auxiliar', 'Coordenador', 'Administrador')),
    CONSTRAINT ck_tdb_colab_disp         CHECK (disponibilidade IN (0, 1))
);

CREATE TABLE tdb_dentistas (
    id              NUMBER(10)    NOT NULL,
    nome            VARCHAR2(100) NOT NULL,
    cpf             VARCHAR2(14),
    email           VARCHAR2(100) NOT NULL,
    senha           VARCHAR2(100) NOT NULL,
    cro             VARCHAR2(10)  NOT NULL,
    especialidade   VARCHAR2(100),
    disponibilidade NUMBER(1)     DEFAULT 1 NOT NULL,
    id_colaborador  NUMBER(10),
    CONSTRAINT pk_tdb_dentistas       PRIMARY KEY (id),
    CONSTRAINT uk_tdb_dentistas_mail  UNIQUE (email),
    CONSTRAINT uk_tdb_dentistas_cro   UNIQUE (cro),
    CONSTRAINT fk_tdb_dent_colab      FOREIGN KEY (id_colaborador) REFERENCES tdb_colaboradores (id),
    CONSTRAINT ck_tdb_dent_disp       CHECK (disponibilidade IN (0, 1))
);

CREATE TABLE tdb_pacientes (
    id           NUMBER(10)    NOT NULL,
    nome         VARCHAR2(100) NOT NULL,
    cpf          VARCHAR2(14),
    data_nasc    VARCHAR2(10),
    telefone     VARCHAR2(20),
    email        VARCHAR2(100),
    id_dentista  NUMBER(10),
    cep          VARCHAR2(9),
    logradouro   VARCHAR2(200),
    bairro       VARCHAR2(100),
    cidade       VARCHAR2(100),
    uf           VARCHAR2(2),
    CONSTRAINT pk_tdb_pacientes  PRIMARY KEY (id),
    CONSTRAINT fk_tdb_pac_dent   FOREIGN KEY (id_dentista) REFERENCES tdb_dentistas (id)
);

CREATE TABLE tdb_campanhas (
    id              NUMBER(10)    NOT NULL,
    nome            VARCHAR2(100) NOT NULL,
    local           VARCHAR2(200) NOT NULL,
    data_inicio     VARCHAR2(10)  NOT NULL,
    data_fim        VARCHAR2(10)  NOT NULL,
    id_colaborador  NUMBER(10),
    CONSTRAINT pk_tdb_campanhas  PRIMARY KEY (id),
    CONSTRAINT fk_tdb_camp_colab FOREIGN KEY (id_colaborador) REFERENCES tdb_colaboradores (id),
    CONSTRAINT ck_tdb_camp_datas CHECK (data_fim >= data_inicio)
);

CREATE TABLE tdb_atendimentos (
    id            NUMBER(10)    NOT NULL,
    id_paciente   NUMBER(10)    NOT NULL,
    id_dentista   NUMBER(10)    NOT NULL,
    id_campanha   NUMBER(10),
    data          VARCHAR2(10)  NOT NULL,
    tipo          VARCHAR2(40)  NOT NULL,
    status        VARCHAR2(20)  NOT NULL,
    observacoes   VARCHAR2(1000),
    exames        VARCHAR2(4000),
    CONSTRAINT pk_tdb_atendimentos PRIMARY KEY (id),
    CONSTRAINT fk_tdb_atend_pac    FOREIGN KEY (id_paciente) REFERENCES tdb_pacientes (id),
    CONSTRAINT fk_tdb_atend_dent   FOREIGN KEY (id_dentista) REFERENCES tdb_dentistas (id),
    CONSTRAINT fk_tdb_atend_camp   FOREIGN KEY (id_campanha) REFERENCES tdb_campanhas (id),
    CONSTRAINT ck_tdb_atend_status CHECK (status IN ('agendado', 'realizado', 'cancelado'))
);

CREATE TABLE tdb_notificacoes (
    id             NUMBER(10)    NOT NULL,
    mensagem       VARCHAR2(1000) NOT NULL,
    data_envio     VARCHAR2(20)   NOT NULL,
    status_envio   VARCHAR2(20)   NOT NULL,
    canal          VARCHAR2(20)   NOT NULL,
    id_colaborador NUMBER(10),
    id_dentista    NUMBER(10),
    CONSTRAINT pk_tdb_notificacoes  PRIMARY KEY (id),
    CONSTRAINT fk_tdb_notif_colab   FOREIGN KEY (id_colaborador) REFERENCES tdb_colaboradores (id),
    CONSTRAINT fk_tdb_notif_dent    FOREIGN KEY (id_dentista)    REFERENCES tdb_dentistas (id),
    CONSTRAINT ck_tdb_notif_canal   CHECK (canal IN ('email', 'sms', 'push'))
);

CREATE TABLE tdb_anotacoes (
    id          NUMBER(10)     NOT NULL,
    texto       VARCHAR2(1000) NOT NULL,
    data        VARCHAR2(20)   NOT NULL,
    autor_id    NUMBER(10)     NOT NULL,
    autor_tipo  VARCHAR2(20)   NOT NULL,
    sobre_id    NUMBER(10)     NOT NULL,
    sobre_tipo  VARCHAR2(20)   NOT NULL,
    CONSTRAINT pk_tdb_anotacoes      PRIMARY KEY (id),
    CONSTRAINT ck_tdb_anot_autortipo CHECK (autor_tipo IN ('colaborador', 'dentista')),
    CONSTRAINT ck_tdb_anot_sobretipo CHECK (sobre_tipo IN ('paciente', 'dentista'))
);

CREATE TABLE tdb_solicitacoes (
    id       NUMBER(10)   NOT NULL,
    tipo     VARCHAR2(30)   NOT NULL,
    dados    VARCHAR2(4000) NOT NULL,
    status   VARCHAR2(20) NOT NULL,
    data     VARCHAR2(20) NOT NULL,
    CONSTRAINT pk_tdb_solicitacoes  PRIMARY KEY (id),
    CONSTRAINT ck_tdb_sol_status    CHECK (status IN ('pendente', 'aprovado', 'recusado')),
    CONSTRAINT ck_tdb_sol_tipo      CHECK (tipo   IN ('dentista', 'colaborador', 'alteracao_paciente'))
);


-- ─── Criando as sequências (geração de IDs) ─────────────────────────

CREATE SEQUENCE seq_tdb_colaboradores START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_dentistas     START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_pacientes     START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_campanhas     START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_atendimentos  START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_notificacoes  START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_anotacoes     START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE seq_tdb_solicitacoes  START WITH 1 INCREMENT BY 1 NOCACHE;

COMMIT;
