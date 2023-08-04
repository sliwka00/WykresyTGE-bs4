import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import time
import numpy as np
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import load_workbook
import holidays
import holidays.countries
import streamlit as st
from bs4 import BeautifulSoup
import requests

cale=[]
kwartaly=[]
msc=[]
print(cale)
df = pd.read_excel(r'abc.xlsx')


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
for produkt in df['Kontrakt']:
    if "_Y-" in produkt:
        if produkt not in cale:
            cale.append(produkt)
    elif "_Q-" in produkt:
        if produkt not in kwartaly:
            kwartaly.append(produkt)
    elif "_M-" in produkt:
        if produkt not in msc:
            msc.append(produkt)
    else:
        continue

msc.sort()
kwartaly.sort()
cale.sort()
print(cale)
print(kwartaly)
print(msc)

st.set_option('deprecation.showPyplotGlobalUse', False)  #usuniecie komunikatu ze strony

# Funkcja rysujaca wykres w matplotlib
def draw_chart(produkt):
    df2=df[df['Kontrakt']==produkt]
    data=df2['Data']
    cena=(df2['DKR'])
    wolumen=(df2['wolumen'])
    # Tworzenie figury i osi
    fig, ax1 = plt.subplots()
    ax1.bar(data, wolumen, color='gray', alpha=0.5)
    ax1.set_ylabel('Wolumen')
    ax2 = ax1.twinx()

    ax2.plot(data, cena, marker='o', linestyle='-', color='blue')
    ax2.set_title(produkt)
    ax2.set_xlabel('Data')
    ax2.set_ylabel('cena')
    #
    #myFmt = mdates.DateFormatter('%d-%m-%Y')
    fig.autofmt_xdate(rotation=35, ha='right')    #rotuje daty wyświetlane pod wykresem

    st.pyplot()

def draw_chartQ(produkt):    # na próbe z plotly, ale nie chce pokazać dobrze 2 skali Y na 1 wykresie
    df2 = df[df['Kontrakt'] == produkt]

    data = df2['Data']
    cena = df2['DKR']
    wolumen = df2['wolumen']

    # Tworzenie wykresu korzystając z biblioteki Plotly
    fig = go.Figure()

    # Dodaj wykres słupkowy dla wolumenu
    fig.add_trace(go.Bar(x=data, y=wolumen, marker_color='gray', opacity=0.5, name='Wolumen'))

    # Dodaj wykres liniowy dla ceny
    fig.add_trace(go.Scatter(x=data, y=cena, mode='markers+lines', line=dict(color='blue'), name='Cena'))

    # Skalowanie osi Y dla wykresu cen i wolumenu
    max_wolumen = wolumen.max()
    max_cena = cena.max()

    # Dodaj drugą oś Y dla wykresu ceny
    fig.update_layout(
        title=produkt,
        xaxis_title='Data',
        yaxis=dict(title='Wolumen', title_font=dict(color='gray'), tickfont=dict(color='gray'), range=[0, max_wolumen * 1.2],side="left"),
        yaxis2=dict(
            title='Cena',
            title_font=dict(color='blue'),
            tickfont=dict(color='blue'),
            overlaying='y',
            side='right',
            range=[0, max_cena * 1.2]
        ),
        hovermode='x',
        legend=dict(
            x=0.5,
            y=1.15,
            orientation='h'
        )
    )

    # Dodaj interaktywny "krzyżak" do wykresu
    fig.update_traces(hoverinfo='text',
                      hovertemplate='<b>Data</b>: %{x}<br><b>Cena</b>: %{y:.2f}',
                      selector=dict(mode='markers+lines'))

    # Wyświetl wykres interaktywny w Streamlit
    st.plotly_chart(fig)


st.set_page_config(layout="wide")   #rozciąga aplikacje na całą strone web
st.title("Wykres liniowy DKR, wraz z słupkami z wolumenem")
col1, col2, col3 = st.columns(3)

with col1:
    selected_Y=st.selectbox("Y - Produkty roczne",cale)
with col2:
    selected_Q = st.selectbox("Q - Produkty kwartalne", kwartaly)
with col3:
    selected_msc=st.selectbox("MSC - Produkty miesięczne", msc)

draw_y,draw_q,draw_msc= st.columns(3)
with draw_y:
    draw_chart(selected_Y)
with draw_q:
    draw_chart(selected_Q)
with draw_msc:
    draw_chart(selected_msc)

