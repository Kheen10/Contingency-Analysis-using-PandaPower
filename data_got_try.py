import pandas as pd
import pandapower as pp
import numpy as np
import pandapower.plotting as plot
import matplotlib.pyplot as plt



def convert_pu_to_si(acline_pu_df, bus_data_df, base_mva, frequency_hz=50):
    bus_kv_map = pd.Series(bus_data_df['Base kV'].values, index=bus_data_df['Bus Number']).to_dict()
    acline_si_df = acline_pu_df.copy()

    for index, row in acline_si_df.iterrows():
        from_bus = row['from_bus']
        base_kv = bus_kv_map[from_bus]
        z_base = (base_kv**2) / base_mva
        
        # Total line impedance in pu (assuming R_pu/km and X_pu/km are stored)
        r_total_pu = row['r_ohm_per_km'] * row['length_km']
        x_total_pu = row['x_ohm_per_km'] * row['length_km']

        # Convert total impedance to ohms
        r_total_ohms = r_total_pu * z_base
        x_total_ohms = x_total_pu * z_base
        
        # Convert total susceptance to SI units
        # Assuming c_nf_per_km is actually B_pu/km.
        # Total B_pu = B_pu/km * length_km
        b_total_pu = row['c_nf_per_km'] * row['length_km']
        b_total_siemens = b_total_pu / z_base
        
        # Convert total impedance/km and capacitance/km to SI units for pandapower
        acline_si_df.at[index, 'r_ohm_per_km'] = r_total_ohms / row['length_km']
        acline_si_df.at[index, 'x_ohm_per_km'] = x_total_ohms / row['length_km']
        
        omega = 2 * np.pi * frequency_hz
        c_total_farads = b_total_siemens / omega
        acline_si_df.at[index, 'c_nf_per_km'] = (c_total_farads / row['length_km']) * 1e9

    return acline_si_df


# Manually enter all your data into pandas DataFrames

# Bus Data
bus_data = pd.DataFrame({
    'Bus Number': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
    'Bus Name': ['BUS 1', 'BUS 2', 'BUS 3', 'BUS 4', 'BUS 5', 'BUS 6', 'BUS 7', 'BUS 8', 'BUS 9', 'BUS 10', 'BUS 11', 'BUS 12', 'BUS 13', 'BUS 14'],
    'Base kV': [138.0] * 14,
    'Voltage (pu)': [1.0600, 1.0450, 1.0100, 1.0177, 1.0195, 1.0700, 1.0615, 1.0900, 1.0559, 1.0510, 1.0569, 1.0552, 1.0504, 1.0355],
    'Normal Vmax (pu)': [1.1000] * 14,
    'Normal Vmin (pu)': [0.9000] * 14
})

# AC Line Data
acline_pu_data = pd.DataFrame({
    'from_bus': [1, 1, 2, 2, 2, 3, 4, 6, 6, 6, 7, 7, 9, 9, 10, 12, 13],
    'to_bus':   [2, 5, 3, 4, 5, 4, 5, 11, 12, 13, 8, 9, 10, 14, 11, 13, 14],
    'length_km': [1] * 17, # assuming 1 km length for simplicity, replace with your values
    'r_ohm_per_km': [0.01938, 0.05403, 0.04699, 0.05811, 0.05695, 0.06701, 0.01335, 0.09498, 0.12291, 0.06615, 0.00000, 0.00000, 0.03181, 0.12711, 0.082050, 0.22092, 0.17093],
    'x_ohm_per_km': [0.05917, 0.22304, 0.19790, 0.17632, 0.17388, 0.17103, 0.04211, 0.19890, 0.25581, 0.13027, 0.17615, 0.11001, 0.08450, 0.27038, 0.192070, 0.19988, 0.34802],
    'c_nf_per_km' : [0.05280, 0.04920, 0.04380, 0.03400, 0.03460, 0.01280, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.00000, 0.000000, 0.00000, 0.00000],
    'max_i_ka': [0.4] * 17
})

# Load Data
loaddata = pd.DataFrame({
    'bus':    [2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14],
    'p_mw':   [21.7, 94.2, 47.8, 7.6, 11.2, 29.5, 9.0, 3.5, 6.1, 13.5, 14.9],
    'q_mvar': [12.7, 19.0, -3.9, 1.6, 7.50, 16.6, 5.8, 1.8, 1.6, 5.80, 5.00]
})

# Plant/Machine Data (representing generators)
# We assume the first entry (bus 1) is the slack bus 
gen_data = pd.DataFrame({
    'bus': [1, 2, 3, 6, 8],
    'p_mw':  [232.392, 40, 0, 0, 0],  # P_mw for the slack bus (1) is 0
    'vm_pu': [1.060, 1.045, 1.010, 1.070, 1.090]
})

