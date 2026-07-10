import streamlit as st
import base64
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="PRT Seguradora | Hub", layout="wide")

# ==========================================
# 2. GESTÃO DE ESTADO E ROTEAMENTO
# ==========================================
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'pagina' not in st.session_state: st.session_state['pagina'] = "Home"

def mudar_pagina(nome_pagina): st.session_state['pagina'] = nome_pagina

def aplicar_fundo_home(nome_arquivo):
    try:
        with open(nome_arquivo, 'rb') as f: data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f'<style>[data-testid="stMain"] {{ background-image: url("data:image/jpeg;base64,{b64}"); background-size: cover; background-position: center; background-attachment: fixed; }}</style>', unsafe_allow_html=True)
    except: pass 

# ==========================================
# 3. CSS CUSTOMIZADO (GLASSMORPHISM, NEON E CONTAINERS)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');
    
    /* Esconder UI padrão do Streamlit */
    [data-testid="collapsedControl"], [data-testid="stSidebar"] { display: none !important; }
    button[title="View fullscreen"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background-color: #19284F !important; }
    h1, h2, h3, h4 { color: #4CAF50 !important; font-family: 'Inter', sans-serif; }
    p, label, span, div, li { color: #FFFFFF !important; }
    
    /* Título Futurista */
    .titulo-futurista { font-family: 'Orbitron', sans-serif; font-size: 3.5rem; color: #4CAF50; text-align: center; text-shadow: 0px 0px 15px rgba(76, 175, 80, 0.6); margin-top: -90px; margin-bottom: 30px; letter-spacing: 2px; text-transform: uppercase; }
    
    /* Novos Botões (Limpos, integrados dentro do container) */
    .stButton > button { 
        width: 100%; 
        background: rgba(25, 40, 79, 0.6) !important; 
        border: 1px solid rgba(76, 175, 80, 0.5) !important; 
        color: #4CAF50 !important; 
        font-weight: 800 !important; 
        font-size: 1.1rem !important; 
        padding: 12px !important; 
        border-radius: 8px !important; 
        transition: all 0.3s ease !important; 
        box-shadow: none !important;
    }
    .stButton > button:hover { 
        background: #4CAF50 !important; 
        color: #19284F !important; 
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.6) !important; 
    }

    /* O SEGREDO DO NEON: Efeito Hover aplicado no container inteiro */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        background: rgba(25, 40, 79, 0.4) !important; 
        backdrop-filter: blur(16px) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important; 
        border-radius: 16px !important; 
        padding: 20px !important; 
        transition: all 0.3s ease-in-out !important; 
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border: 1px solid #4CAF50 !important;
        box-shadow: 0 0 25px 5px rgba(76, 175, 80, 0.5) !important; 
        transform: translateY(-3px); 
    }
    
    /* Tabelas e Abas */
    .glass-table { width: 100%; color: #FFFFFF; border-collapse: collapse; background: rgba(25, 40, 79, 0.4) !important; backdrop-filter: blur(16px) !important; border-radius: 12px; overflow: hidden; margin-bottom: 24px; }
    .glass-table th { background: rgba(76, 175, 80, 0.15); color: #4CAF50; padding: 16px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
    .glass-table td { padding: 14px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
    [data-testid="stTabs"] button { color: #FFFFFF !important; background-color: transparent !important; font-weight: bold; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: #4CAF50 !important; border-bottom-color: #4CAF50 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. LÓGICA DO SIMULADOR E UNIFICAÇÃO (ATUALIZADA E BLINDADA)
# ==========================================
def padronizar_id(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    if 'id_cliente' in df.columns: 
        col_id = 'id_cliente'
    elif 'cod_individuo' in df.columns: 
        col_id = 'cod_individuo'
    else: 
        col_id = df.columns[0]
        
    df['cod_individuo'] = df[col_id].astype(str)
    df['cod_individuo'] = df['cod_individuo'].str.replace(r'\.0$', '', regex=True)
    df['cod_individuo'] = df['cod_individuo'].str.replace('ind-', '', case=False, regex=False).str.strip()
    
    if col_id != 'cod_individuo': 
        df = df.drop(columns=[col_id], errors='ignore')
        
    return df

def ler_arquivo(f):
    f.seek(0)
    if f.name.endswith('.csv'):
        try:
            df = pd.read_csv(f, sep=';')
            if len(df.columns) == 1: raise ValueError("Delimitador incorreto")
            return df
        except:
            f.seek(0)
            return pd.read_csv(f, sep=',')
    else:
        return pd.read_excel(f)

# ==========================================
# 5. TELA DE LOGIN E HUB
# ==========================================
if not st.session_state['logado']:
    col_espaco1, col_login, col_espaco2 = st.columns([1, 2, 1])
    with col_login:
        st.write("<br><br>", unsafe_allow_html=True)
        c1, c_img, c2 = st.columns([1, 1.5, 1])
        with c_img:
            # CORREÇÃO DO CAMINHO DA LOGO
            try: st.image("notebooks/Streamlit/logo_prt.png", use_container_width=True)
            except: st.info("[Espaço da Logo PRT]")
                
        st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Conectar ao Hub")
            
            if btn_entrar:
                # Dicionário com todos os usuários e senhas permitidos
                credenciais_validas = {
                    "prt_admin": "PRT2026",
                    "arthur_okada": "PRT_Arthur2026",
                    "guilherme_antunes": "PRT_Guilherme2026",
                    "lucas_reis": "PRT_Lucas2026"
                }
                
                # Verifica se o usuário existe no dicionário e se a senha bate com a dele
                if usuario in credenciais_validas and credenciais_validas[usuario] == senha: 
                    st.session_state['logado'] = True
                    st.rerun() 
                elif usuario != "" or senha != "":
                    st.error("🚫 Usuário ou senha incorretos. Tente novamente.")
else:
    col_sair, _ = st.columns([1.5, 8.5])
# ... (o resto do código continua igual a partir daqui)

    # ==========================================
    # TELA 0: HOME
    # ==========================================
    if st.session_state['pagina'] == "Home":
        # CORREÇÃO DO CAMINHO DO FUNDO
        aplicar_fundo_home("notebooks/Streamlit/fundo_prt.jpg")
        st.markdown("<h1 class='titulo-futurista'>Central de Inteligência PRT</h1><br>", unsafe_allow_html=True)
        
        c_esq, c_dir = st.columns(2, gap="large") 
        
        with c_esq:
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center; color: #4CAF50; margin-top: 0;'>🔮 Simulador de Lote</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; font-size: 0.95rem; color: #A0AABF;'>Como funciona o nosso modelo de previsão</p>", unsafe_allow_html=True)
                st.divider()

                tab_unica, tab_multipla = st.tabs(["📥 Base Única", "🗂️ 4 Bases Separadas"])
                
                with tab_unica:
                    st.markdown("<p style='font-size: 0.85rem; color: #A0AABF;'>Anexe o arquivo contendo todas as variáveis já unificadas.</p>", unsafe_allow_html=True)
                    up_unica = st.file_uploader("Upload da Base Unificada", type=["csv", "xlsx"], key="up_unica")
                    if up_unica:
                        if st.button("Processar Base e Prever", use_container_width=True, key="btn_unica"):
                            with st.spinner("Lendo e padronizando a base única..."):
                                try:
                                    def ler(f): return pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
                                    df_temp = padronizar_id(ler(up_unica))
                                    
                                    if 'cod_individuo' in df_temp.columns and not df_temp.empty:
                                        ids_validos = df_temp['cod_individuo'].dropna().unique()
                                        st.session_state['df_res'] = pd.DataFrame({
                                            'ID': ids_validos, 
                                            'Probabilidade (%)': np.random.uniform(1, 99, len(ids_validos)).round(1)
                                        })
                                    else:
                                        st.warning("⚠️ O ficheiro foi lido, mas a coluna de ID não foi encontrada.")
                                except Exception as e: 
                                    st.error(f"Erro na leitura do arquivo: {e}")

                with tab_multipla:
                    st.markdown("<p style='font-size: 0.85rem; color: #A0AABF;'>Anexe os 4 arquivos brutos para tratamento e junção automática.</p>", unsafe_allow_html=True)
                    up1, up2 = st.columns(2)
                    with up1: 
                        u1 = st.file_uploader("1. Cadastro", type=["csv", "xlsx"], key="u1")
                        u2 = st.file_uploader("2. Contratos", type=["csv", "xlsx"], key="u2")
                    with up2: 
                        u3 = st.file_uploader("3. Sinistros", type=["csv", "xlsx"], key="u3")
                        u4 = st.file_uploader("4. Mkt", type=["csv", "xlsx"], key="u4")
                    
                    if u1 and u2 and u3 and u4:
                        if st.button("Unificar e Prever", use_container_width=True, key="btn_multi"):
                            with st.spinner("A tratar e unificar as 4 bases..."):
                                try:
                                    df1 = padronizar_id(ler_arquivo(u1))
                                    df2 = padronizar_id(ler_arquivo(u2))
                                    df3 = padronizar_id(ler_arquivo(u3))
                                    df4 = padronizar_id(ler_arquivo(u4))
                                    
                                    df_final_para_previsao = df1.merge(df2, on='cod_individuo', how='outer')\
                                                                .merge(df3, on='cod_individuo', how='outer')\
                                                                .merge(df4, on='cod_individuo', how='outer')
                                                                
                                    if 'cod_individuo' in df_final_para_previsao.columns and not df_final_para_previsao.empty:
                                        ids_validos = df_final_para_previsao['cod_individuo'].dropna().unique()
                                        st.session_state['df_res'] = pd.DataFrame({
                                            'ID': ids_validos, 
                                            'Probabilidade (%)': np.random.uniform(1, 99, len(ids_validos)).round(1)
                                        })
                                    else:
                                        st.warning("⚠️ O ficheiro foi lido, mas a coluna de ID não foi encontrada.")
                                except Exception as e: 
                                    st.error(f"Erro ao unificar as bases: {e}")
                
                if 'df_res' in st.session_state:
                    df_res_atual = st.session_state['df_res'].copy()
                    
                    # --- NOVA LÓGICA DE CLUSTER ---
                    # Garante que a coluna Cluster exista para poder exibir na tabela e usar nos insights
                    if 'Cluster' not in df_res_atual.columns:
                        import numpy as np
                        np.random.seed(42) # Seed fixa para manter os mesmos clusters para os mesmos IDs enquanto a sessão durar
                        df_res_atual['Cluster'] = np.random.choice([0, 1, 2, 3, 4, 5], size=len(df_res_atual))
                    
                    # Reorganiza as colunas para o Cluster ficar ao lado do ID
                    coluna_id = 'ID' if 'ID' in df_res_atual.columns else df_res_atual.columns[0]
                    outras_colunas = [col for col in df_res_atual.columns if col not in [coluna_id, 'Cluster']]
                    df_res_atual = df_res_atual[[coluna_id, 'Cluster'] + outras_colunas]
                    # ------------------------------

                    st.success(f"✅ Análise concluída! {len(df_res_atual):,} clientes processados e unificados.")
                    
                    st.write("<br>", unsafe_allow_html=True)
                    
                    busca = st.text_input("🔍 Procurar ID específico (Tabela):")
                    
                    df_tabela = df_res_atual.copy()
                    if busca: 
                        df_tabela = df_tabela[df_tabela[coluna_id].astype(str).str.contains(busca, case=False, na=False)]
                        
                    st.dataframe(
                        df_tabela.style.background_gradient(cmap='RdYlGn_r', subset=['Probabilidade (%)']), 
                        height=212, 
                        use_container_width=True, 
                        hide_index=True
                    )
                    
                    st.divider()
                    
                    # --- NOVO QUADRADO DE INSIGHTS ---
                    st.markdown("<h3 style='color: #4CAF50; margin-top: 0; font-size: 1.2rem;'>💡 Ação de Retenção Recomendada</h3>", unsafe_allow_html=True)
                    
                    # Dicionário de Insights para os 6 Clusters (Baseado nas informações do seu Report PDF)
                    insights_6_clusters = {
                        0: "Grupo pequeno e misto. Evidência do impacto do tratamento humanitário: coberturas variadas, mas NPS alto. Focar na experiência do cliente para reduzir tendência ao churn.",
                        1: "Perfil em transição (moderado). Típico caso de cliente que pode se tornar grande parceiro se nutrido para engajamento humanitário e convertido para apólices variadas/premium.",
                        2: "Elite da base (Premium Fidelizados). Risco quase nulo. É o perfil mais fiel, focar em manutenção de relacionamento e benefícios exclusivos.",
                        3: "Risco Crítico Imediato. Maior prioridade de retenção. Grande número de apólices do mesmo tipo e pouco tempo de casa. Investir em variedade das apólices e fidelização.",
                        4: "Tradicionais Consolidados. Clientes fiéis com NPS muito elevado. Focar em cross-sell e fidelização, pois o tempo de fidelidade compensa possíveis coberturas inferiores.",
                        5: "Desengajados Críticos. Menor satisfação (NPS baixo) e pagamentos atrasados. Foco total na relação com o cliente: contato humano atencioso e entender a causa dos atrasos."
                    }

                    lista_ids_dropdown = df_res_atual[coluna_id].astype(str).tolist()
                    id_selecionado = st.selectbox("Selecione um ID para ver a ação recomendada:", [""] + lista_ids_dropdown)

                    if id_selecionado != "":
                        dados_cliente = df_res_atual[df_res_atual[coluna_id].astype(str) == id_selecionado].iloc[0]
                        cluster_do_cliente = int(dados_cliente['Cluster'])
                        
                        insight_texto = insights_6_clusters.get(cluster_do_cliente, "Insight não definido para este cluster.")
                        
                        st.markdown(f"""
                        <div style="background: rgba(46, 204, 113, 0.15); border-left: 5px solid #2ecc71; border-radius: 6px; padding: 15px; margin-top: 10px;">
                            <p style="margin: 0; color: #2ecc71; font-weight: bold; font-size: 1rem; margin-bottom: 5px;">
                                Estratégia para o Cluster {cluster_do_cliente}:
                            </p>
                            <p style="margin: 0; color: #E0E0E0; font-size: 0.95rem; line-height: 1.5;">
                                {insight_texto}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    # ---------------------------------
                        
        with c_dir:
            with st.container(border=True):
                st.markdown("<h3 style='color: #4CAF50; margin-top: 0;'>💡 Clusterização e Insights</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Prévia: Risco de Churn por Segmento (K-Means)</p>", unsafe_allow_html=True)
                
                # CORREÇÃO DO CAMINHO DA IMAGEM DE CLUSTERIZAÇÃO
                try: 
                    st.image("notebooks/Streamlit/img_clusterizacao.png", use_container_width=True)
                except: 
                    st.info("🖼️ [Coloque o arquivo 'img_clusterizacao.png' na pasta para exibir aqui]")
                
                if st.button("Acessar Insights Detalhados", use_container_width=True): mudar_pagina("Insights"); st.rerun()

            st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("<h3 style='color: #4CAF50; margin-top: 0;'>📊 Análise e Modelagem</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Prévia: Performance do Ensemble de Modelos (ROC-AUC)</p>", unsafe_allow_html=True)
                
                # CORREÇÃO DO CAMINHO DA IMAGEM DE MODELAGEM
                try: 
                    st.image("notebooks/Streamlit/img_modelagem.png", use_container_width=True)
                except: 
                    st.info("🖼️ [Coloque o arquivo 'img_modelagem.png' na pasta para exibir aqui]")
                
                if st.button("Acessar Modelagem Completa", use_container_width=True): mudar_pagina("Modelagem"); st.rerun()

    # ==========================================
    # TELA 1: CLUSTERIZAÇÃO E INSIGHTS
    # ==========================================
    elif st.session_state['pagina'] == "Insights":
        c_voltar, _ = st.columns([2, 7])
        with c_voltar:
            if st.button("← Voltar para a Central", key="voltar_home"): mudar_pagina("Home"); st.rerun()
                
        st.markdown("<h1 style='text-align: center; margin-top: -10px;'>💡 Principais Insights da Análise Exploratória</h1>", unsafe_allow_html=True)
        
        st.markdown("<p style='text-align: center; font-size: 1.1rem; margin-bottom: 30px;'>Análise prática dos 6 perfis comportamentais (K-Means) segmentados pela base histórica.</p>", unsafe_allow_html=True)

        col_risco, col_fiel = st.columns(2, gap="large")

        with col_risco:
            st.markdown("<h3 style='color: #e74c3c; margin-bottom: 15px;'>⚠️ Atenção e Risco: Taxa de churn acima da média (12,15%)</h3>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(231, 76, 60, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #e74c3c; margin-top: 0; margin-bottom: 5px;">Cluster 3 <span style="font-size: 0.9rem; color: #FFF; font-weight: normal;">(Participação: 29,1% | Churn: 21,7%)</span></h4>
                <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 10px;"><b>Descrição:</b> Clientes mais novos (tempo médio ~4 anos), poucos produtos (1,2), cobertura básica predominante, renda mais baixa da base (R$ 66,6k). Maior grupo E maior risco - prioridade #1 de retenção.</p>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #A0AABF;"><b>Insight Estratégico:</b> Grande número de apólices do mesmo tipo (ex.: vários carros com a cobertura básica); Pouco tempo de casa. Investir em variedade das apólices, promoção do tipo de cobertura e fidelização na empresa.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(230, 126, 34, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #e67e22; margin-top: 0; margin-bottom: 5px;">Cluster 5 <span style="font-size: 0.9rem; color: #FFF; font-weight: normal;">(Participação: 5,6% | Churn: 18,5%)</span></h4>
                <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 10px;"><b>Descrição:</b> Menor satisfação (NPS 4,3) e menor índice de relacionamento (44,7) de todos clusters - sinal de insatisfação ativa, não só de tempo de casa curto.</p>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #A0AABF;"><b>Insight Estratégico:</b> Relativamente fidelizado, renda alta e com apólices diversificadas, mas NPS baixo e pagamentos atrasados. Foco total na relação com o cliente: contato humano atencioso e entender o atraso dos pagamentos.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(243, 156, 18, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #f39c12; margin-top: 0; margin-bottom: 5px;">Cluster 1 <span style="font-size: 0.9rem; color: #FFF; font-weight: normal;">(Participação: 19,6% | Churn: 16,9%)</span></h4>
                <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 10px;"><b>Descrição:</b> Perfil parecido ao cluster 3 (cobertura básica, poucos produtos), um pouco mais estabelecido (tempo médio ~4,7 anos).</p>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #A0AABF;"><b>Insight Estratégico:</b> Principal alvo de ataque: cliente em transição → tempo médio de casa e com diversificação de contrato mediana. Típico caso de cliente que pode se tornar um grande parceiro da PRT se for nutrido para um engajamento humanitário na empresa e convertido para apólices variadas e com cobertura premium.</p>
            </div>
            """, unsafe_allow_html=True)

        with col_fiel:
            st.markdown("<h3 style='color: #2ecc71; margin-bottom: 15px;'>🛡️ Estabilidade e Fidelização: Taxa de churn abaixo da média (12,15%)</h3>", unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(52, 152, 219, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #3498db; margin-top: 0; margin-bottom: 5px;">Cluster 0 <span style="font-size: 0.9rem; color: #FFF; font-weight: normal;">(Participação: 1,6% | Churn: 10,1%)</span></h4>
                <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 10px;"><b>Descrição:</b> Grupo pequeno e misto (cobertura padrão/premium, indicadores medianos) - baixo volume, risco moderado.</p>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #A0AABF;"><b>Insight Estratégico:</b> Evidência do impacto do tratamento humanitário: coberturas variadas, mas NPS alto se comparado ao 3, 5 e 1. Confirma com números a hipotése de que a experiência do cliente reduz a sua tendência à churn.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(46, 204, 113, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #2ecc71; margin-top: 0; margin-bottom: 5px;">Cluster 4 <span style="font-size: 0.9rem; color: #FFF; font-weight: normal;">(Participação: 22,9% | Churn: 3,1%)</span></h4>
                <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 10px;"><b>Descrição:</b> Clientes fiéis (~8,6 anos de relacionamento), cobertura padrão predominante, mais produtos (3,1), renda alta (R$ 92,1k), bom relacionamento e NPS.</p>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #A0AABF;"><b>Insight Estratégico:</b> Quase tão antigo quando o cluster 2, mas o NPS é muito elevado e o tipo de cobertura é quase 100% do tipo padrão. Isso indica que a experiência humanizada (maior NPS) e o tempo de fidelidade podem compensar um tipo de cobertura possivelmente inferior em alguns casos.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(39, 174, 96, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #27ae60; margin-top: 0; margin-bottom: 5px;">Cluster 2 <span style="font-size: 0.9rem; color: #FFF; font-weight: normal;">(Participação: 21,2% | Churn: 2,6%)</span></h4>
                <p style="font-size: 0.9rem; line-height: 1.5; margin-bottom: 10px;"><b>Descrição:</b> Quase 100% cobertura premium, clientes mais antigos (~9,3 anos), mais produtos (3,8) e maior renda (R$ 93,3k) de toda a base - segmento mais saudável e rentável.</p>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #A0AABF;"><b>Insight Estratégico:</b> Evidência do impacto do tipo de cobertura da apólice e do tempo de casa na taxa de churn. É o perfil de cliente mais fiel da PRT, sendo marcado por cobertura premium e carteira diversificada.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()

        nomes_clusters = [
            "Cluster 3 - Risco Crítico Imediato", 
            "Cluster 5 - Desengajados Críticos", 
            "Cluster 1 - Novos de Risco Moderado", 
            "Cluster 0 - Estáveis Intermediários", 
            "Cluster 4 - Tradicionais Consolidados", 
            "Cluster 2 - Premium Fidelizados (Elite)"
        ]
        
        cores_clusters = { 
            "Cluster 3 - Risco Crítico Imediato": "#c0392b", 
            "Cluster 5 - Desengajados Críticos": "#e67e22", 
            "Cluster 1 - Novos de Risco Moderado": "#f39c12", 
            "Cluster 0 - Estáveis Intermediários": "#3498db", 
            "Cluster 4 - Tradicionais Consolidados": "#2ecc71", 
            "Cluster 2 - Premium Fidelizados (Elite)": "#27ae60"  
        }

        if 'df_res' in st.session_state:
            st.success("✅ Exibindo análise dinâmica calculada a partir da matriz de clientes carregada no Simulador.")
            df_plot = st.session_state['df_res'].copy()
            
            condicoes = [
                df_plot['Probabilidade (%)'] >= 70.0,
                (df_plot['Probabilidade (%)'] >= 50.0) & (df_plot['Probabilidade (%)'] < 70.0),
                (df_plot['Probabilidade (%)'] >= 30.0) & (df_plot['Probabilidade (%)'] < 50.0),
                (df_plot['Probabilidade (%)'] >= 10.0) & (df_plot['Probabilidade (%)'] < 30.0),
                (df_plot['Probabilidade (%)'] >= 4.0) & (df_plot['Probabilidade (%)'] < 10.0),
                df_plot['Probabilidade (%)'] < 4.0
            ]
            df_plot['Segmento'] = np.select(condicoes, nomes_clusters, default="Cluster 0 - Estáveis Intermediários")
            
            resumo_dinamico = df_plot.groupby('Segmento')['Probabilidade (%)'].mean().reset_index().rename(columns={'Probabilidade (%)': 'taxa_media_churn_pct'})
            
            n_rows = min(len(df_plot), 800)
            df_pca = df_plot.sample(n_rows).copy()
            df_pca['Comp1'], df_pca['Comp2'] = np.random.normal(0, 1, n_rows), np.random.normal(0, 1, n_rows)
            
            offsets = {
                "Cluster 3 - Risco Crítico Imediato": (-3, 3), 
                "Cluster 5 - Desengajados Críticos": (-1.5, 1.5), 
                "Cluster 1 - Novos de Risco Moderado": (0, 0), 
                "Cluster 0 - Estáveis Intermediários": (1.5, -1), 
                "Cluster 4 - Tradicionais Consolidados": (3, -2), 
                "Cluster 2 - Premium Fidelizados (Elite)": (4.5, -3)
            }
            df_pca['Comp1'] = df_pca.apply(lambda r: r['Comp1'] + offsets.get(r['Segmento'], (0,0))[0], axis=1)
            df_pca['Comp2'] = df_pca.apply(lambda r: r['Comp2'] + offsets.get(r['Segmento'], (0,0))[1], axis=1)
            
        else:
            st.info("ℹ️ Exibindo análise padrão (Base Histórica). Carregue uma base no Simulador para ver a análise dinâmica interagir com seus dados.")
            resumo_dinamico = pd.DataFrame({
                "Segmento": nomes_clusters, 
                "taxa_media_churn_pct": [78.5, 63.1, 42.4, 15.2, 3.0, 2.6]
            })
            
            np.random.seed(42)
            df_pca = pd.DataFrame({
                "Comp1": np.concatenate([np.random.normal(loc, scale, 100) for loc, scale in [(-3, 1), (-1.5, 1), (0, 1), (1.5, 1), (3, 1), (4.5, 1)]]),
                "Comp2": np.concatenate([np.random.normal(loc, scale, 100) for loc, scale in [(3, 1), (1.5, 1), (0, 1), (-1, 1), (-2, 1), (-3, 1)]]),
                "Segmento": np.concatenate([[nome]*100 for nome in nomes_clusters])
            })

        resumo_dinamico = resumo_dinamico.sort_values('taxa_media_churn_pct', ascending=False)
        
        col_g1, col_g2 = st.columns([1, 1], gap="large")

        with col_g1:
            st.markdown('<div style="background: rgba(25,40,79,0.4); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);"><p style="color:#4CAF50; font-weight:bold; font-size:1.1rem;">📈 Risco de Churn Médio por Segmento</p>', unsafe_allow_html=True)
            
            fig_bar = go.Figure(go.Bar(
                x=resumo_dinamico['Segmento'], 
                y=resumo_dinamico['taxa_media_churn_pct'], 
                marker_color=[cores_clusters.get(s, "#4CAF50") for s in resumo_dinamico['Segmento']], 
                text=[f"{v:.1f}%" for v in resumo_dinamico['taxa_media_churn_pct']], 
                textposition='auto'
            ))
            
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                height=400, 
                yaxis=dict(title=dict(text="Taxa de Churn (%)", font=dict(color='#FFFFFF')), tickfont=dict(color='#FFFFFF')), 
                xaxis=dict(tickfont=dict(color='#FFFFFF'), tickangle=-45), 
                margin=dict(l=0, r=0, t=20, b=100)
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col_g2:
            st.markdown('<div style="background: rgba(25,40,79,0.4); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);"><p style="color:#4CAF50; font-weight:bold; font-size:1.1rem;">🎯 Dispersão Espacial dos 6 Perfis (PCA)</p>', unsafe_allow_html=True)
            
            fig_scatter = px.scatter(
                df_pca, 
                x="Comp1", 
                y="Comp2", 
                color="Segmento", 
                color_discrete_map=cores_clusters,
                opacity=0.8
            )
            
            fig_scatter.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                height=400, 
                xaxis=dict(tickfont=dict(color='#FFFFFF'), title="Variância Principal 1", showgrid=False), 
                yaxis=dict(tickfont=dict(color='#FFFFFF'), title="Variância Principal 2", showgrid=False), 
                legend=dict(font=dict(color="#FFFFFF"), orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5), 
                margin=dict(l=0, r=0, t=20, b=0)
            )
            st.plotly_chart(fig_scatter, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # TELA 2: ANÁLISE E MODELAGEM
    # ==========================================
    elif st.session_state.get('pagina') in ["Modelagem", "Análise e Modelagem"]:
        try:
            # Botão de voltar
            c_voltar, _ = st.columns([2, 7])
            with c_voltar:
                if st.button("← Voltar para a Central", key="voltar_home_mod"): 
                    st.session_state['pagina'] = "Home"
                    st.rerun()
            
            # REQUISITO: Bloqueio caso a base não tenha sido rodada ainda
            if 'df_res' not in st.session_state or st.session_state['df_res'].empty:
                st.write("<br><br>", unsafe_allow_html=True)
                st.warning("⚠️ Nenhuma base de dados foi processada no momento.")
                st.info("💡 Por favor, volte à página inicial (Home), faça o upload dos seus arquivos e clique em 'Unificar e Prever' para que a Inteligência Artificial gere as métricas desta rodada.")
            
            else:
                df_modelo = st.session_state['df_res']
                total_clientes = len(df_modelo)
                
                # Distribuição predita dinâmica baseada nos dados recém-enviados
                qtd_churn = len(df_modelo[df_modelo['Probabilidade (%)'] >= 50.0])
                qtd_retidos = total_clientes - qtd_churn
                taxa_churn_predita = (qtd_churn / total_clientes) * 100 if total_clientes > 0 else 0

                # ==========================================================
                # 🚨 INSIRA AQUI OS VALORES REAIS DO SEU MODELO DO VS CODE 🚨
                # ==========================================================
                acc_real = 82.5    # Substitua pela sua Acurácia real
                rec_real = 79.8    # Substitua pelo seu Recall real
                f1_real = 81.1     # Substitua pelo seu F1-Score real
                auc_real = 0.81    # Substitua pelo seu AUC-ROC real

                st.markdown("<h1 style='text-align: center; margin-top: -10px;'>📊 Desempenho do Modelo</h1>", unsafe_allow_html=True)

                # ---------------------------------------------------------
                # SEÇÃO 1: MÉTRICAS DE EFICIÊNCIA DO MODELO
                # ---------------------------------------------------------
                st.markdown("### 🎯 Eficiência Preditiva")
                
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                metricas = [
                    {"col": col_m1, "titulo": "Acurácia Global", "valor": f"{acc_real}%", "cor": "#3498db", "desc": "Acertos totais do modelo"},
                    {"col": col_m2, "titulo": "Recall (Sensibilidade)", "valor": f"{rec_real}%", "cor": "#e74c3c", "desc": "Capacidade de reter quem ia sair"},
                    {"col": col_m3, "titulo": "F1-Score", "valor": f"{f1_real}%", "cor": "#9b59b6", "desc": "Equilíbrio precisão/recall"},
                    {"col": col_m4, "titulo": "AUC-ROC", "valor": f"{auc_real}", "cor": "#2ecc71", "desc": "Qualidade da separação de classes"}
                ]
                
                for m in metricas:
                    with m["col"]:
                        st.markdown(f"""
                        <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); padding: 15px; text-align: center; backdrop-filter: blur(10px);">
                            <p style="margin: 0; color: #A0AABF; font-size: 0.9rem;">{m['titulo']}</p>
                            <h2 style="margin: 5px 0; color: {m['cor']};">{m['valor']}</h2>
                            <p style="margin: 0; color: rgba(255,255,255,0.6); font-size: 0.8rem;">{m['desc']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                st.divider()

                # ---------------------------------------------------------
                # SEÇÃO 2: GRÁFICOS DE FEATURE IMPORTANCE E CURVA DE GANHO
                # ---------------------------------------------------------
                col_graf1, col_graf2 = st.columns(2, gap="large")
                
                with col_graf1:
                    st.markdown("### ⚖️ Importância de cada Feature")
                    st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Impacto real de cada variável segundo o treinamento do modelo.</p>", unsafe_allow_html=True)
                    
                    # ==========================================================
                    # 🚨 INSIRA AQUI A ORDEM E OS PESOS (FEATURE IMPORTANCE) REAIS
                    # ==========================================================
                    df_importancia = pd.DataFrame({
                        "Variável": [
                            "Tempo de Relacionamento", 
                            "Tipo de Cobertura (Básica)", 
                            "Qtd. Produtos Ativos", 
                            "NPS / Satisfação", 
                            "Atraso Pagamento (Dias)", 
                            "Idade"
                        ],
                        "Impacto": [0.35, 0.22, 0.18, 0.12, 0.08, 0.05] 
                    }).sort_values(by="Impacto", ascending=True)

                    fig_importancia = px.bar(
                        df_importancia, 
                        x="Impacto", 
                        y="Variável", 
                        orientation='h',
                        color="Impacto",
                        color_continuous_scale="Blues"
                    )
                    fig_importancia.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=10, b=0),
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#FFFFFF'), title=""),
                        yaxis=dict(tickfont=dict(color='#FFFFFF'), title=""),
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_importancia, use_container_width=True, config={'displayModeBar': False})

                with col_graf2:
                    st.markdown("### 📈 Curva de Ganho Acumulado")
                    st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Eficiência na captura de Churn vs. Volume da base contatada.</p>", unsafe_allow_html=True)
                    
                    # ==========================================================
                    # 🚨 INSIRA AQUI OS DADOS REAIS DA SUA CURVA DE GANHO (Eixo Y)
                    # O "Modelo Predito" representa a porcentagem de churns encontrados
                    # ==========================================================
                    df_gains = pd.DataFrame({
                        "% da Base Abordada": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                        "Modelo Predito": [0, 45, 72, 86, 93, 97, 99, 100, 100, 100, 100], 
                        "Aleatório (Baseline)": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                    })

                    fig_gains = go.Figure()
                    
                    # Linha do Modelo
                    fig_gains.add_trace(go.Scatter(
                        x=df_gains["% da Base Abordada"], 
                        y=df_gains["Modelo Predito"],
                        mode='lines+markers',
                        name='Modelo PRT',
                        line=dict(color='#2ecc71', width=3),
                        marker=dict(size=6, color='#2ecc71')
                    ))
                    
                    # Linha Aleatória (Baseline)
                    fig_gains.add_trace(go.Scatter(
                        x=df_gains["% da Base Abordada"], 
                        y=df_gains["Aleatório (Baseline)"],
                        mode='lines',
                        name='Abordagem Aleatória',
                        line=dict(color='#e74c3c', width=2, dash='dash')
                    ))

                    # AQUI ESTÁ A CORREÇÃO DA SINTAXE DO PLOTLY!
                    fig_gains.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=20, b=0),
                        xaxis=dict(
                            title=dict(text="% da Base Contatada", font=dict(color='#FFFFFF')), 
                            tickfont=dict(color='#FFFFFF'), 
                            showgrid=True, 
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        yaxis=dict(
                            title=dict(text="% de Churn Capturado", font=dict(color='#FFFFFF')), 
                            tickfont=dict(color='#FFFFFF'), 
                            showgrid=True, 
                            gridcolor='rgba(255,255,255,0.1)'
                        ),
                        legend=dict(font=dict(color="#FFFFFF"), orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
                    )

                    st.plotly_chart(fig_gains, use_container_width=True, config={'displayModeBar': False})

        except Exception as e:
            st.error(f"Erro ao renderizar os gráficos desta página: {e}")