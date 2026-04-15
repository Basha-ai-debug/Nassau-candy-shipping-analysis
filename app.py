import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Nassau Candy - Route Efficiency Dashboard",
    page_icon="🍬",
    layout="wide"
)

# Title
st.title("🍬 Nassau Candy Distributor")
st.subheader("Factory-to-Customer Shipping Route Efficiency Analysis")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/Nassau Candy Distributor.csv')
    
    # Date conversion
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y')
    df['Shipping_Lead_Time'] = (df['Ship Date'] - df['Order Date']).dt.days
    
    # Product to factory mapping
    product_factory_map = {
        'Wonka Bar - Nutty Crunch Surprise': "Lot's O' Nuts",
        'Wonka Bar - Fudge Mallows': "Lot's O' Nuts",
        'Wonka Bar -Scrumdiddlyumptious': "Lot's O' Nuts",
        'Wonka Bar - Milk Chocolate': "Wicked Choccy's",
        'Wonka Bar - Triple Dazzle Caramel': "Wicked Choccy's",
        'Laffy Taffy': 'Sugar Shack',
        'SweeTARTS': 'Sugar Shack',
        'Nerds': 'Sugar Shack',
        'Fun Dip': 'Sugar Shack',
        'Fizzy Lifting Drinks': 'Sugar Shack',
        'Everlasting Gobstopper': 'Secret Factory',
        'Hair Toffee': 'The Other Factory',
        'Lickable Wallpaper': 'Secret Factory',
        'Wonka Gum': 'Secret Factory',
        'Kazookles': 'The Other Factory'
    }
    
    df['Factory'] = df['Product Name'].map(product_factory_map)
    df['Route'] = df['Factory'] + ' → ' + df['State/Province']
    
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")

# Date range filter
min_date = df['Order Date'].min()
max_date = df['Order Date'].max()
date_range = st.sidebar.date_input(
    "Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Region filter
regions = ['All'] + sorted(df['Region'].unique().tolist())
selected_region = st.sidebar.selectbox("Select Region", regions)

# Ship mode filter
ship_modes = ['All'] + sorted(df['Ship Mode'].unique().tolist())
selected_shipmode = st.sidebar.selectbox("Ship Mode", ship_modes)

# Lead time threshold
lead_threshold = st.sidebar.slider(
    "Lead Time Threshold (days)",
    min_value=1,
    max_value=30,
    value=7
)

# Apply filters
filtered_df = df.copy()
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['Order Date'] >= pd.to_datetime(date_range[0])) &
        (filtered_df['Order Date'] <= pd.to_datetime(date_range[1]))
    ]
if selected_region != 'All':
    filtered_df = filtered_df[filtered_df['Region'] == selected_region]
if selected_shipmode != 'All':
    filtered_df = filtered_df[filtered_df['Ship Mode'] == selected_shipmode]

# Calculate KPIs
total_orders = filtered_df['Order ID'].nunique()
total_shipments = len(filtered_df)
avg_lead = filtered_df['Shipping_Lead_Time'].mean()
delay_rate = (len(filtered_df[filtered_df['Shipping_Lead_Time'] > lead_threshold]) / total_shipments) * 100 if total_shipments > 0 else 0

# Display KPIs
st.header("📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Orders", f"{total_orders:,}")
with col2:
    st.metric("Total Shipments", f"{total_shipments:,}")
with col3:
    st.metric("Avg Lead Time", f"{avg_lead:.1f} days")
with col4:
    st.metric(f"Delay Rate (>{lead_threshold}d)", f"{delay_rate:.1f}%")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Route Efficiency Overview",
    "📍 Geographic Analysis",
    "🚚 Ship Mode Comparison",
    "🔍 Route Drill-Down"
])

