import pandapower.converter as pc
import pandapower as pp
import pandapower.networks as pn
import matplotlib.pyplot as plt
import pandapower.plotting as plot


# Configuration 
raw_path = "case14.m"     # path to the MATPOWER .m file

# Define frequency 
system_frequency_hz = 60

# Load Network 
try:
    net = pc.from_mpc(raw_path, f_hz=system_frequency_hz)
    print(f"Successfully loaded network from: {raw_path}")
    print(f"Network has {len(net.bus)} buses, {len(net.line)} lines, {len(net.trafo)} transformers.")
except FileNotFoundError:
    print(f"Error: MATPOWER file not found at {raw_path}. Please check the path.")
    exit()
except Exception as e:
    print(f"An error occurred while loading the network: {e}")
    exit()

# Show bus connectivity
print("\n=== Bus Connectivity in the Loaded System ===")
for bus_idx in net.bus.index:
    bus_name = net.bus.at[bus_idx, "name"] if "name" in net.bus.columns else f"Bus {bus_idx}"
    connected = set()

    # Check lines connected to the bus
    for _, line in net.line.iterrows():
        if line["from_bus"] == bus_idx:
            connected.add(net.bus.at[line["to_bus"], "name"] if "name" in net.bus.columns else f"Bus {line['to_bus']}")
        if line["to_bus"] == bus_idx:
            connected.add(net.bus.at[line["from_bus"], "name"] if "name" in net.bus.columns else f"Bus {line['from_bus']}")

    # Check transformers connected to the bus
    for _, trafo in net.trafo.iterrows():
        if trafo["hv_bus"] == bus_idx:
            connected.add(net.bus.at[trafo["lv_bus"], "name"] if "name" in net.bus.columns else f"Bus {trafo['lv_bus']}")
        if trafo["lv_bus"] == bus_idx:
            connected.add(net.bus.at[trafo["hv_bus"], "name"] if "name" in net.bus.columns else f"Bus {trafo['hv_bus']}")

    print(f"Bus {bus_name} (idx: {bus_idx}) is connected to: {sorted(list(connected))}")


# Run power flow
print("\n--- Running Power Flow ---")
try:
    pp.runpp(net)
    print("Power flow successful.")
except Exception as e:
    print(f"Power flow failed: {e}")
    print("Cannot proceed with results summary as power flow did not converge.")
    exit()


