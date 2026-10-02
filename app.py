import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# 1. Configuração da página do Streamlit (Design adaptável para celular)
st.set_page_config(page_title="Gestão de Equipe", page_icon="🚀", layout="wide")

# =====================================================================
# 🔑 COLE SUAS CHAVES DO SUPABASE AQUI EMBAIXO:
SUPABASE_URL = "https://rmaosomqdzzkilmsscbg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJtYW9zb21xZHp6a2lsbXNzY2JnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA4NzY0MzMsImV4cCI6MjEwNjQ1MjQzM30.J6K6aMIzZ-2Godf1dpAkozS12NpXqK8N0BeZhIGazZA"
# =====================================================================

@st.cache_resource
def iniciar_banco():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

supabase = iniciar_banco()

# 👥 Nomes Reais da Sua Equipe
EQUIPE = ["Luiz Fernando", "Vinicius", "Débora", "Laudecir", "Rosane"]

# --- FUNÇÕES DE NEGÓCIO CONECTADAS À NUVEM ---
def buscar_tarefas():
    if supabase:
        try:
            # Busca todas as tarefas no banco de dados na internet
            resposta = supabase.table("tarefas").select("*").execute()
            # Ordena pelo ID para as mais novas não ficarem pulando de posição
            return sorted(resposta.data, key=lambda x: x['id'])
        except Exception as e:
            st.error(f"Erro ao conectar com a nuvem: {e}")
            return []
    return []

def adicionar_tarefa(titulo, descricao, responsavel, e_pedido):
    nova_tarefa = {
        "titulo": titulo,
        "descricao": descricao,
        "responsavel": responsavel,
        "e_pedido": e_pedido,
        "prazo": None,
        "status": "A Fazer"
    }
    if supabase:
        try:
            supabase.table("tarefas").insert(nova_tarefa).execute()
        except Exception as e:
            st.error(f"Erro ao salvar tarefa: {e}")

def atualizar_status(tarefa_id, novo_status):
    if supabase:
        try:
            supabase.table("tarefas").update({"status": novo_status}).eq("id", tarefa_id).execute()
        except Exception as e:
            st.error(f"Erro ao mudar status: {e}")

def definir_prazo_pedido(tarefa_id, data_prazo):
    prazo_formatado = data_prazo.strftime("%d/%m/%Y")
    if supabase:
        try:
            supabase.table("tarefas").update({"status": "Em Andamento", "prazo": prazo_formatado}).eq("id", tarefa_id).execute()
        except Exception as e:
            st.error(f"Erro ao definir prazo: {e}")

# --- INTERFACE VISUAL ---
st.title("📋 Painel de Tarefas e Equipe")

# Filtro por Responsável na barra lateral
with st.sidebar:
    st.header("⚙️ Filtros")
    filtro_usuario = st.selectbox("Ver tarefas de:", ["Todos"] + EQUIPE)
    
    st.divider()
    st.subheader("➕ Novo Chamado / Pedido")
    with st.form("form_tarefa", clear_on_submit=True):
        txt_titulo = st.text_input("Título (ex: Pedido de Peça X)")
        txt_desc = st.text_area("Descrição / Detalhes")
        sel_resp = st.selectbox("Responsável", EQUIPE)
        check_pedido = st.checkbox("É um pedido de peça ou material?")
        botao_enviar = st.form_submit_button("Criar")
        
        if botao_enviar and txt_titulo:
            adicionar_tarefa(txt_titulo, txt_desc, sel_resp, check_pedido)
            st.success("Registrado com sucesso na nuvem!")
            st.rerun()

# Buscar dados reais da internet
todas_tarefas = buscar_tarefas()

# Filtrar se necessário
if filtro_usuario != "Todos":
    tarefas_filtradas = [t for t in todas_tarefas if t["responsavel"] == filtro_usuario]
else:
    tarefas_filtradas = todas_tarefas

# Criar as 3 colunas clássicas do Kanban
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🔴 A Fazer")
    for t in tarefas_filtradas:
        if t["status"] == "A Fazer":
            with st.container(border=True):
                if t["e_pedido"]:
                    st.markdown(f"### ⚙️ [PEDIDO] {t['titulo']}")
                    st.write(t["descricao"])
                    st.caption("⚠️ *Aguardando início para definir prazo de entrega.*")
                else:
                    st.markdown(f"### {t['titulo']}")
                    st.write(t["descricao"])
                
                st.caption(f"👤 Responsável: **{t['responsavel']}**")
                
                if t["e_pedido"]:
                    with st.popover("👉 Iniciar Pedido"):
                        st.write("Insira a previsão fornecida pelo fornecedor:")
                        dt_previsao = st.date_input("Previsão de Entrega", value=datetime.now(), key=f"dt_pk_{t['id']}")
                        if st.button("Confirmar e Mover", key=f"btn_conf_{t['id']}"):
                            definir_prazo_pedido(t["id"], dt_previsao)
                            st.rerun()
                else:
                    if st.button("👉 Iniciar", key=f"btn_ini_{t['id']}"):
                        atualizar_status(t["id"], "Em Andamento")
                        st.rerun()

with col2:
    st.subheader("🟡 Em Andamento")
    for t in tarefas_filtradas:
        if t["status"] == "Em Andamento":
            with st.container(border=True):
                if t["e_pedido"]:
                    st.markdown(f"### ⚙️ [PEDIDO] {t['titulo']}")
                    st.write(t["descricao"])
                    st.markdown(f"📅 **Previsão de Entrega: {t['prazo']}**")
                else:
                    st.markdown(f"### {t['titulo']}")
                    st.write(t["descricao"])
                
                st.caption(f"👤 Responsável: **{t['responsavel']}**")
                if st.button("✅ Concluir", key=f"btn_con_{t['id']}"):
                    atualizar_status(t["id"], "Concluído")
                    st.rerun()

with col3:
    st.subheader("🟢 Concluído")
    for t in tarefas_filtradas:
        if t["status"] == "Concluído":
            with st.container(border=True):
                if t["e_pedido"]:
                    st.markdown(f"### ~~⚙️ [PEDIDO] {t['titulo']}~~")
                    st.write(t["descricao"])
                    st.markdown(f"📅 Entregue (Prazo era: {t['prazo']})")
                else:
                    st.markdown(f"### ~~{t['titulo']}~~")
                    st.write(t["descricao"])
                
                st.caption(f"👤 Responsável: **{t['responsavel']}**")
                
                c_voltar, c_arquivar = st.columns(2)
                with c_voltar:
                    if st.button("🔄 Voltar", key=f"btn_vol_{t['id']}"):
                        atualizar_status(t["id"], "A Fazer")
                        st.rerun()
                with c_arquivar:
                    if st.button("🗄️ Arquivar", key=f"btn_arq_{t['id']}"):
                        atualizar_status(t["id"], "Arquivado")
                        st.rerun()


