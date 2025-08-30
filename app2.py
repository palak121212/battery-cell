import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import time
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Battery Cell Monitor",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-low {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #4caf50;
        font-weight: bold;
    }
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
    .status-critical {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cells_data' not in st.session_state:
    st.session_state.cells_data = {}
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

def get_cell_specs(cell_type):
    """Get cell specifications based on type"""
    specs = {
        "lfp": {
            "nominal_voltage": 3.2,
            "min_voltage": 2.8,
            "max_voltage": 3.6,
            "max_current": 100.0,
            "color": "#2E8B57"
        },
        "nmc": {
            "nominal_voltage": 3.6,
            "min_voltage": 3.2,
            "max_voltage": 4.0,
            "max_current": 120.0,
            "color": "#4169E1"
        },
        "lto": {
            "nominal_voltage": 2.4,
            "min_voltage": 1.5,
            "max_voltage": 2.8,
            "max_current": 200.0,
            "color": "#FF6347"
        },
        "lifepo4": {
            "nominal_voltage": 3.3,
            "min_voltage": 2.5,
            "max_voltage": 3.65,
            "max_current": 150.0,
            "color": "#9370DB"
        }
    }
    return specs.get(cell_type, specs["lfp"])

def check_cell_status(cell_data, cell_type):
    """Check cell status and return status info"""
    specs = get_cell_specs(cell_type)
    voltage = cell_data["voltage"]
    current = cell_data["current"]
    temp = cell_data["temp"]
    
    status = "Good"
    alerts = []
    
    # Voltage checks
    if voltage < specs["min_voltage"]:
        status = "Critical"
        alerts.append(f"⚠️ Voltage too low: {voltage}V (min: {specs['min_voltage']}V)")
    elif voltage > specs["max_voltage"]:
        status = "Critical"
        alerts.append(f"⚠️ Voltage too high: {voltage}V (max: {specs['max_voltage']}V)")
    
    # Current checks
    if abs(current) > specs["max_current"]:
        status = "Warning" if status == "Good" else status
        alerts.append(f"⚠️ Current high: {abs(current)}A (max: {specs['max_current']}A)")
    
    # Temperature checks
    if temp > 45:
        status = "Critical"
        alerts.append(f"🌡️ Temperature too high: {temp}°C")
    elif temp > 40:
        status = "Warning" if status == "Good" else status
        alerts.append(f"🌡️ Temperature elevated: {temp}°C")
    elif temp < 0:
        status = "Warning" if status == "Good" else status
        alerts.append(f"🌡️ Temperature too low: {temp}°C")
    
    return status, alerts

def simulate_real_time_data(cell_key, base_data):
    """Simulate realistic battery cell data changes"""
    cell_type = cell_key.split('_')[2]
    specs = get_cell_specs(cell_type)
    
    # Add small random variations to simulate real conditions
    voltage_variation = random.uniform(-0.05, 0.05)
    temp_variation = random.uniform(-1.0, 1.0)
    current_variation = random.uniform(-2.0, 2.0)
    
    new_voltage = max(specs["min_voltage"], 
                     min(specs["max_voltage"], 
                         base_data["voltage"] + voltage_variation))
    new_temp = max(0, min(50, base_data["temp"] + temp_variation))
    new_current = base_data["current"] + current_variation
    
    return {
        **base_data,
        "voltage": round(new_voltage, 3),
        "temp": round(new_temp, 1),
        "current": round(new_current, 2),
        "capacity": round(new_voltage * abs(new_current), 2),
        "timestamp": datetime.now()
    }

# Main title and description
st.title("🔋 Advanced Battery Cell Monitoring System")
st.markdown("**Real-time monitoring and analysis of battery cells with comprehensive data visualization**")

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Cell setup section
    st.subheader("Cell Setup")
    num_cells = st.number_input("Number of cells to monitor", min_value=1, max_value=16, value=8)
    
    # Cell type selection
    cell_types = ["lfp", "nmc", "lto", "lifepo4"]
    
    # Initialize or update cells based on number
    if len(st.session_state.cells_data) != num_cells:
        st.session_state.cells_data = {}
        for i in range(num_cells):
            cell_type = st.selectbox(f"Cell {i+1} Type", cell_types, key=f"cell_type_{i}")
            specs = get_cell_specs(cell_type)
            
            cell_key = f"cell_{i+1}_{cell_type}"
            st.session_state.cells_data[cell_key] = {
                "voltage": specs["nominal_voltage"],
                "current": 0.0,
                "temp": round(random.uniform(25, 35), 1),
                "capacity": 0.0,
                "min_voltage": specs["min_voltage"],
                "max_voltage": specs["max_voltage"],
                "timestamp": datetime.now()
            }
    
    # Monitoring controls
    st.subheader("Monitoring Controls")
    if st.button("🔄 Start Real-time Monitoring", type="primary"):
        st.session_state.monitoring_active = True
        st.rerun()
    
    if st.button("⏹️ Stop Monitoring"):
        st.session_state.monitoring_active = False
    
    auto_refresh = st.checkbox("Auto-refresh data", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh
    
    refresh_interval = st.selectbox("Refresh interval", [1, 2, 5, 10], index=1)
    
    # Manual data input section
    st.subheader("Manual Data Input")
    selected_cell = st.selectbox("Select cell to update", list(st.session_state.cells_data.keys()))
    
    if selected_cell:
        cell_type = selected_cell.split('_')[2]
        specs = get_cell_specs(cell_type)
        
        new_voltage = st.number_input("Voltage (V)", 
                                    min_value=0.0, 
                                    max_value=5.0, 
                                    value=st.session_state.cells_data[selected_cell]["voltage"],
                                    step=0.1,
                                    format="%.3f")
        
        new_current = st.number_input("Current (A)", 
                                    value=st.session_state.cells_data[selected_cell]["current"],
                                    step=0.1,
                                    format="%.2f")
        
        new_temp = st.number_input("Temperature (°C)", 
                                 min_value=-20.0, 
                                 max_value=80.0,
                                 value=st.session_state.cells_data[selected_cell]["temp"],
                                 step=0.1,
                                 format="%.1f")
        
        if st.button("Update Cell Data"):
            st.session_state.cells_data[selected_cell].update({
                "voltage": new_voltage,
                "current": new_current,
                "temp": new_temp,
                "capacity": round(new_voltage * abs(new_current), 2),
                "timestamp": datetime.now()
            })
            st.success(f"Updated {selected_cell}")

# Real-time monitoring logic
if st.session_state.monitoring_active and st.session_state.auto_refresh:
    time.sleep(refresh_interval)
    # Update all cells with simulated data
    for key in st.session_state.cells_data:
        st.session_state.cells_data[key] = simulate_real_time_data(key, st.session_state.cells_data[key])
    
    # Store historical data
    current_time = datetime.now()
    for key, data in st.session_state.cells_data.items():
        historical_entry = {
            "timestamp": current_time,
            "cell_id": key,
            "voltage": data["voltage"],
            "current": data["current"],
            "temp": data["temp"],
            "capacity": data["capacity"]
        }
        st.session_state.historical_data.append(historical_entry)
    
    # Keep only last 100 data points per cell
    if len(st.session_state.historical_data) > 800:  # 8 cells * 100 points
        st.session_state.historical_data = st.session_state.historical_data[-800:]
    
    st.rerun()

# Main dashboard
if st.session_state.cells_data:
    # Overview metrics
    st.header("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_voltage = sum(data["voltage"] for data in st.session_state.cells_data.values())
    avg_temp = np.mean([data["temp"] for data in st.session_state.cells_data.values()])
    total_capacity = sum(data["capacity"] for data in st.session_state.cells_data.values())
    active_cells = len([data for data in st.session_state.cells_data.values() if data["current"] != 0])
    
    with col1:
        st.metric("Total Voltage", f"{total_voltage:.2f} V")
    with col2:
        st.metric("Average Temperature", f"{avg_temp:.1f} °C")
    with col3:
        st.metric("Total Capacity", f"{total_capacity:.2f} Wh")
    with col4:
        st.metric("Active Cells", f"{active_cells}/{len(st.session_state.cells_data)}")
    
    # Status alerts
    st.subheader("🚨 System Alerts")
    alerts_container = st.container()
    
    all_alerts = []
    for key, data in st.session_state.cells_data.items():
        cell_type = key.split('_')[2]
        status, alerts = check_cell_status(data, cell_type)
        if alerts:
            all_alerts.extend([(key, alert) for alert in alerts])
    
    if all_alerts:
        for cell_key, alert in all_alerts:
            alerts_container.error(f"**{cell_key}**: {alert}")
    else:
        alerts_container.success("✅ All cells operating within normal parameters")
    
    # Individual cell monitoring
    st.header("🔋 Individual Cell Status")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Live Data", "📈 Real-time Graphs", "📊 Historical Analysis", "⚙️ Advanced Settings"])
    
    with tab1:
        # Live data table
        cols = st.columns(2)
        
        for idx, (key, data) in enumerate(st.session_state.cells_data.items()):
            cell_type = key.split('_')[2]
            status, alerts = check_cell_status(data, cell_type)
            specs = get_cell_specs(cell_type)
            
            with cols[idx % 2]:
                with st.container():
                    # Cell header
                    status_color = {"Good": "🟢", "Warning": "🟡", "Critical": "🔴"}
                    st.subheader(f"{status_color.get(status, '⚪')} {key.upper()}")
                    
                    # Create metrics in columns
                    met_col1, met_col2, met_col3 = st.columns(3)
                    
                    with met_col1:
                        voltage_delta = data["voltage"] - specs["nominal_voltage"]
                        st.metric("Voltage", f"{data['voltage']:.3f} V", 
                                delta=f"{voltage_delta:+.3f} V")
                    
                    with met_col2:
                        st.metric("Current", f"{data['current']:.2f} A")
                    
                    with met_col3:
                        st.metric("Temperature", f"{data['temp']:.1f} °C")
                    
                    # Additional info
                    st.write(f"**Capacity:** {data['capacity']:.2f} Wh")
                    st.write(f"**Type:** {cell_type.upper()}")
                    st.write(f"**Range:** {specs['min_voltage']}-{specs['max_voltage']} V")
                    
                    # Status indicator
                    if status == "Good":
                        st.markdown('<p class="status-good">✅ Normal Operation</p>', unsafe_allow_html=True)
                    elif status == "Warning":
                        st.markdown('<p class="status-warning">⚠️ Warning State</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="status-critical">🚨 Critical Alert</p>', unsafe_allow_html=True)
                    
                    st.divider()
    
    with tab2:
        # Real-time graphs
        st.subheader("Real-time Cell Monitoring")
        
        if st.session_state.cells_data:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Cell Voltages', 'Cell Currents', 'Cell Temperatures', 'Cell Capacities'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            cell_names = list(st.session_state.cells_data.keys())
            voltages = [st.session_state.cells_data[key]["voltage"] for key in cell_names]
            currents = [st.session_state.cells_data[key]["current"] for key in cell_names]
            temps = [st.session_state.cells_data[key]["temp"] for key in cell_names]
            capacities = [st.session_state.cells_data[key]["capacity"] for key in cell_names]
            
            # Voltage chart
            fig.add_trace(
                go.Bar(x=cell_names, y=voltages, name="Voltage", 
                      marker_color=[get_cell_specs(key.split('_')[2])["color"] for key in cell_names]),
                row=1, col=1
            )
            
            # Current chart
            fig.add_trace(
                go.Bar(x=cell_names, y=currents, name="Current",
                      marker_color='lightblue'),
                row=1, col=2
            )
            
            # Temperature chart
            fig.add_trace(
                go.Bar(x=cell_names, y=temps, name="Temperature",
                      marker_color='orange'),
                row=2, col=1
            )
            
            # Capacity chart
            fig.add_trace(
                go.Bar(x=cell_names, y=capacities, name="Capacity",
                      marker_color='green'),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False, title_text="Real-time Cell Data Dashboard")
            fig.update_xaxes(tickangle=45)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Gauge charts for critical metrics
            gauge_col1, gauge_col2 = st.columns(2)
            
            with gauge_col1:
                st.subheader("System Voltage Distribution")
                voltage_fig = go.Figure(go.Histogram(
                    x=voltages,
                    nbinsx=10,
                    marker_color='skyblue',
                    opacity=0.7
                ))
                voltage_fig.update_layout(title="Voltage Distribution", height=300)
                st.plotly_chart(voltage_fig, use_container_width=True)
            
            with gauge_col2:
                st.subheader("Temperature Distribution")
                temp_fig = go.Figure(go.Histogram(
                    x=temps,
                    nbinsx=10,
                    marker_color='orange',
                    opacity=0.7
                ))
                temp_fig.update_layout(title="Temperature Distribution", height=300)
                st.plotly_chart(temp_fig, use_container_width=True)
    
    with tab3:
        # Historical analysis
        st.subheader("📈 Historical Data Analysis")
        
        if st.session_state.historical_data:
            # Convert to DataFrame
            df = pd.DataFrame(st.session_state.historical_data)
            
            # Time series charts
            metric_choice = st.selectbox("Select metric to analyze", 
                                       ["voltage", "current", "temp", "capacity"])
            
            # Line chart for selected metric
            fig_time = px.line(df, x='timestamp', y=metric_choice, color='cell_id',
                             title=f'Historical {metric_choice.capitalize()} Trends')
            fig_time.update_layout(height=400)
            st.plotly_chart(fig_time, use_container_width=True)
            
            # Statistical summary
            st.subheader("Statistical Summary")
            summary_stats = df.groupby('cell_id')[['voltage', 'current', 'temp', 'capacity']].agg([
                'mean', 'std', 'min', 'max'
            ]).round(3)
            st.dataframe(summary_stats, use_container_width=True)
            
            # Correlation analysis
            st.subheader("Correlation Matrix")
            numeric_cols = ['voltage', 'current', 'temp', 'capacity']
            corr_matrix = df[numeric_cols].corr()
            
            fig_corr = px.imshow(corr_matrix, 
                               text_auto=True, 
                               aspect="auto",
                               title="Parameter Correlation Matrix")
            st.plotly_chart(fig_corr, use_container_width=True)
            
        else:
            st.info("No historical data available. Start monitoring to collect data over time.")
    
    with tab4:
        # Advanced settings and export
        st.subheader("⚙️ Advanced Configuration")
        
        # Simulation parameters
        st.write("**Simulation Parameters**")
        voltage_noise = st.slider("Voltage noise level", 0.0, 0.2, 0.05, 0.01)
        temp_noise = st.slider("Temperature noise level", 0.0, 5.0, 1.0, 0.1)
        current_noise = st.slider("Current noise level", 0.0, 10.0, 2.0, 0.1)
        
        # Thresholds
        st.write("**Alert Thresholds**")
        temp_warning = st.number_input("Temperature warning (°C)", value=40.0)
        temp_critical = st.number_input("Temperature critical (°C)", value=45.0)
        
        # Data export
        st.write("**Data Export**")
        if st.button("📥 Export Current Data as CSV"):
            if st.session_state.cells_data:
                export_data = []
                for key, data in st.session_state.cells_data.items():
                    export_data.append({
                        "Cell_ID": key,
                        "Voltage_V": data["voltage"],
                        "Current_A": data["current"],
                        "Temperature_C": data["temp"],
                        "Capacity_Wh": data["capacity"],
                        "Timestamp": data["timestamp"]
                    })
                
                df_export = pd.DataFrame(export_data)
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"battery_cells_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        if st.button("🗑️ Clear Historical Data"):
            st.session_state.historical_data = []
            st.success("Historical data cleared")
        
        if st.button("🔄 Reset All Cells"):
            st.session_state.cells_data = {}
            st.session_state.historical_data = []
            st.session_state.monitoring_active = False
            st.success("All data reset")
            st.rerun()

# Data table view
with st.expander("📋 Detailed Data Table", expanded=False):
    if st.session_state.cells_data:
        table_data = []
        for key, data in st.session_state.cells_data.items():
            cell_type = key.split('_')[2]
            status, alerts = check_cell_status(data, cell_type)
            
            table_data.append({
                "Cell ID": key,
                "Type": cell_type.upper(),
                "Voltage (V)": data["voltage"],
                "Current (A)": data["current"],
                "Temperature (°C)": data["temp"],
                "Capacity (Wh)": data["capacity"],
                "Status": status,
                "Last Updated": data["timestamp"].strftime("%H:%M:%S")
            })
        
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)

# Auto-refresh mechanism
if st.session_state.auto_refresh and st.session_state.monitoring_active:
    st.rerun()

# Footer
st.markdown("---")
st.markdown("**Battery Cell Monitor v2.0** | Real-time monitoring with advanced analytics")

# Display monitoring status
if st.session_state.monitoring_active:
    st.sidebar.success("🟢 Monitoring Active")
else:
    st.sidebar.info("⚪ Monitoring Inactive")