def pobierz_dane(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def analizuj_dane(html):
    soup = BeautifulSoup(html, 'html.parser')
    tabelki = soup.find_all('table')
    dataframes = []
    for tabelka in tabelki:
        df = pd.read_html(str(tabelka), header=0, decimal=",", thousands='.')
        dataframes.extend(df)
    return dataframes
def aktualizacja():    #aktualizacja danych jako funkcja która wywołujemy przyciskiem
    wb = load_workbook(filename="abc.xlsx")
    ws = wb["a"]
    ostatni_wiersz = ws.max_row
    ostatnia_data = ws.cell(row=ostatni_wiersz,
                            column=1).value  # uchwycona ostatnia data, dla której są dane w pliku excel
    pl_holidays = holidays.Poland()

    # kod  na ostatni dzień roboczy
    dzisiaj = dt.date.today()
    delta1 = dt.timedelta(days=1)
    delta2 = dt.timedelta(days=2)
    ostatni_dzien = dzisiaj - delta1

    if ostatni_dzien.weekday() == 5:
        ostatni_dzien = ostatni_dzien - delta1
    elif ostatni_dzien.weekday() == 6:
        ostatni_dzien = ostatni_dzien - delta2

    ostatni_dzien_str = str(ostatni_dzien)

    for x in range(len(pl_holidays)):
        if ostatni_dzien_str in pl_holidays:
            ostatni_dzien = ostatni_dzien - delta1
            if ostatni_dzien.weekday() == 5:
                ostatni_dzien = ostatni_dzien - delta1
            elif ostatni_dzien.weekday() == 6:
                ostatni_dzien = ostatni_dzien - delta2
            ostatni_dzien_str = str(ostatni_dzien)

    weekdays = [5, 6]
    data_poczatkowa = dt.datetime.strptime(ostatnia_data,
                                           "%d-%m-%Y") + delta1  # trzeba do ostatniej daty dodać 1 dzień
    start_day = data_poczatkowa
    end_day = ostatni_dzien

    daterange = pd.date_range(start_day, end_day)
    for date in daterange:
        if date.weekday() not in weekdays and date.strftime("%Y-%m-%d") not in pl_holidays:
            dzien = date.strftime("%d-%m-%Y")
            url = 'https://tge.pl/energia-elektryczna-otf?dateShow=' + dzien + '&dateAction=prev'
            html=pobierz_dane(url)
            time.sleep(1)
            if html:
                df_list = analizuj_dane(html)
                for df in df_list:
                    # -----BASE ---
                    print(f'df----->{df}')
                    df.drop('Unnamed: 1', axis=1)  # Usunięcie kolumny 'Unnamed: 1'
                    base = df
                    print(f'base->{base}')
                    print(base)
                    base = base.iloc[:-1]  # Usunięcie ostatniego wiersza z tabeli (podsumowania)
                    base.insert(0, 'data', dzien)  # Dodanie daty w pierwszej kolumnie (0-zerowej)
                    base['typ'] = "BASE"  # Dodajemy kolumnę Typ: "BASE" dla produktów z tabeli base, PEAK dla produktów z tabeli PEAK
                    # -----PEAK-----
                    df.drop('Unnamed: 1', axis=1)
                    peak = df
                    peak = peak.iloc[:-1]
                    peak.insert(0, 'data', dzien)
                    peak['typ'] = 'PEAK'

                    wb = load_workbook(filename="abc.xlsx")
                    ws = wb["a"]
                    for x in dataframe_to_rows(base, index=False, header=False):
                        ws.append(x)  # Append dodaje dane do już istniejących w pliku
                    wb.save("abc.xlsx")
                    for x in dataframe_to_rows(peak, index=False, header=False):
                        ws.append(x)
                    wb.save("abc.xlsx")


st.button('aktualizacja danych z TGE',on_click=aktualizacja)# Przycisk do aktualizacji danych, jeszcze do dopracowania wizualizacja np. popup z postepem, info o zakończeniu

#powtarzam część kodu żeby wyciagnac ostatnia datę poza funkcje i pokazac na strone
wb = load_workbook(filename="abc.xlsx")
ws = wb["a"]
ostatni_wiersz = ws.max_row
ostatnia_data = ws.cell(row=ostatni_wiersz,
                        column=1).value  # uchwycona ostatnia data, dla której są dane w pliku excel
st.write(f'dane aktualne na dzień: {ostatnia_data}')
#https://github.com/sliwka00/WebaooTGEWykresy/blob/master/wykresy.py         ścieżka do 'deploy' na streamlit ale wyskakuje błąd