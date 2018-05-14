# -*- coding: utf-8 -*-
"""
Created on Thu May  3 13:09:02 2018

@author: ksedzro
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 11:10:21 2018

@author: ksedzro
"""

########################################################################################################
# a basic (thermal) unit commitment model, drawn from:                                                 #
# A Computationally Efficient Mixed-Integer Linear Formulation for the Thermal Unit Commitment Problem #
# Miguel Carrion and Jose M. Arroyo                                                                    #
# IEEE Transactions on Power Systems, Volume 21, Number 3, August 2006.                                #
########################################################################################################
import pandas as pd
import numpy as np
from pyomo.environ import *
from pyomo.opt import SolverFactory
model = AbstractModel()
model.dual = Suffix(direction=Suffix.IMPORT_EXPORT)




#=======================================================#
# INPUT DATA                                            #
#=======================================================#
#data_path = 'C:/Users/ksedzro/Documents/Python Scripts/WECC10k/'
data_path = 'C:/Users/ksedzro/Documents/Python Scripts/TEXAS2k/'
#data_path = 'C:/Users/ksedzro/Documents/Python Scripts/NREL 118 data for PSST2/'
print('loading data ...')

gen_df = pd.read_csv(data_path+'generator_data_plexos_withRT.csv',index_col=0)
#bus_df = pd.read_csv(data_path+'bus.csv',index_col=None)
#wind_gen_df = gen_df.loc[wind_generator_names,:].copy()
#wind_gen_bus_df = pd.merge(wind_gen_df,bus_df, left_on=['GEN_BUS'], right_on = 'BUS_ID', left_index=True)
#wind_gen_bus_df.set_index(wind_gen_df.index, inplace=True)
#wind_gen_bus_df.to_csv(data_path+'wind_generator_data.csv')
"""
Scaling Wind Generation
"""
wind_penetration_wanted = 0.080 # 
wind_penetration_current = sum(gen_df.loc[x ,'PMAX'] for x in gen_df.index if x.startswith('wind'))/ sum(gen_df['PMAX'])# 
wind_scaling_facor = wind_penetration_wanted * (1/wind_penetration_current -1)/(1-wind_penetration_wanted)   

for x in gen_df.index:
    if x.startswith('wind'):
        gen_df.loc[x ,'PMAX'] = wind_scaling_facor*gen_df.loc[x ,'PMAX']
    
genfor_df = pd.read_csv(data_path+'generator.csv',index_col=0)

for x in genfor_df.columns:
    if x.startswith('wind'):
        genfor_df.loc[:,x] = wind_scaling_facor*genfor_df.loc[:,x]




genforren_df=pd.DataFrame()
genforren_df=genfor_df.loc[:,gen_df[gen_df['GEN_TYPE']!='Thermal'].index]
genforren_df.fillna(0, inplace=True)

load_df = pd.read_csv(data_path+'loads.csv',index_col=0)

#branch_df = pd.read_csv(data_path+'branch.csv')
#branch_df['BR_ID'] = 'br'+branch_df['BR_ID'].apply(str)
#branch_df['F_BUS'] = 'bus'+branch_df['F_BUS'].apply(str)
#branch_df['T_BUS'] = 'bus'+branch_df['T_BUS'].apply(str)
#branch_df.set_index(['BR_ID'])
#branch_df.to_csv(data_path+'branch.csv')
branch_df = pd.read_csv(data_path+'branch.csv',index_col=['BR_ID'])

#bus_df = pd.read_csv(data_path+'bus.csv')
#bus_df['BUS_ID'] = 'bus'+bus_df['BUS_ID'].apply(str)
#bus_df.set_index('BUS_ID')
#bus_df.to_csv(data_path+'bus.csv')

