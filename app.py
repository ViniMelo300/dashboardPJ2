import streamlit as st
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Dashboard de Mobilidade Urbana")

st.title("Dashboard Interativo de Mobilidade Urbana")
st.markdown("Use os filtros na barra lateral para explorar os dados.")

# --- Carregamento dos Dados ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{file_path}' não foi encontrado. Certifique-se de que ele está na mesma pasta que o app.py.")
        return None

# Carrega o dataframe
df = load_data('mobilidade_urbana_processada.csv')

if df is not None:
    # --- Barra Lateral de Filtros ---
    st.sidebar.header("Filtros Interativos")

    # Filtro de Ruas
    rua_options = df['rua/avenida'].unique()
    rua_filter = st.sidebar.multiselect(
        "Selecione a(s) Rua(s)/Avenida(s):",
        options=rua_options,
        default=rua_options
    )

    # Filtro de Hora
    hora_options = sorted(df['hora'].unique())
    hora_filter = st.sidebar.multiselect(
        "Selecione o(s) Horário(s):",
        options=hora_options,
        default=hora_options
    )

    # Filtro de Clima
    clima_options = df['chuva'].unique()
    clima_filter = st.sidebar.multiselect(
        "Selecione a(s) Condição(ões) Climática(s):",
        options=clima_options,
        default=clima_options
    )
    
    # Filtro de Tipo de Veículo
    veiculo_options = df['tipo_de_veículo'].unique()
    veiculo_filter = st.sidebar.multiselect(
        "Selecione o(s) Tipo(s) de Veículo(s):",
        options=veiculo_options,
        default=veiculo_options
    )

    # --- Aplica os filtros no DataFrame ---
    df_filtrado = df.query(
        "`rua/avenida` == @rua_filter & " +
        "hora == @hora_filter & " +
        "chuva == @clima_filter & " +
        "`tipo_de_veículo` == @veiculo_filter"
    )
    
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados. Por favor, ajuste sua seleção.")
    else:
        # --- Layout do Dashboard com Abas ---
        tab1, tab2, tab3 = st.tabs(["Visão Geral", "Heatmap de Congestionamento", "Análise por Clima e Veículo"])

        with tab1:
            st.header("Visão Geral do Congestionamento")
            
            # --- 1. Ruas com Maior Congestionamento (COM BARRAS GROSSAS) ---
            st.subheader("Ruas com Maior Índice de Congestionamento")
            
            avg_vehicles_by_street = df_filtrado.groupby('rua/avenida')['veículos_por_minuto'].mean().sort_values(ascending=False)
            
            # Converte a Série do pandas em um DataFrame para o Altair
            data_bars = avg_vehicles_by_street.reset_index()

            # Cria o gráfico de barras com Altair
            bar_chart = alt.Chart(data_bars).mark_bar(
                size=80  # Define a espessura da barra
            ).encode(
                x=alt.X('rua/avenida', sort=None, title='Rua/Avenida', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('veículos_por_minuto', title='Média de Veículos por Minuto'),
                color=alt.Color('rua/avenida', title='Local', legend=None),
                tooltip=[
                    alt.Tooltip('rua/avenida', title='Local'),
                    alt.Tooltip('veículos_por_minuto', title='Média Veículos', format='.2f')
                ]
            ).interactive()

            st.altair_chart(bar_chart, use_container_width=True)
            st.markdown("O gráfico acima mostra a média de veículos por minuto nas vias selecionadas.")

            # --- 2. Alertas para Horários Críticos ---
            st.subheader("Horários Críticos")
            avg_vehicles_by_hour = df_filtrado.groupby('hora')['veículos_por_minuto'].mean().sort_values(ascending=False)
            
            col1, col2, col3 = st.columns(3)
            top_horarios = avg_vehicles_by_hour.reset_index().head(3)
            
            if len(top_horarios) > 0:
                col1.metric(f"1º - {top_horarios.iloc[0]['hora']}", f"{top_horarios.iloc[0]['veículos_por_minuto']:.2f} veíc/min")
            if len(top_horarios) > 1:
                col2.metric(f"2º - {top_horarios.iloc[1]['hora']}", f"{top_horarios.iloc[1]['veículos_por_minuto']:.2f} veíc/min")
            if len(top_horarios) > 2:
                col3.metric(f"3º - {top_horarios.iloc[2]['hora']}", f"{top_horarios.iloc[2]['veículos_por_minuto']:.2f} veíc/min")

            st.markdown("Ranking de horários por congestionamento:")
            st.dataframe(avg_vehicles_by_hour)


        with tab2:
            st.header("Análise de Padrões de Tráfego")
            
            # --- 3. Heatmap (COM COR VERMELHA/BRANCA e BORDAS) ---
            st.subheader("Heatmap de Congestionamento (Hora vs. Rua)")
            
            heatmap_data = df_filtrado.groupby(['hora', 'rua/avenida'])['veículos_por_minuto'].mean().reset_index()

            # Criar o heatmap com Altair
            heatmap_chart = alt.Chart(heatmap_data).mark_rect(
                stroke='black',  # Borda preta
                strokeWidth=0.5  # Espessura da borda
            ).encode(
                x=alt.X('hora:O', title='Hora do Dia', sort='ascending', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('rua/avenida:O', title='Rua/Avenida'),
                
                # Escala de cor personalizada: de Branco para Vermelho
                color=alt.Color('veículos_por_minuto:Q', 
                                title='Média Veículos/Min', 
                                scale=alt.Scale(range=['white', 'red'])), 
                
                tooltip=[
                    alt.Tooltip('hora', title='Hora'),
                    alt.Tooltip('rua/avenida', title='Local'),
                    alt.Tooltip('veículos_por_minuto', title='Média de Veículos', format='.2f')
                ]
            ).properties(
                title="Congestionamento por Hora e Local"
            ).interactive()

            # Voltamos a usar 'use_container_width=True'
            st.altair_chart(heatmap_chart, use_container_width=True) 
            
            st.markdown("""
            Passe o mouse sobre o gráfico para ver detalhes. 
            * **Escala de Cor:** Branco (pouco tráfego) -> Vermelho (muito tráfego).
            """)

        with tab3:
            st.header("Classificação por Clima e Tipo de Veículo")

            # --- 4. Gráfico por Condição Climática ---
            st.subheader("Distribuição do Tráfego por Condição Climática")

            fig, ax = plt.subplots(figsize=(10, 6))
            order_clima = ['Tempo seco', 'Chuva leve', 'Chuva intensa']
            sns.boxplot(data=df_filtrado, x='chuva', y='veículos_por_minuto', ax=ax, order=order_clima, palette='pastel')
            ax.set_title('Distribuição de Veículos por Minuto por Clima')
            ax.set_xlabel('Condição Climática')
            ax.set_ylabel('Veículos por Minuto')
            
            st.pyplot(fig)
            st.markdown("Este boxplot mostra a variação do tráfego (mediana, quartis e outliers) para cada condição climática.")

            # --- 5. Tabela por Tipo de Veículo e Clima ---
            st.subheader("Média de Veículos por Tipo e Clima")
            
            avg_by_type_weather = df_filtrado.groupby(['tipo_de_veículo', 'chuva'])['veículos_por_minuto'].mean().unstack()
            
            st.dataframe(avg_by_type_weather.fillna(0)) 
            
        st.sidebar.markdown("---")
        st.sidebar.info("Dashboard criado com base nos requisitos de análise de mobilidade urbana.")
else:
    st.error("Não foi possível carregar os dados. O dashboard não pode ser exibido.")