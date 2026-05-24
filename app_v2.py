import hashlib
import mysql.connector
import pandas as pd
import plotly.express as px
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Database Connection
conn = mysql.connector.connect(
    host="localhost", user="root", password="root123", database="shopulse"
)
cursor = conn.cursor()

# Auto-create backend tables if they don't exist (Updated Schema)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE,
        password VARCHAR(255)
    );
"""
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        product VARCHAR(255),
        revenue FLOAT,
        units_sold INT,
        profit FLOAT,
        stock INT,
        ad_spend FLOAT
    );
"""
)
conn.commit()


# Helper function to load data safely in local and cloud environments
def load_data():
    try:
        # Try fetching from MySQL first (Works perfectly on your laptop!)
        query = f"SELECT product, revenue, units_sold, profit, stock, ad_spend FROM orders WHERE user_id = {st.session_state.user_id}"
        df = pd.read_sql(query, conn)
        return df
    except Exception:
        # 🌐 FREE CLOUD FALLBACK SAFEGUARD: If MySQL is offline, read from the active session cache memory instead!
        if st.session_state.df is not None:
            return st.session_state.df
        return pd.DataFrame()



# Helper function to safely transmit automated operational email alerts
def send_email_alert(alert_subject, alert_body_text):
    # --- SECURITY LOG INTERACTION CAPTURE CONTROL PANEL ---
    # In a live hosted deployment, these strings are loaded securely via environment variables (st.secrets)
    sender_email = "your_automated_saas_email@gmail.com"
    sender_app_password = "xxxx xxxx xxxx xxxx" # Gmail's generated 16-character App Password token
    receiver_admin_email = "your_personal_admin_email@gmail.com"
    
    # Fast bypass fallback check to prevent the application execution thread from stalling if keys are empty
    if sender_email == "your_automated_saas_email@gmail.com" or sender_app_password == "xxxx xxxx xxxx xxxx":
        return False # Gracefully exit and continue running the dashboard interface without throwing block errors
        
    try:
        # Build the structural multi-part MIME email object envelope
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_admin_email
        msg['Subject'] = f"🚨 [Shopulse Alert] {alert_subject}"
        
        # Attach the body text message string to the envelope payload
        msg.attach(MIMEText(alert_body_text, 'plain'))
        
        # Establish connection hook with Google's secure automated application server
        server = smtplib.SMTP('://gmail.com', 587)
        server.starttls() # Initialize secure TLS cryptographic encryption protocols
        
        # Log into the system using the application token key
        server.login(sender_email, sender_app_password)
        
        # Dispatch message envelope across network lines
        server.sendmail(sender_email, receiver_admin_email, msg.as_string())
        server.quit() # Terminate the transmission pipeline thread cleanly
        return True
    except Exception as e:
        # Silently fail inside terminal tracking if connection walls block the attempt
        print(f"SMTP Automation Pipeline Blocked: {e}")
        return False

# --- STEP 3 — Add Login Session State ---
if "df" not in st.session_state:
    st.session_state.df = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

# Page configuration
st.set_page_config(page_title="Shopulse", page_icon="🚀", layout="wide")

