# This is a sample Python script.

# Press Mayus+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import base64
import numpy as np
import pandas as pd
import chart_studio as cs
from numpy.ma.core import _convert2ma
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
from datetime import date
import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Email, Mail, Attachment, FileContent, FileName, FileType, Disposition)
import requests
import time
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import math
import traceback
from termcolor import colored

dic_api_key={'bog':'',
             'cmx':'',
             'fed':'KEUnUz9b1vtfYNhrCvrwSCsiZHqZQmQJCfVsJXcy'}

def poll_job(s, redash_url, job):
    # TODO: add timeout
    while job['status'] not in (3, 4):
        response = s.get('{}/api/jobs/{}'.format(redash_url, job['id']))
        job = response.json()['job']
        time.sleep(1)

    if job['status'] == 3:
        return job['query_result_id']

    return None


def get_fresh_query_result(redash_url, query_id, api_key, params):
    s = requests.Session()
    s.headers.update({'Authorization': 'Key {}'.format(api_key)})

    response = s.post('{}/api/queries/{}/refresh'.format(redash_url, query_id), params=params)

    if response.status_code != 200:
        raise Exception(response.status_code)

    result_id = poll_job(s, redash_url, response.json()['job'])

    if result_id:
        response = s.get('{}/api/queries/{}/results/{}.json'.format(redash_url, query_id, result_id))
        if response.status_code != 200:
            raise Exception('Failed getting results.')
    else:
        raise Exception('Query execution failed.')

    return response.json()['query_result']['data']['rows']


def get_db_query(query_id, params, region_code):
    dic_redash_url = {'spo': 'https://redash.br.frubana.com',
                      'bog': 'https://redash.frubana.com',
                      'baq': 'https://redash.frubana.com',
                      'cmx': 'https://redash.mx.frubana.com',
                      'fed': 'https://redash.federate.frubana.com'}

    dic_api_key = {'spo': '',
                   'bog': '',
                   'baq': '',
                   'cmx': '',
                   'fed': 'KEUnUz9b1vtfYNhrCvrwSCsiZHqZQmQJCfVsJXcy'}

    api_key = dic_api_key[region_code]

    redash_url = dic_redash_url[region_code]

    data = get_fresh_query_result(redash_url, query_id, api_key, params)
    dic = {i: [value for key, value in row.items()] for i, row in enumerate(data)}
    df = pd.DataFrame.from_dict(dic, orient='index', columns=list(data[0].keys()))
    return df

#Formato numero
def formatMoney(x):
  return "${:,.2f}".format(x)
def formatDecimal(x):
  return "{:,.2f}%".format(x)

#Funcion color para tablas
def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'green' if val.find('-') == -1 else 'red'
    return 'color: %s' % color


