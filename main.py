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

# Inlezen Optimaal bestellen dataframes van de apotheken
OB_helpman = pd.read_excel('helpman_OB.xlsx')
OB_hanzeplein = pd.read_excel('hanzeplein_OB.xlsx')
OB_oosterpoort = pd.read_excel('oosterpoort_OB.xlsx')
OB_wiljes = pd.read_excel('wiljes_OB.xlsx')
OB_oosterhaar = pd.read_excel('oosterhaar_OB.xlsx')
OB_musselpark = pd.read_excel('musselpark_OB.xlsx')

# toevoegen van kolom 'apotheek' aan Optimaal bestellen advies
OB_helpman['apotheek'] = 'helpman'
OB_hanzeplein['apotheek'] = 'hanzeplein'
OB_oosterpoort['apotheek'] = 'oosterpoort'
OB_wiljes['apotheek'] = 'wiljes'
OB_oosterhaar['apotheek'] = 'oosterhaar'
OB_musselpark['apotheek'] = 'musselpark'

# samenvoegen van de Optimaal Bestellen dataframes tot één dataframe
optimaal_bestel_advies_ag = pd.concat([OB_helpman, OB_hanzeplein, OB_oosterpoort, OB_wiljes, OB_oosterhaar, OB_musselpark])



# Overzicht van de ingelezen dataframes
recept_ag               # Receptverwerking van alle apotheken binnen de AG
assortiment_ag          # Assortimenten van alle AG apotheken
optimaal_bestel_advies_ag  # Optimaal Besteladvies van apotheek die je wilt bekijken


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

# bereken de voorraadwaarde van iedere winkeldochter
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

# Zorg dat je eerst verder werkt met het juiste optimaal bestel advies door de apotheek te filteren die je geselecteerd hebt

OB_apotheek_selectie = (optimaal_bestel_advies_ag['apotheek'] == Apotheek_analyse)

optimaal_bestel_advies = optimaal_bestel_advies_ag.loc[OB_apotheek_selectie]


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

# =================================================================================================================================================================================================
# TESTEN VAN HET CONCEPT VAN OVERVOORRAAD
# ===================================================================================================================================================================================================




# berekend de overvoorraad uit je assortiment

Apotheek_analyse = 'helpman'

# filter voor assortiment
apotheek_assortiment_analyse = (assortiment_ag['apotheek']==Apotheek_analyse)

# filter het assortiment
assortiment_overvoorraad_analyse = assortiment_ag.loc[apotheek_assortiment_analyse]

# filter voor optimaal bestellen
apotheek_optimaal_bestel_advies_analyse = (optimaal_bestel_advies_ag['apotheek'] == Apotheek_analyse)

# filter het optimaal bestel advies
OB_analyse_overvoorraad = optimaal_bestel_advies_ag.loc[apotheek_optimaal_bestel_advies_analyse]

# merge het assortiment dataframe met het OB dataframe en zorg dat alleen de voorspellling kolom wordt toegevoegd aan het assortiment
assortiment_overvoorraad_analyse_1 = assortiment_overvoorraad_analyse.merge(OB_analyse_overvoorraad[['ZI', 'Voorspelling']], how='left', left_on='zinummer', right_on='ZI').drop(columns='ZI')

# Zet de voorspelling NaN waarden op 0
assortiment_overvoorraad_analyse_1['Voorspelling'] = assortiment_overvoorraad_analyse_1['Voorspelling'].replace(np.nan, 0, regex=True)

# Nu gaan we de verstrekkingen van de analyse apotheek toevoegen aan het dataframe van het assortiment. We nemen het gemiddeld aantal eenheden van de afgelopen 2 maanden om te kijken naar wat een overvoorraad in eenheden en verpakkingen is.

# kopieer oorspronkelijk recept dataframe
recept_overvoorraad_ag = recept_ag.copy()

# Maak van de datumrecept kolom een datetime object
recept_overvoorraad_ag['ddDatumRecept'] = pd.to_datetime(recept_overvoorraad_ag['ddDatumRecept'])

# definieer een filter
recept_ov_apotheek_filter = (recept_overvoorraad_ag['apotheek']==Apotheek_analyse)

# pas filter toe op recept dataframe
recept_ov_apotheek = recept_overvoorraad_ag.loc[recept_ov_apotheek_filter]

# excludeer Distributie, Zorg, dienst, LSP en CF-recepten
distributie_niet_ov = (recept_ov_apotheek['ReceptHerkomst']!='D')
zorg_niet_ov = (recept_ov_apotheek['ReceptHerkomst']!='Z')
dienst_niet_ov = (recept_ov_apotheek['ReceptHerkomst']!='DIENST')
lsp_niet_ov = (recept_ov_apotheek['sdMedewerkerCode']!='LSP')
cf_niet_ov = (recept_ov_apotheek['cf']!='J')

# pad de filters toe
recept_ov_apotheek_1 = recept_ov_apotheek.loc[distributie_niet_ov & zorg_niet_ov & dienst_niet_ov & lsp_niet_ov & cf_niet_ov]

# Nu hebben we alleen ladekast verstrekkingen te pakken. We gaan de verstrekkingen tellen van de afgelopen 2 maanden

# Bepaal de meetdatum
max_datum = recept_ov_apotheek_1['ddDatumRecept'].max()
datum_2_maanden_terug = max_datum - pd.DateOffset(months=2)
print(datum_2_maanden_terug)

# Filter het dataframe nu op alle verstrekkingen van maximaal 2 maanden oud
recept_ov_apotheek_2 = recept_ov_apotheek_1.loc[recept_ov_apotheek_1['ddDatumRecept']>=datum_2_maanden_terug]

# Ga nu het aantal eenheden dat verstrekt is berekenen en bereken hier ook een maandgemiddelde van