bus_df = pd.read_csv(data_path+'bus.csv',index_col=['BUS_ID'])
#bus_name = ['ODESSA 2 0',	'PRESIDIO 2 0',	'O DONNELL 1 0',	'O DONNELL 1 1',	'BIG SPRING 5 0',	'BIG SPRING 5 1',	'VAN HORN 0',	'IRAAN 2 0',	'IRAAN 2 1',	'PRESIDIO 1 0',	'PRESIDIO 1 1',	'SANDERSON 0',	'MONAHANS 2 0',	'GRANDFALLS 0',	'MARFA 0',	'GARDEN CITY 0',	'ODESSA 4 0',	'NOTREES 0',	'MIDLAND 4 0',	'BIG SPRING 1 0',	'BIG SPRING 1 1',	'O DONNELL 2 0',	'O DONNELL 2 1',	'ODESSA 6 0',	'BIG SPRINGS 0',	'BIG SPRINGS 1',	'MIDLAND 2 0',	'COAHOMA 0',	'MIDLAND 3 0',	'ALPINE 0',	'FORT DAVIS 0',	'MCCAMEY 1 0',	'MCCAMEY 1 1',	'BIG SPRING 4 0',	'BIG SPRING 4 1',	'CRANE 0',	'ODESSA 5 0',	'FORT STOCKTON 1 0',	'FORT STOCKTON 1 1',	'ANDREWS 0',	'FORSAN 0',	'FORSAN 1',	'FORSAN 2',	'BIG LAKE 0',	'MIDLAND 5 0',	'OZONA 0',	'MONAHANS 1 0',	'MONAHANS 1 1',	'MONAHANS 1 2',	'MONAHANS 1 3',	'MONAHANS 1 4',	'MONAHANS 1 5',	'MONAHANS 1 6',	'STANTON 0',	'ODONNELL 0',	'LENORAH 0',	'LENORAH 1',	'IRAAN 3 0',	'IRAAN 3 1',	'IRAAN 3 2',	'BIG SPRING 6 0',	'BIG SPRING 6 1',	'BIG SPRING 6 2',	'ODESSA 3 0',	'BIG SPRING 3 0',	'BIG SPRING 3 1',	'BIG SPRING 7 0',	'MIDLAND 1 0',	'IRAAN 1 0',	'IRAAN 1 1',	'ODESSA 1 0',	'ODESSA 1 1',	'ODESSA 1 2',	'ODESSA 1 3',	'ODESSA 1 4',	'ODESSA 1 5',	'ODESSA 1 6',	'ODESSA 1 7',	'ODESSA 1 8',	'ODESSA 1 9',	'ODESSA 1 10',	'FORT STOCKTON 2 0',	'FORT STOCKTON 3 0',	'BIG SPRING 2 0',	'KERMIT 0',	'PECOS 0',	'SHEFFIELD 0',	'MCCAMEY 2 0',	'LAMESA 0',	'GOLDSMITH 0',	'RALLS 2 0',	'PARIS 3 0',	'SAVOY 0',	'SAVOY 1',	'SAVOY 2',	'SAVOY 3',	'SAVOY 4',	'HONEY GROVE 0',	'MEMPHIS 0',	'IOWA PARK 0',	'VERNON 2 0',	'PANHANDLE 2 0',	'PANHANDLE 2 1',	'PANHANDLE 2 2',	'CHILDRESS 0',	'FORESTBURG 0',	'SHERMAN 3 0',	'PANHANDLE 4 0',	'PANHANDLE 4 1',	'PANHANDLE 4 2',	'WICHITA FALLS 6 0',	'PARIS 2 0',	'PARIS 2 1',	'PARIS 2 2',	'PARIS 2 3',	'WICHITA FALLS 4 0',	'WHEELER 0',	'DEPORT 0',	'WICHITA FALLS 3 0',	'SILVERTON 0',	'BONHAM 0',	'MATADOR 0',	'ARTHUR CITY 0',	'LEONARD 0',	'GORDONVILLE 0',	'KNOX CITY 0',	'WICHITA FALLS 7 0',	'LINDSAY 0',	'ECTOR 0',	'SUNSET 0',	'CLARKSVILLE 0',	'PANHANDLE 3 0',	'PANHANDLE 3 1',	'SADLER 0',	'WHITESBORO 0',	'SHEPPARD AFB 0',	'POTTSBORO 0',	'BELLS 0',	'CROSBYTON 0',	'ELECTRA 0',	'PATTONVILLE 0',	'HENRIETTA 0',	'PANHANDLE 6 0',	'BOWIE 0',	'WICHITA FALLS 1 0',	'WICHITA FALLS 1 1',	'WICHITA FALLS 1 2',	'WICHITA FALLS 1 3',	'WHITE DEER 0',	'WHITE DEER 1',	'ROXTON 0',	'VERNON 1 0',	'VERNON 1 1',	'DENISON 2 0',	'SUMNER 0',	'GAINESVILLE 0',	'ASPERMONT 0',	'WICHITA FALLS 5 0',	'WINDTHORST 0',	'HOWE 0',	'ARCHER 2 0',	'ARCHER 2 1',	'COLLINSVILLE 0',	'JAYTON 0',	'JAYTON 1',	'JAYTON 2',	'JAYTON 3',	'MUENSTER 1 0',	'MUENSTER 1 1',	'PADUCAH 0',	'NOCONA 0',	'DODD CITY 0',	'WICHITA FALLS 2 0',	'WICHITA FALLS 2 1',	'WICHITA FALLS 2 2',	'WICHITA FALLS 2 3',	'MONTAGUE 0',	'SPUR 0',	'ARCHER 1 0',	'ARCHER 1 1',	'ANNONA 0',	'SEYMOUR 0',	'DENISON 1 0',	'PANHANDLE 5 0',	'PANHANDLE 5 1',	'PANHANDLE 5 2',	'RALLS 1 0',	'RALLS 1 1',	'RALLS 1 2',	'RALLS 1 3',	'RALLS 1 4',	'SHERMAN 1 0',	'SHERMAN 1 1',	'SHERMAN 1 2',	'SHERMAN 1 3',	'SHERMAN 1 4',	'WHITEWRIGHT 0',	'SHERMAN 2 0',	'ROCHESTER 0',	'BURKBURNETT 0',	'MUENSTER 2 0',	'ARCHER CITY 0',	'PETROLIA 0',	'PARIS 1 0',	'PARIS 1 1',	'PARIS 1 2',	'PARIS 1 3',	'PARIS 1 4',	'PARIS 1 5',	'PARIS 1 6',	'PARIS 1 7',	'BAGWELL 0',	'TELEPHONE 0',	'PANHANDLE 1 0',	'VAN ALSTYNE 0',	'TIOGA 0',	'VALLEY VIEW 0',	'MIAMI 0',	'MIAMI 1',	'TRENTON 0',	'HASKELL 0',	'HASKELL 1',	'HASKELL 2',	'SAINT JO 0',	'KERRVILLE 0',	'KERRVILLE 1',	'SWEETWATER 4 0',	'SWEETWATER 4 1',	'LEAKEY 0',	'HAMLIN 0',	'MERKEL 3 0',	'COLEMAN 0',	'SONORA 0',	'CAMP WOOD 0',	'LLANO 0',	'WILLOW CITY 0',	'ABILENE 4 0',	'KINGSLAND 0',	'ROSCOE 6 0',	'BLACKWELL 0',	'BLACKWELL 1',	'CHRISTOVAL 0',	'CHRISTOVAL 1',	'CHRISTOVAL 2',	'LUEDERS 0',	'COLORADO CITY 0',	'STAMFORD 0',	'ELDORADO 0',	'SAN SABA 0',	'ABILENE 2 0',	'ABILENE 2 1',	'ABILENE 2 2',	'LOMETA 0',	'SAN ANGELO 1 0',	'TUSCOLA 0',	'ABILENE 7 0',	'SNYDER 1 0',	'SNYDER 1 1',	'CHEROKEE 0',	'RICHLAND SPRINGS 0',	'ROSCOE 2 0',	'ROSCOE 2 1',	'ROSCOE 2 2',	'BALLINGER 0',	'SILVER 0',	'SILVER 1',	'SILVER 2',	'SILVER 3',	'SILVER 4',	'ROSCOE 5 0',	'ROSCOE 5 1',	'ROSCOE 5 2',	'ANSON 0',	'DEL RIO 0',	'DEL RIO 1',	'HUNT 0',	'WINGATE 0',	'WINGATE 1',	'WINGATE 2',	'WINGATE 3',	'WINGATE 4',	'STERLING CITY 1 0',	'STERLING CITY 1 1',	'STERLING CITY 1 2',	'STERLING CITY 1 3',	'STERLING CITY 1 4',	'STERLING CITY 1 5',	'ROSCOE 4 0',	'ROSCOE 4 1',	'BRADY 0',	'TRENT 1 0',	'TRENT 1 1',	'OVALO 0',	'NOLAN 0',	'NOLAN 1',	'MILES 0',	'BRACKETTVILLE 2 0',	'BRACKETTVILLE 2 1',	'MASON 0',	'BRACKETTVILLE 3 0',	'ABILENE 6 0',	'HERMLEIGH 0',	'HERMLEIGH 1',	'HERMLEIGH 2',	'HERMLEIGH 3',	'MERKEL 1 0',	'MERKEL 1 1',	'MERKEL 1 2',	'LORAINE 1 0',	'LORAINE 1 1',	'LORAINE 1 2',	'ABILENE 1 0',	'ABILENE 1 1',	'ABILENE 1 2',	'ABILENE 1 3',	'ABILENE 1 4',	'ROCKSPRINGS 0',	'MERKEL 2 0',	'MERKEL 2 1',	'FLUVANNA 2 0',	'FLUVANNA 2 1',	'FLUVANNA 2 2',	'DYESS AFB 0',	'HAWLEY 0',	'BUCHANAN DAM 2 0',	'ABILENE 3 0',	'SWEETWATER 5 0',	'BUCHANAN DAM 1 0',	'BUCHANAN DAM 1 1',	'BUCHANAN DAM 1 2',	'INGRAM 0',	'KEMPNER 0',	'FLUVANNA 1 0',	'FLUVANNA 1 1',	'STERLING CITY 2 0',	'STERLING CITY 2 1',	'STERLING CITY 2 2',	'SAN ANGELO 2 0',	'ROTAN 0',	'SYNDER 0',	'SYNDER 1',	'SYNDER 2',	'BRACKETTVILLE 1 0',	'BRACKETTVILLE 1 1',	'ROSCOE 1 0',	'ROSCOE 1 1',	'UVALDE 0',	'FREDERICKSBURG 0',	'ABILENE 5 0',	'SABINAL 0',	'SWEETWATER 2 0',	'LORAINE 2 0',	'ROSCOE 3 0',	'SAN ANGELO 3 0',	'TUSOCOLA 0',	'EDEN 0',	'SNYDER 2 0',	'SNYDER 2 1',	'SNYDER 2 2',	'SNYDER 2 3',	'SWEETWATER 1 0',	'MENARD 0',	'WINTERS 0',	'GOLDSBORO 0',	'SWEETWATER 3 0',	'GOODFELLOW AFB 0',	'SANTA ANNA 0',	'ROWENA 0',	'TRENT 2 0',	'JUNCTION 0',	'LAMPASAS 0',	'LAUGHLIN A F B 0',	'EDINBURG 3 0',	'LAREDO 7 0',	'LAREDO 7 1',	'BRUNI 2 0',	'MCALLEN 2 0',	'POTEET 0',	'SARITA 3 0',	'SARITA 3 1',	'HEBBRONVILLE 0',	'PROGRESO 0',	'EDINBURG 2 0',	'EAGLE PASS 0',	'EAGLE PASS 1',	'CHARLOTTE 0',	'CORPUS CHRISTI 4 0',	'WOODSBORO 0',	'MERCEDES 0',	'CORPUS CHRISTI 16 0',	'EDCOUCH 0',	'ENCINAL 0',	'MOORE 0',	'CHRISTINE 0',	'CHRISTINE 1',	'CHRISTINE 2',	'MCALLEN 3 0',	'FANNIN 0',	'FANNIN 1',	'FANNIN 2',	'SAN YGNACIO 0',	'KINGSVILLE 0',	'LAREDO 6 0',	'HIDALGO 0',	'CORPUS CHRISTI 18 0',	'CRYSTAL CITY 0',	'SINTON 0',	'BEEVILLE 0',	'MISSION 4 0',	'MISSION 4 1',	'SAN JUAN 0',	'SAN JUAN 1',	'FALCON HEIGHTS 2 0',	'FALCON HEIGHTS 1 0',	'FALCON HEIGHTS 1 1',	'FALCON HEIGHTS 1 2',	'FALCON HEIGHTS 1 3',	'LA JOYA 0',	'SEBASTIAN 2 0',	'SEBASTIAN 2 1',	'BISHOP 0',	'BISHOP 1',	'ARMSTRONG 2 0',	'SKIDMORE 0',	'CORPUS CHRISTI 9 0',	'GREGORY 0',	'GREGORY 1',	'GREGORY 2',	'GREGORY 3',	'GREGORY 4',	'GREGORY 5',	'GREGORY 6',	'GREGORY 7',	'CORPUS CHRISTI 2 0',	'CORPUS CHRISTI 2 1',	'WESLACO 0',	'HARLINGEN 1 0',	'ELSA 0',	'CORPUS CHRISTI 17 0',	'BROWNSVILLE 2 0',	'BROWNSVILLE 2 1',	'CORPUS CHRISTI 10 0',	'MISSION 1 0',	'MISSION 1 1',	'MISSION 1 2',	'MISSION 1 3',	'MISSION 1 4',	'CORPUS CHRISTI 8 0',	'MISSION 3 0',	'CORPUS CHRISTI 3 0',	'CORPUS CHRISTI 3 1',	'CORPUS CHRISTI 3 2',	'CORPUS CHRISTI 3 3',	'CORPUS CHRISTI 3 4',	'CORPUS CHRISTI 3 5',	'RIO HONDO 0',	'CORPUS CHRISTI 5 0',	'PHARR 0',	'SANTA ROSA 1 0',	'SANTA ROSA 1 1',	'SANTA ROSA 1 2',	'SANTA ROSA 1 3',	'SANTA ROSA 1 4',	'SANTA ROSA 1 5',	'SANTA ROSA 1 6',	'SANTA ROSA 1 7',	'SANTA ROSA 1 8',	'SANTA ROSA 1 9',	'ODEM 0',	'CORPUS CHRISTI 13 0',	'LAREDO 3 0',	'OLMITO 0',	'EDINBURG 1 0',	'TAFT 2 0',	'TAFT 2 1',	'PORT ISABEL 0',	'DONNA 0',	'INGLESIDE 0',	'CORPUS CHRISTI 11 0',	'LOS FRESNOS 0',	'HARLINGEN 2 0',	'RIVIERA 0',	'LAREDO 1 0',	'LAREDO 1 1',	'LAREDO 1 2',	'LAREDO 1 3',	'JOURDANTON 0',	'GEORGE WEST 0',	'ROMA 0',	'CORPUS CHRISTI 12 0',	'SANTA MARIA 0',	'MCALLEN 1 0',	'CORPUS CHRISTI 7 0',	'FALFURRIAS 0',	'PETTUS 0',	'BROWNSVILLE 3 0',	'ALICE 0',	'RIO GRANDE CITY 0',	'PREMONT 0',	'FREER 0',	'PEARSALL 0',	'PEARSALL 1',	'PEARSALL 2',	'PEARSALL 3',	'PEARSALL 4',	'PEARSALL 5',	'PEARSALL 6',	'PEARSALL 7',	'SANDIA 0',	'SARITA 1 0',	'SARITA 1 1',	'SARITA 1 2',	'DILLEY 0',	'ORANGE GROVE 0',	'PORTLAND 0',	'LAREDO 4 0',	'LAREDO 4 1',	'THREE RIVERS 0',	'ROCKPORT 0',	'CORPUS CHRISTI 15 0',	'ARMSTRONG 1 0',	'ARMSTRONG 1 1',	'ARMSTRONG 1 2',	'PENITAS 0',	'SULLIVAN CITY 0',	'CORPUS CHRISTI 6 0',	'MISSION 2 0',	'CORPUS CHRISTI 1 0',	'CORPUS CHRISTI 1 1',	'CORPUS CHRISTI 1 2',	'CORPUS CHRISTI 1 3',	'CORPUS CHRISTI 1 4',	'CORPUS CHRISTI 1 5',	'GRULLA 0',	'SARITA 2 0',	'SARITA 2 1',	'HARGILL 0',	'CORPUS CHRISTI 14 0',	'MATHIS 0',	'ARANSAS PASS 0',	'SAN BENITO 0',	'PLEASANTON 0',	'REFUGIO 0',	'LYTLE 0',	'LAREDO 2 0',	'BRUNI 1 0',	'BRUNI 1 1',	'GOLIAD 0',	'SAN DIEGO 0',	'PORT ARANSAS 0',	'TAFT 1 0',	'TAFT 1 1',	'SAN PERLITA 0',	'SAN PERLITA 1',	'ZAPATA 0',	'SANTA ROSA 2 0',	'COTULLA 0',	'QUEMADO 0',	'CARRIZO SPRINGS 0',	'LAREDO 5 0',	'RAYMONDVILLE 0',	'BROWNSVILLE 1 0',	'BROWNSVILLE 1 1',	'SEBASTIAN 1 0',	'OILTON 0',	'OILTON 1',	'OILTON 2',	'GARLAND 5 0',	'KERENS 0',	'LIPAN 0',	'DALLAS 24 0',	'DENTON 4 0',	'ALBANY 2 0',	'DALLAS 21 0',	'PLANO 2 0',	'THORNTON 0',	'DENTON 5 0',	'EARLY 0',	'DECATUR 0',	'KELLER 2 0',	'KELLER 2 1',	'PONDER 0',	'JACKSBORO 1 0',	'JACKSBORO 1 1',	'JACKSBORO 1 2',	'ALEDO 1 0',	'ALEDO 1 1',	'ALEDO 1 2',	'GATESVILLE 4 0',	'CLEBURNE 2 0',	'FORT WORTH 14 0',	'FORT WORTH 23 0',	'FORT WORTH 1 0',	'TROY 0',	'SPRINGTOWN 0',	'PRINCETON 0',	'DALLAS 27 0',	'DALLAS 1 0',	'DALLAS 1 1',	'DALLAS 1 2',	'DALLAS 1 3',	'DALLAS 1 4',	'DALLAS 1 5',	'DALLAS 1 6',	'DALLAS 1 7',	'DALLAS 1 8',	'DALLAS 1 9',	'ROYSE CITY 0',	'BOYD 0',	'STEPHENVILLE 0',	'STEPHENVILLE 1',	'MANSFIELD 0',	'MANSFIELD 1',	'GREENVILLE 1 0',	'GREENVILLE 1 1',	'GREENVILLE 1 2',	'GREENVILLE 1 3',	'PLANO 4 0',	'GROESBECK 0',	'GRAHAM 0',	'GRAHAM 1',	'GRAHAM 2',	'GRAHAM 3',	'MABANK 2 0',	'MABANK 2 1',	'MABANK 2 2',	'MABANK 2 3',	'ARLINGTON 1 0',	'ARLINGTON 1 1',	'ARLINGTON 1 2',	'ARLINGTON 1 3',	'ARLINGTON 1 4',	'ARLINGTON 1 5',	'ARLINGTON 1 6',	'DALLAS 41 0',	'WACO 3 0',	'DALLAS 19 0',	'BANGS 0',	'PROSPER 0',	'EVANT 0',	'TERRELL 1 0',	'TERRELL 1 1',	'AUBREY 0',	'WACO 4 0',	'LORENA 0',	'FORT HOOD 0',	'ARLINGTON 5 0',	'MCKINNEY 3 0',	'MCKINNEY 3 1',	'DALLAS 38 0',	'ARLINGTON 9 0',	'MILFORD 0',	'CLIFTON 1 0',	'CLIFTON 1 1',	'DALLAS 15 0',	'FROST 0',	'GRANDVIEW 0',	'HASLET 0',	'BARDWELL 0',	'LAKE DALLAS 0',	'PLANO 1 0',	'EULESS 2 0',	'FORT WORTH 24 0',	'FLOWER MOUND 2 0',	'DALLAS 11 0',	'COMANCHE 0',	'RICHARDSON 2 0',	'RICHARDSON 2 1',	'FORT WORTH 8 0',	'IRVING 1 0',	'IRVING 1 1',	'IRVING 1 2',	'DALLAS 44 0',	'LANCASTER 1 0',	'PALO PINTO 2 0',	'ADDISON 0',	'HICO 0',	'KRUM 0',	'KAUFMAN 0',	'CADDO MILLS 0',	'PLANO 7 0',	'FORT WORTH 5 0',	'BAIRD 0',	'PERRIN 0',	'BROWNWOOD 0',	'BROWNWOOD 1',	'DALLAS 6 0',	'MARLIN 0',	'MARLIN 1',	'ARLINGTON 6 0',	'DALLAS 8 0',	'JONESBORO 0',	'DALLAS 33 0',	'GOLDTHWAITE 2 0',	'PLANO 5 0',	'BELTON 0',	'BELTON 1',	'TOLAR 0',	'BRECKENRIDGE 0',	'EASTLAND 0',	'COOPER 0',	'WACO 1 0',	'WACO 1 1',	'DALLAS 42 0',	'GATESVILLE 1 0',	'ANNA 0',	'MOODY 0',	'FORT WORTH 2 0',	'WACO 6 0',	'GRAND PRAIRIE 1 0',	'ROWLETT 2 0',	'PLANO 6 0',	'IRVING 5 0',	'DALLAS 7 0',	'BRYSON 2 0',	'MORGAN 0',	'SACHSE 0',	'PARADISE 0',	'RIO VISTA 0',	'STRAWN 0',	'May-00',	'DESOTO 0',	'MESQUITE 2 0',	'ROSEBUD 0',	'DENTON 2 0',	'DALLAS 4 0',	'AXTELL 0',	'NOLANVILLE 0',	'DENTON 1 0',	'DENTON 1 1',	'DENTON 1 2',	'DENTON 1 3',	'DALLAS 39 0',	'DUBLIN 1 0',	'DUBLIN 1 1',	'MERTENS 0',	'WEATHERFORD 1 0',	'PLANO 3 0',	'MALONE 0',	'DENTON 3 0',	'GRAFORD 0',	'ARLINGTON 8 0',	'ROCKWALL 1 0',	'CORSICANA 2 0',	'CORSICANA 2 1',	'GARLAND 2 0',	'GATESVILLE 2 0',	'CARROLLTON 3 0',	'FORT WORTH 26 0',	'RHOME 0',	'VENUS 0',	'OLNEY 2 0',	'CARROLLTON 1 0',	'DALLAS 20 0',	'GORDON 0',	'MERIDIAN 0',	'KILLEEN 4 0',	'KILLEEN 4 1',	'DUNCANVILLE 1 0',	'ARGYLE 0',	'BRYSON 1 0',	'BRYSON 1 1',	'BRYSON 1 2',	'FORT WORTH 12 0',	'MINERAL WELLS 0',	'COOLIDGE 0',	'RICE 0',	'DALLAS 35 0',	'POOLVILLE 0',	'POOLVILLE 1',	'POOLVILLE 2',	'POOLVILLE 3',	'POOLVILLE 4',	'WALNUT SPRINGS 0',	'BEDFORD 2 0',	'HUBBARD 0',	'FERRIS 0',	'GARLAND 4 0',	'DALLAS 32 0',	'PILOT POINT 0',	'FORT WORTH 6 0',	'NORTH RICHLAND HILLS 2 0',	'JUSTIN 0',	'SCURRY 0',	'SANGER 0',	'KILLEEN 1 0',	'MABANK 1 0',	'MEXIA 0',	'CARROLLTON 2 0',	'NEVADA 0',	'ZEPHYR 0',	'TERRELL 2 0',	'DALLAS 14 0',	'DALLAS 13 0',	'DALLAS 28 0',	'HAMILTON 0',	'ARLINGTON 7 0',	'EULESS 1 0',	'FRISCO 1 0',	'SALADO 0',	'OLNEY 1 0',	'OLNEY 1 1',	'OLNEY 1 2',	'GOLDTHWAITE 1 0',	'GOLDTHWAITE 1 1',	'GOLDTHWAITE 1 2',	'GOLDTHWAITE 1 3',	'GOLDTHWAITE 1 4',	'FORT WORTH 22 0',	'GRAPEVINE 0',	'GLEN ROSE 2 0',	'KOPPERL 0',	'BEDFORD 1 0',	'FORT WORTH 29 0',	'DALLAS 5 0',	'GRAND PRAIRIE 2 0',	'DALLAS 22 0',	'FLOWER MOUND 1 0',	'ROANOKE 0',	'MILLSAP 0',	'FORRESTON 0',	'ITALY 0',	'FORNEY 0',	'LAVON 0',	'GLEN ROSE 1 0',	'GLEN ROSE 1 1',	'GLEN ROSE 1 2',	'GLEN ROSE 1 3',	'DE LEON 0',	'KELLER 1 0',	'CEDAR HILL 0',	'MC GREGOR 0',	'COMMERCE 0',	'MIDLOTHIAN 2 0',	'WEST 0',	'BARTLETT 0',	'DALLAS 16 0',	'COPPELL 0',	'WILMER 0',	'DAWSON 0',	'MART 0',	'LITTLE ELM 0',	'TEMPLE 2 0',	'TEMPLE 1 0',	'TEMPLE 1 1',	'TEMPLE 1 2',	'TEMPLE 1 3',	'TEMPLE 1 4',	'QUINLAN 0',	'CHICO 0',	'DUBLIN 2 0',	'ARLINGTON 2 0',	'WOLFE CITY 0',	'DALLAS 26 0',	'WHITNEY 0',	'FORT WORTH 25 0',	'FORT WORTH 27 0',	'JOSHUA 0',	'DALLAS 12 0',	'MCKINNEY 1 0',	'MCKINNEY 1 1',	'MCKINNEY 1 2',	'MCKINNEY 1 3',	'MCKINNEY 1 4',	'MCKINNEY 1 5',	'MCKINNEY 1 6',	'MCKINNEY 1 7',	'MCKINNEY 1 8',	'ALLEN 1 0',	'ALLEN 1 1',	'ALEDO 2 0',	'THE COLONY 0',	'SUNNYVALE 0',	'DALLAS 10 0',	'FORT WORTH 4 0',	'DALLAS 30 0',	'AZLE 0',	'HUTCHINS 0',	'VALLEY MILLS 0',	'DENTON 6 0',	'MESQUITE 3 0',	'GRANBURY 1 0',	'GRANBURY 1 1',	'GRANBURY 1 2',	'GRANBURY 1 3',	'GRANBURY 1 4',	'DALLAS 2 0',	'DALLAS 2 1',	'DALLAS 2 2',	'DALLAS 2 3',	'DALLAS 2 4',	'MOUNT CALM 0',	'RIESEL 2 0',	'DALLAS 17 0',	'ARLINGTON 4 0',	'CELINA 0',	'FORT WORTH 16 0',	'RED OAK 0',	'CLYDE 0',	'IRVING 2 0',	'ROWLETT 1 0',	'JACKSBORO 2 0',	'GRANBURY 3 0',	'SOUTHLAKE 0',	'DALLAS 29 0',	'LEWISVILLE 1 0',	'LEWISVILLE 1 1',	'LEWISVILLE 1 2',	'DALLAS 36 0',	'HILLSBORO 0',	'FORT WORTH 15 0',	'CISCO 0',	'ITASCA 0',	'LANCASTER 2 0',	'GARLAND 1 0',	'GARLAND 1 1',	'DALLAS 9 0',	'DUNCANVILLE 2 0',	'MESQUITE 1 0',	'MAYPEARL 0',	'GARLAND 3 0',	'ALLEN 2 0',	'RIESEL 1 0',	'RIESEL 1 1',	'RIESEL 1 2',	'BRIDGEPORT 0',	'BRIDGEPORT 1',	'BRIDGEPORT 2',	'BRIDGEPORT 3',	'BRIDGEPORT 4',	'BRIDGEPORT 5',	'BRIDGEPORT 6',	'BRIDGEPORT 7',	'BRIDGEPORT 8',	'LEWISVILLE 2 0',	'SEAGOVILLE 0',	'DALLAS 31 0',	'HALTOM CITY 0',	'BALCH SPRINGS 0',	'FORT WORTH 13 0',	'DALLAS 43 0',	'KILLEEN 2 0',	'WACO 5 0',	'FORT WORTH 9 0',	'ENNIS 0',	'ENNIS 1',	'ENNIS 2',	'ENNIS 3',	'DALLAS 3 0',	'DALLAS 3 1',	'RICHARDSON 1 0',	'FORT WORTH 21 0',	'WACO 2 0',	'WACO 2 1',	'ROGERS 0',	'ROGERS 1',	'ROGERS 2',	'CHINA SPRING 0',	'ALBANY 1 0',	'ALBANY 1 1',	'ALBANY 1 2',	'ALBANY 1 3',	'ALBANY 1 4',	'ALBANY 1 5',	'MCKINNEY 2 0',	'GRANBURY 2 0',	'GRANBURY 2 1',	'GRANBURY 2 2',	'GRANBURY 2 3',	'GRANBURY 2 4',	'GRANBURY 2 5',	'CLIFTON 2 0',	'FARMERSVILLE 0',	'ARLINGTON 10 0',	'KILLEEN 3 0',	'KILLEEN 3 1',	'WYLIE 0',	'PALO PINTO 1 0',	'PALO PINTO 1 1',	'PALO PINTO 1 2',	'PALO PINTO 1 3',	'PALO PINTO 1 4',	'PALO PINTO 1 5',	'PALO PINTO 1 6',	'FORT WORTH 10 0',	'JOSEPHINE 0',	'LEWSIVILLE 0',	'LEWSIVILLE 1',	'LEWSIVILLE 2',	'DALLAS 40 0',	'KEMP 0',	'WAXAHACHIE 2 0',	'HURST 0',	'FORT WORTH 18 0',	'WEATHERFORD 2 0',	'ROCKWALL 2 0',	'WEATHERFORD 3 0',	'FORT WORTH 3 0',	'NEWARK 0',	'SANTO 0',	'DALLAS 18 0',	'ELM MOTT 0',	'FORT WORTH 17 0',	'WAXAHACHIE 1 0',	'ARLINGTON 3 0',	'FORT WORTH 20 0',	'FORT WORTH 7 0',	'FORT WORTH 11 0',	'MIDLOTHIAN 1 0',	'MIDLOTHIAN 1 1',	'HEWITT 0',	'ARLINGTON 11 0',	'GRAND PRAIRIE 3 0',	'GRAND PRAIRIE 3 1',	'MELISSA 0',	'COPPERAS COVE 0',	'COPPERAS COVE 1',	'CLEBURNE 1 0',	'GREENVILLE 2 0',	'ALVORD 0',	'GORMAN 0',	'COLLEYVILLE 0',	'HOLLAND 0',	'HOLLAND 1',	'HOLLAND 2',	'TEMPLE 3 0',	'DALLAS 34 0',	'IRVING 4 0',	'FRISCO 2 0',	'FRISCO 2 1',	'GATESVILLE 3 0',	'DALLAS 25 0',	'DALLAS 37 0',	'FORT WORTH 19 0',	'WOODWAY 0',	'MINGUS 0',	'THROCKMORTON 0',	'NEMO 0',	'ABBOTT 0',	'ALVARADO 0',	'CORSICANA 1 0',	'HARKER HEIGHTS 0',	'IRVING 3 0',	'BURLESON 0',	'BURLESON 1',	'FORT WORTH 28 0',	'DALLAS 23 0',	'NORTH RICHLAND HILLS 1 0',	'CROSS PLAINS 0',	'BLOOMING GROVE 0',	'CONVERSE 0',	'SAN ANTONIO 46 0',	'BASTROP 0',	'BASTROP 1',	'BASTROP 2',	'BASTROP 3',	'BASTROP 4',	'BASTROP 5',	'BASTROP 6',	'BASTROP 7',	'MARION 2 0',	'PAIGE 0',	'SAN ANTONIO 42 0',	'WAELDER 0',	'ATASCOSA 0',	'SAN ANTONIO 40 0',	'CIBOLO 0',	'AUSTIN 6 0',	'AUSTIN 25 0',	'HORSESHOE BAY 0',	'LEANDER 1 0',	'LEANDER 1 1',	'LEANDER 1 2',	'AUSTIN 10 0',	'SAN ANTONIO 31 0',	'SAN ANTONIO 49 0',	'ELGIN 0',	'AUSTIN 31 0',	'RUNGE 0',	'YOAKUM 0',	'YOAKUM 1',	'AUSTIN 37 0',	'PFLUGERVILLE 0',	'PFLUGERVILLE 1',	'PFLUGERVILLE 2',	'SAN ANTONIO 12 0',	'SAN ANTONIO 12 1',	'AUSTIN 3 0',	'AUSTIN 3 1',	'AUSTIN 3 2',	'AUSTIN 3 3',	'AUSTIN 3 4',	'SAN ANTONIO 48 0',	'SAN ANTONIO 19 0',	'SAN ANTONIO 2 0',	'SAN ANTONIO 2 1',	'SAN ANTONIO 2 2',	'SAN ANTONIO 2 3',	'SAN ANTONIO 2 4',	'SAN ANTONIO 2 5',	'SAN ANTONIO 2 6',	'SAN ANTONIO 2 7',	'SAN ANTONIO 2 8',	'SAN ANTONIO 2 9',	'BERGHEIM 0',	'NEW BRAUNFELS 2 0',	'NEW BRAUNFELS 2 1',	'NEW BRAUNFELS 2 2',	'D HANIS 0',	'SAN ANTONIO 24 0',	'AUSTIN 7 0',	'BRENHAM 0',	'BRENHAM 1',	'BRENHAM 2',	'BERTRAM 0',	'MARION 1 0',	'MARION 1 1',	'MARION 1 2',	'MARION 1 3',	'MARION 1 4',	'MARION 1 5',	'MARION 1 6',	'MARION 1 7',	'MARION 1 8',	'LA GRANGE 0',	'LA GRANGE 1',	'LA GRANGE 2',	'LA GRANGE 3',	'LA GRANGE 4',	'LA GRANGE 5',	'MARBLE FALLS 1 0',	'MARBLE FALLS 1 1',	'MARBLE FALLS 1 2',	'ROUND ROCK 1 0',	'ROUND ROCK 1 1',	'ROUND ROCK 1 2',	'ROUND ROCK 1 3',	'ROUND ROCK 1 4',	'ROUND ROCK 1 5',	'ROUND ROCK 1 6',	'WIMBERLEY 0',	'GONZALES 0',	'SAN ANTONIO 11 0',	'SAN ANTONIO 14 0',	'HUTTO 0',	'LULING 0',	'SAN ANTONIO 21 0',	'AUSTIN 12 0',	'SAN ANTONIO 15 0',	'ADKINS 0',	'WINCHESTER 0',	'WINCHESTER 1',	'WINCHESTER 2',	'WINCHESTER 3',	'WINCHESTER 4',	'WINCHESTER 5',	'ROCKDALE 1 0',	'ROCKDALE 1 1',	'ROCKDALE 1 2',	'ROCKDALE 1 3',	'ROCKDALE 1 4',	'NATALIA 0',	'AUSTIN 20 0',	'SAN ANTONIO 43 0',	'SAN ANTONIO 5 0',	'TAYLOR 0',	'SMITHVILLE 0',	'CEDAR PARK 0',	'CEDAR PARK 1',	'CEDAR PARK 2',	'SAN ANTONIO 25 0',	'HALLETTSVILLE 0',	'AUSTIN 5 0',	'NEW BRAUNFELS 3 0',	'SUTHERLAND SPRINGS 0',	'AUSTIN 34 0',	'CAMERON 0',	'SAN ANTONIO 35 0',	'MEDINA 0',	'MANCHACA 0',	'SPRING BRANCH 0',	'AUSTIN 19 0',	'FLATONIA 0',	'GRANGER 0',	'FAYETTEVILLE 0',	'GEORGETOWN 2 0',	'AUSTIN 35 0',	'PIPE CREEK 0',	'RED ROCK 0',	'JARRELL 0',	'SAN ANTONIO 1 0',	'SAN ANTONIO 1 1',	'SAN ANTONIO 1 2',	'SAN ANTONIO 1 3',	'SAN ANTONIO 1 4',	'SAN ANTONIO 1 5',	'SAN ANTONIO 1 6',	'SAN ANTONIO 1 7',	'SAN ANTONIO 1 8',	'SAN ANTONIO 36 0',	'SCHULENBURG 0',	'SAN ANTONIO 22 0',	'SAN ANTONIO 22 1',	'DRIPPING SPRINGS 0',	'SAN ANTONIO 26 0',	'MARBLE FALLS 3 0',	'BOERNE 1 0',	'WASHINGTON 0',	'SCHERTZ 0',	'AUSTIN 8 0',	'SEGUIN 1 0',	'SEGUIN 1 1',	'SEGUIN 1 2',	'SEGUIN 1 3',	'SEGUIN 1 4',	'SEGUIN 1 5',	'SEGUIN 1 6',	'SAN ANTONIO 45 0',	'SAN ANTONIO 52 0',	'SAN ANTONIO 52 1',	'SAN ANTONIO 52 2',	'CUERO 2 0',	'CUERO 2 1',	'SAN ANTONIO 10 0',	'AUSTIN 16 0',	'AUSTIN 39 0',	'SAN ANTONIO 51 0',	'SAN ANTONIO 51 1',	'SAN ANTONIO 41 0',	'LA VERNIA 0',	'MANOR 0',	'SAN ANTONIO 38 0',	'GIDDINGS 0',	'AUSTIN 32 0',	'AUSTIN 38 0',	'AUSTIN 30 0',	'AUSTIN 28 0',	'COLUMBUS 0',	'COLUMBUS 1',	'SHINER 0',	'SAN ANTONIO 3 0',	'CALDWELL 0',	'CALDWELL 1',	'AUSTIN 18 0',	'INDUSTRY 0',	'DALE 0',	'SAN ANTONIO 37 0',	'SAN ANTONIO 37 1',	'SAN ANTONIO 37 2',	'SAN ANTONIO 18 0',	'SAN ANTONIO 33 0',	'MARTINDALE 0',	'SAN ANTONIO 17 0',	'SAN ANTONIO 23 0',	'AUSTIN 29 0',	'LEXINGTON 0',	'LEANDER 2 0',	'AUSTIN 15 0',	'MICO 0',	'MARBLE FALLS 2 0',	'MARBLE FALLS 2 1',	'MARBLE FALLS 2 2',	'MARBLE FALLS 2 3',	'MARBLE FALLS 2 4',	'MARBLE FALLS 2 5',	'MARBLE FALLS 2 6',	'AUSTIN 36 0',	'LOCKHART 0',	'AUSTIN 17 0',	'SAN ANTONIO 13 0',	'FALLS CITY 0',	'AUSTIN 27 0',	'AUSTIN 27 1',	'AUSTIN 23 0',	'SAN ANTONIO 27 0',	'BLANCO 0',	'AUSTIN 24 0',	'SAN MARCOS 0',	'SAN MARCOS 1',	'SAN MARCOS 2',	'BUDA 0',	'DEL VALLE 0',	'AUSTIN 4 0',	'SAN ANTONIO 50 0',	'SAN ANTONIO 50 1',	'SAN ANTONIO 50 2',	'BURLINGTON 0',	'AUSTIN 13 0',	'ELMENDORF 0',	'ELMENDORF 1',	'ELMENDORF 2',	'ELMENDORF 3',	'ELMENDORF 4',	'ELMENDORF 5',	'ELMENDORF 6',	'ELMENDORF 7',	'ELMENDORF 8',	'ELMENDORF 9',	'ELMENDORF 10',	'SAN ANTONIO 6 0',	'CANYON LAKE 0',	'JOHNSON CITY 0',	'YORKTOWN 0',	'AUSTIN 2 0',	'AUSTIN 2 1',	'AUSTIN 2 2',	'AUSTIN 2 3',	'AUSTIN 2 4',	'AUSTIN 2 5',	'AUSTIN 2 6',	'LACKLAND A F B 0',	'LIBERTY HILL 0',	'KENEDY 0',	'KENEDY 1',	'CUERO 1 0',	'CUERO 1 1',	'CUERO 1 2',	'CUERO 1 3',	'CUERO 1 4',	'CUERO 1 5',	'CUERO 1 6',	'CUERO 1 7',	'CUERO 1 8',	'CUERO 1 9',	'SAN ANTONIO 20 0',	'VON ORMY 0',	'KYLE 0',	'KYLE 1',	'SEGUIN 2 0',	'SEGUIN 2 1',	'UNIVERSAL CITY 0',	'SPICEWOOD 0',	'SAINT HEDWIG 0',	'SAN ANTONIO 16 0',	'BOERNE 2 0',	'BOERNE 2 1',	'SAN ANTONIO 32 0',	'SAN ANTONIO 32 1',	'AUSTIN 26 0',	'AUSTIN 21 0',	'SAN ANTONIO 44 0',	'CEDAR CREEK 1 0',	'CEDAR CREEK 1 1',	'CEDAR CREEK 1 2',	'CEDAR CREEK 1 3',	'CEDAR CREEK 1 4',	'CEDAR CREEK 1 5',	'NEW BRAUNFELS 1 0',	'NEW BRAUNFELS 1 1',	'NEW BRAUNFELS 1 2',	'NEW BRAUNFELS 1 3',	'NEW BRAUNFELS 1 4',	'NEW BRAUNFELS 1 5',	'NEW BRAUNFELS 1 6',	'NEW BRAUNFELS 1 7',	'AUSTIN 11 0',	'SAN ANTONIO 39 0',	'HONDO 0',	'HONDO 1',	'SAN ANTONIO 4 0',	'NEW ULM 0',	'SAN ANTONIO 8 0',	'AUSTIN 33 0',	'BULVERDE 0',	'GEORGETOWN 3 0',	'GEORGETOWN 3 1',	'GEORGETOWN 3 2',	'GEORGETOWN 3 3',	'GEORGETOWN 3 4',	'SAN ANTONIO 9 0',	'FLORESVILLE 0',	'FLORESVILLE 1',	'SAN ANTONIO 29 0',	'SAN ANTONIO 7 0',	'BUCKHOLTS 0',	'SOMERVILLE 0',	'WEIMAR 0',	'COMFORT 0',	'NORDHEIM 0',	'AUSTIN 9 0',	'AUSTIN 22 0',	'HELOTES 0',	'SAN ANTONIO 47 0',	'SAN ANTONIO 47 1',	'SAN ANTONIO 47 2',	'BANDERA 0',	'SAN ANTONIO 30 0',	'ROCKDALE 2 0',	'CEDAR CREEK 2 0',	'NIXON 0',	'CHAPPELL HILL 0',	'ROUND ROCK 3 0',	'ROUND ROCK 3 1',	'ROUND ROCK 3 2',	'AUSTIN 14 0',	'LEMING 0',	'AUSTIN 1 0',	'AUSTIN 1 1',	'AUSTIN 1 2',	'SAN ANTONIO 28 0',	'ROUND ROCK 2 0',	'ROUND ROCK 4 0',	'ROUND ROCK 4 1',	'SAN ANTONIO 34 0',	'DEVINE 0',	'GEORGETOWN 1 0',	'BURNET 0',	'BURNET 1',	'INEZ 0',	'PASADENA 2 0',	'PASADENA 2 1',	'PASADENA 2 2',	'PASADENA 2 3',	'PASADENA 2 4',	'PASADENA 2 5',	'PASADENA 2 6',	'PASADENA 2 7',	'PRAIRIE VIEW 0',	'CONROE 1 0',	'SIMONTON 0',	'HOUSTON 80 0',	'HOUSTON 1 0',	'HOUSTON 1 1',	'HOUSTON 9 0',	'HOUSTON 73 0',	'NURSERY 0',	'NURSERY 1',	'NURSERY 2',	'NURSERY 3',	'NURSERY 4',	'NURSERY 5',	'NURSERY 6',	'NURSERY 7',	'BACLIFF 0',	'SPRING 1 0',	'HOUSTON 72 0',	'PORT LAVACA 0',	'PORT LAVACA 1',	'PORT LAVACA 2',	'PORT LAVACA 3',	'PORT LAVACA 4',	'PORT LAVACA 5',	'CONROE 5 0',	'CONROE 5 1',	'SUGAR LAND 3 0',	'SUGAR LAND 3 1',	'SUGAR LAND 3 2',	'DAYTON 0',	'DAYTON 1',	'VICTORIA 2 0',	'VICTORIA 2 1',	'VICTORIA 2 2',	'VICTORIA 2 3',	'VICTORIA 2 4',	'KATY 1 0',	'KATY 1 1',	'KATY 1 2',	'MAGNOLIA 2 0',	'HOUSTON 29 0',	'MISSOURI CITY 1 0',	'RICHMOND 1 0',	'HOUSTON 11 0',	'HOUSTON 33 0',	'SPRING 8 0',	'SPRING 8 1',	'POINT COMFORT 2 0',	'POINT COMFORT 2 1',	'POINT COMFORT 2 2',	'POINT COMFORT 2 3',	'POINT COMFORT 2 4',	'POINT COMFORT 2 5',	'POINT COMFORT 2 6',	'POINT COMFORT 2 7',	'POINT COMFORT 2 8',	'HOUSTON 28 0',	'EL CAMPO 0',	'EL CAMPO 1',	'HOUSTON 12 0',	'PORT O CONNOR 0',	'DICKINSON 0',	'GALVESTON 1 0',	'GALVESTON 1 1',	'HOUSTON 10 0',	'BAYTOWN 2 0',	'BAYTOWN 2 1',	'BAYTOWN 2 2',	'BAYTOWN 2 3',	'BAYTOWN 2 4',	'BAYTOWN 2 5',	'BAYTOWN 2 6',	'LEAGUE CITY 0',	'LEAGUE CITY 1',	'LIVERPOOL 0',	'HOUSTON 16 0',	'SUGAR LAND 1 0',	'RICHMOND 2 0',	'HOUSTON 82 0',	'PINEHURST 0',	'PEARLAND 2 0',	'HOUSTON 47 0',	'HOUSTON 79 0',	'HOUSTON 49 0',	'WADSWORTH 0',	'WADSWORTH 1',	'WADSWORTH 2',	'WADSWORTH 3',	'WADSWORTH 4',	'HOUSTON 18 0',	'HOUSTON 88 0',	'TOMBALL 1 0',	'HOUSTON 22 0',	'DEER PARK 0',	'DEER PARK 1',	'DEER PARK 2',	'DEER PARK 3',	'DEER PARK 4',	'DEER PARK 5',	'DEER PARK 6',	'DEER PARK 7',	'DEER PARK 8',	'DEER PARK 9',	'DEER PARK 10',	'DEER PARK 11',	'WALLIS 0',	'HOUSTON 67 0',	'SPRING 4 0',	'SOUTH HOUSTON 0',	'HOUSTON 3 0',	'HOUSTON 3 1',	'HOUSTON 3 2',	'SEADRIFT 0',	'HOUSTON 34 0',	'SUGAR LAND 2 0',	'SUGAR LAND 2 1',	'SUGAR LAND 2 2',	'CONROE 7 0',	'LOLITA 0',	'LAPORTE 0',	'LAPORTE 1',	'LAPORTE 2',	'LAPORTE 3',	'LAPORTE 4',	'LAPORTE 5',	'LAPORTE 6',	'LAPORTE 7',	'LAPORTE 8',	'LAPORTE 9',	'LAPORTE 10',	'LAPORTE 11',	'LAPORTE 12',	'NEW CANEY 0',	'HOUSTON 14 0',	'HOUSTON 2 0',	'HOUSTON 2 1',	'HOUSTON 78 0',	'HOUSTON 40 0',	'BLOOMINGTON 0',	'WILLIS 2 0',	'WILLIS 2 1',	'HOUSTON 51 0',	'PALACIOS 0',	'CONROE 4 0',	'HOUSTON 52 0',	'SPRING 2 0',	'SPRING 2 1',	'KINGWOOD 1 0',	'HOUSTON 5 0',	'HOUSTON 5 1',	'HOUSTON 5 2',	'HOUSTON 5 3',	'HOUSTON 5 4',	'HOUSTON 5 5',	'HOUSTON 5 6',	'HOUSTON 5 7',	'HOUSTON 5 8',	'HOUSTON 5 9',	'HOUSTON 5 10',	'HOUSTON 5 11',	'TEXAS CITY 1 0',	'TEXAS CITY 1 1',	'KINGWOOD 2 0',	'HOUSTON 8 0',	'SPRING 7 0',	'SPRING 7 1',	'SPRING 7 2',	'HOUSTON 41 0',	'FRESNO 0',	'HOUSTON 48 0',	'HOUSTON 58 0',	'PATTISON 0',	'HOUSTON 77 0',	'MISSOURI CITY 2 0',	'MISSOURI CITY 2 1',	'HOUSTON 4 0',	'HOUSTON 4 1',	'HOUSTON 4 2',	'HOUSTON 4 3',	'HOUSTON 4 4',	'HOUSTON 4 5',	'HOUSTON 4 6',	'HOUSTON 4 7',	'HOUSTON 4 8',	'HOUSTON 4 9',	'HOUSTON 4 10',	'HOUSTON 4 11',	'TOMBALL 2 0',	'CYPRESS 1 0',	'CYPRESS 1 1',	'CYPRESS 1 2',	'HEMPSTEAD 0',	'WEST COLUMBIA 0',	'BAYTOWN 1 0',	'BAYTOWN 1 1',	'BAYTOWN 1 2',	'BAYTOWN 1 3',	'BAYTOWN 1 4',	'BAYTOWN 1 5',	'BAYTOWN 1 6',	'BAYTOWN 1 7',	'BAYTOWN 1 8',	'SANTA FE 1 0',	'HOUSTON 27 0',	'SPRING 5 0',	'HOUSTON 46 0',	'HOUSTON 23 0',	'MONTGOMERY 0',	'HUNGERFORD 0',	'HOUSTON 84 0',	'HOUSTON 83 0',	'HOUSTON 24 0',	'HOUSTON 76 0',	'HOUSTON 43 0',	'HOUSTON 81 0',	'HOUSTON 35 0',	'HOUSTON 90 0',	'HOUSTON 90 1',	'HOUSTON 90 2',	'BEASLEY 0',	'HOUSTON 7 0',	'LA MARQUE 0',	'WALLER 0',	'PORTER 0',	'CYPRESS 2 0',	'HOUSTON 30 0',	'FULSHEAR 0',	'LIBERTY 0',	'WINNIE 0',	'HOUSTON 63 0',	'HOUSTON 70 0',	'HOUSTON 55 0',	'CROSBY 0',	'MANVEL 0',	'HOUSTON 54 0',	'HOUSTON 89 0',	'DAMON 0',	'HOUSTON 74 0',	'HOUSTON 26 0',	'HOUSTON 32 0',	'HOCKLEY 0',	'ANGLETON 0',	'ANGLETON 1',	'CONROE 3 0',	'HOUSTON 39 0',	'HOUSTON 59 0',	'PEARLAND 1 0',	'HOUSTON 56 0',	'HOUSTON 13 0',	'CHANNELVIEW 2 0',	'BAY CITY 0',	'BAY CITY 1',	'PASADENA 3 0',	'PASADENA 3 1',	'PASADENA 3 2',	'PASADENA 3 3',	'PASADENA 3 4',	'PASADENA 3 5',	'PASADENA 3 6',	'PASADENA 3 7',	'BROOKSHIRE 0',	'HOUSTON 25 0',	'TEXAS CITY 2 0',	'VICTORIA 3 0',	'VICTORIA 3 1',	'HOUSTON 36 0',	'GANADO 0',	'MONT BELVIEU 0',	'MONT BELVIEU 1',	'MONT BELVIEU 2',	'MONT BELVIEU 3',	'BAYTOWN 3 0',	'BAYTOWN 3 1',	'BAYTOWN 3 2',	'BAYTOWN 3 3',	'BAYTOWN 3 4',	'BAYTOWN 3 5',	'BAYTOWN 3 6',	'BAYTOWN 3 7',	'SPRING 6 0',	'HUMBLE 2 0',	'HOUSTON 69 0',	'SANTA FE 2 0',	'PORT BOLIVAR 0',	'HOUSTON 42 0',	'HOUSTON 85 0',	'HOUSTON 50 0',	'HOUSTON 62 0',	'EAGLE LAKE 0',	'CONROE 2 0',	'WEBSTER 0',	'SWEENY 0',	'BLESSING 0',	'WHARTON 1 0',	'WHARTON 1 1',	'WHARTON 1 2',	'WHARTON 1 3',	'WHARTON 1 4',	'WHARTON 1 5',	'WHARTON 1 6',	'WHARTON 1 7',	'LAKE JACKSON 0',	'LAKE JACKSON 1',	'BELLVILLE 0',	'KATY 4 0',	'HOUSTON 38 0',	'FRIENDSWOOD 0',	'HOUSTON 17 0',	'HOUSTON 66 0',	'FREEPORT 1 0',	'FREEPORT 1 1',	'FREEPORT 1 2',	'FREEPORT 1 3',	'FREEPORT 1 4',	'FREEPORT 1 5',	'FREEPORT 1 6',	'NEWGULF 0',	'NEWGULF 1',	'NEWGULF 2',	'HOUSTON 60 0',	'PASADENA 1 0',	'PASADENA 1 1',	'PASADENA 1 2',	'PASADENA 1 3',	'PASADENA 1 4',	'STAFFORD 0',	'EDNA 0',	'HOUSTON 21 0',	'NEEDVILLE 0',	'SEALY 0',	'KATY 3 0',	'KATY 3 1',	'KATY 3 2',	'HOUSTON 37 0',	'HOUSTON 19 0',	'THOMPSONS 0',	'THOMPSONS 1',	'THOMPSONS 2',	'THOMPSONS 3',	'THOMPSONS 4',	'THOMPSONS 5',	'THOMPSONS 6',	'THOMPSONS 7',	'THOMPSONS 8',	'THOMPSONS 9',	'THOMPSONS 10',	'THOMPSONS 11',	'THOMPSONS 12',	'THOMPSONS 13',	'THOMPSONS 14',	'THOMPSONS 15',	'HOUSTON 61 0',	'GALVESTON 3 0',	'EAST BERNARD 0',	'HOUSTON 20 0',	'CHANNELVIEW 1 0',	'CHANNELVIEW 1 1',	'CHANNELVIEW 1 2',	'CHANNELVIEW 1 3',	'CHANNELVIEW 1 4',	'CHANNELVIEW 1 5',	'CHANNELVIEW 1 6',	'CHANNELVIEW 1 7',	'CHANNELVIEW 1 8',	'CHANNELVIEW 1 9',	'CHANNELVIEW 1 10',	'CHANNELVIEW 1 11',	'CHANNELVIEW 1 12',	'CHANNELVIEW 1 13',	'FREEPORT 3 0',	'HOUSTON 15 0',	'HOUSTON 31 0',	'ROSHARON 0',	'HOUSTON 44 0',	'HOUSTON 75 0',	'HOUSTON 71 0',	'HUMBLE 1 0',	'HOUSTON 68 0',	'WILLIS 1 0',	'WILLIS 1 1',	'WILLIS 1 2',	'BAYTOWN 4 0',	'VAN VLECK 0',	'HUFFMAN 0',	'HOUSTON 53 0',	'HOUSTON 91 0',	'ROSENBERG 0',	'PASADENA 5 0',	'HOUSTON 45 0',	'HOUSTON 6 0',	'HOUSTON 6 1',	'HOUSTON 6 2',	'PASADENA 4 0',	'HOUSTON 57 0',	'GALVESTON 2 0',	'POINT COMFORT 1 0',	'POINT COMFORT 1 1',	'POINT COMFORT 1 2',	'KATY 2 0',	'KATY 2 1',	'SPRING 3 0',	'DANBURY 0',	'WHARTON 2 0',	'VICTORIA 1 0',	'VICTORIA 1 1',	'VICTORIA 1 2',	'HOUSTON 64 0',	'HOUSTON 65 0',	'LA PORTE 0',	'MAGNOLIA 1 0',	'MAGNOLIA 1 1',	'ALVIN 0',	'ALVIN 1',	'ALVIN 2',	'HOUSTON 86 0',	'BRAZORIA 0',	'HOUSTON 87 0',	'FREEPORT 2 0',	'FREEPORT 2 1',	'FREEPORT 2 2',	'CONROE 6 0',	'MADISONVILLE 0',	'NORMANGEE 0',	'ARP 0',	'CENTERVILLE 0',	'LUFKIN 3 0',	'LUFKIN 3 1',	'FLINT 0',	'BULLARD 0',	'CHANDLER 0',	'PLANTERSVILLE 0',	'MARQUEZ 0',	'TENNESSEE COLONY 0',	'ANDERSON 0',	'MINEOLA 0',	'LOVELADY 0',	'HUNTINGTON 0',	'BRYAN 4 0',	'FRANKSTON 0',	'TYLER 4 0',	'TYLER 4 1',	'BEN WHEELER 0',	'GARRISON 0',	'ETOILE 0',	'LUFKIN 1 0',	'LUFKIN 1 1',	'PALESTINE 1 0',	'LINDALE 0',	'WHITEHOUSE 0',	'OVERTON 0',	'GRAND SALINE 0',	'SHIRO 0',	'SHIRO 1',	'SHIRO 2',	'SHIRO 3',	'SHIRO 4',	'SHIRO 5',	'SHIRO 6',	'MIDWAY 0',	'SULPHUR SPRINGS 0',	'VAN 0',	'MURCHISON 0',	'NACOGDOCHES 2 0',	'DIBOLL 0',	'FAIRFIELD 1 0',	'FAIRFIELD 1 1',	'FAIRFIELD 1 2',	'FAIRFIELD 1 3',	'FAIRFIELD 1 4',	'FAIRFIELD 1 5',	'FAIRFIELD 1 6',	'FAIRFIELD 1 7',	'FAIRFIELD 1 8',	'TYLER 8 0',	'ATHENS 1 0',	'BUFFALO 0',	'RUSK 0',	'WINONA 0',	'FAIRFIELD 2 0',	'FAIRFIELD 2 1',	'FAIRFIELD 2 2',	'FAIRFIELD 2 3',	'FAIRFIELD 2 4',	'CUSHING 2 0',	'NACOGDOCHES 3 0',	'FAIRFIELD 3 0',	'TRINIDAD 2 0',	'DIKE 0',	'JEWETT 1 0',	'JEWETT 1 1',	'JEWETT 1 2',	'JEWETT 1 3',	'JEWETT 1 4',	'PALESTINE 2 0',	'EMORY 0',	'MT. ENTERPRISE 0',	'MT. ENTERPRISE 1',	'MT. ENTERPRISE 2',	'MT. ENTERPRISE 3',	'MT. ENTERPRISE 4',	'MT. ENTERPRISE 5',	'MT. ENTERPRISE 6',	'TYLER 9 0',	'FRANKLIN 0',	'FRANKLIN 1',	'FRANKLIN 2',	'FRANKLIN 3',	'FRANKLIN 4',	'FRANKLIN 5',	'FRANKLIN 6',	'TYLER 3 0',	'ELKHART 0',	'WORTHAM 0',	'OAKWOOD 0',	'COOKVILLE 0',	'COLLEGE STATION 1 0',	'COLLEGE STATION 1 1',	'EDGEWOOD 0',	'CUSHING 1 0',	'CUSHING 1 1',	'CUSHING 1 2',	'TYLER 2 0',	'ALTO 0',	'CALVERT 0',	'JEWETT 2 0',	'NAVASOTA 0',	'MOUNT PLEASANT 2 0',	'MOUNT PLEASANT 2 1',	'SCROGGINS 0',	'WILLS POINT 0',	'ATHENS 2 0',	'POINT 0',	'LUFKIN 2 0',	'JACKSONVILLE 1 0',	'JACKSONVILLE 1 1',	'JACKSONVILLE 1 2',	'JACKSONVILLE 1 3',	'JACKSONVILLE 1 4',	'JACKSONVILLE 1 5',	'CROCKETT 0',	'HENDERSON 1 0',	'BRYAN 3 0',	'JACKSONVILLE 2 0',	'BRYAN 5 0',	'MALAKOFF 0',	'CUMBY 0',	'NACOGDOCHES 1 0',	'MOUNT PLEASANT 1 0',	'MOUNT PLEASANT 1 1',	'MOUNT PLEASANT 1 2',	'MOUNT PLEASANT 1 3',	'MOUNT PLEASANT 1 4',	'MOUNT PLEASANT 1 5',	'TEAGUE 0',	'TYLER 7 0',	'TYLER 7 1',	'TYLER 6 0',	'YANTIS 0',	'POLLOK 0',	'TYLER 1 0',	'COLLEGE STATION 2 0',	'COLLEGE STATION 2 1',	'HEARNE 0',	'MOUNT VERNON 0',	'IOLA 0',	'STREETMAN 0',	'COMO 0',	'HENDERSON 2 0',	'TRINIDAD 1 0',	'TRINIDAD 1 1',	'TRINIDAD 1 2',	'ZAVALLA 0',	'GRAPELAND 0',	'BRYAN 2 0',	'CANTON 0',	'TYLER 5 0',	'BREMOND 0',	'BREMOND 1',	'BREMOND 2',	'BRYAN 1 0',	'BRYAN 1 1',	'BRYAN 1 2']
#bus_df['BUS_NAME'] = bus_name
#bus_df.to_csv(data_path+'bus.csv')

