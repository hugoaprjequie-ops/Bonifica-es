from datetime import date
import pandas as pd
import requests
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
# 1. CONFIGURAÇÃO DA CONEXÃO DIRETA COM O SHEETS E APPS SCRIPT
# ==========================================
URL_SHEETS_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTK_JV2DqYdKAOwaWn8P5n_eILUcSwzlpgLxlR_cyMrUPenHZaqdlYuOBrARCE_UgPJ2l0j1hR4yTs0/pub?output=csv"
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbyDyPmnIebm10Usav60IwsGLScLFDOTDyBBAd800pHIiQTK9PNoiNkdU3LHGqGsSjGO/exec"


@st.cache_data(ttl=30)
def carregar_dados_sheets(url):
  if not url:
    return pd.DataFrame()
  try:
    df = pd.read_csv(url)
    df["_excel_row"] = range(2, len(df) + 2)
    return df
  except Exception as e:
    st.error(f"Erro ao carregar dados do Sheets: {e}")
    return pd.DataFrame()


# Inicializa os dados no session_state
if "dados" not in st.session_state:
  st.session_state["dados"] = carregar_dados_sheets(URL_SHEETS_CSV)

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

# Identifica a coluna de data/carimbo
coluna_data = None
if not df.empty:
  for col in df.columns:
    if any(
        termo in col.lower() for termo in ["carimbo", "data", "timestamp"]
    ):
      coluna_data = col
      break

# ==========================================
# 2. FILTROS DE DATA (PADRÃO: HOJE) E GESTÃO
# ==========================================
st.sidebar.header("Filtros")

if not df.empty and coluna_data:
  df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce")
  datas_disponiveis = df[coluna_data].dt.date.dropna().unique()
  datas_disponiveis = sorted(datas_disponiveis, reverse=True)

  opcoes_data = ["Todas as Datas"] + [str(d) for d in datas_disponiveis]

  hoje_str = str(date.today())
  indice_padrao = 0
  if hoje_str in opcoes_data:
    indice_padrao = opcoes_data.index(hoje_str)

  data_escolhida = st.sidebar.selectbox(
      "Filtrar por Data do Envio", opcoes_data, index=indice_padrao
  )

  if data_escolhida != "Todas as Datas":
    df_filtrado_data = df[df[coluna_data].dt.date.astype(str) == data_escolhida]
  else:
    df_filtrado_data = df
else:
  df_filtrado_data = df
  st.sidebar.info("Filtro de data indisponível.")

# ==========================================
# 3. PAINÉIS SEPARADOS POR STATUS
# ==========================================
if df.empty:
  st.warning(
      "⚠️ Nenhum dado encontrado. Verifique a URL do Sheets nas configurações do"
      " código."
  )
else:
  aba_solicitacoes, aba_ok, aba_nok, aba_standby = st.tabs(
      ["📥 Solicitações", "✅ OK (Aprovadas)", "❌ NOK (Reprovadas)", "⏳ Stand By"]
  )


  def renderizar_painel(status_alvo, container):
    with container:
      df_status = (
          df_filtrado_data[df_filtrado_data["Status"] == status_alvo]
          if "Status" in df_filtrado_data.columns
          else pd.DataFrame()
      )

      st.markdown(f"### Total nesta categoria: {len(df_status)}")

      if df_status.empty:
        st.info(f"Nenhuma bonificação com o estado '{status_alvo}'.")
      else:
        for index, row in df_status.iterrows():
          # Tenta buscar o código/nome do PDV para colocar no título do cartão
          titulo_card = "Solicitação de Bonificação"
          for col in df.columns:
            if "PDV" in str(col).upper():
              titulo_card = f"PDV: {str(row[col])}"
              break

          with st.expander(titulo_card):
            col1, col2 = st.columns(2)

            # Lista atualizada com os nomes exatos das perguntas do Forms
            colunas_permitidas_keywords = [
                "carimbo de data/hora",
                "gerente de venda",
                "código do rn responsável",
                "código e nome do pdv",
                "código do pdv",
                "item bonificado",
                "justificativa",
                "revenda",
            ]

            colunas_para_exibir = []
            for col in df.columns:
              if col == "_excel_row":
                continue
              col_lower = str(col).lower()
              if "ação" in col_lower or "não precisa" in col_lower:
                continue

              if any(kw in col_lower for kw in colunas_permitidas_keywords):
                colunas_para_exibir.append(col)

            metade = len(colunas_para_exibir) // 2
            if metade == 0:
              metade = 1

            with col1:
              for col in colunas_para_exibir[:metade]:
                st.write(f"**{col}:** {row[col]}")

            with col2:
              for col in colunas_para_exibir[metade:]:
                st.write(f"**{col}:** {row[col]}")

            st.markdown("---")

            novo_status = st.selectbox(
                "Mover para:",
                ["Solicitações", "OK", "NOK", "STAND BY"],
                index=["Solicitações", "OK", "NOK", "STAND BY"].index(
                    status_alvo
                ),
                key=f"status_acao_{index}",
            )

            if novo_status != status_alvo:
              linha_excel = int(row["_excel_row"])

              if URL_APPS_SCRIPT:
                try:
                  requests.post(
                      URL_APPS_SCRIPT,
                      json={"rowExcel": linha_excel, "novoStatus": novo_status},
                      timeout=10,
                  )
                except Exception as e:
                  st.error(f"Erro ao salvar na planilha: {e}")

              st.session_state["dados"].loc[
                  st.session_state["dados"]["_excel_row"] == linha_excel,
                  "Status",
              ] = novo_status
              st.success(
                  "Estado alterado e salvo na planilha com sucesso! O painel"
                  " foi atualizado."
              )
              st.rerun()


  renderizar_painel("Solicitações", aba_solicitacoes)
  renderizar_painel("OK", aba_ok)
  renderizar_painel("NOK", aba_nok)
  renderizar_painel("STAND BY", aba_standby)
