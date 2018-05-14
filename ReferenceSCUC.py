# -*- coding: utf-8 -*-
"""
Created on Thu May  3 13:09:02 2018

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

data_path = '.../Data_Repository/'

print('loading data ...')

gen_df = pd.read_csv(data_path+'generator_data_plexos_withRT.csv',index_col=0)

"""
Scaling Wind Generation to achieve different penetration levels
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

branch_df = pd.read_csv(data_path+'branch.csv',index_col=['BR_ID'])

bus_df = pd.read_csv(data_path+'bus.csv',index_col=['BUS_ID'])

ptdf_df = pd.read_csv(data_path+'ptdf.csv',index_col=0) # for case 118
valid_id = branch_df[branch_df.loc[:,'RATE_A']>=1500].index

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