kV_level = 230
bus_kVlevel_set = list(bus_df[bus_df['BASEKV']>=kV_level].index)
branch_kVlevel_set = [i for i in branch_df.index if branch_df.loc[i,'F_BUS'] in bus_kVlevel_set and branch_df.loc[i,'T_BUS'] in bus_kVlevel_set]
valid_id = branch_kVlevel_set
ptdf_df = pd.read_csv(data_path+'ptdf.csv',index_col=0) # for case 118
#valid_id = branch_df[branch_df.loc[:,'RATE_A']>=1500].index

#ptdf_df.columns = list(bus_df.index)
#ptdf_df.set_index(branch_df.index, inplace=True)
#ptdf_df.to_csv(data_path+'ptdf.csv')
ptdf_df = ptdf_df.loc[valid_id,:].copy()

gen_df['STARTUP_RAMP']  = gen_df[['STARTUP_RAMP','PMIN']].max(axis=1)
gen_df['SHUTDOWN_RAMP'] = gen_df[['SHUTDOWN_RAMP','PMIN']].max(axis=1)

wind_generator_names  =  [x for x in gen_df.index if x.startswith('wind')]

genth_df = pd.DataFrame(gen_df[gen_df['GEN_TYPE']=='Thermal'])

print('Finished loading data')