def generarReporte():


    font_config = FontConfiguration()
    css_string = CSS(string='''    .col,*[class^="col-"] { border: 1px solid #eee;} @media print { .col, *[class^="col-"] { max-width: none !important; } }  .subtitulo{ text-decoration: underline; text-decoration-color: red; text-decoration-style: solid; } .col-md-6{ padding: 10px; } .grafica{ width: 100%; } .logoFrub{ float: right; width:150px; } .grafica{width: 50%}''', font_config=font_config)
    #Inicio html

    #User_name chart studio
    username = "lmayadiaz"
    api_key = "IbKCqz4yGo17lWz3wS4N"

    #Importar datos
    params = {}
    try:
        datosSellIn = get_db_query(10098, params, 'fed')
        datosSellOut = get_db_query(11193, params, 'fed')
        datosSellOutProd = get_db_query(9031, params, 'fed')
        datosSellInProd = get_db_query(11253, params, 'fed')
        datosTicketProm = get_db_query(11210, params, 'fed')
        datosInvActual = get_db_query(11206, params, 'fed')
        proveedores = datosSellIn['proveedor'].unique()
        #proveedores =  []
        #proveedores.append(("Comercializadora de Desechables Sideral S.A"))
        correos = get_db_query(12618, params, 'fed')

        # Datos chart studio
        cs.tools.set_credentials_file(username=username, api_key=api_key)

        for proveedorAct in proveedores:
            if((proveedorAct != 'ABASTO BASICO') and (proveedorAct != 'ACEITE MARAVILLA')):
                try:
                    print(proveedorAct)
                    # Sell In Total
                    filtroSellIn = datosSellIn[datosSellIn['proveedor'] == proveedorAct]  # Tomar info un proveedor
                    pais = filtroSellIn['ciudad'].unique()
                    if not filtroSellIn.empty:
                        graphSellInSNS = sns.barplot(data=filtroSellIn, x="semana", y="sell_in", color='#F6CE0E')
                        graphSellInSNS.set(xlabel='Semana', ylabel='Sell In Total')
                        graphSellInSNS.set_title("Sell In Total VS Semana")
                        urlSellIn = "SellIn_" + proveedorAct + ".png"
                        for index, row in filtroSellIn.reset_index().iterrows():
                            graphSellInSNS.text(row.name, row.sell_in, "${:,.0f}".format(round(row.sell_in,0)), color='black',ha="center")
                        graphSellInSNS.figure.savefig(urlSellIn, bbox_inches='tight')
                        plt.close()
                        '''figSellIn = px.bar(filtroSellIn, x="semana", y="sell_in",
                                           text=filtroSellIn['sell_in'].apply(formatMoney),
                                           title="¿Cuánto te compramos en estas semanas?",
                                           width=600, height=400,
                                           labels={"Semana": "Semana", "Sell_in": "SellIn "},
                                           # category_orders={"day": ["Thur", "Fri", "Sat", "Sun"], "sex": ["Male", "Female"]},
                                           color_discrete_sequence=["#F6CE0E"],
                                           template="simple_white"
                                           )
                        figSellIn.update_layout(xaxis_type='category')'''
                        # figSellIn.write_image(nameImgSellIn)}
                        #urlSellIn = py.plot(figSellIn, filename='Graph1_' + proveedorAct, auto_open=False)


                    else:
                        urlSellIn = "No tenemos datos registrados para este periodo de tiempo."

                    # Sell Out Total
                    filtroSellOut = datosSellOut[datosSellOut['proveedor'] == proveedorAct]  # Tomar info un proveedor
                    if not filtroSellOut.empty:
                        graphSellOutSNS = sns.barplot(data=filtroSellOut, x="semana", y="SellOut", color='#F6CE0E')
                        graphSellOutSNS.set(xlabel='Semana', ylabel='Sell Out Total')
                        graphSellOutSNS.set_title("Sell Out Total VS Semana")
                        urlSellOut = "SellOut_" + proveedorAct + ".png"
                        for index, row in filtroSellOut.reset_index().iterrows():
                            graphSellOutSNS.text(row.name, row.SellOut, "${:,.0f}".format(round(row.SellOut,0)), color='black',ha="center")
                        graphSellOutSNS.figure.savefig(urlSellOut, bbox_inches='tight')
                        plt.close()
                        '''figSellOut = px.bar(filtroSellOut, x="semana", y="SellOut",
                                            text=filtroSellOut['SellOut'].apply(formatMoney),
                                            title="¿Cómo van las ventas estas semanas?",
                                            width=600, height=400,
                                            labels={"Semana": "Semana", "SellOut": "Sell Out "},
                                            color_discrete_sequence=["#F6CE0E"],
                                            template="simple_white"
                                            )
                        figSellOut.update_layout(xaxis_type='category')
                        # figSellOut.write_image("SellOut.png")
                        urlSellOut = py.plot(figSellOut, filename='Graph2_' + proveedorAct, auto_open=False)'''

                    else:
                        urlSellOut = "No tenemos datos registrados para este periodo de tiempo."

                    # Sell In Productos
                    datosSellInProd = datosSellInProd.rename(columns={'name': 'Producto', 'semana': 'Semana'})
                    filtroSellInProd = datosSellInProd[datosSellInProd['proveedor'] == proveedorAct]
                    if not filtroSellInProd.empty:
                        pivotSellInProd = filtroSellInProd.pivot_table(values="sell_in", index="Producto", columns="Semana",
                                                                       aggfunc=np.sum, fill_value=0)
                        changeSellInProd = pivotSellInProd.pct_change(axis="columns", fill_method="bfill")
                        changeSellInProd = changeSellInProd.fillna("")
                        changeSellInProd = changeSellInProd.replace(np.inf, "")
                        orig = {}
                        crec = {}

                        for i in range(len(changeSellInProd.columns)):
                            orig["col" + str(i)] = pd.to_numeric(pivotSellInProd.iloc[:, i], errors='coerce')
                            crec["colCrec" + str(i)] = pd.to_numeric(changeSellInProd.iloc[:, i], errors='coerce')
                        # change = pd.to_numeric(change, errors='coerce')

                        for i in range(len(changeSellInProd.columns)):
                            crec["colCrec" + str(i)] = crec["colCrec" + str(i)] * 100
                            crec["colCrec" + str(i)] = crec["colCrec" + str(i)].apply(formatDecimal)
                            crec["colCrec" + str(i)] = crec["colCrec" + str(i)].replace("inf%", "")
                            crec["colCrec" + str(i)] = crec["colCrec" + str(i)].replace("nan%", "")
                            crec["colCrec" + str(i)].name = "%Crec" + str(i)
                            orig["col" + str(i)] = orig["col" + str(i)].apply(formatMoney)
                        concat = pd.concat([orig["col" + str(0)]], axis=1)
                        for i in range(len(changeSellInProd.columns)):
                            if i > 0:
                                concat = pd.concat([concat, orig["col" + str(i)], crec["colCrec" + str(i)]], axis=1)
                        if len(concat.columns) == 3:
                            concat = concat.rename(columns={"%Crec1": "%Crec"})
                            concat = concat.style.applymap(color_negative_red, subset=["%Crec"])
                        if len(concat.columns) == 5:
                            concat = concat.rename(columns={"%Crec1": "%Crec", "%Crec2": "%Crec "})
                            concat = concat.style.applymap(color_negative_red, subset=["%Crec", "%Crec "])
                        if len(concat.columns) == 7:
                            concat = concat.rename(columns={"%Crec1": "%Crec", "%Crec2": "%Crec ", "%Crec3": "%Crec  "})
                            concat = concat.style.applymap(color_negative_red, subset=["%Crec", "%Crec ", "%Crec  "])
                        if isinstance(concat, pd.DataFrame):
                            htmlTablesSIProd = concat.to_html(classes='table-results')
                        else:
                            htmlTablesSIProd = concat.render()
                    else:
                        htmlTablesSIProd = "No tenemos datos registrados para este periodo de tiempo."

                    # Sell Out Productos

                    datosSellOutProd = datosSellOutProd.rename(columns={'name': 'Producto', 'semana': 'Semana'})
                    filtroSellOutProd = datosSellOutProd[datosSellOutProd['proveedor'] == proveedorAct]
                    if not filtroSellOutProd.empty:
                        pivotSellOutProd = filtroSellOutProd.pivot_table(values="SellOut", index="Producto", columns="Semana",
                                                                         aggfunc=np.sum, fill_value=0)
                        changeSellOutProd = pivotSellOutProd.pct_change(axis="columns", fill_method="bfill")
                        changeSellOutProd = changeSellOutProd.fillna("")
                        changeSellOutProd = changeSellOutProd.replace(np.inf, "")

                        origSellOut = {}
                        crecSellOut = {}

                        for i in range(len(changeSellOutProd.columns)):
                            origSellOut["col" + str(i)] = pd.to_numeric(pivotSellOutProd.iloc[:, i], errors='coerce')
                            crecSellOut["colCrec" + str(i)] = pd.to_numeric(changeSellOutProd.iloc[:, i], errors='coerce')
                        # change = pd.to_numeric(change, errors='coerce')

                        for i in range(len(changeSellOutProd.columns)):
                            crecSellOut["colCrec" + str(i)] = crecSellOut["colCrec" + str(i)] * 100
                            crecSellOut["colCrec" + str(i)] = crecSellOut["colCrec" + str(i)].apply(formatDecimal)
                            crecSellOut["colCrec" + str(i)] = crecSellOut["colCrec" + str(i)].replace("inf%", "")
                            crecSellOut["colCrec" + str(i)] = crecSellOut["colCrec" + str(i)].replace("nan%", "")
                            crecSellOut["colCrec" + str(i)].name = "%Crec" + str(i)
                            origSellOut["col" + str(i)] = origSellOut["col" + str(i)].apply(formatMoney)

                        concatSellOut = pd.concat([origSellOut["col" + str(0)]], axis=1)
                        for i in range(len(changeSellOutProd.columns)):
                            if i > 0:
                                concatSellOut = pd.concat(
                                    [concatSellOut, origSellOut["col" + str(i)], crecSellOut["colCrec" + str(i)]], axis=1)
                        if len(concatSellOut.columns) == 3:
                            concatSellOut = concatSellOut.rename(columns={"%Crec1": "%Crec"})
                            concatSellOut = concatSellOut.style.applymap(color_negative_red, subset=["%Crec"])
                        if len(concatSellOut.columns) == 5:
                            concatSellOut = concatSellOut.rename(columns={"%Crec1": "%Crec", "%Crec2": "%Crec "})
                            concatSellOut = concatSellOut.style.applymap(color_negative_red, subset=["%Crec", "%Crec "])
                        if len(concatSellOut.columns) == 7:
                            concatSellOut = concatSellOut.rename(
                                columns={"%Crec1": "%Crec", "%Crec2": "%Crec ", "%Crec3": "%Crec  "})
                            concatSellOut = concatSellOut.style.applymap(color_negative_red, subset=["%Crec", "%Crec ", "%Crec  "])
                        if isinstance(concatSellOut, pd.DataFrame):
                            htmlTablesSOProdValor = concatSellOut.to_html(index=False, classes='table-results')
                        else:
                            htmlTablesSOProdValor = concatSellOut.render()
                    else:
                        htmlTablesSOProdValor = "No tenemos datos registrados para este periodo de tiempo."

                    # SellOut productos Cantidad
                    if not filtroSellOutProd.empty:
                        pivotSellOutProdCant = filtroSellOutProd.pivot_table(values="cantidad", index="Producto", columns="Semana",
                                                                             aggfunc=np.sum, fill_value=0)
                        changeSellOutProdCant = pivotSellOutProdCant.pct_change(axis="columns", fill_method="bfill")
                        changeSellOutProdCant = changeSellOutProdCant.fillna("")
                        changeSellOutProdCant = changeSellOutProdCant.replace(np.inf, "")

                        origSellOutCant = {}
                        crecSellOutCant = {}

                        for i in range(len(changeSellOutProdCant.columns)):
                            origSellOutCant["col" + str(i)] = pd.to_numeric(pivotSellOutProdCant.iloc[:, i], errors='coerce')
                            crecSellOutCant["colCrec" + str(i)] = pd.to_numeric(changeSellOutProdCant.iloc[:, i], errors='coerce')
                        # change = pd.to_numeric(change, errors='coerce')

                        for i in range(len(changeSellOutProdCant.columns)):
                            crecSellOutCant["colCrec" + str(i)] = crecSellOutCant["colCrec" + str(i)] * 100
                            crecSellOutCant["colCrec" + str(i)] = crecSellOutCant["colCrec" + str(i)].apply(formatDecimal)
                            crecSellOutCant["colCrec" + str(i)] = crecSellOutCant["colCrec" + str(i)].replace("inf%", "")
                            crecSellOutCant["colCrec" + str(i)] = crecSellOutCant["colCrec" + str(i)].replace("nan%", "")
                            crecSellOutCant["colCrec" + str(i)].name = "%Crec" + str(i)
                            #origSellOutCant["col" + str(i)] = origSellOutCant["col" + str(i)].apply(formatMoney)

                        concatSellOutCant = pd.concat([origSellOutCant["col" + str(0)]], axis=1)
                        for i in range(len(changeSellOutProdCant.columns)):
                            if i > 0:
                                concatSellOutCant = pd.concat(
                                    [concatSellOutCant, origSellOutCant["col" + str(i)], crecSellOutCant["colCrec" + str(i)]],
                                    axis=1)

                        if len(concatSellOutCant.columns) == 3:
                            concatSellOutCant = concatSellOutCant.rename(columns={"%Crec1": "%Crec"})
                            concatSellOutCant = concatSellOutCant.style.applymap(color_negative_red, subset=["%Crec"])
                        if len(concatSellOutCant.columns) == 5:
                            concatSellOutCant = concatSellOutCant.rename(columns={"%Crec1": "%Crec", "%Crec2": "%Crec "})
                            concatSellOutCant = concatSellOutCant.style.applymap(color_negative_red, subset=["%Crec", "%Crec "])
                        if len(concatSellOutCant.columns) == 7:
                            concatSellOutCant = concatSellOutCant.rename(
                                columns={"%Crec1": "%Crec", "%Crec2": "%Crec ", "%Crec3": "%Crec  "})
                            concatSellOutCant = concatSellOutCant.style.applymap(color_negative_red,
                                                                                 subset=["%Crec", "%Crec ", "%Crec  "])
                        if isinstance(concatSellOutCant, pd.DataFrame):
                            htmlTablesSOProdCant = concatSellOutCant.to_html(index=False, classes='table-results')
                        else:
                            htmlTablesSOProdCant = concatSellOutCant.render()
                    else:
                        htmlTablesSOProdCant = "No tenemos datos registrados para este periodo de tiempo."

                    # Ticket Promedio
                    filtroTicketProm = datosTicketProm[datosTicketProm['proveedor'] == proveedorAct]
                    if not filtroTicketProm.empty:
                        plt.figure(figsize=(14, 6))
                        graphTicket = sns.lineplot(data=filtroTicketProm, x="semana", y="ticket_prom", color='#E58F1E')
                        for index, row in filtroTicketProm.reset_index().iterrows():
                            graphTicket.text(row.semana, row.ticket_prom, "${:,.0f}".format(round(row.ticket_prom,0)), color='black', ha="center")
                        start = filtroTicketProm["semana"].min()
                        end = math.ceil(filtroTicketProm["semana"].max()) + 1
                        x_ticks = list(np.arange(start, end, 1))
                        graphTicket.xaxis.set_ticks(x_ticks)
                        graphTicket.xaxis.set_ticklabels([str(tick) for tick in x_ticks])
                        graphTicket.set(ylim=(0, math.ceil(filtroTicketProm["ticket_prom"].max()) * 1.2))
                        graphTicket.set(xlabel='Semana', ylabel='Ticket Promedio')
                        graphTicket.set_title("Ticket Promedio VS Semana")
                        urlTicket = "ticket_" + proveedorAct + ".png"
                        graphTicket.figure.savefig(urlTicket, bbox_inches='tight')
                        plt.close()
                        #figTicket = filtroTicketProm.plot(x="semana", y="ticket_prom", kind="line", color="#afdeca").get_figure()
                        #xint = range(filtroTicketProm["semana"].min().astype(int), math.ceil(filtroTicketProm["semana"].max().astype(int)) + 1)
                        #matplotlib.pyplot.xticks(xint)
                        #figTicket.savefig(urlTicket)
                    else:
                        urlTicket = "No tenemos datos registrados para este periodo de tiempo."

                    # Top 5 Productos Cantidad

                    paramsTopCant = {}
                    paramsTopCant['p_Proveedor'] = proveedorAct
                    try:
                        datosTopCant = get_db_query(10270, paramsTopCant, 'fed')
                        datosTopCant = datosTopCant.rename(columns={'name': 'Producto', 'cantidad': 'Cantidad', 'ciudad':'Ciudad'})
                        datosTopCant = datosTopCant[['Ciudad','Producto', 'Cantidad']]
                        tableTopCant = datosTopCant.to_html(index=False, classes='table-results')
                    except:
                        tableTopCant = "No tenemos datos registrados para este periodo de tiempo."
                        print(colored("Problemas cargando top cant, "+ proveedorAct, 'red'))
                        raise

                    # Top 5 Productos GMV
                    paramsTopGMV = {}
                    paramsTopGMV['p_Proveedor'] = proveedorAct
                    try:
                        datosTopGMV = get_db_query(12418, paramsTopGMV, 'fed')
                        datosTopGMV = datosTopGMV.rename(columns={'name': 'Producto', 'gmv': 'GMV', 'ciudad':'Ciudad'})
                        datosTopGMV = datosTopGMV[['Ciudad','Producto', 'GMV']]
                        datosTopGMV['GMV'] = datosTopGMV['GMV'].apply(formatMoney)
                        tableTopGMV = datosTopGMV.to_html(index=False, classes='table-results')
                    except:
                        tableTopGMV = "No tenemos datos registrados para este periodo de tiempo."
                        print(colored("Problemas cargando top GMV, "+proveedorAct, 'red'))
                        raise


                    # Inventario
                    datosInvActual = datosInvActual.rename(columns={'name': 'Producto', 'disponible': 'Unidades', 'region_code':'Ciudad'})
                    filtroInvActual = datosInvActual[datosInvActual['proveedor'] == proveedorAct]
                    filtroInvActual = filtroInvActual[['Ciudad', 'Producto', 'Unidades']]
                    tableInv = filtroInvActual.to_html(classes="tableInv", index=False)



                    # Genracion HTML

                    htmlstring = '<!DOCTYPE html><html><head><title>Reporte semanal proveedor</title></head><body><style>@import url("https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap");html,body {max-width: 100%;}.col-md-6,.col-md-12 {text-align: left;padding: 0px;}.row {margin: 0;}.contenedor {font-family: Arial;width: 100%;}.contenedor h1 {font-size: 35px;}.encabezado td {text-align: left;font-size: 17px;}.subtitulo {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/border-bottom: 1px solid #E58F1E;padding-bottom: 5px;font-size: 19px;}.seccion {background-color: #f5f7f7;}.seccion1 {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/font-size: 12px;color: #42474d;font-family: Arial;text-align: left;}.grafica {width: 100%;height: 500px;}.logoFrub {float: right;width: 150px;}caption {caption-side: top;text-align: center;color: #42474d;}.enfoque {color: #9AA739;text-align: left;}h5 {color: #42474d;}table {/*width: 70%;*//*border:solid black; *//*margin: 0 auto;*/border: none;page-break-before: auto;}tr {border-bottom: 1px solid #ccc;break-inside: auto;}th {color: #4e545c;font-size: 40px;}.table-results th,.table-results td {border-collapse: collapse !important;border-bottom: 0.5px solid lightgray;}th,td {border-collapse: collapse;font-size: 10px;border: none;}thead:first-of-type {background-color: lightgrey;text-align: right;}thead:first-of-type th:first-of-type {background-color: lightgrey;text-align: left;}td {text-align: right;width: 10%;}.dataframe {width: 65%;}.dataframe td:nth-child(1) {text-align: left;}.dataframe td:nth-child(1),.dataframe td:nth-child(3) {width: 1%;}.tableInv {width: 50%;}.tableInv td:nth-child(1) {text-align: left;width: 2%;}.tableInv td:nth-child(2),.tableInv th:nth-child(2) {width: 20%;text-align: left;}.tableInv td:nth-child(3) {width: 1%;}.graphTicket iframe {height: 420px;width: 100%;text-align: left;justify-content: left;}.termino {font-weight: bold;}.graphTicket img {width: 60%;}img {width: 90%;}.graficas {width: 100%;}.graficas tr {width: 100%;}.graficas td {text-align: center;}.glosario p {font-size: 12px;}ul {list-style-type: none;}.tabla_fechas .first_row th {color: #E58F1E;}.tabla_fechas td,.tabla_fechas th {text-align: center;}</style><table class="contenedor" style="width: 100%;"><tr class="row"><td class="col-md-12"> <img class="logoFrub"src="https://media-exp1.licdn.com/dms/image/C4E0BAQHWoAa7O-o3Hg/company-logo_200_200/0?e=2159024400&v=beta&t=GK7MbsQSka9EDjA-hjE5tHg1HXyEarCre0djqlmTWkg"><h1>Reporte Quincenal</h1><br><table class="encabezado"><tr><td><h5><span class="enfoque">Aliado: </span>'
                    htmlstring += proveedorAct
                    htmlstring += '</h5></td><td><h5><span class="enfoque">Fecha Emisión: </span>'
                    htmlstring += date.today().strftime("%d/%m/%Y")
                    htmlstring += '</h5></td></tr></table></td></tr></table><table class="contenedor seccion"><tr class="row"><td class="col-md-12 glosario"> <br> <br><h3 class="subtitulo">Glosario</h3> <br><p>Aquí encontraras la explicación de algunos términos que utilizamos en el reporte. </p><ul><li><p><span class="termino">Sell In:</span> Indicador de compra al proveedor.</p></li><li><p><span class="termino">Sell Out:</span> Indicador de venta al cliente.</p></li><li><p><span class="termino">Ticket Promedio:</span> Valor promedio de compra del cliente.</p></li></ul></td></tr> <br><tr><td class="col-md-12 glosario"> <br> <br><p>Las semanas evaluadas son las siguientes:</p>'
                    htmlstring += '<table class="tabla_fechas" style="width:30%"><tr class="first_row"><th> Semana </th> <th> Fecha Inicio </th> <th> Fecha Fin </th> </tr>'
                    for i in range(3, -1, -1):
                        htmlstring += '<tr><td>'
                        htmlstring += str((date.today() - datetime.timedelta(days=((7 * i) + 1))).isocalendar()[1])
                        htmlstring += '</td><td>'
                        htmlstring += str((date.today() - datetime.timedelta(days=(7 * (1 + i)))).strftime('%d-%b-%Y'))
                        htmlstring += '</td><td>'
                        htmlstring += str((date.today() - datetime.timedelta(days=((7 * i) + 1))).strftime('%d-%b-%Y'))
                    htmlstring += '</td></tr></table></td></tr></table>'
                    htmlstring += '<table class="contenedor" style="width: 100%;"><tr class="row"><td class="col-md-12"><h3 class="subtitulo">Indicadores de compra y venta</h3></td></tr><tr class="row"><td><table class="graficas"><tr><td><h4 class="seccion1">¿Cuánto te pedimos estas semanas? (Sell In)</h4>'
                    if("png" in urlSellIn):
                        htmlstring += '<img src="'
                        htmlstring += urlSellIn
                        htmlstring += '" alt=""> '
                    else:
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += urlSellIn
                        htmlstring += ' </p> '
                    htmlstring += '</td><td><h4 class="seccion1">¿Cuánto van las ventas estas semanas? (Sell Out)</h4>'
                    if ("png" in urlSellOut):
                        htmlstring += '<img src="'
                        htmlstring += urlSellOut
                        htmlstring += '" alt=""> '
                    else:
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += urlSellOut
                        htmlstring += '</p>'
                    htmlstring += '</td></tr></table></td></tr></table><table class="contenedor seccion"><tr class="row"><td class="col-md-12 tabla"> <br> <br><h3 class="subtitulo">Sell In & Sell Out Productos</h3> <br><h4 class="seccion1">¿Cuánto te hemos pedido por producto? (Sell In Producto)</h4>'
                    if ("No tenemos datos" in htmlTablesSIProd):
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += htmlTablesSIProd
                        htmlstring += '</p>'
                    else:
                        htmlstring += htmlTablesSIProd
                    htmlstring += '</td></tr></table><table class="contenedor seccion"><tr class="row"><td class="col-md-12 tabla"><br><br><h4 class="seccion1">¿Cómo se han vendido tus productos en Valor? (Sell Out Producto Valor)</h4>'
                    if ("No tenemos datos" in htmlTablesSOProdValor):
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += htmlTablesSOProdValor
                        htmlstring += '</p>'
                    else:
                        htmlstring += htmlTablesSOProdValor
                    htmlstring += '</td></tr></table><table class="contenedor seccion"><tr class="row"><td class="col-md-12 tabla"><br><br><h4 class="seccion1">¿Cómo se han vendido tus productos en Unidades? (Sell Out Producto Unidades)</h4>'
                    if ("No tenemos datos" in htmlTablesSOProdCant):
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += htmlTablesSOProdCant
                        htmlstring += '</p>'
                    else:
                        htmlstring += htmlTablesSOProdCant
                    htmlstring += '</td></tr></table><table class="contenedor" style="width: 100%;"><tr class="row"><td class="col-md-12 graphTicket" style="padding: 10px;"><h3 class="subtitulo">Información Ventas</h3><h4 class="seccion1">¿Cómo ha sido la media de las ordenes de tus clientes? (Ticket Promedio)</h4><br>'
                    if ("png" in urlTicket):
                        htmlstring += '<img src="'
                        htmlstring += urlTicket
                        htmlstring += '" alt=""> '
                    else:
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += urlTicket
                        htmlstring += ' </p> '
                    htmlstring += '</td></tr></table><table class="contenedor" style="width: 100%;"><tr class="row"><td class="col-md-12"><h4 class="seccion1">¿Cuáles fueron tus productos más vendidos?</h4><br><table class="graficas"><tr class="row"><td class="col-md-6"><h4 class="seccion1">En Unidades</h4>'
                    if ("No tenemos datos" in tableTopCant):
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += tableTopCant
                        htmlstring += '</p>'
                    else:
                        htmlstring += tableTopCant
                    htmlstring += '</td><td class="col-md-6"><h4 class="seccion1">En Valor</h4>'
                    if ("No tenemos datos" in tableTopGMV):
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += tableTopGMV
                        htmlstring += '</p>'
                    else:
                        htmlstring += tableTopGMV
                    htmlstring += '</td></tr></table></td></tr></table><table class="contenedor" style="width: 100%;"><tr class="row"><td class="col-md-12" style="padding: 10px;"><!--<h3 class="subtitulo">Inventario al día de hoy</h3>--><h4 class="seccion1">¿Cómo estamos de inventario?</h4><p> Al día de hoy cuantas unidades tenemos en nuestras bodegas </p>'
                    if ("No tenemos datos" in tableInv):
                        htmlstring += '<p class="textoSinInfo">'
                        htmlstring += tableInv
                        htmlstring += '</p>'
                    else:
                        htmlstring += tableInv
                    htmlstring += '</td></tr></table></body></html>'

                    #print(htmlstring)
                    #Escribir HTML
                    f = open('reporte_' + proveedorAct + '.html', 'w')
                    htmlstring= htmlstring.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

                    f.write(htmlstring)
                    f.close()

                    #Render to PDF
                    HTML('reporte_'+proveedorAct+'.html').write_pdf('reporte_'+proveedorAct+'.pdf',stylesheets=[CSS(string='@page {size: Letter; font-family:Arial; /* Change from the default size of A4 */ margin: 0.5cm; /* Set margin on each page */}@import url("https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap");html,body {max-width: 100%;}.col-md-6,.col-md-12 {text-align: left;padding: 0px;}.row {margin: 0;}.contenedor {font-family: Arial;width: 100%;}.contenedor h1 {font-size: 35px;}.encabezado td{text-align: left;font-size: 17px;}.subtitulo {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/border-bottom: 1px solid #E58F1E;padding-bottom: 5px;font-size: 19px;}.seccion {background-color: #f5f7f7;}.seccion1 {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/font-size: 12px;color: #42474d;font-family: Arial;text-align: left;}.grafica {width: 100%;height: 500px;}.logoFrub {float: right;width: 150px;}caption {caption-side: top;text-align: center;color: #42474d;}.enfoque {color: #9AA739;text-align: left;}h5 {color: #42474d;}table {/*width: 70%;*//*border:solid black; *//*margin: 0 auto;*/border: none;}tr {border-bottom: 1px solid #ccc;}th {color: #4e545c;font-size: 40px;}.table-results th, .table-results td{border-collapse: collapse !important;border-bottom: 0.5px solid lightgray;}th,td {border-collapse: collapse;font-size: 10px;border: none;}thead:first-of-type {background-color: lightgrey;text-align: right;}thead:first-of-type th:first-of-type {background-color: lightgrey;text-align: left;}td {text-align: right;width: 10%;}.dataframe {width: 65%;}.dataframe td:nth-child(1) {text-align: left;}.dataframe td:nth-child(2) {width: 1%;}.tableInv {width: 50%;}.tableInv td:nth-child(1) {text-align: left;width: 2%;}.tableInv td:nth-child(2),.tableInv th:nth-child(2) {width: 20%;text-align: left;}.tableInv td:nth-child(3) {width: 1%;}.graphTicket iframe {height: 420px;width: 100%;text-align: left;justify-content: left;}.termino{font-weight: bold;}.col-md-12 img{width: 60%;}img{width: 90%;}.graficas{width: 100%;}.graficas tr{width: 100%;}.graficas td{text-align: center;}ul {list-style-type: none;}')])
                    filtrocorreos = correos[correos['name'] == proveedorAct]
                    if not filtrocorreos.empty:
                        correos_finales = filtrocorreos['email'].unique()
                        lista_correos = []
                        lista_correos.append(("laura.maya@frubana.com",''))
                        #if pais == 'COL':
                        #    lista_correos.append(("anamaria.puerta@frubana.com", 'Ana Maria Puerta'))
                        #if pais == 'CMX':
                        #    lista_correos.append(("andrea.viejo@frubana.com", 'Andrea Viejo'))
                        #for correo in correos_finales:
                        #    lista_correos.append((correo, ''))
                    #
                    #    print(lista_coreros)
                        enviarEmail(lista_correos, 'reporte_'+proveedorAct+'.pdf', proveedorAct)
                except:
                    print(colored("Error en proveedor: "+proveedorAct+".", 'red'))
    except:
        traceback.print_exc()

