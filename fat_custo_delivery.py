#!/usr/bin/env python
# coding: utf-8
from operator import index
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns

# Ignore warnings
import sys
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")



# Import files
    df_tickets = pd.read_excel('Pedidos_Semantix_22.02.xlsx')
    df_tickets = df_tickets[(df_tickets['Status ClearSale'] != 'Pedido cancelado') & 
                            (df_tickets['Status ClearSale'] != 'Pagamento não autorizado pelo antifraude')]

    df_fat = pd.read_excel('OrcamentoPL.xlsx')

    df_frete = pd.read_excel('Custo Conta a Conta.xlsx')
    df_frete = df_frete[df_frete['Nome do Mês'].isna() == False].fillna(0)
    df_frete = df_frete.rename(columns={'Nome do Mês':'Meses'})

    df = pd.merge(df_fat, df_frete, on=['Ano','Meses'])
    df = pd.concat([df,df_fat], keys=['Ano', 'Meses'], ignore_index=True).drop_duplicates(subset ='Meses', keep = 'first').fillna(0)

    custoFrete = ['(-)PIS/COFINS combust.','Aluguéis de veículos','Combustível',
                'IPVA','Licenciamento','Mão de obra','Peças','Multas','Pedágio',
                'Pneus','Delivery','HeadCount']

    df['Custo_realizado'] = df[custoFrete].apply(lambda x: x.sum(), axis=1)



# Título do aplicativo
    st.title('Visão delivery\n')
    #st.write('texto'hsilvahs66543)



# Inputs
    tickets = st.sidebar.number_input('Quantidade de tickets do último mês', min_value=1) # Quantidade de tickets do último mês
    tm = st.sidebar.number_input('Ticket médio', min_value=1.00) # Ticket médio
    carros = st.sidebar.number_input('Quantidade total de carros para o Delivery', min_value=1) # Quantidade total de carros para o delivery
    st.sidebar.write('#### Selecione os custos variáveis de acordo com a quantidade de entregas')
    checkbox_1 = st.sidebar.checkbox('PIS/COFINS combust.')    # (-)PIS/COFINS combust.
    checkbox_2 = st.sidebar.checkbox('Aluguéis de veículos')   # Aluguéis de veículos
    checkbox_3 = st.sidebar.checkbox('Combustível')            # Combustível
    checkbox_4 = st.sidebar.checkbox('IPVA')                   # IPVA
    checkbox_5 = st.sidebar.checkbox('Licenciamento')          # Licenciamento
    checkbox_6 = st.sidebar.checkbox('Mão de obra')            # Mão de obra
    checkbox_7 = st.sidebar.checkbox('Peças')                  # Peças
    checkbox_8 = st.sidebar.checkbox('Multas')                 # Multas
    checkbox_9 = st.sidebar.checkbox('Pedágio')                # Pedágio
    checkbox_10 = st.sidebar.checkbox('Pneus')                 # Pneus
    checkbox_11 = st.sidebar.checkbox('Delivery Spot')         # Delivery
    checkbox_12 = st.sidebar.checkbox('Motoristas')            # HeadCount

    checkboxes =[checkbox_1,checkbox_2,checkbox_3,checkbox_4,checkbox_5,checkbox_6,checkbox_7,checkbox_8,checkbox_9,
                checkbox_10, checkbox_11, checkbox_12]



# Custos fixos (cf) e custos variáveis (cv)
    ultimoMes = len(df_frete) - 1 # Linha onde está o último mês
    ini = 2 # Terceira coluna. A partir da próxima, começam os valores de custo (o índice inicial é 0)
    ii = 0 # contador
    cv = 0
    cf = 0
    for check in checkboxes:
        ii = ii + 1
        if check == True:
            cv = cv + (df.iloc[ultimoMes, ii+ini].sum()) / tickets
        else:
            cf = cf + (df.iloc[ultimoMes, ii+ini].sum())



# Estimar os custos dos meses faltantes
    df['Tickets_projetados'] = df.apply(lambda x: (x['Receita PL - Delivery'] / tm) if x['Custo_realizado'] == 0 else 0, axis=1)
    df['Custo_projetado'] = df.apply(lambda x: ((x['Receita PL - Delivery'] / tm)*cv + cf) if x['Custo_realizado'] == 0 else 0, axis=1)
    df['Custo_total'] = df['Custo_realizado'] + df['Custo_projetado']
    df['Custo_x_Faturamento'] = df['Custo_total'] / df['Receita PL - Delivery']



# Gráfico
    df_temp1 = df[['Ano','Meses','Receita PL - Delivery']]
    df_temp1 = df_temp1.rename(columns={'Receita PL - Delivery':'Valor'})
    df_temp1['Tipo'] = 'Receita PL - Delivery'

    df_temp2 = df[['Ano','Meses','Custo_total']]
    df_temp2 = df_temp2.rename(columns={'Custo_total':'Valor'})
    df_temp2['Tipo'] = 'Custo Frete'

    df_temp = df_temp1.append(df_temp2)

    def plot_grafico(dataframe):

        fig, ax = plt.subplots(figsize=(8,6))
        ax = sns.barplot(x = 'Meses', y = 'Valor', hue = 'Tipo', data = dataframe)
        ax.set_title('', fontsize = 16)
        ax.set_xlabel('Meses', fontsize = 12)
        ax.tick_params(rotation = 20, axis = 'x')
        ax.set_ylabel('MR$', fontsize = 12)


        #ax2 = ax.twinx()
        #ax2.set_ylim(ax.get_ylim())
        #ax2.set_yticklabels(np.round(0,0.3))
        #ax2.set_ylabel('Custo/Faturamento')    
    
        return fig

    figura = plot_grafico(df_temp)
    st.pyplot(figura)

    

# Tabela com valores do gráfico
    df_valores = df[['Ano','Meses','Receita PL - Delivery','Custo_total','Custo_x_Faturamento']]
    df_valores['Receita PL - Delivery'] = (df_valores['Receita PL - Delivery'] / 1000000).round(3)
    df_valores['Custo_total'] = (df_valores['Custo_total'] / 1000000).round(3)
    df_valores['Custo_x_Faturamento'] = df_valores['Custo_x_Faturamento'].round(3)

    st.dataframe(df_valores.set_index('Meses')[['Receita PL - Delivery','Custo_total','Custo_x_Faturamento']], 2000, 1000)
    
    d = {'Receita PL - Delivery': df_valores['Receita PL - Delivery'].sum(), 
         'Custo_total': df_valores['Custo_total'].sum(), 
         'Custo_x_Faturamento': (df_valores['Custo_total'].sum() / df_valores['Receita PL - Delivery'].sum())}
         
    df_ano = pd.DataFrame(data=d, index=['Total Anual'])

    st.dataframe(df_ano, 2000, 1000)