with tab1:
    st.header("Route Efficiency Overview")
    
    # Route aggregation
    route_stats = filtered_df.groupby('Route').agg({
        'Shipping_Lead_Time': ['mean', 'median', 'count'],
        'Order ID': 'nunique'
    }).round(2)
    route_stats.columns = ['Avg_Lead_Time', 'Median_Lead_Time', 'Shipment_Count', 'Unique_Orders']
    route_stats = route_stats.reset_index()
    
    # Calculate delay rate
    route_stats['Delay_Rate_%'] = 0
    for idx, route in route_stats.iterrows():
        route_data = filtered_df[filtered_df['Route'] == route['Route']]
        delayed = len(route_data[route_data['Shipping_Lead_Time'] > lead_threshold])
        total = len(route_data)
        route_stats.loc[idx, 'Delay_Rate_%'] = round((delayed / total) * 100, 2) if total > 0 else 0
    
    # Efficiency score
    min_time = route_stats['Avg_Lead_Time'].min()
    max_time = route_stats['Avg_Lead_Time'].max()
    if max_time > min_time:
        route_stats['Efficiency_Score'] = 100 * (1 - (route_stats['Avg_Lead_Time'] - min_time) / (max_time - min_time))
    else:
        route_stats['Efficiency_Score'] = 100
    route_stats['Efficiency_Score'] = route_stats['Efficiency_Score'].round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Most Efficient Routes")
        top_routes = route_stats.nsmallest(10, 'Avg_Lead_Time')
        if len(top_routes) > 0:
            st.dataframe(
                top_routes[['Route', 'Avg_Lead_Time', 'Shipment_Count', 'Delay_Rate_%', 'Efficiency_Score']],
                use_container_width=True
            )
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("⚠️ Top 10 Least Efficient Routes")
        bottom_routes = route_stats.nlargest(10, 'Avg_Lead_Time')
        if len(bottom_routes) > 0:
            st.dataframe(
                bottom_routes[['Route', 'Avg_Lead_Time', 'Shipment_Count', 'Delay_Rate_%', 'Efficiency_Score']],
                use_container_width=True
            )
        else:
            st.info("No data available")
    
    # Route performance chart
    if len(route_stats) > 0:
        st.subheader("Route Performance Distribution")
        fig = px.scatter(
            route_stats,
            x='Avg_Lead_Time',
            y='Shipment_Count',
            size='Delay_Rate_%',
            color='Efficiency_Score',
            hover_name='Route',
            title='Route Efficiency vs Volume',
            labels={'Avg_Lead_Time': 'Average Lead Time (days)', 'Shipment_Count': 'Number of Shipments'}
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Geographic Shipping Analysis")
    
    if len(filtered_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("State Performance")
            state_stats = filtered_df.groupby('State/Province').agg({
                'Shipping_Lead_Time': 'mean',
                'Order ID': 'nunique'
            }).round(2)
            state_stats.columns = ['Avg_Lead_Time', 'Order_Count']
            state_stats = state_stats.reset_index().sort_values('Avg_Lead_Time')
            
            fig = px.bar(
                state_stats.head(15),
                x='State/Province',
                y='Avg_Lead_Time',
                color='Order_Count',
                title='Top 15 Fastest States',
                labels={'Avg_Lead_Time': 'Average Lead Time (days)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Regional Performance")
            region_stats = filtered_df.groupby('Region').agg({
                'Shipping_Lead_Time': ['mean', 'count']
            }).round(2)
            region_stats.columns = ['Avg_Lead_Time', 'Shipment_Count']
            region_stats = region_stats.reset_index()
            
            fig = px.pie(
                region_stats,
                values='Shipment_Count',
                names='Region',
                title='Shipment Distribution by Region'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Factory performance
        if 'Factory' in filtered_df.columns and filtered_df['Factory'].notna().any():
            st.subheader("Factory Performance")
            factory_stats = filtered_df.groupby('Factory').agg({
                'Shipping_Lead_Time': 'mean',
                'Order ID': 'nunique'
            }).round(2)
            factory_stats.columns = ['Avg_Lead_Time', 'Order_Count']
            factory_stats = factory_stats.reset_index()
            
            fig = px.bar(
                factory_stats,
                x='Factory',
                y='Avg_Lead_Time',
                color='Order_Count',
                title='Average Lead Time by Factory',
                labels={'Avg_Lead_Time': 'Days'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available with current filters")

with tab3:
    st.header("Ship Mode Comparison")
    
    if len(filtered_df) > 0:
        mode_stats = filtered_df.groupby('Ship Mode').agg({
            'Shipping_Lead_Time': ['mean', 'median', 'min', 'max', 'count']
        }).round(2)
        mode_stats.columns = ['Avg_Lead_Time', 'Median_Lead_Time', 'Min_Lead_Time', 'Max_Lead_Time', 'Shipment_Count']
        mode_stats = mode_stats.reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Performance Metrics")
            st.dataframe(mode_stats, use_container_width=True)
        
        with col2:
            st.subheader("Delay Rate by Mode")
            delay_data = []
            for mode in filtered_df['Ship Mode'].unique():
                mode_data = filtered_df[filtered_df['Ship Mode'] == mode]
                delayed = len(mode_data[mode_data['Shipping_Lead_Time'] > lead_threshold])
                total = len(mode_data)
                delay_data.append({
                    'Ship Mode': mode,
                    'Delay Rate %': round((delayed / total) * 100, 1) if total > 0 else 0
                })
            delay_df = pd.DataFrame(delay_data)
            
            fig = px.bar(
                delay_df,
                x='Ship Mode',
                y='Delay Rate %',
                title=f'Delay Rate by Mode (>{lead_threshold} days)',
                color='Delay Rate %'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Box plot comparison
        st.subheader("Lead Time Distribution by Ship Mode")
        fig = px.box(
            filtered_df,
            x='Ship Mode',
            y='Shipping_Lead_Time',
            points='outliers',
            title='Shipping Lead Time Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available with current filters")

with tab4:
    st.header("Route Drill-Down Analysis")
    
    if len(filtered_df) > 0:
        # Select route
        available_routes = filtered_df['Route'].unique()
        if len(available_routes) > 0:
            selected_route = st.selectbox("Select Route to Analyze", available_routes)
            
            if selected_route:
                route_data = filtered_df[filtered_df['Route'] == selected_route]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Orders", f"{route_data['Order ID'].nunique():,}")
                with col2:
                    st.metric("Avg Lead Time", f"{route_data['Shipping_Lead_Time'].mean():.1f} days")
                with col3:
                    delay = len(route_data[route_data['Shipping_Lead_Time'] > lead_threshold])
                    delay_pct = (delay / len(route_data)) * 100 if len(route_data) > 0 else 0
                    st.metric(f"Delay Rate (>{lead_threshold}d)", f"{delay_pct:.1f}%")
                
                # Timeline chart
                if len(route_data) > 0:
                    st.subheader("Order Timeline")
                    timeline_data = route_data.sort_values('Order Date')
                    
                    fig = px.scatter(
                        timeline_data,
                        x='Order Date',
                        y='Shipping_Lead_Time',
                        color='Ship Mode',
                        size='Units',
                        hover_data=['City', 'State/Province', 'Product Name'],
                        title=f'Shipping Lead Times for {selected_route}'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Recent orders
                    st.subheader("Recent Orders")
                    recent = route_data.nlargest(10, 'Order Date')[
                        ['Order Date', 'Ship Date', 'Shipping_Lead_Time', 'City', 'Product Name', 'Ship Mode']
                    ]
                    st.dataframe(recent, use_container_width=True)
        else:
            st.info("No routes available with current filters")
    else:
        st.warning("No data available with current filters")

# Footer
st.markdown("---")
st.markdown("📊 **Nassau Candy Distributor** - Factory-to-Customer Route Efficiency Dashboard")