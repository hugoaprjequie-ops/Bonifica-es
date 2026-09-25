import pandas as pd
import streamlit as st

# Configuração inicial da página
st.set_page_config(
    page_title="Painel de Aprovação - Google Forms",
    page_icon="📋",
    layout="wide",
)

st.title("Painel Dinâmico de Aprovação de Solicitações")
st.markdown(
    "Este painel adapta-se a **qualquer** Google Forms conectado ao Google"
    " Sheets. Carregue os dados ou utilize uma ligação direta via CSV"
    " publicado."
)

# Inicializa o session_state se não existir
if "dados" not in st.session_state:
  # Começa vazio para não engessar com dados fictícios
  st.session_state["dados"] = pd.DataFrame()

# Barra lateral para configuração da fonte de dados e filtros
st.sidebar.header("Conexão e Dados")

# Opção 1: Link direto do Google Sheets publicado (CSV)
st.sidebar.subheader("1. Conexão via Link do Google Sheets")
st.sidebar.markdown(
    "No seu Google Sheets: **Partilhar > Publicar na Web > Valores separados por"
    " vírgula (.csv)**. Cole o link abaixo:"
)
url_sheets = st.sidebar.text_input(
    "URL do CSV publicado", placeholder="https://docs.google.com/spreadsheets/..."
)

if st.sidebar.button("Carregar via Link"):
  if url_sheets:
    try:
      df_carregado = pd.read_csv(url_sheets)
      if "Status" not in df_carregado.columns:
        df_carregado["Status"] = "Solicitações"
      if "ID" not in df_carregado.columns:
        df_carregado.insert(0, "ID", range(1, len(df_carregado) + 1))
      st.session_state["dados"] = df_carregado
      st.sidebar.success("Dados carregados com sucesso do Sheets!")
      st.rerun()
    except Exception as e:
      st.sidebar.error(f"Erro ao ligar ao link: {e}")

st.sidebar.markdown("---")

# Opção 2: Upload manual do CSV (como backup rápido)
st.sidebar.subheader("2. Ou Carregar Ficheiro CSV")
ficheiro_csv = st.sidebar.file_uploader("Carregar CSV exportado", type=["csv"])

if ficheiro_csv is not None:
  try:
    df_carregado = pd.read_csv(ficheiro_csv)
    if "Status" not in df_carregado.columns:
      df_carregado["Status"] = "Solicitações"
    if "ID" not in df_carregado.columns:
      df_carregado.insert(0, "ID", range(1, len(df_carregado) + 1))
    st.session_state["dados"] = df_carregado
    st.sidebar.success("Ficheiro carregado com sucesso!")
    st.rerun()
  except Exception as e:
    st.sidebar.error(f"Erro ao ler o ficheiro: {e}")

# Verifica se existem dados carregados
df = st.session_state["dados"]

if df.empty:
  st.warning(
      "⚠️ Nenhum dado encontrado. Por favor, cole o link do Google Sheets"
      " publicado na web ou carregue um ficheiro CSV na barra lateral."
  )
else:
  # Filtro por Status
  st.sidebar.markdown("---")
  st.sidebar.header("Filtros")
  status_disponiveis = ["Todas", "Solicitações", "OK", "NOK", "STAND BY"]
  status_filtro = st.sidebar.selectbox("Filtrar por Status", status_disponiveis)

  if status_filtro != "Todas" and "Status" in df.columns:
    df_filtrado = df[df["Status"] == status_filtro]
  else:
    df_filtrado = df

  st.subheader(f"Lista de Solicitações ({len(df_filtrado)})")

  # Exibição dinâmica de cada linha do Forms como um cartão expansível
  for index, row in df_filtrado.iterrows():
    # Pega o primeiro campo relevante (ex: ID ou primeira coluna de texto) para o título do expander
    status_atual = row.get("Status", "Solicitações")

    # Tenta encontrar uma coluna com identificador ou usa o índice
    titulo_card = f"[{status_atual}] Linha / ID: {row.get('ID', index + 1)}"
    # Se houver uma coluna parecida com 'PDV' ou 'Nome', usa para enriquecer o título
    for col in df.columns:
      if any(
          termo in col.lower()
          for termo in ["pdv", "nome", "revenda", "item", "cliente"]
      ):
        titulo_card = (
            f"[{status_atual}] {col}: {str(row[col])[:40]}"  # noqa: E501
        )
        break

    with st.expander(titulo_card):
      # Mostra dinamicamente todas as colunas que vieram do Google Forms
      col1, col2 = st.columns(2)
      colunas = list(df.columns)
      metade = len(colunas) // 2

      with col1:
        for col in colunas[:metade]:
          if col != "Status":
            st.write(f"**{col}:** {row[col]}")

      with col2:
        for col in colunas[metade:]:
          if col != "Status":
            st.write(f"**{col}:** {row[col]}")

      st.markdown("---")

      # Campo de alteração de estado dinâmico
      idx_atual = (
          ["Solicitações", "OK", "NOK", "STAND BY"].index(status_atual)
          if status_atual in ["Solicitações", "OK", "NOK", "STAND BY"]
          else 0
      )

      novo_status = st.selectbox(
          "Alterar Estado",
          ["Solicitações", "OK", "NOK", "STAND BY"],
          index=idx_atual,
          key=f"status_{row.get('ID', index)}",
      )

      if novo_status != status_atual:
        st.session_state["dados"].loc[
            st.session_state["dados"].index == index, "Status"
        ] = novo_status
        st.success("Estado atualizado com sucesso!")
        st.rerun()
