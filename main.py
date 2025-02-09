import dash.exceptions
import pandas as pd
import openpyxl as pxl
from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import numpy as np
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import dash_bootstrap_templates
from dash_bootstrap_templates import load_figure_template
from dash.exceptions import PreventUpdate
import gunicorn
import xlrd as xlrd

pd.options.mode.chained_assignment = None
pd.options.display.width= None
pd.options.display.max_columns= None
pd.set_option('display.max_rows', 3000)
pd.set_option('display.max_columns', 3000)


# Doel is om een APP te ontwikkelen of een dashboard waarmee je de volgende zaken kan zien.
# Wat zijn de winkeldochters in mijn apotheek?
# Winkeldochter definitie is: Producten die langer dan 4 maanden niet zijn gegaan in mijn apotheek (CGM) en die ik ook moet uitverkopen van Mosadex volgens Optimaal Bestellen

# INZICHTELIJK MAKEN WAT DE WINKELDOCHTERS ZIJN
# We willen van de winkeldochters de volgende dingen kunnen zien:
# (1) Wat is de voorraadwaarde van de winkeldochters
# (2) Waar liggen de winkeldochters
# (3) Informatie over de winkeldochters (hoe staat de min/max nu in het systeem)
# (4) Wat is de AIP per verpakking op dit moment
# (5) Basisinfo moet zijn; PRK, ZI, ETIKETNAAM, INKHVH, EH, AIP ,MIN/MAX, VOORRAAD (EH), VOORRAAD (VERPAKKINGEN), VOORRAADWAARDE, % tov totaal winkeldochters

# INZICHTELIJK MAKEN BIJ WIE WAT GAAT
# We willen de winkeldochters vervolgens kunnen opsplitsen als iets dat we willen
# (1) Verkopen aan andere apotheken omdat het daar gaat uit de ladekast --> hiervoor moeten we weten hoe hard het gaat in een andere apotheek binnen de afgelopen 3 maanden
# (2) Verkopen aan eigen patiënten, maar dan via CF? --> dan moeten we ook weten om welke patiënten dat gaat (op basis van PRK)
# (3) We willen in een tabel zien voor hoeveel (eigen) patiënten dit gaat via CF.
# (4) Voorkeur gaat voor uitverkopen via eigen patiënten bij hoog AIP, daarna pas naar een andere apotheek verplaatsen

# Uitverkopen in eigen apotheek
# (1) Als je wilt uitverkopen binnen je eigen patiënten moet je kijken of er op PRK-nr gezocht kan worden naar patiënten die dit via CF krijgen
# (2) Als resultaat moet je dan een lijst met patiënten krijgen die de afgelopen 3 maanden het product hebben opgehaald.. een extractie van de CF-data van apotheek Helpman.


# Als laatste moet er een export-knop zijn om een tabel te downloaden via excel


# STAP 1: inlezen van de dataframes (Optimaal Bestellen, Assortiment, Receptverwerking)

# recept dataframes inlezen
recept_hanzeplein = pd.read_csv('hanzeplein_recept.txt')
recept_oosterpoort = pd.read_csv('oosterpoort_recept.txt')
recept_helpman = pd.read_csv('helpman_recept.txt')
recept_wiljes = pd.read_csv('wiljes_recept.txt')
recept_oosterhaar = pd.read_csv('oosterhaar_recept.txt')
recept_musselpark = pd.read_csv('musselpark_recept.txt')
# recept kolommen inlezen en bepalen
kolommen_recept = pd.read_excel('kolommen receptverwerking rapport.xlsx')
columns_recept = kolommen_recept.columns
# kolommen receptverwerking toekennen aan dataframes
recept_hanzeplein.columns = columns_recept
recept_oosterpoort.columns = columns_recept
recept_helpman.columns = columns_recept
recept_wiljes.columns = columns_recept
recept_oosterhaar.columns = columns_recept
recept_musselpark.columns = columns_recept
# apotheek kolom maken voor ieder dataframe
recept_hanzeplein['apotheek'] = 'hanzeplein'
recept_oosterpoort['apotheek'] = 'oosterpoort'
recept_helpman['apotheek'] = 'helpman'
recept_wiljes['apotheek'] = 'wiljes'
recept_oosterhaar['apotheek'] = 'oosterhaar'
recept_musselpark['apotheek'] = 'musselpark'

# Samenvoegen van de recept dataframes tot een dataframe

recept_ag = pd.concat([recept_hanzeplein, recept_oosterpoort, recept_helpman, recept_wiljes, recept_oosterhaar, recept_musselpark])

# assortiment dataframes inlezen
assortiment_hanzeplein = pd.read_csv('hanzeplein_assortiment.txt')
assortiment_oosterpoort = pd.read_csv('oosterpoort_assortiment.txt')
assortiment_helpman = pd.read_csv('helpman_assortiment.txt')
assortiment_wiljes = pd.read_csv('wiljes_assortiment.txt')
assortiment_oosterhaar = pd.read_csv('oosterhaar_assortiment.txt')
assortiment_musselpark = pd.read_csv('musselpark_assortiment.txt')
# kolommen inlezen en bepalen assortiment
kolommen_assortiment = pd.read_excel('kolommen assortiment rapport.xlsx')
columns_assortiment = kolommen_assortiment.columns
# toekennen kolommen aan dataframes assortiment
assortiment_hanzeplein.columns = columns_assortiment
assortiment_oosterpoort.columns = columns_assortiment
assortiment_helpman.columns = columns_assortiment
assortiment_wiljes.columns = columns_assortiment
assortiment_oosterhaar.columns = columns_assortiment
assortiment_musselpark.columns = columns_assortiment
# voeg een apotheek kolom toe aan de assortiment dataframes
assortiment_hanzeplein['apotheek'] = 'hanzeplein'
assortiment_oosterpoort['apotheek'] = 'oosterpoort'
assortiment_helpman['apotheek'] = 'helpman'
assortiment_wiljes['apotheek'] = 'wiljes'
assortiment_oosterhaar['apotheek'] = 'oosterhaar'
assortiment_musselpark['apotheek'] = 'musselpark'

# samenvoegen van de assortiment dataframes tot een dataframe
assortiment_ag = pd.concat([assortiment_hanzeplein, assortiment_oosterpoort, assortiment_helpman, assortiment_wiljes, assortiment_oosterhaar, assortiment_musselpark])

