# flux_exchange_mod

Flux_exchange_mod is the top level module for flux exchange between components.

## variables

| Name | Type | Definition |
|------|------|------------|
| version | character(len=128) | is the program version string set automatically at compile time. |
| tag | character(len=128) | is a string set automatically at compile time. |
| do_init | logical | is a flag where if .TRUE., initialize module |
| bound_tol | real, parameter | is the tolerance value used when checking grid-boundary coordinate consistency. |
| d622 | real, parameter | is the ratio of dry-air and water-vapor gas constants. |
| d378 | real, parameter | is the complement of d622, used in humidity conversions. |
| z_ref_heat | real | is the reference height [m] for temperature and relative humidity diagnostics (t_ref, rh_ref, del_h, del_q). |
| z_ref_mom | real | is the reference height [m] for momentum diagnostics (u_ref, v_ref, del_m). |
| do_area_weighted_flux | logical | is a flag where if .TRUE., normalize exchanged fluxes by the area. used in ice_ocean_flux_exchange. |
| debug_stocks | logical | is a flag where if .TRUE., enable extra stock-conservation output for debugging. |
| divert_stocks_report | logical | is a flag where if .TRUE., write stock reports 'stocks.out'. |
| do_runoff | logical | is a flag where if .TRUE., turn on the land runoff interpolation to the ocean |
| do_forecast | logical | is a flag. |
| nblocks | integer | is the number of OpenMP blocks, defaults to 1. |
| partition_fprec_from_lprec | logical | is a flag where if .TRUE., convert liquid precip to snow when t_ref is less than tfreeze parameter |
| tfreeze | real, parameter | Freezing point of water at one atmosphere in [K]. |
| scale_precip_2d | logical | is a flag where if .TRUE., rescale liquid precipitation using a 2-D field from data override. |
| gas_fluxes_initialized | logical | is a flag where if .TRUE., component fluxes have been initialized. |
| ex_gas_fields_atm | type(fmscoupler1dbc_type), target | is a derived type containing atmospheric surface variables that are used in calculating atmosphere-ocean gas fluxes. |
| ex_gas_fields_ice | type(fmscoupler1dbc_type), target | is a derived type containing ice-top and ocean surface variables that are used in calculating atmosphere-ocean gas fluxes. |
| ex_gas_fluxes | type(fmscoupler1dbc_type), target | is a derived type for exchanging gas or tracer fluxes between the atmosphere and ocean, defined by the field table. Also a place holder of intermediate calculations. |
| ni_atm | integer | is the number of x gridpoints in the atm compute domain |
| nj_atm | integer | is the number of y gridpoints in the atm compute domain |
| ccc | real, dimension(3) | is a temporary array used for conservation-check summaries; not used. |
| cplclock | integer | is the FMS clock id to profile land-ice-atmos coupler. |
| dt_atm | real | is the atmosphere timestep [s] |
| dt_cpl | real | is the coupled timesteps in [s]. |
| atm_precip_new | real | is used to take into account implicit evaporation in stock computation |


## gas_exchange_init
### intro
Flux_exchange_mod is the top level module for flux exchange between components.  gas_exchange_init is a subroutine in flux_exchange_mod.
### description
  Subroutine gas_exchange_init initializes the fms_atmos_ocean_type_fluxes, ocean_model_fluxes, and atmos_tracer_flux. The subroutine also calls fms_atmos_ocean_fluxes to initialize ex_gas_fluxes and fields.
### arguments
| Name | Type | Subroutine | Definition |
|------|------|------------|------------|
| gas_fields_atm | intent(inout) | gas_exchange_init | is a derived type containing atmospheric surface variables that are used in the calculation of the atmosphere-ocean gas fluxes. |
| gas_fields_ice | intent(inout) | gas_exchange_init | is a derived type containing ice-top and ocean surface variables that are used in the calculation of the atmosphere-ocean gas fluxes. |
| gas_fluxes | intent(inout) | gas_exchange_init | is a derived type for exchanging gas or tracer fluxes between the atmosphere and ocean, defined by the field table, as well as a place holder of intermediate calculations, such as piston velocities, and parameters that impact the fluxes. |

