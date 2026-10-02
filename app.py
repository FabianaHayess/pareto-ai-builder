
import streamlit as st
import json
import uuid
from datetime import datetime
from jsonschema import Draft202012Validator, FormatChecker


# =========================================================
# CONFIGURAÇÃO
# =========================================================

st.set_page_config(
    page_title="Vitalis | Central de Negociações",
    page_icon="💊",
    layout="wide"
)


# =========================================================
# CARREGAMENTO
# =========================================================

with open("resultados_processados.json", "r", encoding="utf-8") as arquivo:
    resultados = json.load(arquivo)

with open("condicao_post.schema.json", "r", encoding="utf-8") as arquivo:
    schema_erp = json.load(arquivo)


# =========================================================
# METADADOS DOS E-MAILS
# =========================================================

emails = {
    "ALFA": {
        "hora": "09:12",
        "assunto": "Campanha Fim de Ano - Genéricos Alfa",
        "resumo_status": "Evidência do Trade Marketing necessária"
    },
    "GAMA": {
        "hora": "16:40",
        "assunto": "Condições comerciais Q4",
        "resumo_status": "Divergência entre e-mail e anexo"
    },
    "BETA": {
        "hora": "10:05",
        "assunto": "Condição comercial HPC",
        "resumo_status": "Conflito com condição vigente no ERP"
    },
    "NUTRIVIDA": {
        "hora": "18:30",
        "assunto": "Renovação de condição comercial",
        "resumo_status": "Fornecedor inativo no ERP"
    }
}


# =========================================================
# FUNÇÕES
# =========================================================

def status_visual(status):
    if status == "BLOQUEADO":
        return "🔴 Bloqueado"
    if status == "REVISAO_HUMANA":
        return "🟠 Revisão necessária"
    if status == "PRONTO_PARA_APROVACAO":
        return "🟢 Pronto para aprovação"
    return status.replace("_", " ").title()


def nome_amigavel(texto):
    if not texto:
        return ""

    traducoes = {
        "DESCONTO_PERCENTUAL": "Desconto percentual",
        "VERBA_EXPOSICAO": "Verba de exposição",
        "politica_desconto": "Política de desconto",
        "politica_verba": "Política de verba",
        "sobreposicao_erp": "Sobreposição no ERP",
        "fornecedor": "Fornecedor",
        "documento": "Documento",
        "SOBREPOSICAO_CONDICAO_VIGENTE": "Condição vigente encontrada",
        "EVIDENCIA_TRADE_MARKETING_NECESSARIA":
            "Evidência do Trade Marketing necessária",
        "FORNECEDOR_INATIVO": "Fornecedor inativo",
        "CAMPO_AUSENTE": "Campo ausente",
        "DIVERGENCIA_ENTRE_FONTES": "Divergência entre fontes",
        "GERENCIA_COMERCIAL": "Gerência Comercial",
        "DIRETORIA_COMERCIAL": "Diretoria Comercial"
    }

    return traducoes.get(
        texto,
        texto.replace("_", " ").title()
    )


def validar_payload_erp(payload):
    validator = Draft202012Validator(
        schema_erp,
        format_checker=FormatChecker()
    )

    erros = sorted(
        validator.iter_errors(payload),
        key=lambda erro: list(erro.path)
    )

    mensagens = []

    for erro in erros:
        caminho = ".".join(str(item) for item in erro.path)

        if caminho:
            mensagens.append(f"{caminho}: {erro.message}")
        else:
            mensagens.append(erro.message)

    return {
        "valido": len(mensagens) == 0,
        "erros": mensagens
    }


def simular_post_erp(payload, idempotency_key):
    return {
        "http_status": 201,
        "resultado": "CREATED",
        "mensagem": "Condição cadastrada no ERP simulado.",
        "idempotency_key": idempotency_key,
        "cod_condicao": "COND-DEMO-001",
        "recebido_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payload": payload
    }


# =========================================================
# SESSION STATE
# =========================================================

if "payload_beta" not in st.session_state:
    st.session_state.payload_beta = None

