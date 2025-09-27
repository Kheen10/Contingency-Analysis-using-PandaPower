import pandapower as pp
import pandapower.converter as pc
import copy

# Configuration 
raw_path ="case14.m"   # path to the MATPOWER .m file
system_frequency_hz = 60

# Load Network 
net_base = pc.from_mpc(raw_path, f_hz=system_frequency_hz)
print("Network loaded successfully.")

# Set thermal ratings for all lines (MW)
THERMAL_RATE_A = 100  # Normal rating
THERMAL_RATE_B = 120  # Long-term emergency
THERMAL_RATE_C = 140  # Short-term emergency

net_base.line["rate_a"] = THERMAL_RATE_A
net_base.line["rate_b"] = THERMAL_RATE_B
net_base.line["rate_c"] = THERMAL_RATE_C

print("Thermal ratings added to all lines.")


# N-1 Contingency Analysis: All Buses 
for bus_to_off in net_base.bus.index:
    print(f"\n=== N-1 Contingency: Bus {bus_to_off} Out of Service ===")
    
    # Create a fresh copy of the network for each iteration
    net = copy.deepcopy(net_base)
    
    # Turn OFF the bus 
    net.bus.at[bus_to_off, "in_service"] = False
    
    # Run power flow
    try:
        pp.runpp(net)
        print("Power flow converged successfully.")
    except Exception as e:
        print(f"Power flow did NOT converge: {e}")
        continue
    
    # Print Full Results
    print("\n--- Full Bus Results ---")
    print(net.res_bus)

    print("\n--- Full Line Results ---")
    print(net.res_line)

    print("\n--- Full Transformer Results ---")
    print(net.res_trafo)

    print("\n--- Full Generator Results ---")
    print(net.res_gen)

    print("\n--- Full External Grid Results ---")
    print(net.res_ext_grid)

    print("\n--- Full Load Results ---")
    print(net.res_load)

    # Thermal loading for the lines.
    print("\n--- Line Thermal Loading ---")
    for line_idx in net.line.index:
        if not net.line.at[line_idx, "in_service"]:
            continue  # skip out-of-service lines
        p_from = net.res_line.at[line_idx, "p_from_mw"]
        rate_a = net.line.at[line_idx, "rate_a"]
        loading_pct = (p_from / rate_a) * 100 if rate_a else None
        print(f"Line {line_idx}: P={p_from:.2f} MW | RateA={rate_a} MW | Loading={loading_pct:.1f}%")