### flowchart
gas_exchange_init does the following:  
Step 1: CALL ATMOS_TRACER_FLUX_INIT(), OCEAN_MODEL_FLUX_INIT(), ATMOS_TRACER_FLUX_INIT(). ALSO CALLS FMS_ATMOS_OCEAN_FLUXES_INIT() TO ALLOCATE DERIVED TYPES.
Step 2: SET MODULE LEVEL GAS_FIELDS_ATM, GAS_FIELDS_ICE, AND GAS_FLUXES.


## flux_exchange_init
### intro
Flux_exchange_mod is the top level module for flux exchange between components.  flux_exchange_init is a subroutine in flux_exchange_mod.
### description
  Subroutine flux_exchange_init setups derived types, variables, and initializes modules that will be used in flux calculation and exchange. Ocean_tracer_flux_init is called first to get restart filenames for tracer fluxes for restart model runs. Atmos_tracer_flux_init is called last in order to use tracer values set in ocean_tracer_flux_init.
### arguments
| Name | Type | Subroutine | Definition |
|------|------|------------|------------|
| time | intent(inout) | flux_exchange_init | is the model current time |
| atm | intent(inout) | flux_exchange_init | is a derived type to specify atmosphere boundary data |
| land | intent(inout) | flux_exchange_init | is a derived type to specify land boundary data |
| ice | intent(inout) | flux_exchange_init | is a derived type to specify ice boundary data |
| ocean | intent(inout) | flux_exchange_init | is a derived type to specify ocean boundary data |
| ocean_state | intent(inout) | flux_exchange_init | is a pointer to the ocean model's internal state |
| atmos_ice_boundary | intent(inout) | flux_exchange_init | is a derived type holding properties and fluxes passed from atmosphere to ice |
| land_ice_atmos_boundary | intent(inout) | flux_exchange_init | is a derived type holding properties and fluxes passed from exchange grid between atm, land, and ice |
| land_ice_boundary | intent(inout) | flux_exchange_init | is a derived type holding properties and fluxes passed from land to ice |
| ice_ocean_boundary | intent(inout) | flux_exchange_init | is a derived type holding properties and fluxes passed from ice to ocean |
| ocean_ice_boundary | intent(inout) | flux_exchange_init | is a derived type holding properties and fluxes passed from ocean to ice |
| do_ocean | intent(inout) | flux_exchange_init | is a flag indicating whether the ocean component is active |
| slow_ice_ocean_pelist | intent(inout) | flux_exchange_init | is an array holding pes for slow ice-ocean exchange |
| dt_atmos | intent(inout) | flux_exchange_init | is the atmosphere time step in [s] |
| dt_cpld | intent(inout) | flux_exchange_init | is the coupled time step in [s] |

### flowchart
flux_exchange_init does the following:  
Step 1: CALL FMS_SAT_VAPOR_PRES_INIT.
Step 2: SETUP OPENMP PARAMETERS.
Step 3: SET LOGFILE.
Step 4: READ FLUX_EXCHANGE_NML.
Step 5: WRITE NAMELIST TO LOGFILE.
Step 6: SET MODULE LEVEL DT_ATM AND DT_CPL TIMESTEPS.
Step 7: GET OCEAN MODEL GRID CELL AREAS FROM GRID_SPEC.
Step 8: IF ATMPE, CALL ATM_LAND_ICE_FLUX_EXCHANGE_INIT() AND LAND_ICE_FLUX_EXCHANGE_INIT() ALSO CHECK ATM_GRID CONSISTENCY WITH PROVIDED GRID_SPEC.
Step 9: CALL ICE_OCEAN_FLUX_EXCHANGE_INIT().
Step 10: SET DO_INIT TO .FALSE. TO SKIP INITIALIZATION IF FLUX_EXCHANGE_INIT IS CALLED AGAIN.


## flux_check_stocks
### intro
Flux_exchange_mod is the top level module for flux exchange between components.  flux_check_stocks is a subroutine in flux_exchange_mod.
### description
  Subroutine flux_check_stocks computes the current stock values for atm, land, ice, and ocean; and outputs the stock differences with respect to the initial values in the logfile.