def enviarEmail (mails_destino,nombreReporte, nombreProveedor):

    message = Mail(
        from_email=Email("laura.maya@frubana.com", "Equipo MarketPlace"),
        to_emails= mails_destino,
        subject='Reporte Desempeño Frubana 🍉',
        html_content='<!DOCTYPE html> <html> <head> </head> <body style="background-color: #f2f2f2; padding: 20px; text-align: center;"> <table style="margin: auto;width: 50%; text-align: left; font-family: Arial; background-color: white; padding: 20px;"> <tr style="background-color: white;"> <td><img src="https://raw.githubusercontent.com/LMayaFrubana/FormZenDesk/main/unnamed.png" alt=""> <br> <br> <br> <strong>Es tiempo de mejorar nuestros procesos 🍉 </strong> <br> <p>Buen día '+ nombreProveedor + '</p> <p>Nos sentimos muy contentos de poder comunicarles, que hoy les compartimos el informe de sus ventas general y a nivel de producto. Lo anterior con el fin de entregar la información que nos permita tomar acciones en conjunto para aumentar dichas ventas y mejorar los procesos.</p> <p>Adjunto se encuentra el informe en pdf.</p> <br><p>Feliz día ☀️</p> </td> </tr> </table> </body> </html> ')
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        (print(api_key))
        sg = SendGridAPIClient(api_key)

        with open(nombreReporte, 'rb') as f:
            data = f.read()
            f.close()
        encoded_file = base64.b64encode(data).decode()

        attachedFile = Attachment(
            FileContent(encoded_file),
            FileName('Reporte_Desempeno.pdf'),
            FileType('application/pdf'),
            Disposition('attachment')
        )
        message.attachment = attachedFile

        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