# Inlezen Optimaal bestellen dataframe van de betreffende apotheek
optimaal_bestel_advies = pd.read_excel('OB.xlsx')


# Overzicht van de ingelezen dataframes
recept_ag               # Receptverwerking van alle apotheken binnen de AG
assortiment_ag          # Assortimenten van alle AG apotheken
optimaal_bestel_advies  # Optimaal Besteladvies van apotheek die je wilt bekijken


# STAP 2: Overzicht maken van de verstrekkingen via ladekast en CF van iedere apotheek

# zorg ervoor dat je een aantal producten excludeert (zorg, lsp, dienst-recepten en distributierecepten)

# filters voor exclusie

verstrekkingen = recept_ag.copy()

geen_zorgregels = (verstrekkingen['ReceptHerkomst']!='Z')
geen_LSP = (verstrekkingen['sdMedewerkerCode']!='LSP')
geen_dienst_recepten = (verstrekkingen['ReceptHerkomst']!='DIENST')
geen_distributie = (verstrekkingen['ReceptHerkomst']!='D')
geen_cf = (verstrekkingen['cf']=='N')
alleen_cf = (verstrekkingen['cf']=='J')

# datumrange van zoeken vastleggen: 4 maanden korter dan de max waarde van het dataframe

# omzetten naar een datetime kolom
verstrekkingen['ddDatumRecept'] = pd.to_datetime(verstrekkingen['ddDatumRecept'])

# bekijk wat de max datum is van het geimporteerde dataframe
meest_recente_datum = verstrekkingen['ddDatumRecept'].max()

# bereken de begindatum van meten met onderstaande functie --> 4 maanden in het verleden
begin_datum = (meest_recente_datum - pd.DateOffset(months=4))

# stel het dataframe tijdsfilter vast voor meetperiode
datum_range = (verstrekkingen['ddDatumRecept']>=begin_datum)


# ======================================================================================================================================================
# Dataframe met LADEKAST VERSTREKKINGEN
verstrekkingen_1_zonder_cf = verstrekkingen.loc[geen_zorgregels & geen_LSP & geen_dienst_recepten & geen_distributie & geen_cf & datum_range]

# Dataframe met CF VERSTREKKINGEN
verstrekkingen_1_met_cf = verstrekkingen.loc[geen_zorgregels & geen_LSP & geen_dienst_recepten & geen_distributie & alleen_cf & datum_range]

# ======================================================================================================================================================


# pad 1: alleen verstrekkingen vanuit de ladekast gaan tellen per apotheek per zi als totaal
hanzeplein_lade = (verstrekkingen_1_zonder_cf['apotheek']=='hanzeplein')
oosterpoort_lade = (verstrekkingen_1_zonder_cf['apotheek']=='oosterpoort')
helpman_lade = (verstrekkingen_1_zonder_cf['apotheek']=='helpman')
wiljes_lade = (verstrekkingen_1_zonder_cf['apotheek']=='wiljes')
oosterhaar_lade = (verstrekkingen_1_zonder_cf['apotheek']=='oosterhaar')
musselpark_lade = (verstrekkingen_1_zonder_cf['apotheek']=='musselpark')

# hanzeplein
verstrekkingen_1_zonder_cf_hanzeplein = verstrekkingen_1_zonder_cf.loc[hanzeplein_lade]
verstrekkingen_1_zonder_cf_hanzeplein_eenheden = verstrekkingen_1_zonder_cf_hanzeplein.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame('eenheden verstrekt hanzeplein').reset_index()

# oosterpoort
verstrekkingen_1_zonder_cf_oosterpoort = verstrekkingen_1_zonder_cf.loc[oosterpoort_lade]
verstrekkingen_1_zonder_cf_oosterpoort_eenheden = verstrekkingen_1_zonder_cf_oosterpoort.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame('eenheden verstrekt oosterpoort').reset_index()

# helpman
verstrekkingen_1_zonder_cf_helpman = verstrekkingen_1_zonder_cf.loc[helpman_lade]
verstrekkingen_1_zonder_cf_helpman_eenheden = verstrekkingen_1_zonder_cf_helpman.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame('eenheden verstrekt helpman').reset_index()


# wiljes
verstrekkingen_1_zonder_cf_wiljes = verstrekkingen_1_zonder_cf.loc[wiljes_lade]
verstrekkingen_1_zonder_cf_wiljes_eenheden = verstrekkingen_1_zonder_cf_wiljes.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame('eenheden verstrekt wiljes').reset_index()


# oosterhaar
verstrekkingen_1_zonder_cf_oosterhaar = verstrekkingen_1_zonder_cf.loc[oosterhaar_lade]
verstrekkingen_1_zonder_cf_oosterhaar_eenheden = verstrekkingen_1_zonder_cf_oosterhaar.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame('eenheden verstrekt oosterhaar').reset_index()

# musselpark
verstrekkingen_1_zonder_cf_musselpark = verstrekkingen_1_zonder_cf.loc[musselpark_lade]
verstrekkingen_1_zonder_cf_musselpark_eenheden = verstrekkingen_1_zonder_cf_musselpark.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame('eenheden verstrekt musselpark').reset_index()

# bovenstaande dataframes samenvoegen tot één lange rij
# eerst paartjes van twee
hzp_op_lk = verstrekkingen_1_zonder_cf_hanzeplein_eenheden.merge(verstrekkingen_1_zonder_cf_oosterpoort_eenheden[['ndATKODE', 'eenheden verstrekt oosterpoort']], how='left')
hlp_wil_lk = verstrekkingen_1_zonder_cf_helpman_eenheden.merge(verstrekkingen_1_zonder_cf_wiljes_eenheden[['ndATKODE', 'eenheden verstrekt wiljes']], how='left')
oh_mp_lk = verstrekkingen_1_zonder_cf_oosterhaar_eenheden.merge(verstrekkingen_1_zonder_cf_musselpark_eenheden[['ndATKODE', 'eenheden verstrekt musselpark']], how='left')

# 1+2 en 3+4
hzp_op_hlp_wil_lk = hzp_op_lk.merge(hlp_wil_lk[['ndATKODE', 'eenheden verstrekt helpman', 'eenheden verstrekt wiljes']], how='left')
# 1, 2, 3, 4 + 5 en 6
hzp_op_hlp_wil_oh_mp = hzp_op_hlp_wil_lk.merge(oh_mp_lk[['ndATKODE', 'eenheden verstrekt oosterhaar', 'eenheden verstrekt musselpark']], how='left')