"""

#=============== FIRST TIME RUNNING THE CASE? RUN THIS SECTION +++++++++++++++++++++++++++++++++++

nn=6
margcost_df = pd.DataFrame([],index=genth_df.index, columns=[str(i) for i in range(1,nn)])


margcost_df['Pmax0']= genth_df['COST_0']
margcost_df['nlcost']= genth_df['COST_1']
gtherm=genth_df[['COST_'+str(i) for i in range(2*nn)]]
gtherm['nblock'] = list([(np.count_nonzero(np.array(gtherm.loc[i,'COST_1':]))-1)/2 for i in gtherm.index])
gtherm['one'] = 1
gtherm['zero'] = 0
for i in range(1,nn):
    gtherm.loc[:,'denom']= gtherm.loc[:,'COST_'+str(2*i)] - gtherm.loc[:,'COST_'+str(2*i-2)]
    gtherm.loc[:,'num']= gtherm.loc[:,'COST_'+str(2*i+1)] - gtherm.loc[:,'COST_'+str(2*i-1)]
    for j in gtherm.index:
        if (gtherm.loc[j,'COST_'+str(2*i+1)] - gtherm.loc[j,'COST_'+str(2*i-1)])>0:
            margcost_df.loc[j,str(i)]= gtherm.loc[j,'num']/ gtherm.loc[j,'denom']
            margcost_df.loc[j,'Pmax'+str(i)]= gtherm.loc[j,'COST_'+str(2*i)]
        else:
            margcost_df.loc[j,str(i)]= 0
            margcost_df.loc[j,'Pmax'+str(i)]= 0    
margcost_df.fillna(0, inplace=True)
margcost_df['nblock'] = gtherm['nblock']
margcost_df.clip_lower(0,inplace=True)
#uuu=[np.count_nonzero(np.array(margcost_df.loc[i,:])) for i in margcost_df.index]
#---------------------------
#gtherm.head()
#margcost_df.tail()

   
blockmargcost_df = margcost_df [[str(i) for i in range(1,nn)]].copy()

        
blockmaxoutput_df = margcost_df[['Pmax'+str(i) for i in range(nn)]].copy()
for i in blockmaxoutput_df.index:
    blockmaxoutput_df.loc[i,'Pmax'+str(gtherm.loc[i,'nblock'])] = genth_df.loc[i,'PMAX']


for i in range(1,nn):
    blockmaxoutput_df[str(i)] = margcost_df['Pmax'+str(i)] - margcost_df['Pmax'+str(i-1)]


blockmaxoutput_df.clip_lower(0,inplace=True) 
blockoutputlimit_df = blockmaxoutput_df[[str(i) for i in range(1,nn)]].copy()
blockoutputlimit_df.clip_lower(0,inplace=True) 


margcost_df.to_csv(data_path+'marginalcost.csv')
blockmargcost_df.to_csv(data_path+'blockmarginalcost.csv')
blockoutputlimit_df.to_csv(data_path+'blockoutputlimit.csv')
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

"""
margcost_df= pd.read_csv(data_path+'marginalcost.csv', index_col=0)
blockmargcost_df = pd.read_csv(data_path+'blockmarginalcost.csv', index_col=0)
blockoutputlimit_df = pd.read_csv(data_path+'blockoutputlimit.csv', index_col=0)