# Per-bus summary
print("\n=== Per-Bus Summary ===")
for bus_idx in net.bus.index:
    bus_name = net.bus.at[bus_idx, "name"] if "name" in net.bus.columns else f"Bus {bus_idx}"
    print("\n" + "="*50)
    print(f"🔹 {bus_name} (Index: {bus_idx}) Report")
    print("="*50)

    # Voltage & angle
    v_pu = net.res_bus.loc[bus_idx, "vm_pu"]
    va_deg = net.res_bus.loc[bus_idx, "va_degree"]
    print(f"Voltage: {v_pu:.3f} pu | Angle: {va_deg:.2f}°")

    # Active and Reactive Power Balance at Bus (Net Injection)
    p_net = net.res_bus.loc[bus_idx, "p_mw"]
    q_net = net.res_bus.loc[bus_idx, "q_mvar"]
    print(f"Net Injection: {p_net:.2f} MW | {q_net:.2f} Mvar")


    # Generation (from gen + ext_grid if applicable)
    gens = net.gen[net.gen.bus == bus_idx].index
    if not gens.empty:
        for g in gens:
            p_gen = net.res_gen.loc[g, "p_mw"]
            q_gen = net.res_gen.loc[g, "q_mvar"]
            print(f"  > Generation (Gen {g}): {p_gen:.2f} MW | {q_gen:.2f} Mvar")
    ext = net.ext_grid[net.ext_grid.bus == bus_idx].index
    if not ext.empty:
        for e in ext:
            p_gen = net.res_ext_grid.loc[e, "p_mw"]
            q_gen = net.res_ext_grid.loc[e, "q_mvar"]
            print(f"  > Slack Gen (ExtGrid {e}): {p_gen:.2f} MW | {q_gen:.2f} Mvar")

    # Load
    loads = net.load[net.load.bus == bus_idx].index
    if not loads.empty:
        for l in loads:
            p_load = net.res_load.loc[l, "p_mw"]
            q_load = net.res_load.loc[l, "q_mvar"]
            print(f"  > Load (Load {l}): {p_load:.2f} MW | {q_load:.2f} Mvar")

    # Branch flows (lines connected to bus)
    connected_lines = net.line[(net.line.from_bus == bus_idx) | (net.line.to_bus == bus_idx)].index
    if not connected_lines.empty:
        print("  --- Line Flows ---")
        for line_idx in connected_lines:
            fb, tb = net.line.loc[line_idx, ["from_bus", "to_bus"]]
            line_name = net.line.at[line_idx, "name"] if "name" in net.line.columns else f"Line {line_idx}"
            if fb == bus_idx:  # bus_idx is sending end
                p, q = net.res_line.loc[line_idx, ["p_from_mw", "q_from_mvar"]]
                print(f"  > {line_name}: {bus_name} ({bus_idx}) -> {net.bus.at[tb, 'name'] if 'name' in net.bus.columns else f'Bus {tb}'} ({tb}) | P: {p:.2f} MW | Q: {q:.2f} Mvar")
            else:  # bus_idx is receiving end
                p, q = net.res_line.loc[line_idx, ["p_to_mw", "q_to_mvar"]]
                print(f"  > {line_name}: {net.bus.at[fb, 'name'] if 'name' in net.bus.columns else f'Bus {fb}'} ({fb}) -> {bus_name} ({bus_idx}) | P: {p:.2f} MW | Q: {q:.2f} Mvar")

    # Transformer flows (if any)
    connected_trafos = net.trafo[(net.trafo.hv_bus == bus_idx) | (net.trafo.lv_bus == bus_idx)].index
    if not connected_trafos.empty:
        print("  --- Transformer Flows ---")
        for trafo_idx in connected_trafos:
            hv, lv = net.trafo.loc[trafo_idx, ["hv_bus", "lv_bus"]]
            trafo_name = net.trafo.at[trafo_idx, "name"] if "name" in net.trafo.columns else f"Trafo {trafo_idx}"
            if hv == bus_idx:
                p, q = net.res_trafo.loc[trafo_idx, ["p_hv_mw", "q_hv_mvar"]]
                print(f"  > {trafo_name}: HV side at {bus_name} ({bus_idx}) | P: {p:.2f} MW | Q: {q:.2f} Mvar")
            else:
                p, q = net.res_trafo.loc[trafo_idx, ["p_lv_mw", "q_lv_mvar"]]
                print(f"  > {trafo_name}: LV side at {bus_name} ({bus_idx}) | P: {p:.2f} MW | Q: {q:.2f} Mvar")


# Print full results tables
print("\n--- Full Bus Results ---\n", net.res_bus)
print("\n--- Full Line Results ---\n", net.res_line)
print("\n--- Full Transformer Results ---\n", net.res_trafo)
print("\n--- Full Generator Results ---\n", net.res_gen)
print("\n--- Full External Grid Results ---\n", net.res_ext_grid)
print("\n--- Full Load Results ---\n", net.res_load)

# Run diagnostic for common network issues (good practice)
print("\n--- Pandapower Diagnostic Report ---")
pp.diagnostic(net)

# Plotting the Network
print("\n--- Generating Network Plot ---")
try:
    # define bus colors
    gen_buses = net.gen.bus.tolist() + net.ext_grid.bus.tolist()
    ext_grid_bus = net.ext_grid.bus.iloc[0] if not net.ext_grid.empty else None

    bus_colors = []
    for bus_idx in net.bus.index:
        if bus_idx == ext_grid_bus:
            bus_colors.append("red")    # slack bus
        elif bus_idx in gen_buses:
            bus_colors.append("green")  # generators
        else:
            bus_colors.append("blue")   # normal buses

    # simple plot without labels
    plot.simple_plot(
        net,
        bus_color=bus_colors,
        bus_size=0.6,
        gen_size=1.2,
        ext_grid_size=1.5
    )

    # display the plot
    plt.show()

except Exception as e:
    print(f"Plotting failed: {e}")
    
    