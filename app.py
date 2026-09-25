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
    "Substitua o Trello por um painel web simples em Python para gerenciar"
    " solicitações do Google Forms."
)

# Inicializa os dados de exemplo no session_state se não existirem
if "dados" not in st.session_state:
  st.session_state["dados"] = pd.DataFrame([
      {
          "ID": 1,
          "Data": "22/09/2026 13:51",
          "Revenda": "GP7 JEQUIÉ",
          "Gerente": "[10] ADRIANO",
          "Codigo_RN": "109",
          "Codigo_PDV": "5901",
          "Item": "22820 Brahma multipack 21 cc/21 dz",
          "Justificativa": "Pagamento de longe, alinhado com a GV",
          "Status": "Solicitações",
      },
      {
          "ID": 2,
          "Data": "23/09/2026 16:40",
          "Revenda": "GP7 JEQUIÉ",
          "Gerente": "[20] MATHEUS",
          "Codigo_RN": "110",
          "Codigo_PDV": "5902",
          "Item": "18410 Skol 350ml - 1 cx",
          "Justificativa": "Ação promocional PDV parceiro",
          "Status": "OK",
      },
  ])

# Barra lateral para controle e importação de dados do Google Forms/Sheets
st.sidebar.header("Gestão e Filtros")
status_filtro = st.sidebar.selectbox(
    "Filtrar por Status", ["Todas", "Solicitações", "OK", "NOK", "STAND BY"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Atualizar Dados (Google Sheets)")
st.sidebar.markdown(
    "No Google Sheets do seu Forms, vá em **Ficheiro > Fazer o download >"
    " Valores separados por vírgula (.csv)** e carregue o ficheiro abaixo."
)

ficheiro_csv = st.sidebar.file_uploader(
    "Carregar CSV exportado", type=["csv"]
)

if ficheiro_csv is not None:
  try:
    df_novo = pd.read_csv(ficheiro_csv)
    # Garante colunas mínimas se necessário ou substitui a base
    st.sidebar.success("Ficheiro carregado com sucesso!")
  except Exception as e:
    st.sidebar.error(f"Erro ao ler o ficheiro: {e}")

# Filtro de exibição
df = st.session_state["dados"]
if status_filtro != "Todas":
  df_filtrado = df[df["Status"] == status_filtro]
else:
  df_filtrado = df

# Exibição principal dos cartões / solicitações
st.subheader(f"Lista de Pedidos ({len(df_filtrado)})")

if df_filtrado.empty:
  st.info("Nenhuma solicitação encontrada nesta categoria.")
else:
  for index, row in df_filtrado.iterrows():
    # Cabeçalho expansível simulando um cartão
    with st.expander(
        f"[{row['Status']}] PDV: {row['Codigo_PDV']} - Item: {row['Item']}"
    ):
      col1, col2 = st.columns(2)

      with col1:
        st.write(f"**Data do Envio:** {row['Data']}")
        st.write(f"**Revenda:** {row['Revenda']}")
        st.write(f"**Gerente de Venda:** {row['Gerente']}")
        st.write(f"**Código RN:** {row['Codigo_RN']}")

      with col2:
        st.write(f"**Código do PDV:** {row['Codigo_PDV']}")
        st.write(f"**Item Bonificado:** {row['Item']}")
        st.write(f"**Justificativa:** {row['Justificativa']}")

      st.markdown("---")

      # Alteração direta do status do cartão
      novo_status = st.selectbox(
          "Alterar Estado",
          ["Solicitações", "OK", "NOK", "STAND BY"],
          index=["Solicitações", "OK", "NOK", "STAND BY"].index(row["Status"]),
          key=f"status_{row['ID']}",
      )

      if novo_status != row["Status"]:
        st.session_state["dados"].loc[
            st.session_state["dados"]["ID"] == row["ID"], "Status"
        ] = novo_status
        st.success("Estado atualizado com sucesso!")
        st.rerun()