# Hernoem de kolommen tot iets wat goed te lezen is.
hzp_op_hlp_wil_oh_mp.columns = ['ZI', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar', 'musselpark']

# Vervang NaN door 0
hzp_op_hlp_wil_oh_mp['hanzeplein'] = (hzp_op_hlp_wil_oh_mp['hanzeplein'].replace(np.nan, 0, regex=True)).astype(int)
hzp_op_hlp_wil_oh_mp['oosterpoort'] = (hzp_op_hlp_wil_oh_mp['oosterpoort'].replace(np.nan, 0, regex=True)).astype(int)
hzp_op_hlp_wil_oh_mp['helpman'] = (hzp_op_hlp_wil_oh_mp['helpman'].replace(np.nan, 0, regex=True)).astype(int)
hzp_op_hlp_wil_oh_mp['wiljes'] = (hzp_op_hlp_wil_oh_mp['wiljes'].replace(np.nan, 0, regex=True)).astype(int)
hzp_op_hlp_wil_oh_mp['oosterhaar'] = (hzp_op_hlp_wil_oh_mp['oosterhaar'].replace(np.nan, 0, regex=True)).astype(int)
hzp_op_hlp_wil_oh_mp['musselpark'] = (hzp_op_hlp_wil_oh_mp['musselpark'].replace(np.nan, 0, regex=True)).astype(int)


# pad 2: ALLEEN VERSTREKKINGEN VANUIT DE CENTRAL FILLING VOOR ALLE APOTHEKEN

verstrekkingen_cf = verstrekkingen_1_met_cf.groupby(by=['ndATKODE', 'apotheek'])['ndAantal'].sum().to_frame('eenheden verstrekt CF').reset_index()



# ======================================================================================================================================================
eenheden_verstrekt = hzp_op_hlp_wil_oh_mp                       # overzicht van de eenheden die de afgelopen 4 maanden verstrekt zijn.
# ======================================================================================================================================================

# ======================================================================================================================================================
Apotheek_analyse = 'helpman'                    # Filter voor apotheek
# ======================================================================================================================================================

#selecteer het assortiment van de apotheek dat je wilt analyseren
analyse_assortiment = assortiment_ag.copy()

# selecteer het assortiment dat je wilt beoordelen van de specifieke apotheek
apotheek_keuze = (analyse_assortiment['apotheek'] == Apotheek_analyse)

# selecteer de apotheek waarvan je de CF verstrekkingen wilt bekijken voor de winkeldochters
apotheek_keuze_cf = (verstrekkingen_cf['apotheek']== Apotheek_analyse)

# maak het dataframe van de CF verstrekkingen klaar
verstrekkingen_cf_apotheek_analyse = verstrekkingen_cf.loc[apotheek_keuze_cf]


# filter het assortiment van de te analyseren apotheek uit de bult
analyse_assortiment_apotheek = analyse_assortiment.loc[apotheek_keuze]

analyse_assortiment_apotheek['voorraadwaarde'] = ((analyse_assortiment_apotheek['voorraadtotaal']/analyse_assortiment_apotheek['inkhvh'])*analyse_assortiment_apotheek['inkprijs']).astype(int)





# maak het filter voor de verstrekkingen van de apotheek die je op 0 wilt hebben staan
eenheden_verstrekt_apotheek_selectie = (eenheden_verstrekt[Apotheek_analyse]==0)

#filter het verstrekkingsdataframe
eenheden_analyse = eenheden_verstrekt.loc[eenheden_verstrekt_apotheek_selectie]

analyse_bestand = eenheden_analyse.merge(analyse_assortiment_apotheek[['zinummer', 'artikelnaam',
       'inkhvh', 'eh', 'voorraadminimum', 'voorraadmaximum', 'locatie1',
       'voorraadtotaal', 'inkprijs', 'prkode', 'voorraadwaarde']], how='left', left_on = 'ZI', right_on = 'zinummer').drop(columns='zinummer')

voorraad_winkeldochter = (analyse_bestand['voorraadtotaal']>0)

analyse_bestand_1 = analyse_bestand.loc[voorraad_winkeldochter]



# We hebben nu de verstrekkingen bij de andere apotheken in kaart... nu is het zaak om OPTIMAAL BESTELLEN TOE TE VOEGEN AAN DE MIX
# converteer uitverkoop advies type naar string
optimaal_bestel_advies['Uitverk. advies'] = optimaal_bestel_advies['Uitverk. advies'].astype(str)
# alleen uitverkoop-advies - ja
alleen_uitverkopen = (optimaal_bestel_advies['Uitverk. advies']=='True')
# filter dataframe zodat alleen de uitverkoop-advies artikelen naar boven komen.
optimaal_bestel_advies_winkeldochters = optimaal_bestel_advies.loc[alleen_uitverkopen]

# maak het OB dataframe kleiner zodat het beter leesbaar is
optimaal_bestel_advies_winkeldochters_1 = optimaal_bestel_advies_winkeldochters[['PRK Code', 'ZI', 'Artikelomschrijving', 'Inhoud', 'Eenheid','Uitverk. advies' ]]

# merge deze nu met het analyse bestand
wd_bestand = analyse_bestand_1.merge(optimaal_bestel_advies_winkeldochters_1[['ZI', 'Artikelomschrijving', 'Uitverk. advies']], how='inner', on='ZI')

wd_bestand_1 = wd_bestand[['ZI', 'prkode', 'artikelnaam', 'inkhvh', 'eh', 'voorraadminimum',
       'voorraadmaximum', 'voorraadtotaal', 'locatie1', 'inkprijs', 'voorraadwaarde', 'Uitverk. advies', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar',
       'musselpark']]

# merge nu als laatste stap de CF verstrekkingen

winkeldochters_compleet = wd_bestand_1.merge(verstrekkingen_cf_apotheek_analyse[['ndATKODE', 'eenheden verstrekt CF']], how='left', left_on = 'ZI', right_on='ndATKODE').drop(columns='ndATKODE')

winkeldochters_compleet['eenheden verstrekt CF'] = (winkeldochters_compleet['eenheden verstrekt CF'].replace(np.nan, 0, regex=True)).astype(int)


# ======================================================================================================================================================
winkeldochters_compleet                   # Bestand van de winkeldochters!!
# ======================================================================================================================================================


# In de tweede stap maken we het mogelijk om te zoeken naar een ZI nummer om te kijken of er patienten zijn die de winkeldochters eigenlijk via CF ophalen
# concept: via Ctrl+C en Ctrl+V moet je een ZI of PRK in een zoekbalk in kunnen vullen zodat je daarna kan zien welke patiënten deze producten ophalen.
# We pakken een versimpelde vorm van de receptverwerkingsdataframe pakken en gaan daar een filter opgooien van ZI

zoek_CF_verstrekkingen = recept_ag.copy()

Apotheek_analyse_CF = 'helpman'                    # Filter voor apotheek

#definieer nu het filter: dit is de apotheek die je gaat analyseren
filter_apotheek_analyse = (zoek_CF_verstrekkingen['apotheek']== Apotheek_analyse_CF)

# datum range vaststellen
zoek_CF_verstrekkingen['ddDatumRecept'] = pd.to_datetime(zoek_CF_verstrekkingen['ddDatumRecept'])
max_datum_zi_zoek_cf = zoek_CF_verstrekkingen['ddDatumRecept'].max()
# datum -4 maanden
min_datum_zi_zoek_cf = max_datum_zi_zoek_cf - pd.DateOffset(months=4)

# maak een filter voor de datum range
datum_range_filter_zi_zoek_cf = (zoek_CF_verstrekkingen['ddDatumRecept'] >= min_datum_zi_zoek_cf)

# pas filters toe apotheek en datum
zoek_CF_verstrekkingen_1 = zoek_CF_verstrekkingen.loc[filter_apotheek_analyse & datum_range_filter_zi_zoek_cf]

zoek_CF_verstrekkingen_2 = zoek_CF_verstrekkingen_1[['ndPatientnr',
       'ddDatumRecept', 'ndPRKODE', 'ndATKODE', 'sdEtiketNaam', 'ndAantal', 'Uitgifte', 'cf','apotheek']]

# ==================================================================================================
zoek_zi = 15673375                        # Input in het dataframe
# ==================================================================================================

# filter voor zoeken
filter_zi =  (zoek_CF_verstrekkingen_2['ndATKODE'] == zoek_zi)

# toon het dataframe na invoeren van de zoekterm

zoek_CF_verstrekkingen_3 = zoek_CF_verstrekkingen_2.loc[filter_zi]


# laatste stap is het maken van een app waarmee we aan de slag kunnen.



# Maken van de app

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
       dbc.Row([html.H1('Winkeldochters Analyse')]),
       dbc.Row([dcc.RadioItems(id='apotheek', options=recept_ag['apotheek'].unique(), value='helpman', inline=True)]),
       dbc.Row([html.H4('Winkeldochters geselecteerde apotheek')]),
       dbc.Row([html.Div(id='winkeldochters')]),
       dbc.Row([
              dbc.Col([], width=4),
              dbc.Col([], width=5),
              dbc.Col([
                     dbc.Button(id='download',children="Download xlsx", color="success", className="me-1"),
                     dcc.Download(id='download winkeldochters')
              ], width=3)
       ]),

       dbc.Row([html.H4('Zoek CF verstrekkingen op ZI-nummer')]),
       dbc.Row([
              dbc.Col([dcc.Input(id='ZI invoer', type='number', placeholder='Voer ZI in')], width=3),
              dbc.Col([], width=3),
              dbc.Col([], width=6)
       ]),
       dbc.Row([html.Div(id='CF verstrekkingen')]),
])