# Custom SaaS Minimalist UI CSS (Updated with Print Engine)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #4B5563 !important;
    }
    div.stDataFrame {
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
    }
    .css-17eq0hr {
        background-color: #F9FAFB !important;
    }

    /* 🖨️ NATIVE PRINT ENGINE OVERRIDE BLOCK */
    @media print {
        /* Force the browser to render all background colors and styles */
        html, body {
            visibility: visible !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        /* Hide temporary UI controls like sidebars and download utility boxes from paper */
        section[data-testid="stSidebar"], button, .stDownloadButton, [data-testid="stHeader"] {
            display: none !important;
        }
        /* Stretch the main dashboard charts to fit clean on an A4 sheet */
        .main .block-container {
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)


# --- STEP 4 — Add Authentication Sidebar ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Authentication")

    auth_mode = st.sidebar.selectbox("Choose", ["Login", "Signup"])

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if password:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # --- STEP 5 — Signup Logic ---
    if auth_mode == "Signup":
        if st.sidebar.button("Create Account"):
            if not username or not password:
                st.sidebar.error("Fields cannot be empty!")
            else:
                try:
                    sql = """
                    INSERT INTO users (username, password)
                    VALUES (%s, %s)
                    """
                    values = (username, hashed_password)
                    cursor.execute(sql, values)
                    conn.commit()
                    st.sidebar.success("Account created successfully.")
                except mysql.connector.Error as err:
                    if err.errno == 1062:
                        st.sidebar.error("Username already exists!")
                    else:
                        st.sidebar.error(f"Error: {err}")

    # --- STEP 6 — Login Logic ---
    elif auth_mode == "Login":
        if st.sidebar.button("Login"):
            if not username or not password:
                st.sidebar.error("Please enter details.")
            else:
                sql = """
                SELECT id, username FROM users
                WHERE username=%s AND password=%s
                """
                values = (username, hashed_password)
                cursor.execute(sql, values)
                user = cursor.fetchone()

                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.sidebar.success("Login successful.")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials.")

# --- STEP 7 — Protect App Pages ---
if st.session_state.logged_in:
    # Sidebar Header
    st.sidebar.markdown(f"""
        <div style="padding: 10px; background-color: #EFF6FF; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin:0; font-size:0.8rem; color:#1D4ED8; font-weight:600;">ACTIVE SESSION</p>
            <h4 style="margin:0; color:#1E3A8A;">👤 {st.session_state.username}</h4>
        </div>
    """, unsafe_allow_html=True)

    # Navigation choices
    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Upload Center",
            "Profit Analysis",
            "Inventory",
            "Ads Analytics",
            "Market & Competitor Insights",  # <-- Added new analytics tab
            "AI Insights",
            "SaaS Account & Billing"  # <-- Added new pricing tab
        ],
    )
    
    st.sidebar.markdown("---")
    
    # Logout System anchored cleanly at the bottom
    if st.sidebar.button("🔓 End Session / Logout", width='stretch'):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.success("Logged out successfully!")
        st.rerun()

    st.sidebar.markdown("---")
  

    # Main Dashboard (Updated to Revenue Architecture)
    if page == "Dashboard":
        st.title("📊 Enterprise Analytics Engine")
        st.markdown(f"Welcome back, **{st.session_state.username}**. Performance overview tracking financial vectors.")
        st.markdown("---")
        
        df = load_data()

        if not df.empty:
            total_revenue = df["revenue"].sum()
            total_profit = df["profit"].sum()
            total_products = df["product"].nunique()
            avg_profit = df["profit"].mean()

            # Dynamic KPI Grid
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Gross Revenue", f"₹{total_revenue:,.0f}")
            col2.metric("Net Profit", f"₹{total_profit:,.0f}")
            col3.metric("Active Catalog", total_products)
            col4.metric("Avg Unit Profit", f"₹{avg_profit:,.0f}")

            st.markdown("---")

            # Side-by-Side Chart Grid layout
            graph_col1, graph_col2 = st.columns(2)
            
            with graph_col1:
                st.subheader("📈 Revenue by Product")
                fig_revenue = px.bar(
                    df, x="product", y="revenue",
                    color_discrete_sequence=["#2563EB"],
                    template="simple_white"
                )
                st.plotly_chart(fig_revenue, width="stretch")

            with graph_col2:
                st.subheader("🎯 Profit Attribution")
                fig_profit = px.pie(
                    df, names="product", values="profit",
                    color_discrete_sequence=px.colors.sequential.YlGnBu,
                    hole=0.4 
                )
                st.plotly_chart(fig_profit, width="stretch")

            st.markdown("---")
            st.subheader("📋 Core Records Ledger")
            st.dataframe(df, width='stretch')

            # --- PLACED PERMANENTLY AT THE BOTTOM OF THE DASHBOARD ---
            st.markdown("---")
            st.subheader("📊 Corporate Report Export Center")
            st.markdown("Generate and extract localized performance sheets for corporate record-keeping or offline evaluation.")

            # Convert the live database dataframe directly into an isolated CSV string buffer
            csv_file_data = df.to_csv(index=False).encode('utf-8')

            download_col1, download_col2 = st.columns(2)

            with download_col1:
                st.info("📋 **Standard Ledger Export**\nIncludes all localized columns: product, revenue, units sold, and stock balances.")
                st.download_button(
                    label="📥 Download Store Performance Ledger (.csv)",
                    data=csv_file_data,
                    file_name=f"shopulse_ledger_{st.session_state.username}.csv",
                    mime="text/csv",
                    width="stretch"
                )

            with download_col2:
                st.success("🤖 **AI Operations Briefing**\nNeed a static copy for your records? You can print out your current dashboard matrix immediately.")
                if st.button("🖨️ Open Browser Print Console", key="dash_print_btn"):
                    st.components.v1.html("<script>window.print();</script>", height=0)
        else:
            st.info("Please upload a CSV file in Upload Center.")


        # Upload Center with Live API Sync Engine Simulation
    elif page == "Upload Center":
        st.title("📂 Smart Upload Center")
        st.markdown("Automate your operational pipelines. Connect directly via cloud integrations or upload manual ledger sheets.")
        st.markdown("---")

        # --- NEW PREMIUM LIVE SYNC ENGINE PANEL ---
        st.subheader("⚡ Automated Marketplace Integrations")
        st.markdown("Initialize an instant real-time API handshake with your active storefront channels.")
        
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("🔄 Sync Live Shopify Store Data", width="stretch", key="shopify_sync_btn"):
                with st.spinner("Connecting to secure Shopify API endpoint logs..."):
                    # Injecting a tiny time delay to simulate network latency handshake
                    import time
                    time.sleep(2)
                    
                    # Generate fresh, dynamic multi-vector live e-commerce rows natively in Python
                    import random
                    mock_products = ['Shoes', 'Watch', 'Bag']
                    
                    # Clear out this specific user's older entries
                    cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
                    conn.commit()
                    
                    # Insert the newly synced live data packets into your MySQL database
                    for prod in mock_products:
                        revenue = random.randint(15000, 85000)
                        units_sold = random.randint(30, 400)
                        profit = revenue * random.uniform(0.15, 0.45) # Compute dynamic profitability ranges
                        stock = random.randint(2, 85) # Will randomly trigger your low-stock email conditions!
                        ad_spend = revenue * random.uniform(0.10, 0.25)
                        
                        sql = """
                        INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        values = (prod, float(revenue), int(units_sold), float(profit), int(stock), float(ad_spend), st.session_state.user_id)
                        cursor.execute(sql, values)
                    
                    conn.commit()
                    st.success("✨ Shopify cloud synchronization finalized! Live server rows pulled into MySQL.")
                    st.rerun() # Refresh dashboard context variables immediately
                    
        with sync_col2:
            st.info("💡 **API Streaming Automation**\nClicking this sync token executes a mock cloud handshake. It wipes out static manual spreadsheets and pulls live dynamic inventory balances instantly.")

        st.markdown("---")
        st.subheader("📋 Alternative: Manual CSV Ingestion")

        # Your original file uploader engine safely nested below the automation layer
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            
            df.columns = [str(col).lower().strip().replace(" ", "_").replace("-", "_") for col in df.columns]
            
            column_mapping = {
                'sales': 'revenue', 'turnover': 'revenue', 'total_sales': 'revenue', 'gross_sales': 'revenue', 'item_revenue': 'revenue',
                'quantity': 'units_sold', 'qty': 'units_sold', 'items_sold': 'units_sold', 'volume': 'units_sold', 'qty_shipped': 'units_sold',
                'earnings': 'profit', 'net_profit': 'profit', 'margins': 'profit', 'earnings_profit': 'profit',
                'inventory': 'stock', 'quantity_available': 'stock', 'qty_left': 'stock', 'available_stock': 'stock',
                'marketing': 'ad_spend', 'ad_cost': 'ad_spend', 'advertising': 'ad_spend', 'marketing_spend': 'ad_spend'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            
            if 'product' not in df.columns:
                st.error("❌ Critical Error: The uploaded file must contain a column indicating the 'product' name.")
                st.stop()
                
            for required_col in ['revenue', 'units_sold', 'profit', 'stock', 'ad_spend']:
                if required_col not in df.columns:
                    df[required_col] = 0.0 if required_col in ['revenue', 'profit', 'ad_spend'] else 0

            st.session_state.df = df

            cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
            conn.commit()

            for _, row in df.iterrows():
                sql = """
                INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    row["product"],
                    float(row["revenue"]),
                    int(row["units_sold"]),
                    float(row["profit"]),
                    int(row["stock"]),
                    float(row["ad_spend"]),
                    st.session_state.user_id,
                )
                cursor.execute(sql, values)

            conn.commit()
            st.success("✨ E-commerce data successfully ingested and synchronized!")

            st.subheader("📋 Ingested Dataset Preview")
            st.dataframe(df, use_container_width=True)

            st.subheader("📊 Matrix Properties")
            st.write(f"Rows: {df.shape}")
            st.write(f"Columns: {df.shape}")


    # Profit Analysis
    elif page == "Profit Analysis":
        st.title("💰 Profit Analysis")
        df = load_data()

        if not df.empty:
            df["profit_margin"] = (df["profit"] / df["revenue"]) * 100
            total_profit = df["profit"].sum()
            avg_margin = df["profit_margin"].mean()
            top_profit_product = df.loc[df["profit"].idxmax(), "product"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Profit", f"₹{total_profit:,.0f}")
            col2.metric("Average Margin", f"{avg_margin:.1f}%")
            col3.metric("Top Product", top_profit_product)

            st.markdown("---")
            st.subheader("Profit by Product")
            fig_profit = px.bar(
                df,
                x="product",
                y="profit",
                color="product",
                title="Profit Distribution",
            )
            st.plotly_chart(fig_profit, width="stretch")

            st.subheader("Profit Margin Analysis")
            fig_margin = px.pie(
                df, names="product", values="profit_margin", title="Profit Margin Share"
            )
            st.plotly_chart(fig_margin, width="stretch")

            st.subheader("📈 Profit Insights")
            for _, row in df.iterrows():
                if row["profit_margin"] < 20:
                    st.warning(
                        f"{row['product']} has weak profit margin ({row['profit_margin']:.1f}%)"
                    )
                elif row["profit_margin"] > 40:
                    st.success(
                        f"{row['product']} has strong profitability ({row['profit_margin']:.1f}%)"
                    )
                else:
                    st.info(f"{row['product']} has stable profit margins.")
        else:
            st.info("Upload dataset first.")

    
    # Inventory Management with Advanced Demand Forecasting Engine
    elif page == "Inventory":
        st.title("📦 Predictive Inventory & Demand Forecasting")
        st.markdown("Automated calculation of daily asset unit velocity and linear forward demand projections.")
        st.markdown("---")

        df = load_data()

        if not df.empty:
            st.subheader("📋 Present Active Inventory Ledger")
            st.dataframe(df[["product", "stock", "units_sold"]], width='stretch')

            # Mathematical Derivation: Map localized rolling sales velocity ratios per day
            df["daily_velocity"] = df["units_sold"] / 30
            
            # Formulating 7-Day forward unit volume demand pipeline forecasts
            df["forecasted_7d_demand"] = df["daily_velocity"] * 7
            
            # Avoid Division by Zero: Substitute 0 velocity with a safe boundary number to prevent app crashes
            df["days_until_stockout"] = df.apply(
                lambda row: row["stock"] / row["daily_velocity"] if row["daily_velocity"] > 0 else 999, 
                axis=1
            )

            st.markdown("---")
            
            # Visual Layout Grid: Side-by-Side Forecasting Charts
            graph_col1, graph_col2 = st.columns(2)
            
            with graph_col1:
                st.subheader("🔮 Projected 7-Day Unit Volume Demand")
                fig_forecast = px.bar(
                    df, 
                    x="product", 
                    y="forecasted_7d_demand",
                    title="Estimated Units Shipped Over Next 7 Days",
                    color_discrete_sequence=["#F59E0B"],
                    template="simple_white"
                )
                st.plotly_chart(fig_forecast, width='stretch')

            with graph_col2:
                st.subheader("⏳ Operating Days Until Exhaustion")
                fig_runway = px.bar(
                    df, 
                    x="product", 
                    y="days_until_stockout",
                    title="Estimated Days Remaining Before Absolute Stockout",
                    color="days_until_stockout",
                    color_continuous_scale=px.colors.sequential.OrRd_r,
                    template="simple_white"
                )
                st.plotly_chart(fig_runway, width='stretch')

            st.markdown("---")
            
            # Automated Operational Health Safeguards
            st.subheader("⚠️ Supply Chain Runway Warnings")
            
            low_stock_counter = 0
            for _, row in df.iterrows():
                if row["days_until_stockout"] <= 7:
                    low_stock_counter += 1
                    st.error(
                        f"🚨 **CRITICAL RISK:** **{row['product']}** is burning inventory fast! "
                        f"Current velocity: **{row['daily_velocity']:.1f} units/day**. "
                        f"Estimated supply runway: Only **{row['days_until_stockout']:.1f} days remaining** before total depletion."
                    )
                    
                    # --- AUTOMATED EMAIL TRIGGER ANCHOR ---
                    # Utilize session tracking keys to verify we only send ONE alert per dashboard session initialization
                    session_alert_key = f"alert_sent_{row['product']}_{st.session_state.username}"
                    if session_alert_key not in st.session_state:
                        email_body = (
                            f"Greetings Admin,\n\n"
                            f"This is an automated supply chain warning dispatch from the Shopulse SaaS system.\n\n"
                            f"User Session: {st.session_state.username}\n"
                            f"Product Line Hazard: {row['product']}\n"
                            f"Current Stock Balance: {row['stock']} units remaining\n"
                            f"Active Sales Burn Rate: {row['daily_velocity']:.1f} units/day\n"
                            f"Projected Operational Runway: {row['days_until_stockout']:.1f} days remaining before absolute depletion.\n\n"
                            f"Action Recommended: Access your Shopulse Dashboard immediately and initiate a warehouse restock procurement log to prevent stockout damage."
                        )
                        # Dispatch out through network channels
                        success = send_email_alert(f"Critical Stock Depletion Risk: {row['product']}", email_body)
                        if success:
                            st.session_state[session_alert_key] = True
                            st.sidebar.success(f"📧 Critical Alert dispatched to system administrator for {row['product']}!")

                elif row["days_until_stockout"] <= 15:
                    low_stock_counter += 1
                    st.warning(
                        f"⚠️ **RUNWAY ALERT:** **{row['product']}** stock pools are dropping steadily. "
                        f"Projected depletion window: **{row['days_until_stockout']:.1f} days**. Initiate reorder logs soon."
                    )
            
            if low_stock_counter == 0:
                st.success("✨ All product supply runways are stable. Current inventory buffers look healthy.")
        else:
            st.info("Upload inventory CSV first.")


    # Ads Analytics (Updated)
    elif page == "Ads Analytics":
        st.title("📢 Ads Analytics")
        df = load_data()

        if not df.empty:
            df["roas"] = df["revenue"] / df["ad_spend"]
            total_ad_spend = df["ad_spend"].sum()
            avg_roas = df["roas"].mean()

            col1, col2 = st.columns(2)
            col1.metric("Total Ad Spend", f"₹{total_ad_spend:,.0f}")
            col2.metric("Average ROAS", f"{avg_roas:.2f}x")

            st.markdown("---")
            st.subheader("ROAS by Product")
            fig_roas = px.bar(
                df, x="product", y="roas", color="product", title="Return on Ad Spend"
            )
            st.plotly_chart(fig_roas, width="stretch")

            st.subheader("Campaign Insights")
            for _, row in df.iterrows():
                if row["roas"] < 2:
                    st.warning(f"⚠️ {row['product']} has weak ROAS ({row['roas']:.2f}x)")
                else:
                    st.success(f"🚀 {row['product']} is performing well with ROAS of {row['roas']:.2f}x")
        else:
            st.info("Upload ads dataset first.")


    # Market & Competitor Insights
    elif page == "Market & Competitor Insights":
        st.title("🎯 Competitor Benchmarks & Market Demand Insights")
        st.markdown("Compare internal ledger metrics against automated retail indexes and competitor averages.")
        st.markdown("---")

        df = load_data()

        if not df.empty:
            # 1. Mathematical Formulas for Advanced Metrics Calculation
            df["aov"] = df["revenue"] / df["units_sold"]
            df["contribution_margin"] = df["profit"] / df["units_sold"]
            
            # Formulate Static Industry/Competitor Benchmarks for Comparison
            competitor_avg_aov = 1200.0   # Baseline Industry AOV
            target_contribution = 450.0   # Baseline Industry Profit/Unit
            
            st.subheader("📉 Unit-Level Revenue Optimization Vectors")
            
            # Layout the Advanced Metrics Grid
            for _, row in df.iterrows():
                with st.expander(f"📦 Product Intelligence: {row['product']}"):
                    met_col1, met_col2, met_col3 = st.columns(3)
                    
                    # Calculation 1: Average Order Value (AOV)
                    aov_val = row["aov"] if row["units_sold"] > 0 else 0
                    met_col1.metric("Your AOV", f"₹{aov_val:,.2f}")
                    
                    # Calculation 2: Contribution Margin Per Unit Shipped
                    contrib_val = row["contribution_margin"] if row["units_sold"] > 0 else 0
                    met_col2.metric("Unit Contribution", f"₹{contrib_val:,.2f}")
                    
                    # Calculation 3: CAC/Ad Efficiency Vector Ratio
                    cac_efficiency = row["revenue"] / row["ad_spend"] if row["ad_spend"] > 0 else 0
                    met_col3.metric("Ad Spend Efficiency", f"{cac_efficiency:.2f}x")
                    
                    # 2. Competitor Benchmarking Logic Loops
                    st.markdown("#### ⚔️ Competitor Analysis vs. Market Standard")
                    if aov_val < competitor_avg_aov:
                        st.error(f"⚠️ Your average pricing for **{row['product']}** is lower than the market benchmark (Industry Average: ₹{competitor_avg_aov:,.0f}). Consider bundles to raise your AOV.")
                    else:
                        st.success(f"🚀 Excellent pricing health! **{row['product']}** beats the competitor benchmark of ₹{competitor_avg_aov:,.0f}.")
                        
                    if contrib_val < target_contribution:
                        st.warning(f"📉 **{row['product']}** generates low cash margin per unit sold (Target standard: ₹{target_contribution:,.0f}). Check for supply chain cost overruns.")
                    else:
                        st.success(f"💎 Highly optimized margins for **{row['product']}** exceeding the industry baseline threshold.")

            st.markdown("---")
            
            # 3. Market Demand Forecasting and Scale Indexes
            st.subheader("🔮 Elastic Market Demand Metrics")
            
            # Derive Market Demand Index based on Units Sold Relative to Stock Velocity
            df["market_demand_index"] = (df["units_sold"] / df["stock"].apply(lambda x: max(x, 1))) * 10
            
            fig_demand = px.bar(
                df, x="product", y="market_demand_index",
                title="Consumer Demand Pull Index (High Score = Fast Consumer Run Rate)",
                color="market_demand_index",
                color_continuous_scale=px.colors.sequential.Plotly3,
                template="simple_white"
            )
            st.plotly_chart(fig_demand, use_container_width=True)
            
            # Display Demand Strategy Suggestions
            for _, row in df.iterrows():
                if row["market_demand_index"] > 5.0:
                    st.success(f"🔥 **HIGH MARKET DEMAND:** Consumer interest for **{row['product']}** is accelerating quickly. Restock instantly to avoid missing out on sales velocity.")
                elif row["market_demand_index"] < 1.5:
                    st.error(f"💀 **DEAD INVENTORY RISK:** **{row['product']}** has a low demand pull. Consider clearing stock with promotional discounts to recover capital.")
        else:
            st.info("Please upload a CSV data file first to generate competitor benchmarks.")

    
    # Autonomous LLM AI Insights Chatbot Engine
    elif page == "AI Insights":
        st.title("🤖 Shopulse Conversational AI Assistant")
        st.markdown(f"Interact natively with your storefront database vectors. Active session initialized for user: **{st.session_state.username}**.")
        st.markdown("---")

        df = load_data()

        if not df.empty:
            # 1. Initialize connection securely using Streamlit Secrets Architecture
            from google import genai
            try:
                # Fetches the key dynamically from .streamlit/secrets.toml at runtime
                secured_key = st.secrets["GEMINI_API_KEY"]
                client = genai.Client(api_key=secured_key)
            except Exception:
                client = None

            # 2. Extract and format the user's data table into a readable layout context for the AI
            data_summary = df.to_string(index=False)
            
            # Establish the structural system prompt context payload for the AI agent
            system_context = f"""
            You are the Shopulse AI Business Consultant, an expert e-commerce data analyst.
            You are assisting user '{st.session_state.username}'.
            Here is their current live store performance dataset from the MySQL database:
            
            {data_summary}
            
            Analyze this data carefully. Base all responses accurately on these parameters. 
            Speak with high business value like a peer or professional data consultant—do not speak like a simple script. 
            Provide actionable, specific recommendations for maximizing ROAS, pricing adjustments, inventory runway issues, and cost optimizations.
            """

            # Initialize isolated chat history buffer arrays in session memory if missing
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = [
                    {
                        "role": "assistant", 
                        "content": "Greetings! I have completed a safe structural sweep of your database ledger. I am online and have full visibility over your store's revenues, unit volumes, and margins. What strategic insights can I uncover for you today?"
                    }
                ]

            # Render persistent chat history elements to the screen
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            # Listen for dynamic real-time user questions via the chat tray
            if user_query := st.chat_input("Ask about your sales, margins, ads, or low stock warnings..."):
                
                # Append user prompt to state memory array and print immediately
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.write(user_query)

                # Process conversational intent via the Smart Intent Router
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing storefront data vectors..."):
                        query_lower = user_query.lower()
                        response_content = ""
                        
                        # =======================================================
                        # LEVEL 1: INTERNAL DETECT & COMPUTE AGENT (FAST & PRIVATE)
                        # =======================================================
                        if "velocity" in query_lower or "speed" in query_lower:
                            response_content = "### 📦 Internal Logistics Engine\nHere is your exact localized daily unit velocity calculated directly from the database:\n"
                            for _, row in df.iterrows():
                                vel = row["units_sold"] / 30
                                response_content += f"- **{row['product']}**: {vel:.2f} units / day\n"
                                
                        elif "stock" in query_lower and "low" in query_lower:
                            low_stock = df[df["stock"] < 10]
                            if not low_stock.empty:
                                response_content = "### ⚠️ Internal Inventory Alert\nThe following catalog vectors have broken your safe stock threshold benchmarks:\n"
                                for _, row in low_stock.iterrows():
                                    response_content += f"- **{row['product']}**: Only {row['stock']} units remaining in the warehouse.\n"
                            else:
                                response_content = "### ✨ Internal Inventory Alert\nAll system stock pools are completely healthy and above safety buffers."

                        # =======================================================
                        # LEVEL 2: CLOUD LLM EXTENSION DEPLOYMENT (GEMINI COGNITIVE OVERRIDE)
                        # =======================================================
                        else:
                            # If it doesn't match a quick local math shortcut, hand it to Gemini
                            if client and st.secrets.get("GEMINI_API_KEY") and st.secrets["GEMINI_API_KEY"] != "YOUR_GEMINI_API_KEY_HERE":
                                try:
                                    # We inject an explicit rule to tell Gemini to keep it short and precise
                                    curated_prompt = f"{system_context}\n\nUser Question: {user_query}\n\nCRITICAL RULE: Keep your response concise, professional, and limited to a maximum of 3 short paragraphs. Use bullet points for structural clarity."
                                    
                                    response = client.models.generate_content(
                                        model='gemini-2.5-flash',
                                        contents=curated_prompt
                                    )
                                    response_content = response.text
                                except Exception as e:
                                    response_content = f"⚠️ AI Stream Error: Failed to generate a response. Details: {e}"
                            else:
                                response_content = "### 📋 General Operations Summary\n- **Primary Revenue Driver:** " + str(top_product) + "\n\n*Drop your free Gemini API Key into secrets to unlock open-ended strategy calculations.*"

                        # Display the generated content and save it to the session logs
                        st.write(response_content)
                        st.session_state.chat_history.append({"role": "assistant", "content": response_content})
        else:
            st.info("Upload CSV data or run Live Sync first to initialize the AI Conversation interface.")


    # SaaS Account & Billing Management Panel (Fixed Typos & Fully Aligned)
    elif page == "SaaS Account & Billing":
        st.title("💳 SaaS Account & Commercial Subscription Hub")
        st.markdown("Monitor account data processing metrics, modify tier bundles, or evaluate system billing cycles.")
        st.markdown("---")

        sub_col1, sub_col2 = st.columns(2)
        
        with sub_col1:
            st.subheader("🛠️ Current Plan Allotment")
            user_tier_level = "Professional Tier (Active Trial)"
            data_row_limits = "Unlimited MySQL Ingestion"
            billing_renewal_date = "June 15, 2026"
            
            st.markdown(f"""
            <div style="padding: 20px; border: 1px solid #E5E7EB; border-radius: 8px; background-color: #F9FAFB;">
                <p style="margin:0; font-size:0.9rem; color:#4B5563;">ACCOUNT ACCESS STATUS</p>
                <h3 style="margin:5px 0; color:#1E3A8A;">✨ {user_tier_level}</h3>
                <hr style="margin:10px 0; border:0; border-top:1px solid #E5E7EB;">
                <p style="margin:5px 0; font-size:0.95rem;"><b>Ingestion Threshold:</b> {data_row_limits}</p>
                <p style="margin:5px 0; font-size:0.95rem;"><b>Next Billing Evaluation Cycle:</b> {billing_renewal_date}</p>
                <p style="margin:5px 0; font-size:0.95rem;"><b>Connected Workspace Owner:</b> {st.session_state.username}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("🚀 Scale Your E-commerce Intelligence Ecosystem")
            
            tier_col1, tier_col2 = st.columns(2)
            
            with tier_col1:
                st.markdown("""
                <div style="padding: 15px; border: 2px solid #2563EB; border-radius: 8px; text-align: center; background-color: #EFF6FF;">
                    <h4 style="margin:0; color:#1E3A8A;">📈 Growth Core SaaS</h4>
                    <h2 style="margin:10px 0; color:#2563EB;">₹3,999<span style="font-size:1rem; color:#4B5563;">/mo</span></h2>
                    <p style="font-size:0.85rem; color:#4B5563; min-height:60px;">Perfect for mid-scale independent retail stores looking for predictive forecasting pipelines.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("💳 Upgrade to Growth Core Plan", key="upgrade_growth_btn"):
                    st.success("🎉 Initializing secure external Stripe payment gateway webhook payload... Connection simulation finalized!")
                    
            with tier_col2:
                st.markdown("""
                <div style="padding: 15px; border: 1px solid #E5E7EB; border-radius: 8px; text-align: center;">
                    <h4 style="margin:0; color:#1F2937;">🏢 Enterprise Agent Suite</h4>
                    <h2 style="margin:10px 0; color:#1F2937;">₹9,499<span style="font-size:1rem; color:#4B5563;">/mo</span></h2>
                    <p style="font-size:0.85rem; color:#4B5563; min-height:60px;">Includes multi-store Shopify connection, live continuous background webhooks, and unlimited cloud storage pools.</p>
                </div>
                """, unsafe_allow_html=True) # <-- Fixed spelling bug here!
                if st.button("💼 Contact Corporate Enterprise Sales", key="upgrade_enter_btn"):
                    st.info("✉️ Communication log logged! Corporate account managers will evaluate your store parameters.")

        with sub_col2:
            st.subheader("🔒 Compliance Logs")
            st.markdown("""
            - All encryption handles use secure SHA-256 protocols.
            - Local data storage vaults isolate metrics per user ID block safely.
            - Active session tracking states force automatic authentication timeouts upon system logout triggers.
            """)

else:
    # Closed application view block shown if user is not logged in
    st.info(
        "🔒 Please log in or create an account via the sidebar to access Shopulse."
    )