# bereken het aantal eenheden dat verstrekt is per artikel
recept_ov_apotheek_3 = recept_ov_apotheek_2.groupby(by=['ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame('eenheden verstrekt').reset_index()

# bereken het maandgemiddelde en maak hier een aparte kolom van
recept_ov_apotheek_3['gem eh verstrekt per maand CGM'] = (recept_ov_apotheek_3['eenheden verstrekt']/2).astype(int)

# bereken het aantal verpakkingen dat teveel op voorraad is

# Voeg de inkoophoeveelheid toe aan het bestaande dataframe
recept_ov_apotheek_4 = recept_ov_apotheek_3.merge(assortiment_overvoorraad_analyse_1[['zinummer', 'etiketnaam','inkhvh']], how='left', left_on=['ndATKODE', 'sdEtiketNaam'], right_on=['zinummer', 'etiketnaam']).drop(columns=['etiketnaam', 'zinummer'])

# bereken hoeveel verpakkingen er per maand gemiddeld verstrekt worden
recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = (recept_ov_apotheek_4['gem eh verstrekt per maand CGM']/recept_ov_apotheek_4['inkhvh'])

# zet alle NaN waarden op 0
recept_ov_apotheek_4['gem eh verstrekt per maand CGM'] = recept_ov_apotheek_4['gem eh verstrekt per maand CGM'].replace(np.nan, 0, regex=True)
recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = recept_ov_apotheek_4['gem verp verstrekt per maand CGM'].replace(np.nan, 0, regex=True)
recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = recept_ov_apotheek_4['gem verp verstrekt per maand CGM'].round(1)

# nu moeten we de dataframes gaan samenvoegen zodat we de overvoorraad kunnen berekenen.
assortiment_overvoorraad_analyse_2 = assortiment_overvoorraad_analyse_1.merge(recept_ov_apotheek_4[['ndATKODE', 'sdEtiketNaam','gem verp verstrekt per maand CGM']], how='left', left_on=['zinummer', 'etiketnaam'], right_on=['ndATKODE', 'sdEtiketNaam']).drop(columns='ndATKODE')

# maak de boel netjes de verstrekkingen, en Voorspelling met NaN moeten worden vervangen door 0
assortiment_overvoorraad_analyse_2['Voorspelling'] = assortiment_overvoorraad_analyse_2['Voorspelling'].replace(np.nan, 0, regex=True)
assortiment_overvoorraad_analyse_2['gem verp verstrekt per maand CGM'] = assortiment_overvoorraad_analyse_2['gem verp verstrekt per maand CGM'].replace(np.nan, 0, regex=True)

# Bereken de voorraad in verpakkingen
assortiment_overvoorraad_analyse_2['voorraadtotaal verp'] = (assortiment_overvoorraad_analyse_2['voorraadtotaal']/assortiment_overvoorraad_analyse_2['inkhvh']).round(1)

# Overvoorraad berekenen in verpakkingen en AIP
assortiment_overvoorraad_analyse_2['overvoorraad verp'] = assortiment_overvoorraad_analyse_2['voorraadtotaal verp'] - assortiment_overvoorraad_analyse_2['gem verp verstrekt per maand CGM']
assortiment_overvoorraad_analyse_2['overvoorraad aip'] = assortiment_overvoorraad_analyse_2['overvoorraad verp'] * assortiment_overvoorraad_analyse_2['inkprijs']

# Nu kun je het dataframe analyseren op een postitieve waarde van de overvoorraad
overvoorraad_filter_verpakkingen = (assortiment_overvoorraad_analyse_2['overvoorraad verp']>1)

# pas het filter toe
assortiment_overvoorraad_analyse_3 = assortiment_overvoorraad_analyse_2.loc[overvoorraad_filter_verpakkingen]

# maak de boel wat schoner door wat kolommen te droppen
assortiment_overvoorraad_analyse_4 = assortiment_overvoorraad_analyse_3[['produktgroep', 'zinummer', 'artikelnaam',
       'inkhvh', 'eh', 'voorraadminimum', 'voorraadmaximum', 'locatie1',
       'voorraadtotaal', 'voorraadtotaal verp', 'inkprijs', 'apotheek',
       'Voorspelling', 'gem verp verstrekt per maand CGM'
       , 'overvoorraad verp', 'overvoorraad aip']]

# sorteer het dataframe van hoog naar laag op basis van AIP overvoorraad
assortiment_overvoorraad_analyse_5 = assortiment_overvoorraad_analyse_4.sort_values(by=['overvoorraad aip'], ascending=False)

# nu moeten we nog weten waar we alles naartoe moeten verschepen.
# de eenheden die verstrekt kunnen worden naar andere apotheken (op basis van de laatste 2 maanden moeten worden weergegeven)

# ============================== VERSTREKKINGEN PER APOTHEEK VAN ALLE APOTHEKEN METEN ==================

verstrekkingen_ag = recept_ag.copy()

# maak van de datum een datetime kolom
verstrekkingen_ag['ddDatumRecept'] = pd.to_datetime(verstrekkingen_ag['ddDatumRecept'])

# filters voor exclusie (zorg, dienst, lsp, cf, distributie)
distributie_niet = (verstrekkingen_ag['ReceptHerkomst']!='D')
zorg_niet = (verstrekkingen_ag['ReceptHerkomst']!='Z')
dienst_niet = (verstrekkingen_ag['ReceptHerkomst']!='DIENST')
lsp_niet = (verstrekkingen_ag['sdMedewerkerCode']!='LSP')
cf_niet = (verstrekkingen_ag['cf']!='J')
cf_wel = (verstrekkingen_ag['cf']=='J')

# pas de filters toe op het dataframe

verstrekkingen_ag_1 = verstrekkingen_ag.loc[distributie_niet & zorg_niet & dienst_niet & lsp_niet & cf_niet]

# Bepaal de meetdatum voor de laatste 2 maanden
max_datum_verstrekkingen = verstrekkingen_ag_1['ddDatumRecept'].max()
datum_2_maanden_terug_verstrekkingen = max_datum_verstrekkingen - pd.DateOffset(months=2)

# pas het dataframe aan, aan het tijdframe dat je wilt bekijken
verstrekkingen_ag_2 = verstrekkingen_ag_1.loc[verstrekkingen_ag_1['ddDatumRecept']>=datum_2_maanden_terug_verstrekkingen]

# Tel nu de eenheden die verstrekt zijn in de ladekast van iedere apotheek apart en bereken hier ook een maandgemiddelde van

verstrekkingen_ag_3 = verstrekkingen_ag_2.groupby(by=['apotheek', 'ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame('eenheden verstrekt 2 mnd (CGM)').reset_index()


#maak nu een pivot table hiervan zodat je alle apotheken op een rijtje naast elkaar hebt.

verstrekkingen_ag_4 = verstrekkingen_ag_3.pivot_table(index=['ndATKODE', 'sdEtiketNaam'],
                                                      columns='apotheek',
                                                      values='eenheden verstrekt 2 mnd (CGM)').reset_index()

# nu moeten we voor alle kolommen genaamd hanzeplein, helpman, musselpark, oosterhaar, oosterpoort en wiljes een functie schrijven die alle NaN waarden omzet naar 0

for col in verstrekkingen_ag_4.columns[2:]:
    verstrekkingen_ag_4[col] = verstrekkingen_ag_4[col].replace(np.nan, 0, regex=True)


# nu moeten we de dataframes gaan mergen zodat we een totoal overzicht kunnen maken voor de apotheek van de overvoorraad

assortiment_overvoorraad_analyse_6 = assortiment_overvoorraad_analyse_5.merge(verstrekkingen_ag_4[['ndATKODE', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar', 'musselpark']], how='left', left_on='zinummer', right_on='ndATKODE').drop(columns='ndATKODE')


# nu gaan we hier de CF verstrekkingen nog aan toevoegen

# nu alleen de CF verstrekkingen pakken
verstrekkingen_ag_5 = verstrekkingen_ag.loc[distributie_niet & zorg_niet & dienst_niet & lsp_niet & cf_wel]

verstrekkingen_ag_6 = verstrekkingen_ag_5.loc[(verstrekkingen_ag_5['ddDatumRecept']>=datum_2_maanden_terug_verstrekkingen)]

verstrekkingen_ag_7 = verstrekkingen_ag_6.loc[(verstrekkingen_ag_6['apotheek']==Apotheek_analyse)]

verstrekkingen_ag_8 = verstrekkingen_ag_7.groupby(by=['ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame('eenheden verstrekt CF CGM apotheek analyse').reset_index()

cf_verstrekkingen_analyse_apotheek = verstrekkingen_ag_8








# nu mergen we alles tot een dataframe samenkomend dataframe

assortiment_overvoorraad_analyse_7 = assortiment_overvoorraad_analyse_6.merge(cf_verstrekkingen_analyse_apotheek[['ndATKODE', 'eenheden verstrekt CF CGM apotheek analyse']], how='left', left_on='zinummer', right_on='ndATKODE').drop(columns='ndATKODE')

#vanaf hier maken we er een dash ag grid van

#assortiment_overvoorraad_analyse_7.to_excel('overvoorraad_analyse.xlsx')

# ============================= OVERZICHT DATAFRAMES ============================
assortiment_overvoorraad_analyse_5                      # Analyse van de overvoorraad in het assortiment van de geselecteerde apotheek
verstrekkingen_ag_4                                     # alle verstrekkingen uit de ladekast van artikelen uit alle apotheken (afgelopen 2 maanden)
assortiment_overvoorraad_analyse_6                      # alle overvoorraad samen met alle ladekast verstrekkingen van alle apotheken
cf_verstrekkingen_analyse_apotheek                      # alle CF verstrekkingen van de apotheek die bekeken wordt in de analyse
assortiment_overvoorraad_analyse_7                      # het DEFINTIEVE DATAFRAME MET over voorraad: ladekast verstrekkingen en CF verstrekkingen
# ============================= OVERZICHT DATAFRAMES ============================



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

       dbc.Row([html.H4('Overvoorraad Analyse')]),
       dbc.Row([html.Div(id='overvoorraad')]),                  # Overvoorraad dahs ag grid
       dbc.Row([
           dbc.Col([],width=10),
           dbc.Col([
                dbc.Button(id='download_overvoorraad', children="Download xlsx", color="success", className="me-1"),    #knopje voor downloaden
                dcc.Download(id='download_ov')                                                                # download optie
           ], width=2)
       ]),

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

       # bereken de voorraadwaarde van iedere winkeldochter
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

       # Zorg dat je eerst verder werkt met het juiste optimaal bestel advies door de apotheek te filteren die je geselecteerd hebt

       OB_apotheek_selectie = (optimaal_bestel_advies_ag['apotheek'] == Apotheek_analyse)

       optimaal_bestel_advies = optimaal_bestel_advies_ag.loc[OB_apotheek_selectie]

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

       winkeldochters_grid = dag.AgGrid(
              rowData=winkeldochters_compleet.to_dict('records'),
              columnDefs=[{'field': i } for i in winkeldochters_compleet.columns],
              dashGridOptions={'enableCellTextSelection':'True'}
       )
       return winkeldochters_grid

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

       # bereken de voorraadwaarde van iedere winkeldochter
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

       # Zorg dat je eerst verder werkt met het juiste optimaal bestel advies door de apotheek te filteren die je geselecteerd hebt

       OB_apotheek_selectie = (optimaal_bestel_advies_ag['apotheek'] == Apotheek_analyse)

       optimaal_bestel_advies = optimaal_bestel_advies_ag.loc[OB_apotheek_selectie]

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

# Callback voor het dash ag grid van de overvoorraad
@callback(
            Output('overvoorraad', 'children'),
            Input('apotheek', 'value')
)
def overvoorraad(apotheek):
    # =================================================================================================================================================================================================
    # TESTEN VAN HET CONCEPT VAN OVERVOORRAAD
    # ===================================================================================================================================================================================================

    # berekend de overvoorraad uit je assortiment

    Apotheek_analyse = apotheek

    # filter voor assortiment
    apotheek_assortiment_analyse = (assortiment_ag['apotheek'] == Apotheek_analyse)

    # filter het assortiment
    assortiment_overvoorraad_analyse = assortiment_ag.loc[apotheek_assortiment_analyse]

    # filter voor optimaal bestellen
    apotheek_optimaal_bestel_advies_analyse = (optimaal_bestel_advies_ag['apotheek'] == Apotheek_analyse)

    # filter het optimaal bestel advies
    OB_analyse_overvoorraad = optimaal_bestel_advies_ag.loc[apotheek_optimaal_bestel_advies_analyse]

    # merge het assortiment dataframe met het OB dataframe en zorg dat alleen de voorspellling kolom wordt toegevoegd aan het assortiment
    assortiment_overvoorraad_analyse_1 = assortiment_overvoorraad_analyse.merge(
        OB_analyse_overvoorraad[['ZI', 'Voorspelling']], how='left', left_on='zinummer', right_on='ZI').drop(
        columns='ZI')

    # Zet de voorspelling NaN waarden op 0
    assortiment_overvoorraad_analyse_1['Voorspelling'] = assortiment_overvoorraad_analyse_1['Voorspelling'].replace(
        np.nan, 0, regex=True)

    # Nu gaan we de verstrekkingen van de analyse apotheek toevoegen aan het dataframe van het assortiment. We nemen het gemiddeld aantal eenheden van de afgelopen 2 maanden om te kijken naar wat een overvoorraad in eenheden en verpakkingen is.

    # kopieer oorspronkelijk recept dataframe
    recept_overvoorraad_ag = recept_ag.copy()

    # Maak van de datumrecept kolom een datetime object
    recept_overvoorraad_ag['ddDatumRecept'] = pd.to_datetime(recept_overvoorraad_ag['ddDatumRecept'])

    # definieer een filter
    recept_ov_apotheek_filter = (recept_overvoorraad_ag['apotheek'] == Apotheek_analyse)

    # pas filter toe op recept dataframe
    recept_ov_apotheek = recept_overvoorraad_ag.loc[recept_ov_apotheek_filter]

    # excludeer Distributie, Zorg, dienst, LSP en CF-recepten
    distributie_niet_ov = (recept_ov_apotheek['ReceptHerkomst'] != 'D')
    zorg_niet_ov = (recept_ov_apotheek['ReceptHerkomst'] != 'Z')
    dienst_niet_ov = (recept_ov_apotheek['ReceptHerkomst'] != 'DIENST')
    lsp_niet_ov = (recept_ov_apotheek['sdMedewerkerCode'] != 'LSP')
    cf_niet_ov = (recept_ov_apotheek['cf'] != 'J')

    # pad de filters toe
    recept_ov_apotheek_1 = recept_ov_apotheek.loc[
        distributie_niet_ov & zorg_niet_ov & dienst_niet_ov & lsp_niet_ov & cf_niet_ov]

    # Nu hebben we alleen ladekast verstrekkingen te pakken. We gaan de verstrekkingen tellen van de afgelopen 2 maanden

    # Bepaal de meetdatum
    max_datum = recept_ov_apotheek_1['ddDatumRecept'].max()
    datum_2_maanden_terug = max_datum - pd.DateOffset(months=2)
    print(datum_2_maanden_terug)

    # Filter het dataframe nu op alle verstrekkingen van maximaal 2 maanden oud
    recept_ov_apotheek_2 = recept_ov_apotheek_1.loc[recept_ov_apotheek_1['ddDatumRecept'] >= datum_2_maanden_terug]

    # Ga nu het aantal eenheden dat verstrekt is berekenen en bereken hier ook een maandgemiddelde van

    # bereken het aantal eenheden dat verstrekt is per artikel
    recept_ov_apotheek_3 = recept_ov_apotheek_2.groupby(by=['ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame(
        'eenheden verstrekt').reset_index()

    # bereken het maandgemiddelde en maak hier een aparte kolom van
    recept_ov_apotheek_3['gem eh verstrekt per maand CGM'] = (recept_ov_apotheek_3['eenheden verstrekt'] / 2).astype(
        int)

    # bereken het aantal verpakkingen dat teveel op voorraad is

    # Voeg de inkoophoeveelheid toe aan het bestaande dataframe
    recept_ov_apotheek_4 = recept_ov_apotheek_3.merge(
        assortiment_overvoorraad_analyse_1[['zinummer', 'etiketnaam', 'inkhvh']], how='left',
        left_on=['ndATKODE', 'sdEtiketNaam'], right_on=['zinummer', 'etiketnaam']).drop(
        columns=['etiketnaam', 'zinummer'])

    # bereken hoeveel verpakkingen er per maand gemiddeld verstrekt worden
    recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = (
                recept_ov_apotheek_4['gem eh verstrekt per maand CGM'] / recept_ov_apotheek_4['inkhvh'])

    # zet alle NaN waarden op 0
    recept_ov_apotheek_4['gem eh verstrekt per maand CGM'] = recept_ov_apotheek_4[
        'gem eh verstrekt per maand CGM'].replace(np.nan, 0, regex=True)
    recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = recept_ov_apotheek_4[
        'gem verp verstrekt per maand CGM'].replace(np.nan, 0, regex=True)
    recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = recept_ov_apotheek_4[
        'gem verp verstrekt per maand CGM'].round(1)

    # nu moeten we de dataframes gaan samenvoegen zodat we de overvoorraad kunnen berekenen.
    assortiment_overvoorraad_analyse_2 = assortiment_overvoorraad_analyse_1.merge(
        recept_ov_apotheek_4[['ndATKODE', 'sdEtiketNaam', 'gem verp verstrekt per maand CGM']], how='left',
        left_on=['zinummer', 'etiketnaam'], right_on=['ndATKODE', 'sdEtiketNaam']).drop(columns='ndATKODE')

    # maak de boel netjes de verstrekkingen, en Voorspelling met NaN moeten worden vervangen door 0
    assortiment_overvoorraad_analyse_2['Voorspelling'] = assortiment_overvoorraad_analyse_2['Voorspelling'].replace(
        np.nan, 0, regex=True)
    assortiment_overvoorraad_analyse_2['gem verp verstrekt per maand CGM'] = assortiment_overvoorraad_analyse_2[
        'gem verp verstrekt per maand CGM'].replace(np.nan, 0, regex=True)

    # Bereken de voorraad in verpakkingen
    assortiment_overvoorraad_analyse_2['voorraadtotaal verp'] = (
                assortiment_overvoorraad_analyse_2['voorraadtotaal'] / assortiment_overvoorraad_analyse_2[
            'inkhvh']).round(1)

    # Overvoorraad berekenen in verpakkingen en AIP
    assortiment_overvoorraad_analyse_2['overvoorraad verp'] = assortiment_overvoorraad_analyse_2[
                                                                  'voorraadtotaal verp'] - \
                                                              assortiment_overvoorraad_analyse_2[
                                                                  'gem verp verstrekt per maand CGM']
    assortiment_overvoorraad_analyse_2['overvoorraad aip'] = assortiment_overvoorraad_analyse_2['overvoorraad verp'] * \
                                                             assortiment_overvoorraad_analyse_2['inkprijs']

    # Nu kun je het dataframe analyseren op een postitieve waarde van de overvoorraad
    overvoorraad_filter_verpakkingen = (assortiment_overvoorraad_analyse_2['overvoorraad verp'] > 1)

    # pas het filter toe
    assortiment_overvoorraad_analyse_3 = assortiment_overvoorraad_analyse_2.loc[overvoorraad_filter_verpakkingen]

    # maak de boel wat schoner door wat kolommen te droppen
    assortiment_overvoorraad_analyse_4 = assortiment_overvoorraad_analyse_3[['produktgroep', 'zinummer', 'artikelnaam',
                                                                             'inkhvh', 'eh', 'voorraadminimum',
                                                                             'voorraadmaximum', 'locatie1',
                                                                             'voorraadtotaal', 'voorraadtotaal verp',
                                                                             'inkprijs', 'apotheek',
                                                                             'Voorspelling',
                                                                             'gem verp verstrekt per maand CGM'
        , 'overvoorraad verp', 'overvoorraad aip']]

    # sorteer het dataframe van hoog naar laag op basis van AIP overvoorraad
    assortiment_overvoorraad_analyse_5 = assortiment_overvoorraad_analyse_4.sort_values(by=['overvoorraad aip'],
                                                                                        ascending=False)

    # nu moeten we nog weten waar we alles naartoe moeten verschepen.
    # de eenheden die verstrekt kunnen worden naar andere apotheken (op basis van de laatste 2 maanden moeten worden weergegeven)

    # ============================== VERSTREKKINGEN PER APOTHEEK VAN ALLE APOTHEKEN METEN ==================

    verstrekkingen_ag = recept_ag.copy()

    # maak van de datum een datetime kolom
    verstrekkingen_ag['ddDatumRecept'] = pd.to_datetime(verstrekkingen_ag['ddDatumRecept'])

    # filters voor exclusie (zorg, dienst, lsp, cf, distributie)
    distributie_niet = (verstrekkingen_ag['ReceptHerkomst'] != 'D')
    zorg_niet = (verstrekkingen_ag['ReceptHerkomst'] != 'Z')
    dienst_niet = (verstrekkingen_ag['ReceptHerkomst'] != 'DIENST')
    lsp_niet = (verstrekkingen_ag['sdMedewerkerCode'] != 'LSP')
    cf_niet = (verstrekkingen_ag['cf'] != 'J')
    cf_wel = (verstrekkingen_ag['cf'] == 'J')

    # pas de filters toe op het dataframe

    verstrekkingen_ag_1 = verstrekkingen_ag.loc[distributie_niet & zorg_niet & dienst_niet & lsp_niet & cf_niet]

    # Bepaal de meetdatum voor de laatste 2 maanden
    max_datum_verstrekkingen = verstrekkingen_ag_1['ddDatumRecept'].max()
    datum_2_maanden_terug_verstrekkingen = max_datum_verstrekkingen - pd.DateOffset(months=2)

    # pas het dataframe aan, aan het tijdframe dat je wilt bekijken
    verstrekkingen_ag_2 = verstrekkingen_ag_1.loc[
        verstrekkingen_ag_1['ddDatumRecept'] >= datum_2_maanden_terug_verstrekkingen]

    # Tel nu de eenheden die verstrekt zijn in de ladekast van iedere apotheek apart en bereken hier ook een maandgemiddelde van

    verstrekkingen_ag_3 = verstrekkingen_ag_2.groupby(by=['apotheek', 'ndATKODE', 'sdEtiketNaam'])[
        'ndAantal'].sum().to_frame('eenheden verstrekt 2 mnd (CGM)').reset_index()

    # maak nu een pivot table hiervan zodat je alle apotheken op een rijtje naast elkaar hebt.

    verstrekkingen_ag_4 = verstrekkingen_ag_3.pivot_table(index=['ndATKODE', 'sdEtiketNaam'],
                                                          columns='apotheek',
                                                          values='eenheden verstrekt 2 mnd (CGM)').reset_index()

    # nu moeten we voor alle kolommen genaamd hanzeplein, helpman, musselpark, oosterhaar, oosterpoort en wiljes een functie schrijven die alle NaN waarden omzet naar 0

    for col in verstrekkingen_ag_4.columns[2:]:
        verstrekkingen_ag_4[col] = verstrekkingen_ag_4[col].replace(np.nan, 0, regex=True)

    # nu moeten we de dataframes gaan mergen zodat we een totoal overzicht kunnen maken voor de apotheek van de overvoorraad

    assortiment_overvoorraad_analyse_6 = assortiment_overvoorraad_analyse_5.merge(
        verstrekkingen_ag_4[['ndATKODE', 'hanzeplein', 'oosterpoort', 'helpman', 'wiljes', 'oosterhaar', 'musselpark']],
        how='left', left_on='zinummer', right_on='ndATKODE').drop(columns='ndATKODE')

    # nu gaan we hier de CF verstrekkingen nog aan toevoegen

    # nu alleen de CF verstrekkingen pakken
    verstrekkingen_ag_5 = verstrekkingen_ag.loc[distributie_niet & zorg_niet & dienst_niet & lsp_niet & cf_wel]

    verstrekkingen_ag_6 = verstrekkingen_ag_5.loc[
        (verstrekkingen_ag_5['ddDatumRecept'] >= datum_2_maanden_terug_verstrekkingen)]

    verstrekkingen_ag_7 = verstrekkingen_ag_6.loc[(verstrekkingen_ag_6['apotheek'] == Apotheek_analyse)]

    verstrekkingen_ag_8 = verstrekkingen_ag_7.groupby(by=['ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame(
        'eenheden verstrekt CF CGM apotheek analyse').reset_index()

    cf_verstrekkingen_analyse_apotheek = verstrekkingen_ag_8

    # nu mergen we alles tot een dataframe samenkomend dataframe

    assortiment_overvoorraad_analyse_7 = assortiment_overvoorraad_analyse_6.merge(
        cf_verstrekkingen_analyse_apotheek[['ndATKODE', 'eenheden verstrekt CF CGM apotheek analyse']], how='left',
        left_on='zinummer', right_on='ndATKODE').drop(columns='ndATKODE')

    # vanaf hier maken we er een dash ag grid van

    # assortiment_overvoorraad_analyse_7.to_excel('overvoorraad_analyse.xlsx')

    # ============================= OVERZICHT DATAFRAMES ============================
    assortiment_overvoorraad_analyse_5  # Analyse van de overvoorraad in het assortiment van de geselecteerde apotheek
    verstrekkingen_ag_4  # alle verstrekkingen uit de ladekast van artikelen uit alle apotheken (afgelopen 2 maanden)
    assortiment_overvoorraad_analyse_6  # alle overvoorraad samen met alle ladekast verstrekkingen van alle apotheken
    cf_verstrekkingen_analyse_apotheek  # alle CF verstrekkingen van de apotheek die bekeken wordt in de analyse
    assortiment_overvoorraad_analyse_7  # het DEFINTIEVE DATAFRAME MET over voorraad: ladekast verstrekkingen en CF verstrekkingen
    # ============================= OVERZICHT DATAFRAMES ============================


    # maak een dash ag grid van het dataframe
    overvoorraad_grid = dag.AgGrid(
        rowData=assortiment_overvoorraad_analyse_7.to_dict('records'),
        columnDefs=[{'field': i} for i in assortiment_overvoorraad_analyse_7.columns],
        dashGridOptions={'enableCellTextSelection': 'True'}
    )
    return overvoorraad_grid

# Callback voor de overvoorraad in excel te downloaden
@callback(
    Output('download_ov', 'data'),
    Output('download_overvoorraad', 'n_clicks'),
    Input('download_overvoorraad', 'n_clicks'),
    Input('apotheek', 'value')
)
def download_overvoorraad(n_clicks, apotheek):

    if n_clicks is None:
        raise PreventUpdate

    else:
        # =================================================================================================================================================================================================
        # TESTEN VAN HET CONCEPT VAN OVERVOORRAAD
        # ===================================================================================================================================================================================================

        # berekend de overvoorraad uit je assortiment

        Apotheek_analyse = apotheek

        # filter voor assortiment
        apotheek_assortiment_analyse = (assortiment_ag['apotheek'] == Apotheek_analyse)

        # filter het assortiment
        assortiment_overvoorraad_analyse = assortiment_ag.loc[apotheek_assortiment_analyse]

        # filter voor optimaal bestellen
        apotheek_optimaal_bestel_advies_analyse = (optimaal_bestel_advies_ag['apotheek'] == Apotheek_analyse)

        # filter het optimaal bestel advies
        OB_analyse_overvoorraad = optimaal_bestel_advies_ag.loc[apotheek_optimaal_bestel_advies_analyse]

        # merge het assortiment dataframe met het OB dataframe en zorg dat alleen de voorspellling kolom wordt toegevoegd aan het assortiment
        assortiment_overvoorraad_analyse_1 = assortiment_overvoorraad_analyse.merge(
            OB_analyse_overvoorraad[['ZI', 'Voorspelling']], how='left', left_on='zinummer', right_on='ZI').drop(
            columns='ZI')

        # Zet de voorspelling NaN waarden op 0
        assortiment_overvoorraad_analyse_1['Voorspelling'] = assortiment_overvoorraad_analyse_1['Voorspelling'].replace(
            np.nan, 0, regex=True)

        # Nu gaan we de verstrekkingen van de analyse apotheek toevoegen aan het dataframe van het assortiment. We nemen het gemiddeld aantal eenheden van de afgelopen 2 maanden om te kijken naar wat een overvoorraad in eenheden en verpakkingen is.

        # kopieer oorspronkelijk recept dataframe
        recept_overvoorraad_ag = recept_ag.copy()

        # Maak van de datumrecept kolom een datetime object
        recept_overvoorraad_ag['ddDatumRecept'] = pd.to_datetime(recept_overvoorraad_ag['ddDatumRecept'])

        # definieer een filter
        recept_ov_apotheek_filter = (recept_overvoorraad_ag['apotheek'] == Apotheek_analyse)

        # pas filter toe op recept dataframe
        recept_ov_apotheek = recept_overvoorraad_ag.loc[recept_ov_apotheek_filter]

        # excludeer Distributie, Zorg, dienst, LSP en CF-recepten
        distributie_niet_ov = (recept_ov_apotheek['ReceptHerkomst'] != 'D')
        zorg_niet_ov = (recept_ov_apotheek['ReceptHerkomst'] != 'Z')
        dienst_niet_ov = (recept_ov_apotheek['ReceptHerkomst'] != 'DIENST')
        lsp_niet_ov = (recept_ov_apotheek['sdMedewerkerCode'] != 'LSP')
        cf_niet_ov = (recept_ov_apotheek['cf'] != 'J')

        # pad de filters toe
        recept_ov_apotheek_1 = recept_ov_apotheek.loc[
            distributie_niet_ov & zorg_niet_ov & dienst_niet_ov & lsp_niet_ov & cf_niet_ov]

        # Nu hebben we alleen ladekast verstrekkingen te pakken. We gaan de verstrekkingen tellen van de afgelopen 2 maanden

        # Bepaal de meetdatum
        max_datum = recept_ov_apotheek_1['ddDatumRecept'].max()
        datum_2_maanden_terug = max_datum - pd.DateOffset(months=2)
        print(datum_2_maanden_terug)

        # Filter het dataframe nu op alle verstrekkingen van maximaal 2 maanden oud
        recept_ov_apotheek_2 = recept_ov_apotheek_1.loc[recept_ov_apotheek_1['ddDatumRecept'] >= datum_2_maanden_terug]

        # Ga nu het aantal eenheden dat verstrekt is berekenen en bereken hier ook een maandgemiddelde van

        # bereken het aantal eenheden dat verstrekt is per artikel
        recept_ov_apotheek_3 = recept_ov_apotheek_2.groupby(by=['ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame(
            'eenheden verstrekt').reset_index()

        # bereken het maandgemiddelde en maak hier een aparte kolom van
        recept_ov_apotheek_3['gem eh verstrekt per maand CGM'] = (
                    recept_ov_apotheek_3['eenheden verstrekt'] / 2).astype(int)

        # bereken het aantal verpakkingen dat teveel op voorraad is

        # Voeg de inkoophoeveelheid toe aan het bestaande dataframe
        recept_ov_apotheek_4 = recept_ov_apotheek_3.merge(
            assortiment_overvoorraad_analyse_1[['zinummer', 'etiketnaam', 'inkhvh']], how='left',
            left_on=['ndATKODE', 'sdEtiketNaam'], right_on=['zinummer', 'etiketnaam']).drop(
            columns=['etiketnaam', 'zinummer'])

        # bereken hoeveel verpakkingen er per maand gemiddeld verstrekt worden
        recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = (
                    recept_ov_apotheek_4['gem eh verstrekt per maand CGM'] / recept_ov_apotheek_4['inkhvh'])

        # zet alle NaN waarden op 0
        recept_ov_apotheek_4['gem eh verstrekt per maand CGM'] = recept_ov_apotheek_4[
            'gem eh verstrekt per maand CGM'].replace(np.nan, 0, regex=True)
        recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = recept_ov_apotheek_4[
            'gem verp verstrekt per maand CGM'].replace(np.nan, 0, regex=True)
        recept_ov_apotheek_4['gem verp verstrekt per maand CGM'] = recept_ov_apotheek_4[
            'gem verp verstrekt per maand CGM'].round(1)

        # nu moeten we de dataframes gaan samenvoegen zodat we de overvoorraad kunnen berekenen.
        assortiment_overvoorraad_analyse_2 = assortiment_overvoorraad_analyse_1.merge(
            recept_ov_apotheek_4[['ndATKODE', 'sdEtiketNaam', 'gem verp verstrekt per maand CGM']], how='left',
            left_on=['zinummer', 'etiketnaam'], right_on=['ndATKODE', 'sdEtiketNaam']).drop(columns='ndATKODE')

        # maak de boel netjes de verstrekkingen, en Voorspelling met NaN moeten worden vervangen door 0
        assortiment_overvoorraad_analyse_2['Voorspelling'] = assortiment_overvoorraad_analyse_2['Voorspelling'].replace(
            np.nan, 0, regex=True)
        assortiment_overvoorraad_analyse_2['gem verp verstrekt per maand CGM'] = assortiment_overvoorraad_analyse_2[
            'gem verp verstrekt per maand CGM'].replace(np.nan, 0, regex=True)

        # Bereken de voorraad in verpakkingen
        assortiment_overvoorraad_analyse_2['voorraadtotaal verp'] = (
                    assortiment_overvoorraad_analyse_2['voorraadtotaal'] / assortiment_overvoorraad_analyse_2[
                'inkhvh']).round(1)

        # Overvoorraad berekenen in verpakkingen en AIP
        assortiment_overvoorraad_analyse_2['overvoorraad verp'] = assortiment_overvoorraad_analyse_2[
                                                                      'voorraadtotaal verp'] - \
                                                                  assortiment_overvoorraad_analyse_2[
                                                                      'gem verp verstrekt per maand CGM']
        assortiment_overvoorraad_analyse_2['overvoorraad aip'] = assortiment_overvoorraad_analyse_2[
                                                                     'overvoorraad verp'] * \
                                                                 assortiment_overvoorraad_analyse_2['inkprijs']

        # Nu kun je het dataframe analyseren op een postitieve waarde van de overvoorraad
        overvoorraad_filter_verpakkingen = (assortiment_overvoorraad_analyse_2['overvoorraad verp'] > 1)

        # pas het filter toe
        assortiment_overvoorraad_analyse_3 = assortiment_overvoorraad_analyse_2.loc[overvoorraad_filter_verpakkingen]

        # maak de boel wat schoner door wat kolommen te droppen
        assortiment_overvoorraad_analyse_4 = assortiment_overvoorraad_analyse_3[
            ['produktgroep', 'zinummer', 'artikelnaam',
             'inkhvh', 'eh', 'voorraadminimum', 'voorraadmaximum', 'locatie1',
             'voorraadtotaal', 'voorraadtotaal verp', 'inkprijs', 'apotheek',
             'Voorspelling', 'gem verp verstrekt per maand CGM'
                , 'overvoorraad verp', 'overvoorraad aip']]

        # sorteer het dataframe van hoog naar laag op basis van AIP overvoorraad
        assortiment_overvoorraad_analyse_5 = assortiment_overvoorraad_analyse_4.sort_values(by=['overvoorraad aip'],
                                                                                            ascending=False)

        # nu moeten we nog weten waar we alles naartoe moeten verschepen.
        # de eenheden die verstrekt kunnen worden naar andere apotheken (op basis van de laatste 2 maanden moeten worden weergegeven)

        # ============================== VERSTREKKINGEN PER APOTHEEK VAN ALLE APOTHEKEN METEN ==================

        verstrekkingen_ag = recept_ag.copy()

        # maak van de datum een datetime kolom
        verstrekkingen_ag['ddDatumRecept'] = pd.to_datetime(verstrekkingen_ag['ddDatumRecept'])

        # filters voor exclusie (zorg, dienst, lsp, cf, distributie)
        distributie_niet = (verstrekkingen_ag['ReceptHerkomst'] != 'D')
        zorg_niet = (verstrekkingen_ag['ReceptHerkomst'] != 'Z')
        dienst_niet = (verstrekkingen_ag['ReceptHerkomst'] != 'DIENST')
        lsp_niet = (verstrekkingen_ag['sdMedewerkerCode'] != 'LSP')
        cf_niet = (verstrekkingen_ag['cf'] != 'J')
        cf_wel = (verstrekkingen_ag['cf'] == 'J')

        # pas de filters toe op het dataframe

        verstrekkingen_ag_1 = verstrekkingen_ag.loc[distributie_niet & zorg_niet & dienst_niet & lsp_niet & cf_niet]

        # Bepaal de meetdatum voor de laatste 2 maanden
        max_datum_verstrekkingen = verstrekkingen_ag_1['ddDatumRecept'].max()
        datum_2_maanden_terug_verstrekkingen = max_datum_verstrekkingen - pd.DateOffset(months=2)

        # pas het dataframe aan, aan het tijdframe dat je wilt bekijken
        verstrekkingen_ag_2 = verstrekkingen_ag_1.loc[
            verstrekkingen_ag_1['ddDatumRecept'] >= datum_2_maanden_terug_verstrekkingen]

        # Tel nu de eenheden die verstrekt zijn in de ladekast van iedere apotheek apart en bereken hier ook een maandgemiddelde van

        verstrekkingen_ag_3 = verstrekkingen_ag_2.groupby(by=['apotheek', 'ndATKODE', 'sdEtiketNaam'])[
            'ndAantal'].sum().to_frame('eenheden verstrekt 2 mnd (CGM)').reset_index()

        # maak nu een pivot table hiervan zodat je alle apotheken op een rijtje naast elkaar hebt.

        verstrekkingen_ag_4 = verstrekkingen_ag_3.pivot_table(index=['ndATKODE', 'sdEtiketNaam'],
                                                              columns='apotheek',
                                                              values='eenheden verstrekt 2 mnd (CGM)').reset_index()

        # nu moeten we voor alle kolommen genaamd hanzeplein, helpman, musselpark, oosterhaar, oosterpoort en wiljes een functie schrijven die alle NaN waarden omzet naar 0

        for col in verstrekkingen_ag_4.columns[2:]:
            verstrekkingen_ag_4[col] = verstrekkingen_ag_4[col].replace(np.nan, 0, regex=True)

        # nu moeten we de dataframes gaan mergen zodat we een totoal overzicht kunnen maken voor de apotheek van de overvoorraad

        assortiment_overvoorraad_analyse_6 = assortiment_overvoorraad_analyse_5.merge(verstrekkingen_ag_4[
                                                                                          ['ndATKODE', 'hanzeplein',
                                                                                           'oosterpoort', 'helpman',
                                                                                           'wiljes', 'oosterhaar',
                                                                                           'musselpark']], how='left',
                                                                                      left_on='zinummer',
                                                                                      right_on='ndATKODE').drop(
            columns='ndATKODE')

        # nu gaan we hier de CF verstrekkingen nog aan toevoegen

        # nu alleen de CF verstrekkingen pakken
        verstrekkingen_ag_5 = verstrekkingen_ag.loc[distributie_niet & zorg_niet & dienst_niet & lsp_niet & cf_wel]

        verstrekkingen_ag_6 = verstrekkingen_ag_5.loc[
            (verstrekkingen_ag_5['ddDatumRecept'] >= datum_2_maanden_terug_verstrekkingen)]

        verstrekkingen_ag_7 = verstrekkingen_ag_6.loc[(verstrekkingen_ag_6['apotheek'] == Apotheek_analyse)]

        verstrekkingen_ag_8 = verstrekkingen_ag_7.groupby(by=['ndATKODE', 'sdEtiketNaam'])['ndAantal'].sum().to_frame(
            'eenheden verstrekt CF CGM apotheek analyse').reset_index()

        cf_verstrekkingen_analyse_apotheek = verstrekkingen_ag_8

        # nu mergen we alles tot een dataframe samenkomend dataframe

        assortiment_overvoorraad_analyse_7 = assortiment_overvoorraad_analyse_6.merge(
            cf_verstrekkingen_analyse_apotheek[['ndATKODE', 'eenheden verstrekt CF CGM apotheek analyse']], how='left',
            left_on='zinummer', right_on='ndATKODE').drop(columns='ndATKODE')

        # vanaf hier maken we er een dash ag grid van

        # assortiment_overvoorraad_analyse_7.to_excel('overvoorraad_analyse.xlsx')

        # ============================= OVERZICHT DATAFRAMES ============================
        assortiment_overvoorraad_analyse_5  # Analyse van de overvoorraad in het assortiment van de geselecteerde apotheek
        verstrekkingen_ag_4  # alle verstrekkingen uit de ladekast van artikelen uit alle apotheken (afgelopen 2 maanden)
        assortiment_overvoorraad_analyse_6  # alle overvoorraad samen met alle ladekast verstrekkingen van alle apotheken
        cf_verstrekkingen_analyse_apotheek  # alle CF verstrekkingen van de apotheek die bekeken wordt in de analyse
        assortiment_overvoorraad_analyse_7  # het DEFINTIEVE DATAFRAME MET over voorraad: ladekast verstrekkingen en CF verstrekkingen
        # ============================= OVERZICHT DATAFRAMES ============================

        overvoorraad_excel = dcc.send_data_frame(assortiment_overvoorraad_analyse_7.to_excel('overvoorraad.xlsx', index=False))

        return overvoorraad_excel

if __name__ == '__main__':
    app.run_server(debug=True)