# Callback voor het tonen van de winkeldochters van de geselecteerde apotheek
@callback(
         Output('winkeldochters', 'children'),
         Input('apotheek', 'value')
)
def winkeldochters_apotheek(apotheek):
       # STAP 2: Overzicht maken van de verstrekkingen via ladekast en CF van iedere apotheek

       # zorg ervoor dat je een aantal producten excludeert (zorg, lsp, dienst-recepten en distributierecepten)

       # filters voor exclusie

       verstrekkingen = recept_ag.copy()

       geen_zorgregels = (verstrekkingen['ReceptHerkomst'] != 'Z')
       geen_LSP = (verstrekkingen['sdMedewerkerCode'] != 'LSP')
       geen_dienst_recepten = (verstrekkingen['ReceptHerkomst'] != 'DIENST')
       geen_distributie = (verstrekkingen['ReceptHerkomst'] != 'D')
       geen_cf = (verstrekkingen['cf'] == 'N')
       alleen_cf = (verstrekkingen['cf'] == 'J')

       # datumrange van zoeken vastleggen: 4 maanden korter dan de max waarde van het dataframe

       # omzetten naar een datetime kolom
       verstrekkingen['ddDatumRecept'] = pd.to_datetime(verstrekkingen['ddDatumRecept'])

       # bekijk wat de max datum is van het geimporteerde dataframe
       meest_recente_datum = verstrekkingen['ddDatumRecept'].max()

       # bereken de begindatum van meten met onderstaande functie --> 4 maanden in het verleden
       begin_datum = (meest_recente_datum - pd.DateOffset(months=4))

       # stel het dataframe tijdsfilter vast voor meetperiode
       datum_range = (verstrekkingen['ddDatumRecept'] >= begin_datum)

       # ======================================================================================================================================================
       # Dataframe met LADEKAST VERSTREKKINGEN
       verstrekkingen_1_zonder_cf = verstrekkingen.loc[
              geen_zorgregels & geen_LSP & geen_dienst_recepten & geen_distributie & geen_cf & datum_range]

       # Dataframe met CF VERSTREKKINGEN
       verstrekkingen_1_met_cf = verstrekkingen.loc[
              geen_zorgregels & geen_LSP & geen_dienst_recepten & geen_distributie & alleen_cf & datum_range]

       # ======================================================================================================================================================

       # pad 1: alleen verstrekkingen vanuit de ladekast gaan tellen per apotheek per zi als totaal
       hanzeplein_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'hanzeplein')
       oosterpoort_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'oosterpoort')
       helpman_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'helpman')
       wiljes_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'wiljes')
       oosterhaar_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'oosterhaar')
       musselpark_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'musselpark')

       # hanzeplein
       verstrekkingen_1_zonder_cf_hanzeplein = verstrekkingen_1_zonder_cf.loc[hanzeplein_lade]
       verstrekkingen_1_zonder_cf_hanzeplein_eenheden = verstrekkingen_1_zonder_cf_hanzeplein.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt hanzeplein').reset_index()

       # oosterpoort
       verstrekkingen_1_zonder_cf_oosterpoort = verstrekkingen_1_zonder_cf.loc[oosterpoort_lade]
       verstrekkingen_1_zonder_cf_oosterpoort_eenheden = \
       verstrekkingen_1_zonder_cf_oosterpoort.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame(
              'eenheden verstrekt oosterpoort').reset_index()

       # helpman
       verstrekkingen_1_zonder_cf_helpman = verstrekkingen_1_zonder_cf.loc[helpman_lade]
       verstrekkingen_1_zonder_cf_helpman_eenheden = verstrekkingen_1_zonder_cf_helpman.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt helpman').reset_index()

       # wiljes
       verstrekkingen_1_zonder_cf_wiljes = verstrekkingen_1_zonder_cf.loc[wiljes_lade]
       verstrekkingen_1_zonder_cf_wiljes_eenheden = verstrekkingen_1_zonder_cf_wiljes.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt wiljes').reset_index()

       # oosterhaar
       verstrekkingen_1_zonder_cf_oosterhaar = verstrekkingen_1_zonder_cf.loc[oosterhaar_lade]
       verstrekkingen_1_zonder_cf_oosterhaar_eenheden = verstrekkingen_1_zonder_cf_oosterhaar.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt oosterhaar').reset_index()

       # musselpark
       verstrekkingen_1_zonder_cf_musselpark = verstrekkingen_1_zonder_cf.loc[musselpark_lade]
       verstrekkingen_1_zonder_cf_musselpark_eenheden = verstrekkingen_1_zonder_cf_musselpark.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt musselpark').reset_index()

       # bovenstaande dataframes samenvoegen tot één lange rij
       # eerst paartjes van twee
       hzp_op_lk = verstrekkingen_1_zonder_cf_hanzeplein_eenheden.merge(
              verstrekkingen_1_zonder_cf_oosterpoort_eenheden[['ndATKODE', 'eenheden verstrekt oosterpoort']],
              how='left')
       hlp_wil_lk = verstrekkingen_1_zonder_cf_helpman_eenheden.merge(
              verstrekkingen_1_zonder_cf_wiljes_eenheden[['ndATKODE', 'eenheden verstrekt wiljes']], how='left')
       oh_mp_lk = verstrekkingen_1_zonder_cf_oosterhaar_eenheden.merge(
              verstrekkingen_1_zonder_cf_musselpark_eenheden[['ndATKODE', 'eenheden verstrekt musselpark']], how='left')

       # 1+2 en 3+4
       hzp_op_hlp_wil_lk = hzp_op_lk.merge(
              hlp_wil_lk[['ndATKODE', 'eenheden verstrekt helpman', 'eenheden verstrekt wiljes']], how='left')
       # 1, 2, 3, 4 + 5 en 6
       hzp_op_hlp_wil_oh_mp = hzp_op_hlp_wil_lk.merge(
              oh_mp_lk[['ndATKODE', 'eenheden verstrekt oosterhaar', 'eenheden verstrekt musselpark']], how='left')

       # Hernoem de kolommen tot iets wat goed te lezen is.
       hzp_op_hlp_wil_oh_mp.columns = ['ZI', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar',
                                       'musselpark']

       # Vervang NaN door 0
       hzp_op_hlp_wil_oh_mp['hanzeplein'] = (hzp_op_hlp_wil_oh_mp['hanzeplein'].replace(np.nan, 0, regex=True)).astype(
              int)
       hzp_op_hlp_wil_oh_mp['oosterpoort'] = (
              hzp_op_hlp_wil_oh_mp['oosterpoort'].replace(np.nan, 0, regex=True)).astype(int)
       hzp_op_hlp_wil_oh_mp['helpman'] = (hzp_op_hlp_wil_oh_mp['helpman'].replace(np.nan, 0, regex=True)).astype(int)
       hzp_op_hlp_wil_oh_mp['wiljes'] = (hzp_op_hlp_wil_oh_mp['wiljes'].replace(np.nan, 0, regex=True)).astype(int)
       hzp_op_hlp_wil_oh_mp['oosterhaar'] = (hzp_op_hlp_wil_oh_mp['oosterhaar'].replace(np.nan, 0, regex=True)).astype(
              int)
       hzp_op_hlp_wil_oh_mp['musselpark'] = (hzp_op_hlp_wil_oh_mp['musselpark'].replace(np.nan, 0, regex=True)).astype(
              int)

       # pad 2: ALLEEN VERSTREKKINGEN VANUIT DE CENTRAL FILLING VOOR ALLE APOTHEKEN

       verstrekkingen_cf = verstrekkingen_1_met_cf.groupby(by=['ndATKODE', 'apotheek'])['ndAantal'].sum().to_frame(
              'eenheden verstrekt CF').reset_index()

       # ======================================================================================================================================================
       eenheden_verstrekt = hzp_op_hlp_wil_oh_mp  # overzicht van de eenheden die de afgelopen 4 maanden verstrekt zijn.
       # ======================================================================================================================================================

       # ======================================================================================================================================================
       Apotheek_analyse = apotheek  # Filter voor apotheek
       # ======================================================================================================================================================

       # selecteer het assortiment van de apotheek dat je wilt analyseren
       analyse_assortiment = assortiment_ag.copy()

       # selecteer het assortiment dat je wilt beoordelen van de specifieke apotheek
       apotheek_keuze = (analyse_assortiment['apotheek'] == Apotheek_analyse)

       # selecteer de apotheek waarvan je de CF verstrekkingen wilt bekijken voor de winkeldochters
       apotheek_keuze_cf = (verstrekkingen_cf['apotheek'] == Apotheek_analyse)

       # maak het dataframe van de CF verstrekkingen klaar
       verstrekkingen_cf_apotheek_analyse = verstrekkingen_cf.loc[apotheek_keuze_cf]

       # filter het assortiment van de te analyseren apotheek uit de bult
       analyse_assortiment_apotheek = analyse_assortiment.loc[apotheek_keuze]

       analyse_assortiment_apotheek['voorraadwaarde'] = (
                      (analyse_assortiment_apotheek['voorraadtotaal'] / analyse_assortiment_apotheek['inkhvh']) *
                      analyse_assortiment_apotheek['inkprijs']).astype(int)

       # maak het filter voor de verstrekkingen van de apotheek die je op 0 wilt hebben staan
       eenheden_verstrekt_apotheek_selectie = (eenheden_verstrekt[Apotheek_analyse] == 0)

       # filter het verstrekkingsdataframe
       eenheden_analyse = eenheden_verstrekt.loc[eenheden_verstrekt_apotheek_selectie]

       analyse_bestand = eenheden_analyse.merge(analyse_assortiment_apotheek[['zinummer', 'artikelnaam',
                                                                              'inkhvh', 'eh', 'voorraadminimum',
                                                                              'voorraadmaximum', 'locatie1',
                                                                              'voorraadtotaal', 'inkprijs', 'prkode',
                                                                              'voorraadwaarde']], how='left',
                                                left_on='ZI', right_on='zinummer').drop(columns='zinummer')

       voorraad_winkeldochter = (analyse_bestand['voorraadtotaal'] > 0)

       analyse_bestand_1 = analyse_bestand.loc[voorraad_winkeldochter]

       # We hebben nu de verstrekkingen bij de andere apotheken in kaart... nu is het zaak om het optimaal bestellen toe te voegen aan de mix.
       # converteer uitverkoop advies type naar string
       optimaal_bestel_advies['Uitverk. advies'] = optimaal_bestel_advies['Uitverk. advies'].astype(str)
       # alleen uitverkoop-advies - ja
       alleen_uitverkopen = (optimaal_bestel_advies['Uitverk. advies'] == 'True')
       # filter dataframe zodat alleen de uitverkoop-advies artikelen naar boven komen.
       optimaal_bestel_advies_winkeldochters = optimaal_bestel_advies.loc[alleen_uitverkopen]

       # maak het OB dataframe kleiner zodat het beter leesbaar is
       optimaal_bestel_advies_winkeldochters_1 = optimaal_bestel_advies_winkeldochters[
              ['PRK Code', 'ZI', 'Artikelomschrijving', 'Inhoud', 'Eenheid', 'Uitverk. advies']]

       # merge deze nu met het analyse bestand
       wd_bestand = analyse_bestand_1.merge(
              optimaal_bestel_advies_winkeldochters_1[['ZI', 'Artikelomschrijving', 'Uitverk. advies']], how='inner',
              on='ZI')

       wd_bestand_1 = wd_bestand[['ZI', 'prkode', 'artikelnaam', 'inkhvh', 'eh', 'voorraadminimum',
                                  'voorraadmaximum', 'voorraadtotaal', 'locatie1', 'inkprijs', 'voorraadwaarde',
                                  'Uitverk. advies', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar',
                                  'musselpark']]

       # merge nu als laatste stap de CF verstrekkingen

       winkeldochters_compleet = wd_bestand_1.merge(
              verstrekkingen_cf_apotheek_analyse[['ndATKODE', 'eenheden verstrekt CF']], how='left', left_on='ZI',
              right_on='ndATKODE').drop(columns='ndATKODE')

       winkeldochters_compleet['eenheden verstrekt CF'] = (
              winkeldochters_compleet['eenheden verstrekt CF'].replace(np.nan, 0, regex=True)).astype(int)

       wd_grid = dag.AgGrid(
              rowData=winkeldochters_compleet.to_dict('records'),
              columnDefs=[{'field': i } for i in winkeldochters_compleet.columns],
              dashGridOptions={'enableCellTextSelection':'True'}
       )
       return wd_grid

