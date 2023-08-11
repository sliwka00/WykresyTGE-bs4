import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
import os
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go

lista=[]
# Pobierz aktualną ścieżkę do bieżącego pliku (ratio.py)
current_directory = os.path.dirname(os.path.abspath(__file__))

# Utwórz ścieżkę do pliku abc.xlsx w katalogu nadrzędnym
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
file_path_abc_xlsx = os.path.join(parent_directory, 'abc.xlsx')
df = pd.read_excel(file_path_abc_xlsx) # otwieram excel



df = df.replace('-',np.nan)   #zamienia  "-" na Nan w komórkach gdzie nie ma ceny
df = df.astype({'DKR':float})  #zamienia kolumne DKR na floaty (dane były jako string)
df['kontrakt short'] = df['Kontrakt'].str.split("_").str[-1]       #Skraca nazwe kontraktu do uniwersalnego (dla base i peak) żeby je sparować
df['Data']=pd.to_datetime(df['Data'], format='%d-%m-%Y')
df['wolumen'] = [float(str(val).replace(u'\xa0','').replace(',','.')) for val in df['wolumen'].values]   #wyrzucenie dziwnych znaków z wolumenu i zamiana na float
df3 = df[['Data','DKR','typ','wolumen','kontrakt short']]  #stworzenie skróconego df bez zbędnych kolumn
df_base = df3[df3['typ'] == 'BASE']     #stworzenie df dla base
df_peak = df3[df3['typ'] == 'PEAK']
df_wsp = pd.merge(df_base,df_peak, on=['Data','kontrakt short'])  #połączenie df_base i df_peak dzieki temu można dodać kolumne ratio
df_wsp['ratio']=df_wsp['DKR_y']/df_wsp['DKR_x']  #kolumna z ratio

# Pętla do uzupełniania listy produktów, które znajdują sie w pliku zródłowym
for produkt in df['kontrakt short']:
    if produkt not in lista and "W-" not in produkt:
        lista.append(produkt)
    else:
        continue
lista.sort()
print(lista)

def draw_ratio2(produkt):    # wyświetla ratio + 2 słupki wolumenowe base i peak
    df_temp=df_wsp[df_wsp['kontrakt short']==produkt]
    data=df_temp['Data']
    ratio=df_temp['ratio']
    wol_peak=df_temp['wolumen_y']
    wol_base=df_temp['wolumen_x']
    # Tworzenie figury i osi
    fig, ax1 = plt.subplots()
    ax1.bar(data, wol_peak, color='red', alpha=0.5)
    ax1.set_ylabel('Wolumen peak->czerwony \n wolumen base->zielony ')

    ax3=ax1.twinx()
    ax3.bar(data, wol_base, color='green', alpha=0.5)
    ax3.axes.get_yaxis().set_visible(False)
    ax3.set_ylabel('Wolumen base')

    ax2 = ax1.twinx()
    ax2.plot(data, ratio, marker='o', linestyle='-', color='blue')
    ax2.set_title(produkt)
    ax2.set_xlabel('Data')
    ax2.set_ylabel('Ratio Peak/Base')
    fig.autofmt_xdate(rotation=35, ha='right')    #rotuje daty wyświetlane pod wykresem
    st.pyplot()
def draw_interactive(produkt):    # na próbe z plotly, ale nie chce pokazać dobrze 2 skali Y na 1 wykresie
    df_temp = df_wsp[df_wsp['kontrakt short'] == produkt]
    data = df_temp['Data']
    ratio = df_temp['ratio']
    wol_peak = df_temp['wolumen_y']
    wol_base = df_temp['wolumen_x']
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # Add traces
    fig.add_trace(
        go.Scatter(x=data, y=ratio, name="ratio",mode='markers+lines', line=dict(color='blue')),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(x=data, y=wol_peak, name="Wolumen peak-> czerwony",marker_color='red', opacity=0.5),
        secondary_y=True,
    )
    fig.add_trace(
        go.Bar(x=data, y=wol_base, name="Wolumen base-> zielony",marker_color='green', opacity=0.5),
        secondary_y=True,
    )
    #Dodaj interaktywny "krzyżak" do wykresu
    fig.update_traces(hoverinfo='text',
                      hovertemplate='<b>Data</b>: %{x}<br><b>ratio</b>: %{y:.2f}',
                      selector=dict(mode='markers+lines'))


    st.plotly_chart(fig)

st.title("Wykres ratio Peak/Base dla DKR")
selected_ratio=st.selectbox("Wybierz produkt", lista)

interactive= st.checkbox("włącz wykres interaktywny")
if interactive==True:
    draw_interactive(selected_ratio)
else:
    draw_ratio2(selected_ratio)