# Two-Winding Transformer Data (if any)
twowindings_data = pd.DataFrame({
    'hv_bus': [4, 4, 5],
    'lv_bus': [7, 9, 6],
    'sn_mva': [100, 100, 100],  # Example MVA, replace with your values
    'vn_hv_kv': [138, 138, 138],
    'vn_lv_kv': [138, 138, 138],
    'vkr_percent': [0.209120, 0.556180, 0.252020],
    'vk_percent': [5, 5, 5],
    'pfe_kw': [0.0, 0.0, 0.0],
    'i0_percent': [0.0, 0.0, 0.0]
})

# Fixed Shunt Data (if any)
fixedshuntdata = pd.DataFrame({
    'bus': [9],
    'q_mvar': [19.0]
})

pss_e_base_mva = 100.0  
acline_data = convert_pu_to_si(acline_pu_data, bus_data, pss_e_base_mva)


# Create an empty pandapower network 
net = pp.create_empty_network()

# Add buses to the network
bus_num_to_pp_idx = {}
for _, row in bus_data.iterrows():
    bus_num = int(row['Bus Number'])
    pp_idx = pp.create_bus(net, vn_kv=row['Base kV'], name=row['Bus Name'])
    bus_num_to_pp_idx[bus_num] = pp_idx
print("Buses added successfully.")

# Add network elements

# Add Two-Winding Transformers
if not twowindings_data.empty:
    for _, row in twowindings_data.iterrows():
        hv_bus_pp_idx = bus_num_to_pp_idx[int(row['hv_bus'])]
        lv_bus_pp_idx = bus_num_to_pp_idx[int(row['lv_bus'])]
        pp.create_transformer_from_parameters(
            net,
            hv_bus=hv_bus_pp_idx,
            lv_bus=lv_bus_pp_idx,
            sn_mva=row['sn_mva'],
            vn_hv_kv=row['vn_hv_kv'],
            vn_lv_kv=row['vn_lv_kv'],
            vkr_percent=row['vkr_percent'],
            vk_percent=row['vk_percent'],
            pfe_kw=row['pfe_kw'],
            i0_percent=row['i0_percent']
        )
    print("Two-Winding Transformers added successfully.")

# Add AC Lines
for _, row in acline_data.iterrows():
    from_bus_pp_idx = bus_num_to_pp_idx[int(row['from_bus'])]
    to_bus_pp_idx = bus_num_to_pp_idx[int(row['to_bus'])]
    pp.create_line_from_parameters(
        net,
        from_bus=from_bus_pp_idx,
        to_bus=to_bus_pp_idx,
        length_km=row['length_km'],
        r_ohm_per_km=row['r_ohm_per_km'],
        x_ohm_per_km=row['x_ohm_per_km'],
        c_nf_per_km=row['c_nf_per_km'],
        max_i_ka=row['max_i_ka']
    )
print("AC Lines added successfully.")

# Add Fixed Shunts
if not fixedshuntdata.empty:
    for _, row in fixedshuntdata.iterrows():
        bus_pp_idx = bus_num_to_pp_idx[int(row['bus'])]
        pp.create_shunt(net, bus=bus_pp_idx, q_mvar=row['q_mvar'], p_mw=row.get('p_mw', 0.0))
    print("Fixed Shunts added successfully.")

# Add Loads
for _, row in loaddata.iterrows():
    bus_pp_idx = bus_num_to_pp_idx[int(row['bus'])]
    pp.create_load(net, bus=bus_pp_idx, p_mw=row['p_mw'], q_mvar=row['q_mvar'])
print("Loads added successfully.")

# Add Generators (Machines/Plants)
slack_bus_found = False
for _, row in gen_data.iterrows():
    bus_pp_idx = bus_num_to_pp_idx[int(row['bus'])]
    if not slack_bus_found:
        pp.create_ext_grid(net, bus=bus_pp_idx, vm_pu=row['vm_pu'])
        slack_bus_found = True
    else:
        pp.create_gen(net, bus=bus_pp_idx, p_mw=row['p_mw'], vm_pu=row['vm_pu'])

if not slack_bus_found:
    print("Warning: No slack bus was created.")
print("Generators and external grid added successfully.")

# Plot
try:
    plot.simple_plot(net, plot_loads=True, plot_gens=True, trafo_color='green')
    plt.show()
    pp.diagnostic(net)
except Exception as e:
    print(f"An error occurred during plotting or diagnostics: {e}")

# Run power flow analysis
try:
    pp.runpp(net)
    print("\nPower flow analysis successful.")
except Exception as e:
    print(f"\nError during power flow calculation: {e}")
    exit()

# Print results
print("\n--- Bus Results ---")
print(net.res_bus)

print("\n--- Line Results ---")
print(net.res_line)

print("\n--- Transformer Results ---")
print(net.res_trafo)

print("\n--- Generator Results ---")
print(net.res_gen)

print("\n--- External Grid Results ---")
print(net.res_ext_grid)

print("\n--- Load Results ---")
print(net.res_load)