print('Creating dictionaries ...')

load_dict = dict()
load_s_df = load_df[load_df.columns.difference(['LOAD'])].copy()
columns = load_s_df.columns
for i, t in load_s_df.iterrows():
    for col in columns:
        load_dict[(col, i)] = t[col]
 
print('Start with the ptdf dictionary')
       
#ptdf_dict = dict()
#columns = ptdf_df.columns
#for i, t in ptdf_df.iterrows():
#    for col in columns:
#        ptdf_dict[(col, i)] = t[col]
        
        
ptdf_dict = ptdf_df.to_dict('index') # should be indexed ptdf_dict[l][b]
print('Done with the ptdf dictionary')
  

  
   
genforren_dict = dict()
columns = genforren_df.columns
for i, t in genforren_df.iterrows():
    for col in columns:
        genforren_dict[(col, i+1)] = t[col]

print('Done with the forecast dictionary')

blockmargcost_dict = dict()    
columns = blockmargcost_df.columns
for i, t in blockmargcost_df.iterrows():
    for col in columns:
        #print (i,t)
        blockmargcost_dict[(i,col)] = t[col]        

print('Done with the block marginal cost dictionary')

blockoutputlimit_dict = dict()
columns = blockoutputlimit_df.columns
for i, t in blockoutputlimit_df.iterrows():
    for col in columns:
        #print (i,t)
        blockoutputlimit_dict[(i,col)] = t[col]
