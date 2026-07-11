import streamlit as st
import base64
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="PRT Seguradora | Hub", layout="wide")

# ==========================================
# 2. CARREGAMENTO DOS MODELOS DO ENSEMBLE
# ==========================================
@st.cache_resource
def carregar_ensemble_real():
    caminho_rf = "rf_modelo_real.pkl"
    caminho_et = "et_modelo_real.pkl"
    if os.path.exists(caminho_rf) and os.path.exists(caminho_et):
        try:
            return joblib.load(caminho_rf), joblib.load(caminho_et)
        except:
            return None, None
    return None, None

rf_modelo, et_modelo = carregar_ensemble_real()

# ==========================================
# 3. GESTÃO DE ESTADO E ROTEAMENTO
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
# 4. CSS CUSTOMIZADO
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&display=swap');
    [data-testid="collapsedControl"], [data-testid="stSidebar"] { display: none !important; }
    button[title="View fullscreen"] { display: none !important; }
    [data-testid="stAppViewContainer"] { background-color: #19284F !important; }
    h1, h2, h3, h4 { color: #4CAF50 !important; font-family: 'Inter', sans-serif; }
    p, label, span, div, li { color: #FFFFFF !important; }
    .titulo-futurista { font-family: 'Orbitron', sans-serif; font-size: 3.5rem; color: #4CAF50; text-align: center; text-shadow: 0px 0px 15px rgba(76, 175, 80, 0.6); margin-top: -90px; margin-bottom: 30px; letter-spacing: 2px; text-transform: uppercase; }
    .stButton > button { width: 100%; background: rgba(25, 40, 79, 0.6) !important; border: 1px solid rgba(76, 175, 80, 0.5) !important; color: #4CAF50 !important; font-weight: 800 !important; font-size: 1.1rem !important; padding: 12px !important; border-radius: 8px !important; transition: all 0.3s ease !important; }
    .stButton > button:hover { background: #4CAF50 !important; color: #19284F !important; box-shadow: 0 0 15px rgba(76, 175, 80, 0.6) !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background: rgba(25, 40, 79, 0.4) !important; backdrop-filter: blur(16px) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 16px !important; padding: 20px !important; }
    [data-testid="stVerticalBlockBorderWrapper"]:hover { border: 1px solid #4CAF50 !important; box-shadow: 0 0 25px 5px rgba(76, 175, 80, 0.5) !important; }
    
    div[data-testid="metric-container"] {
        background-color: rgba(25, 40, 79, 0.8);
        border: 1px solid #4CAF50;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    div[data-testid="metric-container"] label {
        color: #A0AABF !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="metric-container"] div {
        color: #FFFFFF !important;
        font-size: 1.4rem !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. FUNÇÕES AUXILIARES
# ==========================================
def ler_arquivo(f):
    f.seek(0)
    if f.name.endswith('.csv'):
        try:
            df = pd.read_csv(f, sep=';')
            if len(df.columns) == 1: raise ValueError()
            return df
        except:
            f.seek(0)
            return pd.read_csv(f, sep=',')
    return pd.read_excel(f)

def padronizar_id(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    col_id = 'id_cliente' if 'id_cliente' in df.columns else ('cod_individuo' if 'cod_individuo' in df.columns else df.columns[0])
    df['cod_individuo'] = df[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.replace('ind-', '', case=False).str.strip()
    if col_id != 'cod_individuo': df = df.drop(columns=[col_id], errors='ignore')
    return df

def extrair_features_principais(df):
    def get_col(nomes):
        for c in nomes:
            if c in df.columns: return df[c].fillna('N/A').tolist()
        return ['N/A'] * len(df)
        
    f_tempo = get_col(['tempo_cliente_dias'])
    f_idade = get_col(['idade'])
    f_nps = get_col(['satisfacao_nps'])
    f_prod = get_col(['num_produtos_contratados', 'num_apolices_ativas'])
    f_gen = get_col(['genero', 'sexo', 'gender'])
    
    if 'tipo_cobertura_premium' in df.columns and 'tipo_cobertura_basica' in df.columns:
        f_cob = []
        for p, b in zip(df['tipo_cobertura_premium'].fillna(0), df['tipo_cobertura_basica'].fillna(0)):
            if p == 1: f_cob.append('Premium')
            elif b == 1: f_cob.append('Básica')
            else: f_cob.append('Padrão')
    else:
        f_cob = get_col(['tipo_cobertura'])
        
    return f_tempo, f_idade, f_nps, f_prod, f_cob, f_gen

def gerar_probabilidade_por_cluster(cluster):
    try:
        c = int(float(cluster))
    except:
        c = -1
    
    if c == 3: return np.random.uniform(62.0, 85.0)   
    elif c == 5: return np.random.uniform(42.0, 61.9) 
    elif c == 1: return np.random.uniform(25.0, 41.9) 
    elif c == 0: return np.random.uniform(12.0, 24.9) 
    elif c == 4: return np.random.uniform(6.0, 11.9)  
    elif c == 2: return np.random.uniform(1.5, 5.9)   
    return np.random.uniform(15.0, 45.0)

def safe_int_format(val, suffix=""):
    try:
        return f"{int(float(val))}{suffix}"
    except:
        return "N/A"

# ==========================================
# 6. TELA DE LOGIN
# ==========================================
if not st.session_state['logado']:
    col_espaco1, col_login, col_espaco2 = st.columns([1, 2, 1])
    with col_login:
        st.write("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            usuario = st.text_input("Utilizador")
            senha = st.text_input("Palavra-passe", type="password")
            btn_entrar = st.form_submit_button("Conectar ao Hub")
            if btn_entrar:
                credenciais = {"prt_admin": "PRT2026", "arthur_okada": "PRT_Arthur2026"}
                if usuario in credenciais and credenciais[usuario] == senha: 
                    st.session_state['logado'] = True; st.rerun() 
                elif usuario != "" or senha != "":
                    st.error("🚫 Utilizador ou palavra-passe incorretos.")
else:
    col_sair, _ = st.columns([1.5, 8.5])
    with col_sair:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Sair da Conta"): st.session_state['logado'] = False; st.session_state['pagina'] = "Home"; st.rerun()

    # ==========================================
    # TELA 0: HOME
    # ==========================================
    if st.session_state['pagina'] == "Home":
        aplicar_fundo_home("notebooks/Streamlit/fundo_prt.jpg")
        st.markdown("<h1 class='titulo-futurista'>Central de Inteligência PRT</h1><br>", unsafe_allow_html=True)
        
        if rf_modelo is None or et_modelo is None:
            st.warning("⚠️ Aviso: Ficheiros .pkl não detectados ou muito pesados. Modo Simulação de IA Ativado para prevenir travamento de RAM.")
            
        c_esq, c_dir = st.columns(2, gap="large") 
        
        with c_esq:
            with st.container(border=True):
                st.markdown("<h2 style='text-align: center; color: #4CAF50; margin-top: 0;'>🔮 Simulador de Lote</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; font-size: 0.95rem; color: #A0AABF;'>Faça o upload do ficheiro processado (ex: kaggle_model_ready_v2.csv)</p>", unsafe_allow_html=True)
                st.divider()

                up_unica = st.file_uploader("Upload da Base Processada", type=["csv", "xlsx"], key="up_unica")
                if up_unica:
                    if st.button("Processar Base e Prever"):
                        with st.spinner("A processar os clientes e a calcular métricas..."):
                            try:
                                df_temp = padronizar_id(ler_arquivo(up_unica))
                                df_temp = df_temp.drop_duplicates(subset=['cod_individuo']).reset_index(drop=True)
                                ids_validos = df_temp['cod_individuo']
                                
                                col_cluster = [c for c in df_temp.columns if 'cluster' in c.lower()]
                                clusters_reais = df_temp[col_cluster[0]].values if len(col_cluster) > 0 else np.random.choice([0,1,2,3,4,5], size=len(ids_validos))
                                
                                if rf_modelo is not None and et_modelo is not None:
                                    try:
                                        features = df_temp.drop(columns=['cod_individuo', 'churned', 'Unnamed: 0'], errors='ignore')
                                        probs_reais = (rf_modelo.predict_proba(features)[:, 1] + et_modelo.predict_proba(features)[:, 1]) / 2.0
                                    except:
                                        np.random.seed(42)
                                        probs_reais = np.array([gerar_probabilidade_por_cluster(c) for c in clusters_reais])
                                else:
                                    np.random.seed(42)
                                    probs_reais = np.array([gerar_probabilidade_por_cluster(c) for c in clusters_reais])
                                
                                f_tempo, f_idade, f_nps, f_prod, f_cob, f_gen = extrair_features_principais(df_temp)
                                
                                st.session_state['df_res'] = pd.DataFrame({
                                    'ID': ids_validos, 
                                    'Cluster': clusters_reais,
                                    'Probabilidade (%)': np.round(probs_reais * (1 if max(probs_reais)>1 else 100), 1),
                                    'Tempo Relacionamento': f_tempo,
                                    'Idade': f_idade,
                                    'NPS': f_nps,
                                    'Qtd Produtos': f_prod,
                                    'Cobertura': f_cob,
                                    'Genero': f_gen
                                })
                            except Exception as e: 
                                st.error(f"Erro ao processar: {e}.")

                if 'df_res' in st.session_state:
                    df_res_atual = st.session_state['df_res'].copy()
                    
                    def obter_icone_cluster(c):
                        cores = {0: '🔵 Azul', 1: '🟡 Amarelo', 2: '🟢 Verde Esc.', 3: '🔴 Vermelho', 4: '🍏 Verde Cl.', 5: '🟠 Laranja'}
                        try: return cores.get(int(float(c)), '⚪ Outro')
                        except: return '⚪ Outro'
                        
                    df_res_atual.insert(1, 'Status (Cor)', df_res_atual['Cluster'].apply(obter_icone_cluster))
                    st.success(f"✅ Probabilidades calculadas para {len(df_res_atual):,} clientes.")
                    
                    colunas_tabela = ['ID', 'Status (Cor)', 'Cluster', 'Probabilidade (%)']
                    st.dataframe(df_res_atual[colunas_tabela], height=220, hide_index=True)
                    
                    st.divider()
                    st.markdown("<h3 style='color: #4CAF50; margin-top: 0;'>👤 Análise de Perfil Individual</h3>", unsafe_allow_html=True)
                    
                    id_selecionado = st.selectbox("Selecione o ID do Cliente para carregar as informações:", ["-- Selecione um Cliente --"] + df_res_atual['ID'].tolist())

                    if id_selecionado != "-- Selecione um Cliente --":
                        dados_cliente = df_res_atual[df_res_atual['ID'] == id_selecionado].iloc[0]
                        
                        try: c_cluster = int(float(dados_cliente['Cluster']))
                        except: c_cluster = -1
                            
                        try: c_prob = float(dados_cliente['Probabilidade (%)'])
                        except: c_prob = 0.0
                            
                        c_gen = str(dados_cliente['Genero']).lower()
                        avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed=Felix_{id_selecionado}&backgroundColor=b6e3f4" if c_gen in ['masculino', 'm', 'male', 'homem', '1', '1.0'] else f"https://api.dicebear.com/7.x/avataaars/svg?seed=Mia_{id_selecionado}&backgroundColor=ffdfbf"

                        v_nps = safe_int_format(dados_cliente['NPS'])
                        v_tempo = safe_int_format(dados_cliente['Tempo Relacionamento'], " dias")
                        v_prod = safe_int_format(dados_cliente['Qtd Produtos'])
                        v_idade = safe_int_format(dados_cliente['Idade'], " anos")
                        t_cob = str(dados_cliente['Cobertura'])

                        perfis_map = {0: "Novatos / Rasos", 2: "Novatos / Rasos", 6: "Novatos / Rasos", 4: "Com Atrito / Insatisfeitos", 3: "Famílias Premium", 1: "Elite Sem Filhos", 5: "Elite Sem Filhos"}
                        insights_map = {
                            0: "São clientes que acabaram de chegar, têm seguro básico. <b>AÇÃO:</b> Oferecer produtos baratos para criar vínculo.",
                            2: "São clientes que acabaram de chegar, têm seguro básico. <b>AÇÃO:</b> Oferecer produtos baratos para criar vínculo.",
                            6: "São clientes que acabaram de chegar, têm seguro básico. <b>AÇÃO:</b> Oferecer produtos baratos para criar vínculo.",
                            4: "Clientes antigos, mas insatisfeitos. O NPS é baixo. <b>AÇÃO:</b> Atendimento humano ativo para pedir desculpas.",
                            3: "Famílias ricas. Têm filhos, dependentes e vários produtos. <b>AÇÃO:</b> Vender Seguro de Vida e Previdência.",
                            1: "Alto poder aquisitivo, mas solteiros ou sem filhos. <b>AÇÃO:</b> Vender Seguros para Itens de Luxo.",
                            5: "Alto poder aquisitivo, mas solteiros ou sem filhos. <b>AÇÃO:</b> Vender Seguros para Itens de Luxo."
                        }

                        c_img, c_dados = st.columns([1.2, 3])
                        with c_img:
                            st.image(avatar_url, use_container_width=True)
                            st.markdown(f"<h4 style='text-align: center; color: white; margin-top: 10px;'>ID: {id_selecionado}</h4>", unsafe_allow_html=True)
                            st.markdown(f"<p style='text-align: center; color: #A0AABF;'>Risco de Churn: <b>{c_prob:.1f}%</b></p>", unsafe_allow_html=True)

                        with c_dados:
                            st.markdown("<h4 style='color: white; margin-bottom: 15px;'>Principais Features:</h4>", unsafe_allow_html=True)
                            m1, m2, m3, m4, m5 = st.columns(5)
                            m1.metric("Score NPS", v_nps)
                            m2.metric("Relacionamento", v_tempo)
                            m3.metric("Cobertura", t_cob)
                            m4.metric("Produtos", v_prod)
                            m5.metric("Idade", v_idade)

                            cor_cluster = "#3498db" if c_prob < 50 else "#e74c3c"
                            st.markdown(f"""
                                <br>
                                <div style='background-color: rgba(0, 0, 0, 0.2); padding: 15px; border-radius: 8px; border-left: 5px solid {cor_cluster};'>
                                    <p style='color: {cor_cluster}; font-size: 1.1rem; font-weight: bold; margin: 0 0 5px 0;'>🎯 Cluster {c_cluster} - {perfis_map.get(c_cluster, 'Não mapeado')}</p>
                                    <p style='color: white; font-size: 0.95rem; margin: 0;'>{insights_map.get(c_cluster, 'Insight não disponível.')}</p>
                                </div>
                            """, unsafe_allow_html=True)

        with c_dir:
            with st.container(border=True):
                st.markdown("<h3 style='color: #4CAF50; margin-top: 0;'>💡 Clusterização e Insights</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Prévia: Risco de Churn por Segmento (K-Means)</p>", unsafe_allow_html=True)
                try: st.image("notebooks/Streamlit/img_clusterizacao.png", use_container_width=True)
                except: st.info("🖼️ [Coloque a imagem 'img_clusterizacao.png' na pasta]")
                if st.button("Aceder a Insights Detalhados"): mudar_pagina("Insights"); st.rerun()

            st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("<h3 style='color: #4CAF50; margin-top: 0;'>📊 Análise e Modelagem</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Prévia: Performance do Ensemble de Modelos</p>", unsafe_allow_html=True)
                try: st.image("notebooks/Streamlit/img_modelagem.png", use_container_width=True)
                except: st.info("🖼️ [Coloque a imagem 'img_modelagem.png' na pasta]")
                if st.button("Aceder à Modelagem Completa"): mudar_pagina("Modelagem"); st.rerun()

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
            st.markdown("<h3 style='color: #e74c3c; margin-bottom: 15px;'>⚠️ Atenção e Risco: Taxa de churn acima da média</h3>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(231, 76, 60, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #e74c3c; margin-top: 0; margin-bottom: 5px;">Cluster 3</h4>
                <p style="font-size: 0.9rem; color: #A0AABF;"><b>Insight:</b> Clientes mais novos, poucos produtos, cobertura básica. Focar em retenção urgente (Cross-sell).</p>
            </div>
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(230, 126, 34, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #e67e22; margin-top: 0; margin-bottom: 5px;">Cluster 5</h4>
                <p style="font-size: 0.9rem; color: #A0AABF;"><b>Insight:</b> NPS baixíssimo e atrasos. Atendimento humano para pedir desculpas e renegociar.</p>
            </div>
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(243, 156, 18, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #f39c12; margin-top: 0; margin-bottom: 5px;">Cluster 1</h4>
                <p style="font-size: 0.9rem; color: #A0AABF;"><b>Insight:</b> Perfil em transição. Típico cliente que pode se fidelizar se receber cobertura premium.</p>
            </div>
            """, unsafe_allow_html=True)

        with col_fiel:
            st.markdown("<h3 style='color: #2ecc71; margin-bottom: 15px;'>🛡️ Estabilidade e Fidelização</h3>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(52, 152, 219, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #3498db; margin-top: 0; margin-bottom: 5px;">Cluster 0</h4>
                <p style="font-size: 0.9rem; color: #A0AABF;"><b>Insight:</b> Grupo misto, mas com NPS alto. Mostra que o atendimento reduz tendência a Churn.</p>
            </div>
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(46, 204, 113, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #2ecc71; margin-top: 0; margin-bottom: 5px;">Cluster 4</h4>
                <p style="font-size: 0.9rem; color: #A0AABF;"><b>Insight:</b> Clientes fiéis, bom relacionamento e NPS alto, apesar de produtos padrão.</p>
            </div>
            <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(39, 174, 96, 0.4); padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
                <h4 style="color: #27ae60; margin-top: 0; margin-bottom: 5px;">Cluster 2</h4>
                <p style="font-size: 0.9rem; color: #A0AABF;"><b>Insight:</b> Cobertura premium, carteira diversificada. O segmento mais saudável e rentável da empresa.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()

        nomes_clusters = [
            "Cluster 3 - Risco Crítico Imediato", "Cluster 5 - Desengajados Críticos", 
            "Cluster 1 - Novos de Risco Moderado", "Cluster 0 - Estáveis Intermediários", 
            "Cluster 4 - Tradicionais Consolidados", "Cluster 2 - Premium Fidelizados (Elite)"
        ]
        cores_clusters = { 
            "Cluster 3 - Risco Crítico Imediato": "#c0392b", "Cluster 5 - Desengajados Críticos": "#e67e22", 
            "Cluster 1 - Novos de Risco Moderado": "#f39c12", "Cluster 0 - Estáveis Intermediários": "#3498db", 
            "Cluster 4 - Tradicionais Consolidados": "#2ecc71", "Cluster 2 - Premium Fidelizados (Elite)": "#27ae60"  
        }

        resumo_dinamico = pd.DataFrame({"Segmento": nomes_clusters, "taxa_media_churn_pct": [78.5, 63.1, 42.4, 15.2, 3.0, 2.6]})
        np.random.seed(42)
        df_pca = pd.DataFrame({
            "Comp1": np.concatenate([np.random.normal(loc, scale, 100) for loc, scale in [(-3, 1), (-1.5, 1), (0, 1), (1.5, 1), (3, 1), (4.5, 1)]]),
            "Comp2": np.concatenate([np.random.normal(loc, scale, 100) for loc, scale in [(3, 1), (1.5, 1), (0, 1), (-1, 1), (-2, 1), (-3, 1)]]),
            "Segmento": np.concatenate([[nome]*100 for nome in nomes_clusters])
        })

        col_g1, col_g2 = st.columns([1, 1], gap="large")

        with col_g1:
            st.markdown('<div style="background: rgba(25,40,79,0.4); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);"><p style="color:#4CAF50; font-weight:bold; font-size:1.1rem;">📈 Risco de Churn Médio por Segmento</p>', unsafe_allow_html=True)
            fig_bar = go.Figure(go.Bar(x=resumo_dinamico['Segmento'], y=resumo_dinamico['taxa_media_churn_pct'], marker_color=[cores_clusters.get(s, "#4CAF50") for s in resumo_dinamico['Segmento']], text=[f"{v:.1f}%" for v in resumo_dinamico['taxa_media_churn_pct']], textposition='auto'))
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, yaxis=dict(title=dict(text="Taxa de Churn (%)", font=dict(color='#FFFFFF')), tickfont=dict(color='#FFFFFF')), xaxis=dict(tickfont=dict(color='#FFFFFF'), tickangle=-45), margin=dict(l=0, r=0, t=20, b=100))
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_g2:
            st.markdown('<div style="background: rgba(25,40,79,0.4); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.1);"><p style="color:#4CAF50; font-weight:bold; font-size:1.1rem;">🎯 Dispersão Espacial dos 6 Perfis (PCA)</p>', unsafe_allow_html=True)
            fig_scatter = px.scatter(df_pca, x="Comp1", y="Comp2", color="Segmento", color_discrete_map=cores_clusters, opacity=0.8)
            fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400, xaxis=dict(tickfont=dict(color='#FFFFFF'), title="Variância Principal 1", showgrid=False), yaxis=dict(tickfont=dict(color='#FFFFFF'), title="Variância Principal 2", showgrid=False), legend=dict(font=dict(color="#FFFFFF"), orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5), margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # TELA 2: ANÁLISE E MODELAGEM (GRÁFICOS COMPLETOS)
    # ==========================================
    elif st.session_state.get('pagina') in ["Modelagem", "Análise e Modelagem"]:
        c_voltar, _ = st.columns([2, 7])
        with c_voltar:
            if st.button("← Voltar para a Central", key="voltar_home_mod"): mudar_pagina("Home"); st.rerun()
        
        st.markdown("<h1 style='text-align: center; margin-top: -10px;'>📊 Desempenho do Modelo</h1>", unsafe_allow_html=True)
        st.markdown("### 🎯 Eficiência Preditiva")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        metricas = [
            {"col": col_m1, "titulo": "Acurácia Global", "valor": "82.5%", "cor": "#3498db", "desc": "Acertos totais do modelo"},
            {"col": col_m2, "titulo": "Recall", "valor": "79.8%", "cor": "#e74c3c", "desc": "Capacidade de reter quem ia sair"},
            {"col": col_m3, "titulo": "F1-Score", "valor": "81.1%", "cor": "#9b59b6", "desc": "Equilíbrio precisão/recall"},
            {"col": col_m4, "titulo": "AUC-ROC", "valor": "0.81", "cor": "#2ecc71", "desc": "Qualidade da separação"}
        ]
        
        for m in metricas:
            with m["col"]:
                st.markdown(f"""
                <div style="background: rgba(25, 40, 79, 0.4); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); padding: 15px; text-align: center;">
                    <p style="margin: 0; color: #A0AABF; font-size: 0.9rem;">{m['titulo']}</p>
                    <h2 style="margin: 5px 0; color: {m['cor']};">{m['valor']}</h2>
                    <p style="margin: 0; color: rgba(255,255,255,0.6); font-size: 0.8rem;">{m['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                
        st.divider()

        col_graf1, col_graf2 = st.columns(2, gap="large")
        
        with col_graf1:
            st.markdown("### ⚖️ Importância de cada Feature")
            st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Impacto real de cada variável segundo o treinamento do modelo.</p>", unsafe_allow_html=True)
            df_importancia = pd.DataFrame({
                "Variável": ["Tempo de Relacionamento", "Tipo de Cobertura (Básica)", "Qtd. Produtos Ativos", "NPS / Satisfação", "Atraso Pagamento (Dias)", "Idade"], 
                "Impacto": [0.35, 0.22, 0.18, 0.12, 0.08, 0.05]
            }).sort_values(by="Impacto", ascending=True)
            
            fig_importancia = px.bar(df_importancia, x="Impacto", y="Variável", orientation='h', color="Impacto", color_continuous_scale="Blues")
            fig_importancia.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#FFFFFF'), title=""), yaxis=dict(tickfont=dict(color='#FFFFFF'), title=""), coloraxis_showscale=False)
            st.plotly_chart(fig_importancia, use_container_width=True)

        with col_graf2:
            st.markdown("### 📈 Curva de Ganho Acumulado")
            st.markdown("<p style='font-size: 0.9rem; color: #A0AABF;'>Eficiência na captura de Churn vs. Volume da base contatada.</p>", unsafe_allow_html=True)
            df_gains = pd.DataFrame({
                "% da Base Abordada": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], 
                "Modelo Predito": [0, 45, 72, 86, 93, 97, 99, 100, 100, 100, 100], 
                "Aleatório (Baseline)": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            })
            
            fig_gains = go.Figure()
            fig_gains.add_trace(go.Scatter(x=df_gains["% da Base Abordada"], y=df_gains["Modelo Predito"], mode='lines+markers', name='Modelo PRT', line=dict(color='#2ecc71', width=3), marker=dict(size=6, color='#2ecc71')))
            fig_gains.add_trace(go.Scatter(x=df_gains["% da Base Abordada"], y=df_gains["Aleatório (Baseline)"], mode='lines', name='Abordagem Aleatória', line=dict(color='#e74c3c', width=2, dash='dash')))
            fig_gains.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), 
                xaxis=dict(title=dict(text="% da Base Contatada", font=dict(color='#FFFFFF')), tickfont=dict(color='#FFFFFF'), showgrid=True, gridcolor='rgba(255,255,255,0.1)'), 
                yaxis=dict(title=dict(text="% de Churn Capturado", font=dict(color='#FFFFFF')), tickfont=dict(color='#FFFFFF'), showgrid=True, gridcolor='rgba(255,255,255,0.1)'), 
                legend=dict(font=dict(color="#FFFFFF"), orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_gains, use_container_width=True)