def subirDrive():
    from pydrive.drive import GoogleDrive
    from pydrive.auth import GoogleAuth

    import os

    # Below code does the authentication
    # part of the code
    gauth = GoogleAuth()

    # Creates local webserver and auto
    # handles authentication.
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    # replace the value of this variable
    # with the absolute path of the directory
    path = r"test.png"

    # iterating thought all the files/folder
    # of the desired directory
    # for x in os.listdir(path):

    # f = drive.CreateFile({'title': x})
    # f.SetContentFile(os.path.join(path, x))
    # f.Upload()

    # Due to a known bug in pydrive if we
    # don't empty the variable used to
    # upload the files to Google Drive the
    # file stays open in memory and causes a
    # memory leak, therefore preventing its
    # deletion
    f = drive.CreateFile({'title': 'test.png'})
    f.SetContentFile(os.path.join('test.png'))
    f.Upload()
    print(f.get('id'))

    f = None

def obtenerCorreos():
    params = {}
    proveedorAct = 'MYSTERY PROTEINAS FERRERIA'
    correos = get_db_query(8417, params, 'fed')
    filtrocorreos = correos[correos['name']==proveedorAct]
    correos_finales = filtrocorreos['email'].unique()
    lista_coreros = []
    for correo in correos_finales:
        lista_coreros.append((correo, ''))

    print(lista_coreros)
    enviarEmail(lista_coreros,'reporte_'+proveedorActual+'.pdf')