print('Done with all dictionaries')
#================================================


#
# Reserve Parameters
FlexibleRampFactor = 0.1
ReserveFactor = 0.1
RegulatingReserveFactor = 0.1

#****************************************************************************************************************************************************#

# MODEL COMPONENTS

"""SETS & PARAMETERS"""
##########################################################
# string indentifiers for the sets of different types of generators. #
##########################################################
model.AllGenerators = Set(initialize=gen_df.index)
model.ThermalGenerators = Set(initialize=gen_df[gen_df['GEN_TYPE']=='Thermal'].index)
model.NonThermalGenerators = Set(initialize=gen_df[gen_df['GEN_TYPE']!='Thermal'].index)
model.RenewableGenerators = Set(initialize=gen_df[gen_df['GEN_TYPE']=='Renewable'].index)
model.HydroGenerators = Set(initialize=gen_df[gen_df['GEN_TYPE']=='Hydro'].index)
model.WindGenerators = Set(initialize=wind_generator_names)

##########################################################
# Set of Generator Blocks Set.                               #
##########################################################
model.Blocks = Set(initialize = blockmargcost_df.columns)
#model.GenNumBlocks = Param(model.ThermalGenerators, initialize=margcost_df['nblock'].to_dict())
model.BlockSize = Param(model.ThermalGenerators, model.Blocks, initialize=blockoutputlimit_dict)
##########################################################
# string indentifiers for the set of thermal generators buses. #
##########################################################

model.GenBuses = Param(model.AllGenerators, initialize=gen_df['GEN_BUS'].to_dict())

##########################################################
# string indentifiers for the set of load buses. #
##########################################################

model.LoadBuses = Set(initialize=load_s_df.columns)

##########################################################
# string indentifiers for the set of branches. #
##########################################################

model.Branches = Set(initialize=branch_df.index)
model.EnforcedBranches = Set(initialize=valid_id)

model.Buses = Set(initialize=bus_df.index)


#################################################################
# Line capacity limits: units are MW. #
#################################################################

model.LineLimits = Param(model.Branches, within=NonNegativeReals, initialize=branch_df['RATE_A'].to_dict())


#################################################################
# PTDF. #
#################################################################

#model.PTDF = Param(model.Buses, model.Branches, within=Reals, initialize=ptdf_dict)


###################################################
# the number of time periods under consideration, #
# in addition to the corresponding set.           #
###################################################

model.NumTimePeriods = Param(within=PositiveIntegers, initialize=len(load_df.index))

model.TimePeriods = RangeSet(1, model.NumTimePeriods)

#################################################################
# the global system demand, for each time period. units are MW. #
#################################################################

model.Demand = Param(model.TimePeriods, within=NonNegativeReals, initialize=load_df['LOAD'].to_dict())

#################################################################
# the bus-by-bus demand, for each time period. units are MW. #
#################################################################

model.BusDemand = Param(model.LoadBuses, model.TimePeriods, within=NonNegativeReals, initialize=load_dict)

# Power forecasts

model.PowerForecast = Param(model.NonThermalGenerators, model.TimePeriods, within=NonNegativeReals, initialize=genforren_dict)

##################################################################
# the global system reserve, for each time period. units are MW. #
##################################################################

model.ReserveRequirements = Param(model.TimePeriods, initialize=0.0, within=NonNegativeReals, default=0.0)

####################################################################################
# minimum and maximum generation levels, for each thermal generator. units are MW. #
# could easily be specified on a per-time period basis, but are not currently.     #
####################################################################################

model.MinimumPowerOutput = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=genth_df['PMIN'].to_dict())

def maximum_power_output_validator(m, v, g):
   return v >= value(m.MinimumPowerOutput[g])

model.MaximumPowerOutput = Param(model.ThermalGenerators, within=NonNegativeReals, validate=maximum_power_output_validator, initialize=genth_df['PMAX'].to_dict())

#################################################
# generator ramp up/down rates. units are MW/h. #
#################################################

# limits for normal time periods
model.NominalRampUpLimit = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=genth_df['RAMP_10'].to_dict())
model.NominalRampDownLimit = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=genth_df['RAMP_10'].to_dict())

# limits for time periods in which generators are brought on or off-line. 
# must be no less than the generator minimum output. 
def at_least_generator_minimum_output_validator(m, v, g):
   return v >= m.MinimumPowerOutput[g]

model.StartupRampLimit = Param(model.ThermalGenerators, within=NonNegativeReals, validate=at_least_generator_minimum_output_validator, initialize=genth_df['STARTUP_RAMP'].to_dict())
model.ShutdownRampLimit = Param(model.ThermalGenerators, within=NonNegativeReals, validate=at_least_generator_minimum_output_validator, initialize=genth_df['SHUTDOWN_RAMP'].to_dict())

##########################################################################################################
# the minimum number of time periods that a generator must be on-line (off-line) once brought up (down). #
##########################################################################################################

model.MinimumUpTime = Param(model.ThermalGenerators, within=NonNegativeIntegers, initialize=genth_df['MINIMUM_UP_TIME'].to_dict(), mutable=True)
model.MinimumDownTime = Param(model.ThermalGenerators, within=NonNegativeIntegers, initialize=genth_df['MINIMUM_DOWN_TIME'].to_dict(), mutable=True)

##############################################
# Flexible Ramping                           # 
##############################################

def _flexible_ramp_up_requirement_rule(m, t):
    if  t ==(len(m.TimePeriods)) :
        return max(0.0,(m.FlexibleRampFactor * sum(value(m.BusDemand[b,t]) for b in m.LoadBuses)))
    else:    
        return max(0.0,((1+m.FlexibleRampFactor) * sum(value(m.BusDemand[b,t+1]) for b in m.LoadBuses) - sum(value(m.BusDemand[b,t]) for b in m.LoadBuses)))

def _flexible_ramp_down_requirement_rule(m, t):
    if  t ==(len(m.TimePeriods)) :
        return max(0.0, (m.FlexibleRampFactor * sum(value(m.BusDemand[b,t]) for b in m.LoadBuses)))
    else:    
        return max(0.0, (sum(value(m.BusDemand[b,t]) for b in m.LoadBuses) - (1-m.FlexibleRampFactor) * sum(value(m.BusDemand[b,t+1]) for b in m.LoadBuses)) ) 

#def initialize_flexible_ramp(model, flexible_ramp_factor=0.0, flexible_ramp_Up_requirement=_flexible_ramp_up_requirement_rule, flexible_ramp_Dn_requirement=_flexible_ramp_down_requirement_rule):

model.FlexibleRampFactor = Param(within=Reals, initialize=FlexibleRampFactor, default=0.0, mutable=True)
model.FlexibleRampUpRequirement = Param(model.TimePeriods, initialize=_flexible_ramp_up_requirement_rule, within=Reals, default=0.0, mutable=True)    
model.FlexibleRampDnRequirement = Param(model.TimePeriods, initialize=_flexible_ramp_down_requirement_rule, within=Reals, default=0.0, mutable=True)       

#############################################
# unit on state at t=0 (initial condition). #
#############################################

# if positive, the number of hours prior to (and including) t=0 that the unit has been on.
# if negative, the number of hours prior to (and including) t=0 that the unit has been off.
# the value cannot be 0, by definition.

def t0_state_nonzero_validator(m, v, g):
    return v != 0

model.UnitOnT0State = Param(model.ThermalGenerators, within=Integers, validate=t0_state_nonzero_validator, initialize=genth_df['GEN_STATUS'].to_dict())

def t0_unit_on_rule(m, g):
    return value(m.UnitOnT0State[g]) >= 1

model.UnitOnT0 = Param(model.ThermalGenerators, within=Binary, initialize=t0_unit_on_rule)

#######################################################################################
# the number of time periods that a generator must initally on-line (off-line) due to #
# its minimum up time (down time) constraint.                                         #
#######################################################################################

def initial_time_periods_online_rule(m, g):
   if not value(m.UnitOnT0[g]):
      return 0
   else:
      return min(value(m.NumTimePeriods), \
                 max(0, \
                     value(m.MinimumUpTime[g]) - value(m.UnitOnT0State[g])))

model.InitialTimePeriodsOnLine = Param(model.ThermalGenerators, within=NonNegativeIntegers, initialize=initial_time_periods_online_rule)

def initial_time_periods_offline_rule(m, g):
   if value(m.UnitOnT0[g]):
      return 0
   else:
      return min(value(m.NumTimePeriods), \
                 max(0, \
                     value(m.MinimumDownTime[g]) + value(m.UnitOnT0State[g]))) # m.UnitOnT0State is negative if unit is off

model.InitialTimePeriodsOffLine = Param(model.ThermalGenerators, within=NonNegativeIntegers, initialize=initial_time_periods_offline_rule)

####################################################################
# generator power output at t=0 (initial condition). units are MW. #
####################################################################

model.PowerGeneratedT0 = Param(model.AllGenerators, within=NonNegativeReals, initialize=gen_df['PMIN'].to_dict())