@callback(
       Output('download winkeldochters', 'data'),
       Output('download', 'n_clicks'),
       Input('download', 'n_clicks'),
       Input('apotheek', 'value')

)
def download_winkeldochters(n_clicks, apotheek):

       if not n_clicks:
              raise PreventUpdate
       # STAP 2: Overzicht maken van de verstrekkingen via ladekast en CF van iedere apotheek

       # zorg ervoor dat je een aantal producten excludeert (zorg, lsp, dienst-recepten en distributierecepten)

       # filters voor exclusie

       verstrekkingen = recept_ag.copy()

       geen_zorgregels = (verstrekkingen['ReceptHerkomst'] != 'Z')
       geen_LSP = (verstrekkingen['sdMedewerkerCode'] != 'LSP')
       geen_dienst_recepten = (verstrekkingen['ReceptHerkomst'] != 'DIENST')
       geen_distributie = (verstrekkingen['ReceptHerkomst'] != 'D')
       geen_cf = (verstrekkingen['cf'] == 'N')
       alleen_cf = (verstrekkingen['cf'] == 'J')

       # datumrange van zoeken vastleggen: 4 maanden korter dan de max waarde van het dataframe

       # omzetten naar een datetime kolom
       verstrekkingen['ddDatumRecept'] = pd.to_datetime(verstrekkingen['ddDatumRecept'])

       # bekijk wat de max datum is van het geimporteerde dataframe
       meest_recente_datum = verstrekkingen['ddDatumRecept'].max()

       # bereken de begindatum van meten met onderstaande functie --> 4 maanden in het verleden
       begin_datum = (meest_recente_datum - pd.DateOffset(months=4))

       # stel het dataframe tijdsfilter vast voor meetperiode
       datum_range = (verstrekkingen['ddDatumRecept'] >= begin_datum)

       # ======================================================================================================================================================
       # Dataframe met LADEKAST VERSTREKKINGEN
       verstrekkingen_1_zonder_cf = verstrekkingen.loc[
              geen_zorgregels & geen_LSP & geen_dienst_recepten & geen_distributie & geen_cf & datum_range]

       # Dataframe met CF VERSTREKKINGEN
       verstrekkingen_1_met_cf = verstrekkingen.loc[
              geen_zorgregels & geen_LSP & geen_dienst_recepten & geen_distributie & alleen_cf & datum_range]

       # ======================================================================================================================================================

       # pad 1: alleen verstrekkingen vanuit de ladekast gaan tellen per apotheek per zi als totaal
       hanzeplein_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'hanzeplein')
       oosterpoort_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'oosterpoort')
       helpman_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'helpman')
       wiljes_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'wiljes')
       oosterhaar_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'oosterhaar')
       musselpark_lade = (verstrekkingen_1_zonder_cf['apotheek'] == 'musselpark')

       # hanzeplein
       verstrekkingen_1_zonder_cf_hanzeplein = verstrekkingen_1_zonder_cf.loc[hanzeplein_lade]
       verstrekkingen_1_zonder_cf_hanzeplein_eenheden = verstrekkingen_1_zonder_cf_hanzeplein.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt hanzeplein').reset_index()

       # oosterpoort
       verstrekkingen_1_zonder_cf_oosterpoort = verstrekkingen_1_zonder_cf.loc[oosterpoort_lade]
       verstrekkingen_1_zonder_cf_oosterpoort_eenheden = \
       verstrekkingen_1_zonder_cf_oosterpoort.groupby(by=['ndATKODE'])['ndAantal'].sum().to_frame(
              'eenheden verstrekt oosterpoort').reset_index()

       # helpman
       verstrekkingen_1_zonder_cf_helpman = verstrekkingen_1_zonder_cf.loc[helpman_lade]
       verstrekkingen_1_zonder_cf_helpman_eenheden = verstrekkingen_1_zonder_cf_helpman.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt helpman').reset_index()

       # wiljes
       verstrekkingen_1_zonder_cf_wiljes = verstrekkingen_1_zonder_cf.loc[wiljes_lade]
       verstrekkingen_1_zonder_cf_wiljes_eenheden = verstrekkingen_1_zonder_cf_wiljes.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt wiljes').reset_index()

       # oosterhaar
       verstrekkingen_1_zonder_cf_oosterhaar = verstrekkingen_1_zonder_cf.loc[oosterhaar_lade]
       verstrekkingen_1_zonder_cf_oosterhaar_eenheden = verstrekkingen_1_zonder_cf_oosterhaar.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt oosterhaar').reset_index()

       # musselpark
       verstrekkingen_1_zonder_cf_musselpark = verstrekkingen_1_zonder_cf.loc[musselpark_lade]
       verstrekkingen_1_zonder_cf_musselpark_eenheden = verstrekkingen_1_zonder_cf_musselpark.groupby(by=['ndATKODE'])[
              'ndAantal'].sum().to_frame('eenheden verstrekt musselpark').reset_index()

       # bovenstaande dataframes samenvoegen tot één lange rij
       # eerst paartjes van twee
       hzp_op_lk = verstrekkingen_1_zonder_cf_hanzeplein_eenheden.merge(
              verstrekkingen_1_zonder_cf_oosterpoort_eenheden[['ndATKODE', 'eenheden verstrekt oosterpoort']],
              how='left')
       hlp_wil_lk = verstrekkingen_1_zonder_cf_helpman_eenheden.merge(
              verstrekkingen_1_zonder_cf_wiljes_eenheden[['ndATKODE', 'eenheden verstrekt wiljes']], how='left')
       oh_mp_lk = verstrekkingen_1_zonder_cf_oosterhaar_eenheden.merge(
              verstrekkingen_1_zonder_cf_musselpark_eenheden[['ndATKODE', 'eenheden verstrekt musselpark']], how='left')

       # 1+2 en 3+4
       hzp_op_hlp_wil_lk = hzp_op_lk.merge(
              hlp_wil_lk[['ndATKODE', 'eenheden verstrekt helpman', 'eenheden verstrekt wiljes']], how='left')
       # 1, 2, 3, 4 + 5 en 6
       hzp_op_hlp_wil_oh_mp = hzp_op_hlp_wil_lk.merge(
              oh_mp_lk[['ndATKODE', 'eenheden verstrekt oosterhaar', 'eenheden verstrekt musselpark']], how='left')

       # Hernoem de kolommen tot iets wat goed te lezen is.
       hzp_op_hlp_wil_oh_mp.columns = ['ZI', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar',
                                       'musselpark']

       # Vervang NaN door 0
       hzp_op_hlp_wil_oh_mp['hanzeplein'] = (hzp_op_hlp_wil_oh_mp['hanzeplein'].replace(np.nan, 0, regex=True)).astype(
              int)
       hzp_op_hlp_wil_oh_mp['oosterpoort'] = (
              hzp_op_hlp_wil_oh_mp['oosterpoort'].replace(np.nan, 0, regex=True)).astype(int)
       hzp_op_hlp_wil_oh_mp['helpman'] = (hzp_op_hlp_wil_oh_mp['helpman'].replace(np.nan, 0, regex=True)).astype(int)
       hzp_op_hlp_wil_oh_mp['wiljes'] = (hzp_op_hlp_wil_oh_mp['wiljes'].replace(np.nan, 0, regex=True)).astype(int)
       hzp_op_hlp_wil_oh_mp['oosterhaar'] = (hzp_op_hlp_wil_oh_mp['oosterhaar'].replace(np.nan, 0, regex=True)).astype(
              int)
       hzp_op_hlp_wil_oh_mp['musselpark'] = (hzp_op_hlp_wil_oh_mp['musselpark'].replace(np.nan, 0, regex=True)).astype(
              int)

       # pad 2: ALLEEN VERSTREKKINGEN VANUIT DE CENTRAL FILLING VOOR ALLE APOTHEKEN

       verstrekkingen_cf = verstrekkingen_1_met_cf.groupby(by=['ndATKODE', 'apotheek'])['ndAantal'].sum().to_frame(
              'eenheden verstrekt CF').reset_index()

       # ======================================================================================================================================================
       eenheden_verstrekt = hzp_op_hlp_wil_oh_mp  # overzicht van de eenheden die de afgelopen 4 maanden verstrekt zijn.
       # ======================================================================================================================================================

       # ======================================================================================================================================================
       Apotheek_analyse = 'helpman'  # Filter voor apotheek
       # ======================================================================================================================================================

       # selecteer het assortiment van de apotheek dat je wilt analyseren
       analyse_assortiment = assortiment_ag.copy()

       # selecteer het assortiment dat je wilt beoordelen van de specifieke apotheek
       apotheek_keuze = (analyse_assortiment['apotheek'] == Apotheek_analyse)

       # selecteer de apotheek waarvan je de CF verstrekkingen wilt bekijken voor de winkeldochters
       apotheek_keuze_cf = (verstrekkingen_cf['apotheek'] == Apotheek_analyse)

       # maak het dataframe van de CF verstrekkingen klaar
       verstrekkingen_cf_apotheek_analyse = verstrekkingen_cf.loc[apotheek_keuze_cf]

       # filter het assortiment van de te analyseren apotheek uit de bult
       analyse_assortiment_apotheek = analyse_assortiment.loc[apotheek_keuze]

       analyse_assortiment_apotheek['voorraadwaarde'] = (
                      (analyse_assortiment_apotheek['voorraadtotaal'] / analyse_assortiment_apotheek['inkhvh']) *
                      analyse_assortiment_apotheek['inkprijs']).astype(int)

       # maak het filter voor de verstrekkingen van de apotheek die je op 0 wilt hebben staan
       eenheden_verstrekt_apotheek_selectie = (eenheden_verstrekt[Apotheek_analyse] == 0)

       # filter het verstrekkingsdataframe
       eenheden_analyse = eenheden_verstrekt.loc[eenheden_verstrekt_apotheek_selectie]

       analyse_bestand = eenheden_analyse.merge(analyse_assortiment_apotheek[['zinummer', 'artikelnaam',
                                                                              'inkhvh', 'eh', 'voorraadminimum',
                                                                              'voorraadmaximum', 'locatie1',
                                                                              'voorraadtotaal', 'inkprijs', 'prkode',
                                                                              'voorraadwaarde']], how='left',
                                                left_on='ZI', right_on='zinummer').drop(columns='zinummer')

       voorraad_winkeldochter = (analyse_bestand['voorraadtotaal'] > 0)

       analyse_bestand_1 = analyse_bestand.loc[voorraad_winkeldochter]

       # We hebben nu de verstrekkingen bij de andere apotheken in kaart... nu is het zaak om OPTIMAAL BESTELLEN TOE TE VOEGEN AAN DE MIX
       # converteer uitverkoop advies type naar string
       optimaal_bestel_advies['Uitverk. advies'] = optimaal_bestel_advies['Uitverk. advies'].astype(str)
       # alleen uitverkoop-advies - ja
       alleen_uitverkopen = (optimaal_bestel_advies['Uitverk. advies'] == 'True')
       # filter dataframe zodat alleen de uitverkoop-advies artikelen naar boven komen.
       optimaal_bestel_advies_winkeldochters = optimaal_bestel_advies.loc[alleen_uitverkopen]

       # maak het OB dataframe kleiner zodat het beter leesbaar is
       optimaal_bestel_advies_winkeldochters_1 = optimaal_bestel_advies_winkeldochters[
              ['PRK Code', 'ZI', 'Artikelomschrijving', 'Inhoud', 'Eenheid', 'Uitverk. advies']]

       # merge deze nu met het analyse bestand
       wd_bestand = analyse_bestand_1.merge(
              optimaal_bestel_advies_winkeldochters_1[['ZI', 'Artikelomschrijving', 'Uitverk. advies']], how='inner',
              on='ZI')

       wd_bestand_1 = wd_bestand[['ZI', 'prkode', 'artikelnaam', 'inkhvh', 'eh', 'voorraadminimum',
                                  'voorraadmaximum', 'voorraadtotaal', 'locatie1', 'inkprijs', 'voorraadwaarde',
                                  'Uitverk. advies', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar',
                                  'musselpark']]

       # merge nu als laatste stap de CF verstrekkingen

       winkeldochters_compleet = wd_bestand_1.merge(
              verstrekkingen_cf_apotheek_analyse[['ndATKODE', 'eenheden verstrekt CF']], how='left', left_on='ZI',
              right_on='ndATKODE').drop(columns='ndATKODE')

       winkeldochters_compleet['eenheden verstrekt CF'] = (
              winkeldochters_compleet['eenheden verstrekt CF'].replace(np.nan, 0, regex=True)).astype(int)
       n_clicks = None

       return dcc.send_data_frame(winkeldochters_compleet.to_excel, "winkeldochters.xlsx"), n_clicks


