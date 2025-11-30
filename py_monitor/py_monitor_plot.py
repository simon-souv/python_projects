import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go # Needed for trace transfer

# 1. Load the data
file_name = "output.csv"
df = pd.read_csv(file_name)

# 2. Convert 'epoch_timestamp' to datetime objects
df['datetime'] = pd.to_datetime(df['epoch_timestamp'], unit='s')

# 3. Determine the top 10 PIDs by maximum memory usage
top_pids = df.groupby('pid')['memory_rss_mb'].max().nlargest(10).index

# 4. Filter the DataFrame to include only the top PIDs
df_top_pids = df[df['pid'].isin(top_pids)].copy()

# 5. Create a combined label for better plotting
df_top_pids['pid_name_label'] = df_top_pids['pid'].astype(str) + ' (' + df_top_pids['name'] + ')'

# --- NEW STEP 6: Generate two separate Plotly Express figures ---

# 6a. Generate the MEMORY plot (fig_mem)
fig_mem = px.line(
    df_top_pids,
    x='datetime',
    y='memory_rss_mb',
    color='pid_name_label',
    labels={
        'datetime': 'Time',
        'memory_rss_mb': 'Memory RSS (MB)',
        'pid_name_label': 'Process ID (Name)'
    }
)

# 6b. Generate the CPU plot (fig_cpu)
fig_cpu = px.line(
    df_top_pids,
    x='datetime',
    y='cpu_percent',
    color='pid_name_label',
    labels={
        'datetime': 'Time',
        'cpu_percent': 'CPU Percent (%)',
        'pid_name_label': 'Process ID (Name)'
    }
)

# --- NEW STEP 7: Combine the figures into a single subplot ---

# Create a figure with 2 rows (one for memory, one for CPU)
# shared_xaxes=True links the time axis across both plots
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.1,
    subplot_titles=("Memory Usage (RSS) Over Time", "CPU Usage Over Time")
)

# 7a. Add traces (lines) from the Memory figure (fig_mem) to the first row (Top plot)
for trace in fig_mem.data:
    fig.add_trace(go.Scatter(
        x=trace.x,
        y=trace.y,
        name=trace.name,
        legendgroup=trace.name,
        line=trace.line,
        mode='lines',
        showlegend=True
    ), row=1, col=1)

# 7b. Add traces (lines) from the CPU figure (fig_cpu) to the second row (Bottom plot)
for trace in fig_cpu.data:
    # Set showlegend=False here to prevent duplicating the legend
    fig.add_trace(go.Scatter(
        x=trace.x,
        y=trace.y,
        name=trace.name,
        legendgroup=trace.name,
        line=trace.line,
        mode='lines',
        showlegend=False
    ), row=2, col=1)

# --- NEW STEP 8: Update layout for the combined figure ---

fig.update_layout(
    title_text='Top 10 Processes: Performance Metrics Over Time',
    height=800,
    legend_title_text='Process ID (Name)',
    hovermode='x unified'
)

# Update axis titles
fig.update_yaxes(title_text='Memory RSS (MB)', row=1, col=1)
fig.update_yaxes(title_text='CPU Percent (%)', row=2, col=1)
fig.update_xaxes(title_text='Time', row=2, col=1)

# 9. Save the interactive plot as an HTML file
output_html_file = 'performance_metrics_combined_plotly.html'
fig.write_html(output_html_file)