##################################################################################################################
# production cost coefficients (for the quadratic) a0=constant, a1=linear coefficient, a2=quadratic coefficient. #
##################################################################################################################

#model.ProductionCostA0 = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=gen_df['COST_0'].to_dict()) # units are $/hr (or whatever the time unit is).
model.ProductionCostA1 = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=margcost_df['1'].to_dict()) # units are $/MWhr.
#model.ProductionCostA2 = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=gen_df['COST_2'].to_dict()) # units are $/(MWhr^2).
model.BlockMarginalCost = Param(model.ThermalGenerators, model.Blocks, within=NonNegativeReals, initialize=blockmargcost_dict)


##################################################################################
# shutdown and startup cost for each generator. in the literature, these are often set to 0. #
##################################################################################

model.ShutdownCostCoefficient = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=genth_df['STARTUP'].to_dict()) # units are $.

model.StartupCostCoefficient = Param(model.ThermalGenerators, within=NonNegativeReals, initialize=genth_df['SHUTDOWN'].to_dict()) # units are $.

#
################################################################################
# Spinning and Regulating Reserves
###############################################################################

def _reserve_requirement_rule(m, t):
    return m.ReserveFactor * sum(value(m.BusDemand[b,t]) for b in m.LoadBuses)

#def initialize_global_reserves(model, reserve_factor=0.0, reserve_requirement=_reserve_requirement_rule):

model.ReserveFactor = Param(within=Reals, initialize=ReserveFactor, default=0.0, mutable=True)
model.SpinningReserveRequirement = Param(model.TimePeriods, initialize=_reserve_requirement_rule, within=NonNegativeReals, default=0.0, mutable=True)

def _regulating_requirement_rule(m, t):
    return m.RegulatingReserveFactor * sum(value(m.BusDemand[b,t]) for b in m.LoadBuses)

#def initialize_regulating_reserves_requirement(model, regulating_reserve_factor=0.0, regulating_reserve_requirement=_regulating_requirement_rule):

model.RegulatingReserveFactor = Param(within=Reals, initialize=RegulatingReserveFactor, default=0.0, mutable=True)
model.RegulatingReserveRequirement = Param(model.TimePeriods, initialize=_regulating_requirement_rule, within=NonNegativeReals, default=0.0, mutable=True)
       


#*********************************************************************************************************************************************************#
"""VARIABLES"""
#==============================================================================
#  VARIABLE DEFINITION
#==============================================================================
#def initialize_flexible_ramp_reserves(model):
model.FlexibleRampUpAvailable = Var(model.ThermalGenerators | model.WindGenerators, model.TimePeriods, initialize=0.0, within=NonNegativeReals)
model.FlexibleRampDnAvailable = Var(model.ThermalGenerators | model.WindGenerators, model.TimePeriods, initialize=0.0, within=NonNegativeReals)
    
#def initialize_regulating_reserves(model):
model.RegulatingReserveUpAvailable = Var(model.ThermalGenerators, model.TimePeriods, initialize=0.0, within=NonNegativeReals)    
model.RegulatingReserveDnAvailable = Var(model.ThermalGenerators, model.TimePeriods, initialize=0.0, within=NonNegativeReals)    

#def initialize_spinning_reserves(model):
model.SpinningReserveUpAvailable = Var(model.AllGenerators, model.TimePeriods, initialize=0.0, within=NonNegativeReals)



# indicator variables for each generator, at each time period.
model.UnitOn = Var(model.ThermalGenerators, model.TimePeriods, within=Binary,initialize=0)

# amount of power produced by each generator, at each time period.
model.PowerGenerated = Var(model.AllGenerators, model.TimePeriods, within=NonNegativeReals, initialize=0.0)
# amount of power produced by each generator, in each block, at each time period.
model.BlockPowerGenerated = Var(model.ThermalGenerators, model.Blocks, model.TimePeriods, within=NonNegativeReals, initialize=0.0)

# maximum power output for each generator, at each time period.
model.MaximumPowerAvailable = Var(model.AllGenerators, model.TimePeriods, within=NonNegativeReals, initialize=0.0)

###################
# cost components #
###################

# production cost associated with each generator, for each time period.
model.ProductionCost = Var(model.ThermalGenerators, model.TimePeriods, within=NonNegativeReals, initialize=0.0)

# startup and shutdown costs for each generator, each time period.
model.StartupCost = Var(model.ThermalGenerators, model.TimePeriods, within=NonNegativeReals, initialize=0.0)
model.ShutdownCost = Var(model.ThermalGenerators, model.TimePeriods, within=NonNegativeReals, initialize=0.0)

# cost over all generators, for all time periods.
model.TotalProductionCost = Var(within=NonNegativeReals, initialize=0.0)

# all other overhead / fixed costs, e.g., associated with startup and shutdown.
model.TotalFixedCost = Var(within=NonNegativeReals, initialize=0.0)


#*****************************************************************************************************************************************************#
"""CONSTRAINTS"""
#==============================================================================
# CONSTRAINTS
#==============================================================================


############################################
# supply-demand constraints                #
############################################
# meet the demand at each time period.
# encodes Constraint 2 in Carrion and Arroyo.
def production_equals_demand_rule(m, t):
   return sum(m.PowerGenerated[g, t] for g in m.AllGenerators)  == m.Demand[t]

model.ProductionEqualsDemand = Constraint(model.TimePeriods, rule=production_equals_demand_rule)


############################################
# generation limit and ramping constraints #
############################################

# enforce the generator power output limits on a per-period basis.
# the maximum power available at any given time period is dynamic,
# bounded from above by the maximum generator output.

# the following three constraints encode Constraints 16 and 17 defined in Carrion and Arroyo.

# NOTE: The expression below is what we really want - however, due to a pyomo bug, we have to split it into two constraints:
# m.MinimumPowerOutput[g] * m.UnitOn[g, t] <= m.PowerGenerated[g,t] <= m.MaximumPowerAvailable[g, t]
# When fixed, merge back parts "a" and "b", leaving two constraints.

def enforce_generator_output_limits_rule_part_a(m, g, t):
   return m.MinimumPowerOutput[g] * m.UnitOn[g, t] <= m.PowerGenerated[g,t]

model.EnforceGeneratorOutputLimitsPartA = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_generator_output_limits_rule_part_a)

def enforce_generator_output_limits_rule_part_b(m, g, t):
   return m.PowerGenerated[g,t] <= m.MaximumPowerAvailable[g, t]

model.EnforceGeneratorOutputLimitsPartB = Constraint(model.AllGenerators, model.TimePeriods, rule=enforce_generator_output_limits_rule_part_b)

def enforce_generator_output_limits_rule_part_c(m, g, t):
   return m.MaximumPowerAvailable[g, t] <= m.MaximumPowerOutput[g] * m.UnitOn[g, t]

model.EnforceGeneratorOutputLimitsPartC = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_generator_output_limits_rule_part_c)


def enforce_generator_block_output_rule(m, g, t):
   return m.PowerGenerated[g, t] == sum(m.BlockPowerGenerated[g,k,t] for k in m.Blocks) + m.UnitOn[g,t]*margcost_df.loc[g,'Pmax0']

model.EnforceGeneratorBlockOutput = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_generator_block_output_rule)

def enforce_generator_block_output_limit_rule(m, g, k, t):
   return m.BlockPowerGenerated[g,k,t] <= m.BlockSize[g,k]

model.EnforceGeneratorBlockOutputLimit = Constraint(model.ThermalGenerators, model.Blocks, model.TimePeriods, rule=enforce_generator_block_output_limit_rule)


def enforce_renewable_generator_output_limits_rule(m, g, t):
   return  m.PowerGenerated[g, t]<= m.PowerForecast[g,t]

model.EnforceRenewableOutputLimits = Constraint(model.NonThermalGenerators, model.TimePeriods, rule=enforce_renewable_generator_output_limits_rule)

# impose upper bounds on the maximum power available for each generator in each time period, 
# based on standard and start-up ramp limits.

# the following constraint encodes Constraint 18 defined in Carrion and Arroyo.

def enforce_max_available_ramp_up_rates_rule(m, g, t):
   # 4 cases, split by (t-1, t) unit status (RHS is defined as the delta from m.PowerGenerated[g, t-1])
   # (0, 0) - unit staying off:   RHS = maximum generator output (degenerate upper bound due to unit being off) 
   # (0, 1) - unit switching on:  RHS = startup ramp limit 
   # (1, 0) - unit switching off: RHS = standard ramp limit minus startup ramp limit plus maximum power generated (degenerate upper bound due to unit off)
   # (1, 1) - unit staying on:    RHS = standard ramp limit
   if t == 1:
      return m.MaximumPowerAvailable[g, t] - m.RegulatingReserveUpAvailable[g,t] - m.SpinningReserveUpAvailable[g,t] <= \
                  m.PowerGeneratedT0[g] +  m.NominalRampUpLimit[g] * m.UnitOnT0[g] + \
                                              m.StartupRampLimit[g] * (m.UnitOn[g, t] - m.UnitOnT0[g]) + \
                                              m.MaximumPowerOutput[g] * (1 - m.UnitOn[g, t])
   else:
      return m.MaximumPowerAvailable[g, t] -m.RegulatingReserveUpAvailable[g,t] - m.SpinningReserveUpAvailable[g,t] <= \
                  m.PowerGenerated[g, t-1] + m.NominalRampUpLimit[g] * m.UnitOn[g, t-1] + \
                                              m.StartupRampLimit[g] * (m.UnitOn[g, t] - m.UnitOn[g, t-1]) + \
                                              m.MaximumPowerOutput[g] * (1 - m.UnitOn[g, t])

model.EnforceMaxAvailableRampUpRates = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_max_available_ramp_up_rates_rule)

# the following constraint encodes Constraint 19 defined in Carrion and Arroyo.

def enforce_max_available_ramp_down_rates_rule(m, g, t):
   # 4 cases, split by (t, t+1) unit status
   # (0, 0) - unit staying off:   RHS = 0 (degenerate upper bound)
   # (0, 1) - unit switching on:  RHS = maximum generator output minus shutdown ramp limit (degenerate upper bound) - this is the strangest case.
   # (1, 0) - unit switching off: RHS = shutdown ramp limit
   # (1, 1) - unit staying on:    RHS = maximum generator output (degenerate upper bound)
   if t == value(m.NumTimePeriods):
      return Constraint.Skip
   else:
      return m.MaximumPowerAvailable[g, t] <= \
             m.MaximumPowerOutput[g] * m.UnitOn[g, t+1] + \
             m.ShutdownRampLimit[g] * (m.UnitOn[g, t] - m.UnitOn[g, t+1])

model.EnforceMaxAvailableRampDownRates = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_max_available_ramp_down_rates_rule)

# the following constraint encodes Constraint 20 defined in Carrion and Arroyo.

def enforce_ramp_down_limits_rule(m, g, t):
   # 4 cases, split by (t-1, t) unit status: 
   # (0, 0) - unit staying off:   RHS = maximum generator output (degenerate upper bound)
   # (0, 1) - unit switching on:  RHS = standard ramp-down limit minus shutdown ramp limit plus maximum generator output - this is the strangest case.
   # (1, 0) - unit switching off: RHS = shutdown ramp limit 
   # (1, 1) - unit staying on:    RHS = standard ramp-down limit 
   if t == 1:
      return m.PowerGeneratedT0[g] - m.PowerGenerated[g, t] - m.RegulatingReserveDnAvailable[g,t] <= \
             m.NominalRampDownLimit[g] * m.UnitOn[g, t] + \
             m.ShutdownRampLimit[g] * (m.UnitOnT0[g] - m.UnitOn[g, t]) + \
             m.MaximumPowerOutput[g] * (1 - m.UnitOnT0[g])                
   else:
      return m.PowerGenerated[g, t-1] - m.PowerGenerated[g, t] - m.RegulatingReserveDnAvailable[g,t] <= \
             m.NominalRampDownLimit[g] * m.UnitOn[g, t] + \
             m.ShutdownRampLimit[g] * (m.UnitOn[g, t-1] - m.UnitOn[g, t]) + \
             m.MaximumPowerOutput[g] * (1 - m.UnitOn[g, t-1])             

model.EnforceNominalRampDownLimits = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_ramp_down_limits_rule)

#############################################
# constraints for computing cost components #
#############################################
# New ADDITION
def production_cost_function(m, g, t):
    return m.ProductionCost[g,t] == value(m.ProductionCostA1[g])*(m.PowerGenerated[g,t])
#model.ComputeProductionCost = Constraint(model.ThermalGenerators, model.TimePeriods, rule=production_cost_function)

def production_cost_function(m, g, t):
    return m.ProductionCost[g,t] == sum(value(m.BlockMarginalCost[g,k])*(m.BlockPowerGenerated[g,k,t]) for k in m.Blocks) + m.UnitOn[g,t]*margcost_df.loc[g,'nlcost']
model.ComputeProductionCost = Constraint(model.ThermalGenerators, model.TimePeriods, rule=production_cost_function)
#---------------------------------------

# compute the per-generator, per-time period production costs. this is a "simple" piecewise linear construct.
# the first argument to piecewise is the index set. the second and third arguments are respectively the input and output variables. 
"""
model.ComputeProductionCosts = Piecewise(model.ThermalGenerators * model.TimePeriods, model.ProductionCost, model.PowerGenerated, pw_pts=model.PowerGenerationPiecewisePoints, f_rule=production_cost_function, pw_constr_type='LB')
"""
# compute the total production costs, across all generators and time periods.
def compute_total_production_cost_rule(m):
   return m.TotalProductionCost == sum(m.ProductionCost[g, t] for g in m.ThermalGenerators for t in m.TimePeriods)

