#!/usr/bin/env python
# coding: utf-8
from multiprocessing.sharedctypes import Value
from operator import concat, index
from datetime import datetime, timedelta
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
    # Relatório de Pedidos por Loja referente ao último mês- Semantix
    df_tickets = pd.read_excel('Pedidos_Semantix.xlsx')
    df_tickets = df_tickets[(df_tickets['Status ClearSale'] != 'Pedido cancelado') & 
                            (df_tickets['Status ClearSale'] != 'Pagamento não autorizado pelo antifraude')]

    # Query no Impala referente às vedas do último mês
    df_digital = pd.read_excel('query_estudo_frete_vtex.xlsx')

    # Planilha de orçamento com valores atualizados até o último mês
    df_fat = pd.read_excel('OrcamentoPL.xlsx')

    # Planilha de distâncias dos clientes para as lojas em que compraram
    df_dist = pd.read_excel('distancias_clientesDelivery_lojas.xlsx')
    df_dist = df_dist[(df_dist.distancia_km.notnull())]

    # Planilha exportada do BI "Ecommerce, delivery" com os custos com frete
    df_frete = pd.read_excel('Custo Conta a Conta.xlsx')
    df_frete = df_frete[df_frete['Date - Mês'].isna() == False].fillna(0)
    df_frete = df_frete.rename(columns={'Date - Mês':'Meses',
                                    'Date - Ano':'Ano'})

    df = pd.merge(df_fat, df_frete, on=['Ano','Meses'])
    df = pd.concat([df,df_fat], keys=['Ano', 'Meses'], ignore_index=True).drop_duplicates(subset ='Meses', keep = 'first').fillna(0)

    custoFrete = ['(-)PIS/COFINS combust.','Aluguéis de veículos','Combustível',
                'IPVA','Licenciamento','Mão de obra','Peças','Multas','Pedágio',
                'Pneus','Delivery','HeadCount']

    df['Custo_realizado'] = df[custoFrete].apply(lambda x: x.sum(), axis=1)



# Funções
    def verifica_express(serie):
        if serie['Tipo Entrega'] == 'Express':
            if (serie['Periodo Entrega'] == 'morning') and ((serie['aprovacao_hora'] > 16) or (serie['aprovacao_hora'] <= 10)):
                x = serie['Tipo Entrega']
            elif (serie['Periodo Entrega'] == 'afternoon') and ((serie['aprovacao_hora'] <= 16) and (serie['aprovacao_hora'] > 10)):
                x = serie['Tipo Entrega']
            else:
                x = 'Convencional'
        else:
            x = serie['Tipo Entrega']

        return x


    def ajusta_data(dados):
        hora = int((datetime.strftime(dados, '%d/%m/%Y %H:%M:%S').split(' ')[1]).split(':')[0])
        if (hora >= 12):
            return datetime.strptime(datetime.strftime(dados, '%d/%m/%Y 12:00:00'), '%d/%m/%Y %H:%M:%S')
        elif (hora < 8):
            return datetime.strptime(datetime.strftime(dados - timedelta(1), '%d/%m/%Y 12:00:00'), '%d/%m/%Y %H:%M:%S')
        else:
            return datetime.strptime(datetime.strftime(dados, '%d/%m/%Y 08:00:00'), '%d/%m/%Y %H:%M:%S')


    def proximo_periodo_entrega(dados):
        dt1 = datetime.strptime(datetime.strftime(dados['dt_aprovacao_ajustado'], '%d/%m/%Y'), '%d/%m/%Y')
        h1 = int(datetime.strftime(dados['dt_aprovacao_ajustado'], '%H'))
        dt2 = datetime.strptime(datetime.strftime(dados['dt_entrega_ajustado'], '%d/%m/%Y'), '%d/%m/%Y')
        h2 = int(datetime.strftime(dados['dt_entrega_ajustado'], '%H'))
        if (h2 - h1 < 0):
            x = (dt2 - dt1).days * 2 - 1
        elif (h2 - h1 == 0):
            x = (dt2 - dt1).days * 2
        else:
            x = (dt2 - dt1).days * 2 + 1
        if x <= 0:
            return 1
        else:
            return x