if "idempotency_beta" not in st.session_state:
    st.session_state.idempotency_beta = None

if "resultado_erp_beta" not in st.session_state:
    st.session_state.resultado_erp_beta = None

if "beta_corrigida" not in st.session_state:
    st.session_state.beta_corrigida = None


# =========================================================
# CABEÇALHO
# =========================================================

st.title("💊 Vitalis")
st.markdown("## Central de Negociações Comerciais")

st.caption(
    "Propostas recebidas por e-mail, interpretadas por IA "
    "e verificadas automaticamente antes da decisão comercial."
)

st.divider()


# =========================================================
# INDICADORES
# =========================================================

total = len(resultados)

revisao = sum(
    1 for p in resultados.values()
    if p["status_final"] == "REVISAO_HUMANA"
)

bloqueados = sum(
    1 for p in resultados.values()
    if p["status_final"] == "BLOQUEADO"
)

prontos = sum(
    1 for p in resultados.values()
    if p["status_final"] == "PRONTO_PARA_APROVACAO"
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Recebidas", total)
c2.metric("Revisão necessária", revisao)
c3.metric("Bloqueadas", bloqueados)
c4.metric("Prontas para aprovação", prontos)

st.divider()


# =========================================================
# CAIXA DE ENTRADA
# =========================================================

st.markdown("## 📥 Caixa de entrada")

st.caption(
    "As propostas são processadas automaticamente após o recebimento."
)

casos = list(resultados.keys())

caso = st.radio(
    "Selecione uma negociação",
    casos,
    horizontal=True,
    label_visibility="collapsed"
)

for nome in casos:

    p = resultados[nome]
    e = emails[nome]

    with st.container(border=True):

        col_hora, col_email, col_status = st.columns([1, 5, 3])

        with col_hora:
            st.markdown(f"**{e['hora']}**")

        with col_email:
            st.markdown(f"**{p['extracao']['fornecedor']}**")
            st.write(e["assunto"])

        with col_status:
            st.markdown(f"**{status_visual(p['status_final'])}**")
            st.caption(e["resumo_status"])

st.divider()


# =========================================================
# NEGOCIAÇÃO
# =========================================================

proposta = resultados[caso]
extracao = proposta["extracao"]
email = emails[caso]

st.markdown(f"## 📄 Análise da negociação — {caso}")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown(f"**Fornecedor:** {extracao['fornecedor']}")
    st.markdown(f"**Assunto:** {email['assunto']}")

with col2:
    st.markdown(f"### {status_visual(proposta['status_final'])}")

st.divider()


# =========================================================
# 1. INTERPRETAÇÃO DA IA
# =========================================================

st.markdown("### 🤖 1. Interpretação da IA")

st.caption(
    "O agente transforma o conteúdo não estruturado em dados. "
    "A origem de cada informação permanece visível para revisão."
)


# =========================================================
# PROVENIÊNCIA / CONFIABILIDADE
# =========================================================

if caso == "BETA":

    condicao_original = extracao["condicoes"][0]

    st.markdown("#### Evidências da extração")

    dados_evidencia = [
        ("Fornecedor", "Distribuidora Beta", "🟢 Explícito no e-mail"),
        ("Categoria recebida", "HPC", "🟢 Explícito no e-mail"),
        (
            "Categoria ERP",
            "HIGIENE_BELEZA",
            "🔵 Normalizado pelo sistema"
        ),
        (
            "Desconto",
            f"{condicao_original['percentual']}%",
            "🟢 Explícito no e-mail"
        ),
        (
            "Lojas recebidas",
            "Tijuca, Méier, Botafogo",
            "🟢 Explícito no e-mail"
        ),
        (
            "Códigos ERP",
            "LOJA-104, LOJA-107, LOJA-112",
            "🔵 Validados no ERP"
        ),
        (
            "Data inicial",
            condicao_original["data_inicio"],
            "🟢 Explícito no e-mail"
        ),
        (
            "Data final",
            condicao_original["data_fim"],
            "🟢 Explícito no e-mail"
        )
    ]

    for campo, valor, origem in dados_evidencia:

        c1, c2, c3 = st.columns([2, 3, 3])

        with c1:
            st.write(f"**{campo}**")

        with c2:
            st.write(valor)

        with c3:
            st.caption(origem)


    st.caption(
        "🟢 Informação explicitamente presente na fonte  •  "
        "🔵 Informação normalizada ou confirmada por sistema  •  "
        "🟠 Inferência que exige confirmação  •  "
        "🔴 Informação ausente ou conflitante"
    )

else:

    st.write(
        "**Categoria identificada:**",
        extracao.get("categoria") or "Não identificada"
    )


# =========================================================
# CONDIÇÕES
# =========================================================

st.markdown("#### Condições identificadas")

for numero, condicao in enumerate(
    extracao.get("condicoes", []),
    start=1
):

    with st.container(border=True):

        st.markdown(
            f"**Condição {numero} — "
            f"{nome_amigavel(condicao.get('tipo'))}**"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            if condicao.get("percentual") is not None:
                st.metric(
                    "Desconto",
                    f"{condicao['percentual']}%"
                )

            if condicao.get("valor") is not None:
                st.metric(
                    "Valor",
                    f"R$ {condicao['valor']:,.2f}"
                )

        with c2:

            st.write("**Data inicial**")
            st.write(
                condicao.get("data_inicio")
                or "Não informada"
            )

            st.write("**Data final**")
            st.write(
                condicao.get("data_fim")
                or "Não informada"
            )

        with c3:

            st.write("**Lojas**")

            lojas = condicao.get("lojas", [])

            st.write(
                ", ".join(lojas)
                if lojas
                else "Não informadas"
            )

        if condicao.get("contrapartida"):

            st.info(
                "Contrapartida: "
                + condicao["contrapartida"]
            )


# =========================================================
# GAMA — EVIDÊNCIA DE CONFLITO
# =========================================================

if caso == "GAMA":

    st.markdown("#### Evidências que exigem revisão")

    st.warning(
        "Desconto: o e-mail informa 12%, "
        "enquanto o anexo informa 12,5%."
    )

    st.error(
        "Data final: não informada nas fontes."
    )

    st.caption(
        "O sistema não escolhe automaticamente qual percentual "
        "deve prevalecer."
    )


# =========================================================
# ALFA — EVIDÊNCIA
# =========================================================

if caso == "ALFA":

    st.markdown("#### Evidência pendente")

    st.warning(
        "O desconto de 28% depende de aprovação de campanha "
        "sazonal pelo Trade Marketing. Essa aprovação não está "
        "comprovada nas fontes recebidas."
    )


# =========================================================
# NUTRIVIDA — SEGURANÇA
# =========================================================

if caso == "NUTRIVIDA":

    st.markdown("#### Tratamento seguro do documento")

    st.info(
        "O conteúdo do e-mail foi tratado como dado não confiável. "
        "Instruções encontradas dentro do documento não têm "
        "autoridade para aprovar condições ou alterar regras."
    )


# =========================================================
# CORREÇÃO HUMANA — BETA
# =========================================================

if caso == "BETA":

    st.markdown("### ✏️ Conferir ou corrigir dados")

    st.caption(
        "O responsável pode corrigir a interpretação antes "
        "de qualquer decisão ou envio ao ERP."
    )

    condicao_base = extracao["condicoes"][0]

    if st.session_state.beta_corrigida:
        valores = st.session_state.beta_corrigida
    else:
        valores = {
            "percentual": condicao_base["percentual"],
            "data_inicio": condicao_base["data_inicio"],
            "data_fim": condicao_base["data_fim"],
            "contrapartida": condicao_base["contrapartida"]
        }

    with st.expander("Corrigir dados extraídos"):

        percentual_editado = st.number_input(
            "Desconto (%)",
            min_value=0.01,
            max_value=100.0,
            value=float(valores["percentual"]),
            step=0.5
        )

        data_inicio_editada = st.text_input(
            "Data inicial",
            value=valores["data_inicio"]
        )

        data_fim_editada = st.text_input(
            "Data final",
            value=valores["data_fim"]
        )

        contrapartida_editada = st.text_area(
            "Contrapartida",
            value=valores["contrapartida"]
        )

        if st.button("Salvar correções"):

            st.session_state.beta_corrigida = {
                "percentual": percentual_editado,
                "data_inicio": data_inicio_editada,
                "data_fim": data_fim_editada,
                "contrapartida": contrapartida_editada
            }

            # Qualquer alteração invalida um payload preparado antes.
            st.session_state.payload_beta = None
            st.session_state.idempotency_beta = None
            st.session_state.resultado_erp_beta = None

            st.success(
                "Correções salvas. As validações devem ser "
                "consideradas novamente antes da aprovação."
            )


# =========================================================
# PENDÊNCIAS DOCUMENTAIS
# =========================================================

if extracao.get("campos_ausentes"):

    for campo in extracao["campos_ausentes"]:

        st.warning(
            "Campo não informado: "
            + nome_amigavel(campo)
        )


if extracao.get("divergencias"):

    for divergencia in extracao["divergencias"]:

        st.warning(divergencia)


# =========================================================
# 2. VERIFICAÇÕES
# =========================================================

st.markdown("### 🛡️ 2. Verificações automáticas")

st.caption(
    "Política comercial e dados do ERP são verificados "
    "por regras determinísticas, não pelo agente."
)


for nome, verificacao in proposta["verificacoes"].items():

    if not isinstance(verificacao, dict):
        continue

    status = verificacao.get("status")

    with st.container(border=True):

        st.markdown(
            f"#### {nome_amigavel(nome)}"
        )

        if status in ["OK", "DENTRO_DA_POLITICA"]:
            st.success("Verificação concluída")

        elif status == "BLOQUEADO":
            st.error("Bloqueio encontrado")

        else:
            st.warning("Revisão humana necessária")

        if verificacao.get("motivo"):

            st.write(
                "**Motivo:**",
                nome_amigavel(verificacao["motivo"])
            )

        if verificacao.get("mensagem"):
            st.write(verificacao["mensagem"])

        if verificacao.get("detalhe"):
            st.error(verificacao["detalhe"])

        if verificacao.get("alcada"):

            st.write(
                "**Alçada necessária:**",
                nome_amigavel(verificacao["alcada"])
            )

        if verificacao.get("condicoes_conflitantes"):

            st.write(
                "**Condição existente no ERP:**",
                ", ".join(
                    verificacao["condicoes_conflitantes"]
                )
            )

        for problema in verificacao.get("problemas", []):

            st.warning(
                nome_amigavel(
                    problema.get("tipo")
                )
            )

            for detalhe in problema.get("detalhes", []):
                st.write("• " + str(detalhe))


# =========================================================
# AVISO SOBRE CORREÇÕES
# =========================================================

if caso == "BETA" and st.session_state.beta_corrigida:

    corrigida = st.session_state.beta_corrigida

    st.info(
        "Dados considerados na decisão: "
        f"{corrigida['percentual']}% | "
        f"{corrigida['data_inicio']} a "
        f"{corrigida['data_fim']}."
    )

    # Revalidação simples do teto da categoria
    if corrigida["percentual"] > 20:

        st.error(
            "A correção alterou o desconto para um valor "
            "acima do teto de 20% de Higiene e Beleza. "
            "A negociação não pode seguir neste fluxo."
        )

        beta_pode_seguir = False

    else:

        st.success(
            "Desconto corrigido permanece dentro do teto "
            "de 20% da categoria."
        )

        beta_pode_seguir = True

else:

    beta_pode_seguir = True


# =========================================================
# 3. DECISÃO COMERCIAL
# =========================================================

st.markdown("### 👤 3. Decisão comercial")

status_final = proposta["status_final"]


# =========================================================
# BLOQUEADO
# =========================================================

if status_final == "BLOQUEADO":

    st.error(
        "Esta negociação possui um bloqueio impeditivo "
        "e não pode seguir para cadastro no ERP."
    )

    st.button(
        "Aprovar negociação",
        disabled=True,
        use_container_width=True
    )


# =========================================================
# BETA
# =========================================================

elif caso == "BETA":

    st.warning(
        "Existe uma condição vigente para o mesmo fornecedor, "
        "categoria, lojas e período."
    )

    st.markdown(
        "#### Condição atualmente cadastrada no ERP"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Condição", "COND-003")
    c2.metric("Desconto atual", "11%")
    c3.metric("Vigência até", "31/12/2026")

    st.markdown(
        "#### Como deseja tratar a nova proposta?"
    )

    decisao_beta = st.radio(
        "Decisão",
        [
            "Solicitar correção ao fornecedor",
            "Rejeitar a nova proposta",
            "Substituir COND-003 pela nova condição"
        ],
        label_visibility="collapsed"
    )


    # -----------------------------------------------------
    # SUBSTITUIR
    # -----------------------------------------------------

    if decisao_beta == (
        "Substituir COND-003 pela nova condição"
    ):

        if st.session_state.beta_corrigida:

            dados_beta = st.session_state.beta_corrigida

        else:

            dados_beta = {
                "percentual":
                    extracao["condicoes"][0]["percentual"],

                "data_inicio":
                    extracao["condicoes"][0]["data_inicio"],

                "data_fim":
                    extracao["condicoes"][0]["data_fim"],

                "contrapartida":
                    extracao["condicoes"][0]["contrapartida"]
            }


        st.info(
            f"A nova condição de {dados_beta['percentual']}% "
            "substituirá explicitamente a COND-003."
        )


        st.markdown(
            "#### Identificação do aprovador"
        )

        col_nome, col_matricula = st.columns(2)

        with col_nome:

            nome_aprovador = st.text_input(
                "Nome do aprovador",
                placeholder="Ex.: Maria Silva"
            )

        with col_matricula:

            matricula_aprovador = st.text_input(
                "Matrícula",
                placeholder="Ex.: MAT-1025"
            )


        observacao = st.text_area(
            "Justificativa / observação",
            placeholder=(
                "Registre a justificativa da decisão."
            )
        )


        confirmar = st.checkbox(
            "Confirmo a substituição da COND-003."
        )


        dados_preenchidos = (
            bool(nome_aprovador.strip())
            and
            bool(matricula_aprovador.strip())
            and
            confirmar
            and
            beta_pode_seguir
        )


        if st.button(
            "Aprovar e preparar cadastro no ERP",
            type="primary",
            disabled=not dados_preenchidos,
            use_container_width=True
        ):

            payload_beta = {
                "cod_fornecedor": "FORN-002",
                "cod_categoria": "HIGIENE_BELEZA",
                "tipo": "DESCONTO_PERCENTUAL",

                "lojas": [
                    "LOJA-104",
                    "LOJA-107",
                    "LOJA-112"
                ],

                "percentual":
                    dados_beta["percentual"],

                "data_inicio":
                    dados_beta["data_inicio"],

                "data_fim":
                    dados_beta["data_fim"],

                "contrapartida":
                    dados_beta["contrapartida"],

                "cod_condicao_substituida":
                    "COND-003",

                "aprovador": {
                    "matricula":
                        matricula_aprovador.strip(),

                    "nome":
                        nome_aprovador.strip()
                },

                "origem": {
                    "tipo": "EMAIL",
                    "referencia": extracao["fonte"]
                }
            }


            resultado_validacao = validar_payload_erp(
                payload_beta
            )


            if resultado_validacao["valido"]:

                st.session_state.payload_beta = payload_beta

                st.session_state.idempotency_beta = str(
                    uuid.uuid4()
                )

                st.success(
                    "Aprovação registrada. "
                    "Payload validado contra o contrato do ERP."
                )

            else:

                st.error(
                    "O payload não passou pela validação "
                    "do contrato do ERP."
                )

                for erro in resultado_validacao["erros"]:
                    st.write("• " + erro)


        # -------------------------------------------------
        # ETAPA 4
        # -------------------------------------------------

        if st.session_state.payload_beta is not None:

            st.markdown("### 📦 4. Cadastro no ERP")

            st.success(
                "Payload validado pelo JSON Schema."
            )

            st.write("**Idempotency-Key:**")

            st.code(
                st.session_state.idempotency_beta
            )


            with st.expander(
                "Visualizar payload que será enviado"
            ):

                st.json(
                    st.session_state.payload_beta
                )


            st.warning(
                "Integração ERP simulada. "
                "Em produção, esta etapa executaria "
                "POST /condicoes no integrador do ERP."
            )


            if st.button(
                "Enviar ao ERP simulado",
                type="primary",
                use_container_width=True
            ):

                st.session_state.resultado_erp_beta = (
                    simular_post_erp(
                        st.session_state.payload_beta,
                        st.session_state.idempotency_beta
                    )
                )


        # -------------------------------------------------
        # SUCESSO / AUDITORIA
        # -------------------------------------------------

        if st.session_state.resultado_erp_beta is not None:

            resposta = st.session_state.resultado_erp_beta

            st.success(
                "✅ 201 Created — cadastro concluído "
                "no ERP simulado."
            )

            c1, c2 = st.columns(2)

            c1.metric(
                "Nova condição",
                resposta["cod_condicao"]
            )

            c2.metric(
                "HTTP",
                resposta["http_status"]
            )


            st.markdown(
                "#### 🧾 Registro de auditoria"
            )

            auditoria = {
                "acao": "SUBSTITUICAO_CONDICAO",
                "condicao_substituida": "COND-003",
                "nova_condicao": resposta["cod_condicao"],
                "aprovador":
                    st.session_state.payload_beta["aprovador"],
                "origem":
                    st.session_state.payload_beta["origem"],
                "idempotency_key":
                    resposta["idempotency_key"],
                "data_hora":
                    resposta["recebido_em"]
            }

            st.json(auditoria)


    # -----------------------------------------------------
    # SOLICITAR CORREÇÃO
    # -----------------------------------------------------

    elif decisao_beta == (
        "Solicitar correção ao fornecedor"
    ):

        motivo = st.text_area(
            "Motivo da solicitação"
        )

        if st.button(
            "Registrar solicitação de correção",
            use_container_width=True
        ):

            st.success(
                "Solicitação registrada. "
                "Nenhum dado foi enviado ao ERP."
            )


    # -----------------------------------------------------
    # REJEITAR
    # -----------------------------------------------------

    else:

        motivo = st.text_area(
            "Motivo da rejeição"
        )

        if st.button(
            "Registrar rejeição",
            use_container_width=True
        ):

            st.success(
                "Rejeição registrada. "
                "Nenhum dado foi enviado ao ERP."
            )


# =========================================================
# OUTROS CASOS
# =========================================================

else:

    st.warning(
        "Existem pendências que precisam ser resolvidas "
        "antes que esta negociação possa ser aprovada."
    )

    observacao = st.text_area(
        "Observação do responsável",
        placeholder=(
            "Informe a correção, evidência "
            "ou justificativa necessária."
        )
    )

    st.button(
        "Solicitar correção / evidência",
        use_container_width=True
    )

    st.button(
        "Aprovar negociação",
        disabled=True,
        use_container_width=True
    )


# =========================================================
# RESILIÊNCIA
# =========================================================

with st.expander(
    "Como a integração lida com indisponibilidade do ERP?"
):

    st.markdown(
        """
**201 — Sucesso:** registra a condição e a auditoria.

**422 — Regra ou dado inválido:** não repete automaticamente;
a negociação volta para revisão.

**429 — Limite de requisições:** aguarda e tenta novamente.

**503 — ERP indisponível:** aplica novas tentativas com espera
progressiva.

A mesma **Idempotency-Key** é preservada nas novas tentativas para
evitar cadastro duplicado.
"""
    )


# =========================================================
# RODAPÉ
# =========================================================

st.divider()

st.caption(
    "A IA interpreta. "
    "O código valida. "
    "O humano decide. "
    "O integrador grava."
)