# Callback voor de ZI zoeker van de apotheek die je geselecteerd hebt
@callback(
            Output('CF verstrekkingen', 'children'),
            Input('apotheek', 'value'),
            Input('ZI invoer', 'value')
)
def zoek_CF_verstrekkingen(apotheek, zi):
       # In de tweede stap maken we het mogelijk om te zoeken naar een ZI nummer om te kijken of er patienten zijn die de winkeldochters eigenlijk via CF ophalen
       # concept: via Ctrl+C en Ctrl+V moet je een ZI of PRK in een zoekbalk in kunnen vullen zodat je daarna kan zien welke patiënten deze producten ophalen.
       # We pakken een versimpelde vorm van de receptverwerkingsdataframe pakken en gaan daar een filter opgooien van ZI

       zoek_CF_verstrekkingen = recept_ag.copy()

       Apotheek_analyse_CF = apotheek  # Filter voor apotheek

       # definieer nu het filter: dit is de apotheek die je gaat analyseren
       filter_apotheek_analyse = (zoek_CF_verstrekkingen['apotheek'] == Apotheek_analyse_CF)

       # datum range vaststellen
       zoek_CF_verstrekkingen['ddDatumRecept'] = pd.to_datetime(zoek_CF_verstrekkingen['ddDatumRecept'])
       max_datum_zi_zoek_cf = zoek_CF_verstrekkingen['ddDatumRecept'].max()
       # datum -4 maanden
       min_datum_zi_zoek_cf = max_datum_zi_zoek_cf - pd.DateOffset(months=4)

       # maak een filter voor de datum range
       datum_range_filter_zi_zoek_cf = (zoek_CF_verstrekkingen['ddDatumRecept'] >= min_datum_zi_zoek_cf)

       # pas filters toe apotheek en datum
       zoek_CF_verstrekkingen_1 = zoek_CF_verstrekkingen.loc[filter_apotheek_analyse & datum_range_filter_zi_zoek_cf]

       zoek_CF_verstrekkingen_2 = zoek_CF_verstrekkingen_1[['ndPatientnr',
                                                            'ddDatumRecept', 'ndPRKODE', 'ndATKODE', 'sdEtiketNaam',
                                                            'ndAantal', 'Uitgifte', 'cf', 'apotheek']]

       # ==================================================================================================
       zoek_zi = zi  # Input in het dataframe
       # ==================================================================================================

       # filter voor zoeken
       filter_zi = (zoek_CF_verstrekkingen_2['ndATKODE'] == zoek_zi)

       # toon het dataframe na invoeren van de zoekterm

       zoek_CF_verstrekkingen_3 = zoek_CF_verstrekkingen_2.loc[filter_zi]

       CF_grid = dag.AgGrid(
                rowData=zoek_CF_verstrekkingen_3.to_dict('records'),
                columnDefs=[{'field': i } for i in zoek_CF_verstrekkingen_3.columns],
                dashGridOptions={'enableCellTextSelection':'True'}
         )
       return CF_grid


if __name__ == '__main__':
    app.run_server(debug=True)