model.ComputeTotalProductionCost = Constraint(rule=compute_total_production_cost_rule)

# compute the per-generator, per-time period shutdown costs.
def compute_shutdown_costs_rule(m, g, t):
   if t is 1:
      return m.ShutdownCost[g, t] >= m.ShutdownCostCoefficient[g] * (m.UnitOnT0[g] - m.UnitOn[g, t])
   else:
      return m.ShutdownCost[g, t] >= m.ShutdownCostCoefficient[g] * (m.UnitOn[g, t-1] - m.UnitOn[g, t])

model.ComputeShutdownCosts = Constraint(model.ThermalGenerators, model.TimePeriods, rule=compute_shutdown_costs_rule)



def compute_startup_costs_rule(m, g, t):
   if t is 1:
      return m.StartupCost[g, t] >= m.StartupCostCoefficient[g] * (-m.UnitOnT0[g] + m.UnitOn[g, t])
   else:
      return m.StartupCost[g, t] >= m.StartupCostCoefficient[g] * (-m.UnitOn[g, t-1] + m.UnitOn[g, t])

model.ComputeStartupCosts = Constraint(model.ThermalGenerators, model.TimePeriods, rule=compute_startup_costs_rule)

# compute the total startup and shutdown costs, across all generators and time periods.
def compute_total_fixed_cost_rule(m):
   return m.TotalFixedCost == sum(m.StartupCost[g, t] + m.ShutdownCost[g, t]  for g in m.ThermalGenerators for t in m.TimePeriods)

model.ComputeTotalFixedCost = Constraint(rule=compute_total_fixed_cost_rule)

#*****

#############################################
# constraints for line capacity limits #
#############################################

print('Building network constraints ...')

def enforce_line_capacity_limits_rule_a(m, l, t):
    return sum(ptdf_dict[l][m.GenBuses[g]]*m.PowerGenerated[g,t] for g in m.AllGenerators) - \
           sum(ptdf_dict[l][b]*m.BusDemand[b,t] for b in m.LoadBuses) <= m.LineLimits[l]

model.EnforceLineCapacityLimitsA = Constraint(model.EnforcedBranches, model.TimePeriods, rule=enforce_line_capacity_limits_rule_a)   
    
def enforce_line_capacity_limits_rule_b(m, l, t):
    return sum(ptdf_dict[l][m.GenBuses[g]]*m.PowerGenerated[g,t] for g in m.AllGenerators) - \
           sum(ptdf_dict[l][b]*m.BusDemand[b,t] for b in m.LoadBuses) >= -m.LineLimits[l]
#           
model.EnforceLineCapacityLimitsB = Constraint(model.EnforcedBranches, model.TimePeriods, rule=enforce_line_capacity_limits_rule_b)


#######################
# up-time constraints #
#######################

# constraint due to initial conditions.
def enforce_up_time_constraints_initial(m, g):
   if value(m.InitialTimePeriodsOnLine[g]) is 0:
      return Constraint.Skip
   return sum((1 - m.UnitOn[g, t]) for g in m.ThermalGenerators for t in m.TimePeriods if t <= value(m.InitialTimePeriodsOnLine[g])) == 0.0

model.EnforceUpTimeConstraintsInitial = Constraint(model.ThermalGenerators, rule=enforce_up_time_constraints_initial)

# constraint for each time period after that not involving the initial condition.
def enforce_up_time_constraints_subsequent(m, g, t):
   if t <= value(m.InitialTimePeriodsOnLine[g]):
      # handled by the EnforceUpTimeConstraintInitial constraint.
      return Constraint.Skip
   elif t <= (value(m.NumTimePeriods) - value(m.MinimumUpTime[g]) + 1):
      # the right-hand side terms below are only positive if the unit was off in the previous time period but on in this one =>
      # the value is the minimum number of subsequent consecutive time periods that the unit is required to be on.
      if t is 1:
         return sum(m.UnitOn[g, n] for n in m.TimePeriods if n >= t and n <= (t + value(m.MinimumUpTime[g]) - 1)) >= \
                (m.MinimumUpTime[g] * (m.UnitOn[g, t] - m.UnitOnT0[g]))
      else:
         return sum(m.UnitOn[g, n] for n in m.TimePeriods if n >= t and n <= (t + value(m.MinimumUpTime[g]) - 1)) >= \
                (m.MinimumUpTime[g] * (m.UnitOn[g, t] - m.UnitOn[g, t-1]))
   else:
      # handle the final (MinimumUpTime[g] - 1) time periods - if a unit is started up in 
      # this interval, it must remain on-line until the end of the time span.
      if t == 1: # can happen when small time horizons are specified
         return sum((m.UnitOn[g, n] - (m.UnitOn[g, t] - m.UnitOnT0[g])) for n in m.TimePeriods if n >= t) >= 0.0
      else:
         return sum((m.UnitOn[g, n] - (m.UnitOn[g, t] - m.UnitOn[g, t-1])) for n in m.TimePeriods if n >= t) >= 0.0

model.EnforceUpTimeConstraintsSubsequent = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_up_time_constraints_subsequent)

#########################
# down-time constraints #
#########################

# constraint due to initial conditions.
def enforce_down_time_constraints_initial(m, g):
   if value(m.InitialTimePeriodsOffLine[g]) is 0: 
      return Constraint.Skip
   return sum(m.UnitOn[g, t] for g in m.ThermalGenerators for t in m.TimePeriods if t <= value(m.InitialTimePeriodsOffLine[g])) == 0.0

model.EnforceDownTimeConstraintsInitial = Constraint(model.ThermalGenerators, rule=enforce_down_time_constraints_initial)

# constraint for each time period after that not involving the initial condition.
def enforce_down_time_constraints_subsequent(m, g, t):
   if t <= value(m.InitialTimePeriodsOffLine[g]):
      # handled by the EnforceDownTimeConstraintInitial constraint.
      return Constraint.Skip
   elif t <= (value(m.NumTimePeriods) - value(m.MinimumDownTime[g]) + 1):
      # the right-hand side terms below are only positive if the unit was off in the previous time period but on in this one =>
      # the value is the minimum number of subsequent consecutive time periods that the unit is required to be on.
      if t is 1:
         return sum((1 - m.UnitOn[g, n]) for n in m.TimePeriods if n >= t and n <= (t + value(m.MinimumDownTime[g]) - 1)) >= \
                (m.MinimumDownTime[g] * (m.UnitOnT0[g] - m.UnitOn[g, t]))
      else:
         return sum((1 - m.UnitOn[g, n] for n in m.TimePeriods if n >= t and n <= (t + value(m.MinimumDownTime[g]) - 1))) >= \
                (m.MinimumDownTime[g] * (m.UnitOn[g, t-1] - m.UnitOn[g, t]))
   else:
      # handle the final (MinimumDownTime[g] - 1) time periods - if a unit is shut down in
      # this interval, it must remain off-line until the end of the time span.
      if t == 1: # can happen when small time horizons are specified
         return sum(((1 - m.UnitOn[g, n]) - (m.UnitOnT0[g] - m.UnitOn[g, t])) for n in m.TimePeriods if n >= t) >= 0.0
      else:
         return sum(((1 - m.UnitOn[g, n]) - (m.UnitOn[g, t-1] - m.UnitOn[g, t])) for n in m.TimePeriods if n >= t) >= 0.0

model.EnforceDownTimeConstraintsSubsequent = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_down_time_constraints_subsequent)

##--------------------------------------------------------------------------------------------------
def enforce_wind_generator_output_limits_b(m, g, t):
   return m.PowerGenerated[g,t]    - m.FlexibleRampDnAvailable[g,t]     >= 0 

def enforce_wind_generator_output_limits_a(m, g, t):
   return m.PowerGenerated[g,t]    + m.FlexibleRampUpAvailable[g,t]  <= m.MaximumPowerAvailable[g,t]

#add flexible ramp constraint        
def enforce_flexible_ramp_up_requirement_rule(m, t):
    return sum(m.FlexibleRampUpAvailable[g,t] for g in (m.ThermalGenerators  |m.WindGenerators)) >= m.FlexibleRampUpRequirement[t]  
  
def enforce_flexible_ramp_down_requirement_rule(m, t):
    return sum(m.FlexibleRampDnAvailable[g,t] for g in (m.ThermalGenerators  |m.WindGenerators)) >= m.FlexibleRampDnRequirement[t]    

def enforce_flexible_ramp_down_limits_rule(m, g, t):
    if t < (len(m.TimePeriods)):
        return  m.PowerGenerated[g, t] - m.FlexibleRampDnAvailable[g,t] >= m.MinimumPowerOutput[g] * m.UnitOn[g, t+1]
    else:
       return m.PowerGenerated[g, t] - m.FlexibleRampDnAvailable[g,t] >= m.MinimumPowerOutput[g] * m.UnitOn[g, t]

def enforce_flexible_ramp_up_limits_rule(m, g, t):
    if t < (len(m.TimePeriods)):
        return m.PowerGenerated[g, t] + m.FlexibleRampUpAvailable[g,t] <= m.MaximumPowerAvailable[g, t+1]
    else:
        return m.PowerGenerated[g, t] + m.FlexibleRampUpAvailable[g,t] <= m.MaximumPowerAvailable[g, t]
    
#def constraint_for_Flexible_Ramping(model):
model.EnforceFlexibleRampUpRates = Constraint(model.TimePeriods, rule=enforce_flexible_ramp_up_requirement_rule)
model.EnforceFlexibleRampDownRates = Constraint(model.TimePeriods, rule=enforce_flexible_ramp_down_requirement_rule)
model.EnforceFlexibleRampDownLimits = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_flexible_ramp_down_limits_rule)
model.EnforceFlexibleRampUpLimits = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_flexible_ramp_up_limits_rule)    
model.EnforceWindFlexibleRampUpLimits = Constraint(model.WindGenerators, model.TimePeriods, rule=enforce_wind_generator_output_limits_a)    
model.EnforceWindFlexibleRampDnLimits = Constraint(model.WindGenerators, model.TimePeriods, rule=enforce_wind_generator_output_limits_b)    
#---------------------------------------------------------------

# ensure there is sufficient maximal power output available to meet both the 
# demand and the spinning reserve requirements in each time period.
# encodes Constraint 3 in Carrion and Arroyo.
def enforce_reserve_requirements_rule(m, t):
   return sum(m.MaximumPowerAvailable[g, t] for g in m.AllGenerators) >= m.Demand[t] + m.RegulatingReserveRequirement[t] + m.SpinningReserveRequirement[t]

model.EnforceReserveRequirements = Constraint(model.TimePeriods, rule=enforce_reserve_requirements_rule)



###
def calculate_spinning_reserve_up_available_per_generator(m, g, t):
    return m.SpinningReserveUpAvailable[g, t]  <= m.MaximumPowerAvailable[g,t] - m.PowerGenerated[g,t]

def enforce_spinning_reserve_requirement_rule(m,  t):
    return sum(m.SpinningReserveUpAvailable[g,t] for g in m.ThermalGenerators) >= m.SpinningReserveRequirement[t]

def enforce_SpinningReserve_up_reserve_limit(m, g, t):
     return m.SpinningReserveUpAvailable[g,t]  <= m.UnitOn[g, t]*m.NominalRampUpLimit[g]/6 # 10 minutes

def enforce_regulating_up_reserve_requirement_rule(m, t):
     return sum(m.RegulatingReserveUpAvailable[g,t] for g in m.ThermalGenerators) >= m.RegulatingReserveRequirement[t]
 
def enforce_regulating_down_reserve_requirement_rule(m, t):
     return sum(m.RegulatingReserveDnAvailable[g,t] for g in m.ThermalGenerators) >= m.RegulatingReserveRequirement[t]


def enforce_regulating_up_reserve_limit(m, g, t):
     return m.RegulatingReserveUpAvailable[g,t]  <= m.UnitOn[g, t]*m.NominalRampUpLimit[g]/6

def enforce_regulating_down_reserve_limit(m, g, t):
     return m.RegulatingReserveDnAvailable[g,t]  <= m.UnitOn[g, t]*m.NominalRampUpLimit[g]/6



model.CalculateRegulatingReserveUpPerGenerator = Constraint(model.ThermalGenerators, model.TimePeriods, rule=calculate_spinning_reserve_up_available_per_generator)
model.EnforceSpinningReserveUp = Constraint(model.TimePeriods, rule=enforce_spinning_reserve_requirement_rule) 
model.EnforceRegulatingUpReserveRequirements = Constraint(model.TimePeriods, rule=enforce_regulating_up_reserve_requirement_rule)
model.EnforceRegulatingDnReserveRequirements = Constraint(model.TimePeriods, rule=enforce_regulating_down_reserve_requirement_rule)  
model.EnforceSpiningReserveRates = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_SpinningReserve_up_reserve_limit)    
model.EnforceRegulationUpRates = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_regulating_up_reserve_limit)  
model.EnforceRegulationDnRates = Constraint(model.ThermalGenerators, model.TimePeriods, rule=enforce_regulating_down_reserve_limit)    
#------------------------------------------------------

#

# Objectives
#

def total_cost_objective_rule(m):
   return m.TotalProductionCost + m.TotalFixedCost


model.TotalCostObjective = Objective(rule=total_cost_objective_rule, sense=minimize)


