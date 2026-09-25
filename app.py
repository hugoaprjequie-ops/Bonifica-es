import pandas as pd
import streamlit as st

# Configuração inicial da página
st.set_page_config(
    page_title="Painel de Aprovação - Google Forms",
    page_icon="📋",
    layout="wide",
)

st.title("Painel de Aprovação de Bonificações")
st.markdown(
    "Gerencie e aprove as solicitações enviadas através do Google Forms."
)

# ==========================================
# 1. CONFIGURAÇÃO DA CONEXÃO DIRETA COM O SHEETS
# ==========================================
# Cole abaixo o link CSV publicado do seu Google Sheets para automatizar a leitura:
URL_SHEETS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTK_JV2DqYdKAOwaWn8P5n_eILUcSwzlpgLxlR_cyMrUPenHZaqdlYuOBrARCE_UgPJ2l0j1hR4yTs0/pub?output=csv"


@st.cache_data(ttl=60)  # Atualiza os dados a cada 60 segundos
def carregar_dados_sheets(url):
  if not url:
    return pd.DataFrame()
  try:
    df = pd.read_csv(url)
    return df
  except Exception as e:
    st.error(f"Erro ao carregar dados do Sheets: {e}")
    return pd.DataFrame()


# Inicializa os dados no session_state
if "dados" not in st.session_state:
  if URL_SHEETS_CSV:
    st.session_state["dados"] = carregar_dados_sheets(URL_SHEETS_CSV)
  else:
    # Base vazia ou mock inicial caso o link não esteja preenchido ainda
    st.session_state["dados"] = pd.DataFrame()

df = st.session_state["dados"]

# Botão para atualizar dados manualmente do Sheets
if st.sidebar.button("Atualizar Dados do Sheets"):
  if URL_SHEETS_CSV:
    st.session_state["dados"] = carregar_dados_sheets(URL_SHEETS_CSV)
    st.success("Dados atualizados com sucesso!")
    st.rerun()
  else:
    st.warning("Por favor, insira a URL_SHEETS_CSV no código do aplicativo.")

# Garante a existência da coluna de Status
if not df.empty and "Status" not in df.columns:
  df["Status"] = "Solicitações"

# Garante a existência de uma coluna de Data para o filtro (procura por colunas de carimbo/data)
coluna_data = None
if not df.empty:
  for col in df.columns:
    if any(
        termo in col.lower() for termo in ["carimbo", "data", "timestamp"]
    ):
      coluna_data = col
      break

# ==========================================
# 2. FILTROS DE DATA E GESTÃO NA BARRA LATERAL
# ==========================================
st.sidebar.header("Filtros")

if not df.empty and coluna_data:
  # Tenta converter a coluna para data
  df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce")
  datas_disponiveis = df[coluna_data].dt.date.dropna().unique()
  datas_disponiveis = sorted(datas_disponiveis, reverse=True)

  opcoes_data = ["Todas as Datas"] + [str(d) for d in datas_disponiveis]
  data_escolhida = st.sidebar.selectbox("Filtrar por Data do Envio", opcoes_data)

  if data_escolhida != "Todas as Datas":
    df = df[df[coluna_data].dt.date.astype(str) == data_escolhida]
else:
  st.sidebar.info(
      "Filtro de data indisponível (coluna de data não identificada automaticamente"
      " ou dados vazios)."
  )

# ==========================================
# 3 e 4. PAINÉIS SEPARADOS POR STATUS
# ==========================================
if df.empty:
  st.warning(
      "⚠️ Nenhum dado encontrado. Adicione a `URL_SHEETS_CSV` diretamente no"
      " arquivo `app.py` para conectar ao seu Google Forms/Sheets."
  )
else:
  # Cria abas correspondentes aos painéis de status
  aba_solicitacoes, aba_ok, aba_nok, aba_standby = st.tabs(
      ["📥 Solicitações", "✅ OK (Aprovadas)", "❌ NOK (Reprovadas)", "⏳ Stand By"]
  )


  def renderizar_painel(status_alvo, container):
    with container:
      df_filtrado = (
          df[df["Status"] == status_alvo]
          if "Status" in df.columns
          else pd.DataFrame()
      )

      st.markdown(f"### Total nesta categoria: {len(df_filtrado)}")

      if df_filtrado.empty:
        st.info(f"Nenhuma bonificação com o estado '{status_alvo}'.")
      else:
        for index, row in df_filtrado.iterrows():
          # Monta o título do cartão de forma limpa (sem IDs numéricos desnecessários)
          titulo_card = f"Solicitação - {row.get(df.columns[1], 'Detalhes')}"
          for col in df.columns:
            if any(
                termo in col.lower()
                for termo in ["pdv", "revenda", "item", "cliente", "gerente"]
            ):
              titulo_card = f"{col}: {str(row[col])}"
              break

          with st.expander(titulo_card):
            col1, col2 = st.columns(2)
            colunas = [c for c in df.columns if c != "Status"]
            metade = len(colunas) // 2

            with col1:
              for col in colunas[:metade]:
                st.write(f"**{col}:** {row[col]}")

            with col2:
              for col in colunas[metade:]:
                st.write(f"**{col}:** {row[col]}")

            st.markdown("---")

            # Botão / Seletor para alterar o status e mover para o painel correspondente
            novo_status = st.selectbox(
                "Mover para:",
                ["Solicitações", "OK", "NOK", "STAND BY"],
                index=["Solicitações", "OK", "NOK", "STAND BY"].index(
                    status_alvo
                ),
                key=f"status_acao_{index}",
            )

            if novo_status != status_alvo:
              st.session_state["dados"].loc[
                  st.session_state["dados"].index == index, "Status"
              ] = novo_status
              st.success("Estado alterado com sucesso! O painel foi atualizado.")
              st.rerun()


  # Renderiza cada painel na sua aba correspondente
  renderizar_painel("Solicitações", aba_solicitacoes)
  renderizar_painel("OK", aba_ok)
  renderizar_painel("NOK", aba_nok)
  renderizar_painel("STAND BY", aba_standby)
