from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import numpy as np
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json
import re
from datetime import datetime as dt

os.chdir('/home/clautc/Proyectos_/dakar')
config = dict(
    web="https://es.wikipedia.org/wiki/Anexo:Estad%C3%ADsticas_del_Rally_Dakar",
    path="/usr/bin/chromedriver_linux/chromedriver",
 )

class ColectarDakar:
    def __init__(self, configuracion=config):
        self.configuracion = configuracion


    def inicio_sesion(self):
        driver = webdriver.Chrome(executable_path=self.configuracion['path'])
        driver.get(self.configuracion['web'])
        wait = WebDriverWait(driver, 5)
        driver.maximize_window()
        return driver, wait

    def select_tablas(self, driver, wait):
        tablas_wiki = driver.find_elements(By.XPATH, '//div//*[contains(@class, "wikitable")]')
        tablas_select = []
        for t in tablas_wiki:
            if 'Ruta' in t.text.split():
                tablas_select.append(t)
                continue
        return tablas_select

    def crear_data(self, tablas_select):

        titulos_1 = tablas_select[0].find_elements(By.XPATH, '*//tr')[0].text
        titulos_2 = tablas_select[0].find_elements(By.XPATH, '*//tr')[0].text
        filas = []
        for t in tablas_select:
            filas_ele = t.find_elements(By.XPATH, '*//td')
            for f in filas_ele:
                filas.append(f.text)
                print(f.text)
        filas.remove('2008')
        filas.remove('No se disputó por amenazas de Al Qaeda')
        filas_Series = pd.DataFrame(filas)
        categorias_africa = ['anio', 'ruta', 'auto_pil', 'auto_fab', 'moto_pil', 'moto_fab', 'camion_pil',
                                   'camion_fab']*29
        categorias_suda = ['anio', 'ruta', 'auto_pil', 'auto_fab', 'moto_pil', 'moto_fab', 'camion_pil',
                             'camion_fab', 'cuatrimoto_pil', 'cuatrimoto_fab', 'sxs_pil', 'sxs_fab']*11
        categorias_arabia = ['anio', 'ruta', 'auto_pil', 'auto_fab', 'moto_pil', 'moto_fab', 'camion_pil',
                           'camion_fab', 'cuatrimoto_pil', 'cuatrimoto_fab', 'sxs_pil', 'sxs_fab', 'prototipo_pil',
                             'prototipo_fab', 'clasico_pil', 'clasico_fab']*4
        categorias=[]

        for af in categorias_africa:
            categorias.append(af)
        for sa in categorias_suda:
            categorias.append(sa)
        for ar in categorias_arabia:
            categorias.append(ar)
        africa = range(1,30,1)
        suda = range(31,42,1)
        arabia= range(43,47,1)
        number=[]
        for a in africa:
            for n in range(8):
                number.append(a)
        for s in suda:
            for n in range(12):
                number.append(s)
        for ar in arabia:
            for n in range(16):
                number.append(ar)


        data = pd.concat([pd.DataFrame(number), filas_Series, pd.DataFrame(categorias)], join='outer', axis=1)
        data.columns = ['number','data', 'columnas']
        pivot_data = data.pivot(index='number', columns='columnas', values='data').reset_index(drop=True)
        moto_data = pivot_data[['anio', 'moto_pil', 'moto_fab', 'ruta']]
        pivot_data.to_feather('data/data_dakar.feather')

        return pivot_data

    def procesar_data(self, moto_data):
        moto_data.loc[moto_data.moto_fab.str.match('KTM.*'), 'fabricante'] = 'KTM'
        moto_data.loc[moto_data.moto_fab.str.match('BMW.*'), 'fabricante'] = 'BMW'
        moto_data.loc[moto_data.moto_fab.str.match('Honda.*'), 'fabricante'] = 'Honda'
        moto_data.loc[moto_data.moto_fab.str.match('Yamaha.*'), 'fabricante'] = 'Yamaha'
        moto_data.loc[moto_data.moto_fab.str.match('Gas.*'), 'fabricante'] = 'Gas Gas'
        moto_data.loc[moto_data.moto_fab.str.match('Cagiva.*'), 'fabricante'] = 'Cagiva'
        if moto_data.fabricante.isna().sum() == 0:
            print('se creó con éxito la variable fabricante')
        moto_data['anio2'] = pd.to_datetime(moto_data.anio, format='%Y')
        moto_data['year'] = moto_data.anio2.dt.year
        moto_data.loc[moto_data.year <= 2008, 'dakar'] = 'África'
        moto_data.loc[(moto_data.year > 2008) & (moto_data.year <=2019), 'dakar'] = 'América del Sur'
        moto_data.loc[moto_data.year > 2019, 'dakar'] = 'Arabia Saudí'
        moto_data.to_feather('data/data_moto.feather')