### arguments
| Name | Type | Subroutine | Definition |
|------|------|------------|------------|
| time | intent(inout) | flux_check_stocks | is the model's current time |
| atm | intent(inout) | flux_check_stocks | is the atmosphere boundary data type used to compute atmosphere stocks |
| lnd | intent(inout) | flux_check_stocks | is the land boundary data type used to compute land stocks |
| ice | intent(inout) | flux_check_stocks | is the ice boundary data type used to compute ice stocks |
| ocn_state | intent(inout) | flux_check_stocks | is a pointer to the ocean model's internal state used to compute ocean stocks |

### flowchart
flux_check_stocks does the following:  
Step 1: FOR WATER, HEAT, AND SALT STOCKS FOR EACH COMPONENT, GET CURRENT STOCK VALUE AND COMPARE WITH INTEGRATED FLUXES FOR ATM WATER STOCK. FOR ATM, INTEGRATE ATM_PRECIP_NEW FOR IMPLICIT EVAPORATION.
Step 2: PRINT FOR EACH ELEMENT, S(t): TOTAL STOCK, S(t)-S(0): CHANGE IN STOCK WITH RESPECT TO INITIAL VALUE, F(t): CUMULATIVE FLUX INTO COMPONENT FROM OTHER COMPONENTS F(t) - [S(t)-S(0)]: DIFFERENCE BETWEEN THE FLUXES AND STOCK CHANGE (S(t)-S(0))/F(t): RELATIVE ERROR


## flux_init_stocks
### intro
Flux_exchange_mod is the top level module for flux exchange between components.  flux_init_stocks is a subroutine in flux_exchange_mod.
### description
  Subroutine flux_init_stocks initializes the stock values for the atmosphere, land, ice, and ocean. Stocks are the globally integrated total amount of conserved quantities such as mass and energy and is used to check conservation.
### arguments
| Name | Type | Subroutine | Definition |
|------|------|------------|------------|
| time | intent(inout) | flux_init_stocks | is the model's current time |
| atm | intent(inout) | flux_init_stocks | is a derived type holding atmosphere boundary data |
| lnd | intent(inout) | flux_init_stocks | is a derived type holding land boundary data |
| ice | intent(inout) | flux_init_stocks | is a derived type holding ice boundary data |
| ocn_state | intent(inout) | flux_init_stocks | is a pointer to ocean model's internal state |

### flowchart
flux_init_stocks does the following:  
Step 1: IF DIVERT_STOCKS_REPORT IS FALSE, OPEN STOCKS OUTPUT FILE TO STDOUT. IF DIVERT_STOCKS_REPORT IS TRUE, OPEN STOCKS OUTPUT FILE TO "stocks.out". ONLY THE ROOT PE WILL WRITE TO THE FILE.
Step 2: INITIALIZE WATER, HEAT, AND SALT STOCK VALUES FOR EACH COMPONENT. FOR ATMOSPHERE, INTEGRATE ATM_PRECIP_NEW TO GET THE INITIAL ISTOCK_WATER.
Step 3: INITIALIZE STOCKS IN FMS.


## check_atm_grid
### intro
Flux_exchange_mod is the top level module for flux exchange between components.  check_atm_grid is a subroutine in flux_exchange_mod.
### description
  Subroutine check_atm_grid checks the consistency of the atmosphere grid specified in the model with the grid specified in the grid_file.

atm


is a derived type holding atmosphere boundary data containing grid information



grid_file


is the path to the grid specification file.
### arguments
| Name | Type | Subroutine | Definition |
|------|------|------------|------------|
| atm | intent(inout) | check_atm_grid | is a derived type holding atmosphere boundary data containing grid information |
| grid_file | intent(inout) | check_atm_grid | is the path to the grid specification file |

### flowchart
check_atm_grid does the following:  
Step 1: GET GLOBAL, COMPUTE, AND DATA DOMAIN INDICES AND SIZES FOR THE ATMOSPHERE COMPONENT.
Step 2: OPEN GRID_FILE.
Step 3: CHECK GRID SIZES ARE CONSISTENT.
Step 4: CHECK LON, LAT, AND GRID CELL AREAS ARE CONSISTENT.