def probarUnicode():
    basicString = '¿Cuántas unidades te han comprado'
    f = open('pruebaTexto.html', 'w')
    basicString = basicString.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

    f.write(basicString)
    f.close()
def convertirPDF():
    HTML().write_pdf('reporte_tabla.pdf',stylesheets=[CSS(string='@page {size: Letter; /* Change from the default size of A4 */ margin: 0in 0.44in 0.2in 0.44in; /* Set margin on each page */}@import url("https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap");html,body {max-width: 100%;}.col-md-6,.col-md-12 {text-align: left;padding: 0px;}.row {margin: 0;}.contenedor {font-family: Arial;width: 100%;}.contenedor h1 {font-size: 35px;}.encabezado td{text-align: left;font-size: 17px;}.subtitulo {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/border-bottom: 1px solid #E58F1E;padding-bottom: 5px;font-size: 19px;}.seccion {background-color: #f5f7f7;}.seccion1 {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/font-size: 12px;color: #42474d;font-family: Arial;text-align: left;}.grafica {width: 100%;height: 500px;}.logoFrub {float: right;width: 150px;}caption {caption-side: top;text-align: center;color: #42474d;}.enfoque {color: #9AA739;text-align: left;}h5 {color: #42474d;}table {/*width: 70%;*//*border:solid black; *//*margin: 0 auto;*/border: none;}tr {border-bottom: 1px solid #ccc;}th {color: #4e545c;font-size: 40px;}.table-results{page-break-before: auto;}.table-results th, .table-results td{border-collapse: collapse !important;border-bottom: 0.5px solid lightgray;}th,td {border-collapse: collapse;font-size: 10px;border: none;}thead:first-of-type {background-color: lightgrey;text-align: right;}thead:first-of-type th:first-of-type {background-color: lightgrey;text-align: left;}td {text-align: right;width: 10%;}.dataframe {width: 65%;}.dataframe td:nth-child(1) {text-align: left;}.dataframe td:nth-child(2) {width: 1%;}.tableInv {width: 50%;}.tableInv td:nth-child(1) {text-align: left;width: 2%;}.tableInv td:nth-child(2),.tableInv th:nth-child(2) {width: 20%;text-align: left;}.tableInv td:nth-child(3) {width: 1%;}.graphTicket iframe {height: 420px;width: 100%;text-align: left;justify-content: left;}.termino{font-weight: bold;}.col-md-12 img{width: 60%;}img{width: 90%;}.graficas{width: 100%;}.graficas tr{width: 100%;}.graficas td{text-align: center;}ul {list-style-type: none;}')])