# Acrécimo de informações na base de pedidos da Semantix
    df_periodos = df_tickets[(df_tickets['Tipo Entrega'] != 'Retirada')]

    df_periodos['Dt Aprovação ClearSale'] = df_periodos['Dt Aprovação ClearSale'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y %H:%M:%S'))
    df_periodos['Dt Inicio Prevista Entrega/Retirada'] = df_periodos['Dt Inicio Prevista Entrega/Retirada'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y %H:%M:%S'))
    df_periodos['aprovacao_hora'] = df_periodos['Dt Aprovação ClearSale'].dt.hour

    df_periodos['tipo_entrega_ajustado'] = df_periodos.apply(lambda x: verifica_express(x), axis=1)
    df_periodos['dt_aprovacao_ajustado'] = df_periodos['Dt Aprovação ClearSale'].apply(lambda x: ajusta_data(x))
    df_periodos['dt_entrega_ajustado'] = df_periodos['Dt Inicio Prevista Entrega/Retirada'].apply(lambda x: ajusta_data(x))

    df_periodos['proximo_periodo_entrega'] = df_periodos.apply(lambda x: proximo_periodo_entrega(x), axis=1)



# Título do aplicativo
    st.title('Visão delivery\n')
    #st.write('texto'hsilvahs66543)



# Variáveis
    digital = df_digital[(df_digital.canal_venda == 'DELIVERY') | (df_digital.canal_venda == 'ECOMMERCE')].valor.sum() / df_digital.valor.sum() # Porcentagem da receita do ecommerce que vem do Ecommerce e do Delivery
    tickets_digital = df_digital[(df_digital.canal_venda == 'DELIVERY') | (df_digital.canal_venda == 'ECOMMERCE')].vendas.sum()
    valor_digital = df_digital[(df_digital.canal_venda == 'DELIVERY') | (df_digital.canal_venda == 'ECOMMERCE')].valor.sum()

    frete_dist_1 = round(df_dist.distancia_km.describe()[4], 1) # Primeiro quartil de distância
    frete_dist_2 = round(df_dist.distancia_km.describe()[5], 1) # Segundo quartil ou mediana de distância
    frete_dist_3 = round(df_dist.distancia_km.describe()[6], 1) # Terceiro quartil de distância

    q1 = len(df_dist[df_dist.distancia_km <= frete_dist_1]) / len(df_dist)
    q2 = len(df_dist[(df_dist.distancia_km > frete_dist_1) & (df_dist.distancia_km <= frete_dist_2)]) / len(df_dist)
    q3 = len(df_dist[(df_dist.distancia_km > frete_dist_2) & (df_dist.distancia_km <= frete_dist_3)]) / len(df_dist)
    q4 = len(df_dist[(df_dist.distancia_km > frete_dist_3)]) / len(df_dist)

    p1 = len(df_periodos[df_periodos.tipo_entrega_ajustado == 'Express']) / len(df_periodos)
    p2 = len(df_periodos[(df_periodos.tipo_entrega_ajustado != 'Express') & (df_periodos.proximo_periodo_entrega == 1)]) / len(df_periodos)
    p3 = len(df_periodos[(df_periodos.tipo_entrega_ajustado != 'Express') & (df_periodos.proximo_periodo_entrega > 1) & (df_periodos.proximo_periodo_entrega <= 4)]) / len(df_periodos)
    p4 = len(df_periodos[(df_periodos.tipo_entrega_ajustado != 'Express') & (df_periodos.proximo_periodo_entrega > 4)]) / len(df_periodos)


# Inputs
    tickets = st.sidebar.number_input('Quantidade de tickets para entrega (último mês)', min_value=1, value=tickets_digital) # Quantidade de tickets do último mês (Ecommerce + Delivery)
    tm = st.sidebar.number_input('Ticket médio', min_value=1.0, value=valor_digital/tickets_digital) # Ticket médio (Ecommerce + Delivery)
    carros = st.sidebar.number_input('Quantidade total de carros para o Delivery', min_value=1, value=89) # Quantidade total de carros para o delivery
    maxEntregas = st.sidebar.number_input('Máximo de pedidos entregues por mês por carro', min_value=1, value=600) # Quantidade máxima de entregas por mês por carro
    fator = st.sidebar.number_input('Fator de multiplicação do faturamento', value=1.00) # Fator de multiplicação do faturamento

    st.sidebar.write('#### Selecione os custos variáveis de acordo com a quantidade de entregas')
    checkbox_1 = st.sidebar.checkbox('PIS/COFINS combust.')    # (-)PIS/COFINS combust.
    checkbox_2 = st.sidebar.checkbox('Aluguéis de veículos')   # Aluguéis de veículos
    checkbox_3 = st.sidebar.checkbox('Combustível', True)      # Combustível
    checkbox_4 = st.sidebar.checkbox('IPVA')                   # IPVA
    checkbox_5 = st.sidebar.checkbox('Licenciamento')          # Licenciamento
    checkbox_6 = st.sidebar.checkbox('Mão de obra', True)      # Mão de obra
    checkbox_7 = st.sidebar.checkbox('Peças', True)            # Peças
    checkbox_8 = st.sidebar.checkbox('Multas')                 # Multas
    checkbox_9 = st.sidebar.checkbox('Pedágio', True)          # Pedágio
    checkbox_10 = st.sidebar.checkbox('Pneus')                 # Pneus
    checkbox_11 = st.sidebar.checkbox('Delivery Spot', True)   # Delivery
    checkbox_12 = st.sidebar.checkbox('Motoristas')            # HeadCount

    checkboxes =[checkbox_1,checkbox_2,checkbox_3,checkbox_4,checkbox_5,checkbox_6,checkbox_7,checkbox_8,checkbox_9,
                checkbox_10, checkbox_11, checkbox_12]

    st.sidebar.write('### Simulador de fretes')
    st.sidebar.write('#### Preços por distâncias')
    frete1 = st.sidebar.number_input('Preço do frete até {} km (1º quartil)'.format(frete_dist_1), value=14.9) # Preço cobrado de frete de compras abaixo de 150 reais
    frete2 = st.sidebar.number_input('Preço do frete entre {} e {} km (2º quartil)'.format(frete_dist_1, frete_dist_2), value=14.9) # Preço cobrado de frete de compras abaixo de 150 reais
    frete3 = st.sidebar.number_input('Preço do frete entre {} e {} km (3º quartil)'.format(frete_dist_2, frete_dist_3), value=14.9) # Preço cobrado de frete de compras abaixo de 150 reais
    frete4 = st.sidebar.number_input('Preço do frete acima de {} km (4º quartil)'.format(frete_dist_3), value=14.9) # Preço cobrado de frete de compras abaixo de 150 reais

    st.sidebar.write('#### Adicionais de frete por período de entrega')
    frete_add1 = st.sidebar.number_input('Adicional até 2h (express)', value=9.9) # Adicional até 2h (express)
    frete_add2 = st.sidebar.number_input('Adicional para o 1º período', value=4.9) # Adicional para o próximo período de entrega
    frete_add3 = st.sidebar.number_input('Adicional entre 2º e 4º períodos', value=2.9) # Adicional entre os períodos 2 e 4 de entrega
    frete_add4 = st.sidebar.number_input('Adicional acima do 4º perído', value=0) # Adicional acima do período 4

    st.sidebar.write('#### Frete grátis')
    limite_frete = st.sidebar.number_input('Preço mínimo para isenção do frete', value=150) # Preço mínimo para isenção do frete



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
            cf = cf + (df.iloc[ultimoMes, ii+ini].sum()) / carros

# Outras váriáveis
    entrega_total = len(df_tickets[(df_tickets['Tipo Entrega'] != 'Retirada')]) / len(df_tickets) # Porcentagem dos pedidos que foram entrega
    entrega_com_frete = len(df_tickets[(df_tickets['Tipo Entrega'] != 'Retirada') & (df_tickets['Total do Pedido'] < limite_frete)]) / len(df_tickets) # Porcentagem dos pedidos que foram entrega com cobrança de frete

# Estimar os custos dos meses faltantes
    df['Receita PL - Delivery'] = df.apply(lambda x: x['Receita PL']*digital*fator if x['Receita PL - Delivery'] == 0 else x['Receita PL - Delivery'], axis=1)
    df['Tickets_projetados'] = df.apply(lambda x: (x['Receita PL - Delivery']*digital / tm) if x['Custo_realizado'] == 0 else 0, axis=1)
    df['Carros_necessarios'] = (df.apply(lambda x: (x['Tickets_projetados']*entrega_total / maxEntregas) if x['Custo_realizado'] == 0 else 0, axis=1)).round(0)

    df['Custo_projetado'] = df.apply(lambda x: x['Tickets_projetados']*cv + carros*cf if x['Carros_necessarios'] != 0 else 0, axis=1)
    df['Custo_projetado'] = df.apply(lambda x: x['Tickets_projetados']*cv + x['Carros_necessarios']*cf if (x['Carros_necessarios'] > carros) else x['Custo_projetado'], axis=1)

    df['Receita_frete'] = df['Tickets_projetados'] * entrega_com_frete * ((q1*frete1 + q2*frete2 + q3*frete3 + q4*frete4) + (p1*frete_add1 + p2*frete_add2 + p3*frete_add3 + p4*frete_add4))
    df['Custo_total'] = df.apply(lambda x: x['Custo_realizado'] + x['Custo_projetado'] - x['Receita_frete'] if x['Receita_frete'] != 0 else 0, axis=1)
    df['Custo_x_Faturamento'] = df['Custo_total'] / df['Receita PL - Delivery']



# Gráfico
    df_filtered = df[df.Custo_total != 0]

    df_temp1 = df_filtered[['Ano','Meses','Receita PL - Delivery']]
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
    df_valores = df[df.Custo_total != 0][['Ano','Meses','Receita PL - Delivery','Custo_total','Custo_x_Faturamento','Receita_frete']]
    df_valores['Receita PL - Delivery'] = (df_valores['Receita PL - Delivery'] / 1000000).round(3)
    df_valores['Custo_total'] = (df_valores['Custo_total'] / 1000000).round(3)
    df_valores['Custo_x_Faturamento'] = df_valores['Custo_x_Faturamento'].round(3)
    df_valores['Receita_frete'] = (df_valores['Receita_frete'] / 1000000).round(3)

    st.dataframe(df_valores.set_index('Meses')[['Receita PL - Delivery','Custo_total','Custo_x_Faturamento','Receita_frete']])
    
    d = {'Receita PL - Delivery': df_valores['Receita PL - Delivery'].sum(), 
         'Custo_total': df_valores['Custo_total'].sum(), 
         'Custo_x_Faturamento': (df_valores['Custo_total'].sum() / df_valores['Receita PL - Delivery'].sum()),
         'Receita_frete': df_valores['Receita_frete'].sum()
         }
         
    df_ano = pd.DataFrame(data=d, index=['Total   '])

    st.dataframe(df_ano)



# Preço médio do frete
    st.write('')
    st.write('##### Preço médio do frete seguindo a proporção de distância e períodos das compras atuais')
    st.write('R$ {} de frete'.format(round(q1*frete1 + q2*frete2 + q3*frete3 + q4*frete4, 2)))
    st.write('R$ {} de acréscimo'.format(round(p1*frete_add1 + p2*frete_add2 + p3*frete_add3 + p4*frete_add4, 2)))
    st.write('Total R$ {}'.format(round(q1*frete1 + q2*frete2 + q3*frete3 + q4*frete4, 2) + round(p1*frete_add1 + p2*frete_add2 + p3*frete_add3 + p4*frete_add4, 2)))
    st.write('')



# Mostrar quantos carros seriam necessários para a configuração feita
    st.write('')
    st.write('##### Quantidade de carros necessários levando em consideração cada mês:')
    st.write('Mínimo: ' + str(int(df[df['Carros_necessarios'] != 0]['Carros_necessarios'].min())) + ' carros')
    st.write('Máximo: ' + str(int(df[df['Carros_necessarios'] != 0]['Carros_necessarios'].max())) + ' carros')
    st.write('Média: ' + str(int(df[df['Carros_necessarios'] != 0]['Carros_necessarios'].mean())) + ' carros')