def probarColores():
    from termcolor import colored

    print (colored('hello', 'red'))
def convertirHTML():
    f = open('PRUEBACARACTERES.html', 'w')
    htmlstring = "<!DOCTYPE html><html><head><title>Reporte semanal proveedor</title></head><body><p>Hola á y la é y la í ¿</p></body></html>"
    htmlstring = htmlstring.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

    f.write(htmlstring)
    f.close()
    HTML('PRUEBACARACTERES.html').write_pdf('pruebacaracteres.pdf', stylesheets=[CSS(string='@page {size: Letter; /* Change from the default size of A4 */ margin: 0in 0.44in 0.2in 0.44in; /* Set margin on each page */}@import url("https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700;800&display=swap");html,body {max-width: 100%;}.col-md-6,.col-md-12 {text-align: left;padding: 0px;}.row {margin: 0;}.contenedor {font-family: Arial;width: 100%;}.contenedor h1 {font-size: 35px;}.encabezado td{text-align: left;font-size: 17px;}.subtitulo {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/border-bottom: 1px solid #E58F1E;padding-bottom: 5px;font-size: 19px;}.seccion {background-color: #f5f7f7;}.seccion1 {/*text-decoration: underline;text-decoration-color: #ef931c;text-decoration-style: solid;*/font-size: 12px;color: #42474d;font-family: Arial;text-align: left;}.grafica {width: 100%;height: 500px;}.logoFrub {float: right;width: 150px;}caption {caption-side: top;text-align: center;color: #42474d;}.enfoque {color: #9AA739;text-align: left;}h5 {color: #42474d;}table {/*width: 70%;*//*border:solid black; *//*margin: 0 auto;*/border: none;}tr {border-bottom: 1px solid #ccc;}th {color: #4e545c;font-size: 40px;}.table-results{page-break-before: auto;}.table-results th, .table-results td{border-collapse: collapse !important;border-bottom: 0.5px solid lightgray;}th,td {border-collapse: collapse;font-size: 10px;border: none;}thead:first-of-type {background-color: lightgrey;text-align: right;}thead:first-of-type th:first-of-type {background-color: lightgrey;text-align: left;}td {text-align: right;width: 10%;}.dataframe {width: 65%;}.dataframe td:nth-child(1) {text-align: left;}.dataframe td:nth-child(2) {width: 1%;}.tableInv {width: 50%;}.tableInv td:nth-child(1) {text-align: left;width: 2%;}.tableInv td:nth-child(2),.tableInv th:nth-child(2) {width: 20%;text-align: left;}.tableInv td:nth-child(3) {width: 1%;}.graphTicket iframe {height: 420px;width: 100%;text-align: left;justify-content: left;}.termino{font-weight: bold;}.col-md-12 img{width: 60%;}img{width: 90%;}.graficas{width: 100%;}.graficas tr{width: 100%;}.graficas td{text-align: center;}ul {list-style-type: none;}')])


if __name__ == '__main__':
    #probarUnicode()
    generarReporte()
    #lista_coreros = []
    #lista_coreros.append(("laura.maya@frubana.com", 'Laura Maya'))
    #enviarEmail(lista_coreros,"reporte_3 Castillos.pdf", "Provedorsazo" )
    #subirDrive()
    #convertirPDF()
    #obtenerCorreos()
    #probarColores()
    #convertirHTML()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/

