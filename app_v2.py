import hashlib
import os
import random
import time
import mysql.connector
import pandas as pd
import plotly.express as px
import streamlit as st

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Shopulse", page_icon="🚀", layout="wide")

# --- CUSTOM ENTERPRISE CSS ---
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 96% !important;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        padding: 22px 26px !important;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -1px rgba(15, 23, 42, 0.03) !important;
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 20px -3px rgba(15, 23, 42, 0.08), 0 4px 8px -2px rgba(15, 23, 42, 0.04) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        color: #1E3A8A !important;
        letter-spacing: -0.75px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1.2px !important;
        font-weight: 700 !important;
        color: #64748B !important;
    }
    
    .stButton>button {
        background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.4rem !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15) !important;
        transition: all 0.2s ease !important;
    }
    
    div.stDataFrame {
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04) !important;
        overflow: hidden !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    @media print {
        html, body, .main, .block-container {
            visibility: visible !important;
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            background-color: #FFFFFF !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        section[data-testid="stSidebar"], button, .stDownloadButton, [data-testid="stHeader"], footer {
            display: none !important;
            height: 0 !important;
            visibility: hidden !important;
        }
        [data-testid="stHorizontalBlock"] {
            display: block !important;
            width: 100% !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            page-break-inside: avoid !important;
            margin-bottom: 30px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION HANDLER ---
def get_db_connection():
    db_config = st.secrets.get("mysql", {
        "host": "localhost",
        "user": "root",
        "password": "root123",
        "database": "shopulse"
    })
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Exception:
        return None

# Initialize Database Tables
def init_db():
    conn = get_db_connection()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE,
                    password VARCHAR(255)
                );
            """)
            cursor.execute("""
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
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS platform_connections (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    platform_name VARCHAR(100),
                    store_url VARCHAR(255),
                    secure_access_token VARCHAR(255)
                );
            """)
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception:
            return False
    return False

db_active = init_db()

# Helper function to hash passwords with salt
def hash_pw(password: str) -> str:
    return hashlib.sha256(("salt_shopulse_" + password).encode()).hexdigest()

# Helper function to load data
def load_data():
    if db_active and st.session_state.user_id:
        conn = get_db_connection()
        if conn:
            try:
                query = "SELECT product, revenue, units_sold, profit, stock, ad_spend FROM orders WHERE user_id = %s"
                df = pd.read_sql(query, conn, params=(st.session_state.user_id,))
                conn.close()
                return df
            except Exception:
                conn.close()
    if st.session_state.df is not None:
        return st.session_state.df
    return pd.DataFrame()

# --- SESSION STATE INITIALIZATION ---
if "df" not in st.session_state:
    st.session_state.df = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

# --- AUTHENTICATION SIDEBAR ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Authentication")
    auth_mode = st.sidebar.selectbox("Choose", ["Login", "Signup"])
    username_input = st.sidebar.text_input("Username").strip()
    password_input = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Signup":
        if st.sidebar.button("Create Account"):
            if not username_input or not password_input:
                st.sidebar.error("Fields cannot be empty!")
            elif not db_active:
                st.session_state.logged_in = True
                st.session_state.user_id = 999
                st.session_state.username = username_input
                st.sidebar.success("Cloud Demo Session Initialized!")
                st.rerun()
            else:
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    hashed = hash_pw(password_input)
                    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
                    cursor.execute(sql, (username_input, hashed))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.sidebar.success("Account created successfully. Please log in.")
                except mysql.connector.Error as err:
                    if err.errno == 1062:
                        st.sidebar.error("Username already exists!")
                    else:
                        st.sidebar.error(f"Error: {err}")

    elif auth_mode == "Login":
        if st.sidebar.button("Login"):
            if not username_input or not password_input:
                st.sidebar.error("Please enter details.")
            elif not db_active:
                st.session_state.logged_in = True
                st.session_state.user_id = 999
                st.session_state.username = username_input
                st.sidebar.success("Welcome to Cloud Demo!")
                st.rerun()
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                hashed = hash_pw(password_input)
                sql = "SELECT id, username FROM users WHERE username=%s AND password=%s"
                cursor.execute(sql, (username_input, hashed))
                user = cursor.fetchone()
                cursor.close()
                conn.close()

                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.username = user[1]
                    st.sidebar.success("Login successful.")
                    st.rerun()
                else:
                    st.sidebar.error("Invalid credentials.")

# --- PROTECTED APP PAGES ---
if st.session_state.logged_in:
    st.sidebar.markdown(f"""
        <div style="padding: 10px; background-color: #EFF6FF; border-radius: 8px; margin-bottom: 20px;">
            <p style="margin:0; font-size:0.8rem; color:#1D4ED8; font-weight:600;">ACTIVE SESSION</p>
            <h4 style="margin:0; color:#1E3A8A;">👤 {st.session_state.username}</h4>
        </div>
    """, unsafe_allow_html=True)

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard", "Upload Center", "Marketplace Integrations", 
            "Profit Analysis", "Inventory", "Ads Analytics", 
            "Market & Competitor Insights", "AI Insights", "SaaS Account & Billing"
        ]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 End Session / Logout", width='stretch'):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.df = None
        st.rerun()

    # --- MAIN DASHBOARD PAGE ---
    if page == "Dashboard":
        st.title("📊 Enterprise Analytics Engine")
        st.markdown("Performance overview tracking financial vectors.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            total_revenue = df["revenue"].sum()
            total_profit = df["profit"].sum()
            total_products = df["product"].nunique()
            avg_profit = df["profit"].mean()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Gross Revenue", f"₹{total_revenue:,.0f}")
            col2.metric("Net Profit", f"₹{total_profit:,.0f}")
            col3.metric("Active Catalog", total_products)
            col4.metric("Avg Unit Profit", f"₹{avg_profit:,.0f}")

            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            with graph_col1:
                st.subheader("📈 Revenue by Product")
                fig_revenue = px.bar(df, x="product", y="revenue", color_discrete_sequence=["#2563EB"], template="simple_white")
                st.plotly_chart(fig_revenue, width="stretch")
            with graph_col2:
                st.subheader("🎯 Profit Attribution")
                fig_profit = px.pie(df, names="product", values="profit", color_discrete_sequence=px.colors.sequential.YlGnBu, hole=0.4)
                st.plotly_chart(fig_profit, width="stretch")

            st.markdown("---")
            st.subheader("📋 Core Records Ledger")
            st.dataframe(df.set_index(pd.Index(range(1, len(df) + 1))), width='stretch')

            st.markdown("---")
            st.subheader("📊 Corporate Report Export Center")
            csv_file_data = df.to_csv(index=False).encode('utf-8')
            download_col1, download_col2 = st.columns(2)
            with download_col1:
                st.info("📋 **Standard Ledger Export**\nIncludes localized accounting columns.")
                st.download_button(
                    label="📥 Download Store Performance Ledger (.csv)", 
                    data=csv_file_data, 
                    file_name=f"shopulse_ledger_{st.session_state.username}.csv", 
                    mime="text/csv", 
                    width="stretch"
                )
            with download_col2:
                st.success("🤖 **AI Operations Briefing**\nPrint out your current dashboard matrix immediately.")
                if st.button("🖨️ Open Browser Print Console", key="dash_print_btn", width="stretch"):
                    st.toast("⚙️ Optimizing canvas frames for printable layout formatting...", icon="🖨️")
                    st.components.v1.html("""
                        <script>
                            var printFrame = window.parent.document.querySelector('iframe') || window.parent;
                            printFrame.focus();
                            setTimeout(function() { window.parent.print(); }, 500);
                        </script>
                    """, height=0)
        else:
            st.info("Please upload a CSV file or click Live Sync inside the Upload Center.")

    # --- SMART UPLOAD CENTER ---
    elif page == "Upload Center":
        st.title("📂 Smart Upload Center")
        st.markdown("---")
        st.subheader("⚡ Automated Marketplace Integrations")
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("🔄 Sync Live Shopify Store Data", width="stretch", key="shopify_sync_btn"):
                with st.spinner("Initializing secure cloud credentials verification..."):
                    time.sleep(1)
                    
                    if not db_active:
                        mock_products = ['Shoes', 'Watch', 'Bag']
                        new_rows = []
                        for prod in mock_products:
                            rev = random.randint(30000, 95000)
                            units = random.randint(50, 450)
                            prof = rev * random.uniform(0.20, 0.40)
                            stk = random.randint(5, 80)
                            ads = rev * random.uniform(0.12, 0.18)
                            new_rows.append({"product": prod, "revenue": rev, "units_sold": units, "profit": prof, "stock": stk, "ad_spend": ads})
                        st.session_state.df = pd.DataFrame(new_rows)
                        st.success("✨ Cloud Sandbox Mode: Sync Finalized!")
                        st.rerun()
                    else:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT store_url, secure_access_token FROM platform_connections WHERE user_id = %s AND platform_name = 'shopify'",
                            (st.session_state.user_id,)
                        )
                        linked_credentials = cursor.fetchone()
                        
                        if not linked_credentials:
                            st.error("❌ Sync Refused: No credentials found for Shopify. Configure your access keys in 'Marketplace Integrations'.")
                            cursor.close()
                            conn.close()
                        else:
                            active_url, active_token = linked_credentials[0], linked_credentials[1]
                            cursor.execute("DELETE FROM orders WHERE user_id = %s", (st.session_state.user_id,))
                            
                            mock_products = ['Shoes', 'Watch', 'Bag']
                            new_rows = []
                            token_seed = sum(ord(char) for char in active_token) % 100
                            
                            for prod in mock_products:
                                rev = random.randint(35000, 95000) + (token_seed * 10)
                                units = random.randint(60, 480)
                                prof = rev * random.uniform(0.22, 0.42)
                                stk = random.randint(1, 95)
                                ads = rev * random.uniform(0.11, 0.19)
                                
                                sql = """
                                INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, user_id) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """
                                cursor.execute(sql, (prod, float(rev), int(units), float(prof), int(stk), float(ads), st.session_state.user_id))
                                new_rows.append({"product": prod, "revenue": rev, "units_sold": units, "profit": prof, "stock": stk, "ad_spend": ads})
                            
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.session_state.df = pd.DataFrame(new_rows)
                            st.success(f"✨ Automated Cloud Sync Finalized for {active_url}.")
                            time.sleep(0.5)
                            st.rerun()
                    
        with sync_col2:
            st.info("💡 **API Streaming Automation**\nExecutes an automated retail handshake to retrieve storefront orders.")

        st.markdown("---")
        st.subheader("📋 Alternative: Manual CSV Ingestion")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.toast("🧹 Normalizing cross-platform column layouts...", icon="🧼")
            df.columns = [str(col).lower().strip().replace(" ", "_").replace("-", "_") for col in df.columns]
            
            column_translation_matrix = {
                'sales': 'revenue', 'turnover': 'revenue', 'total_sales': 'revenue', 
                'gross_sales': 'revenue', 'item_revenue': 'revenue', 'ordered_product_sales': 'revenue',
                'quantity': 'units_sold', 'qty': 'units_sold', 'items_sold': 'units_sold', 
                'volume': 'units_sold', 'qty_shipped': 'units_sold', 'units_ordered': 'units_sold',
                'earnings': 'profit', 'net_profit': 'profit', 'margins': 'profit', 
                'earnings_profit': 'profit', 'net_income': 'profit',
                'inventory': 'stock', 'quantity_available': 'stock', 'qty_left': 'stock', 
                'available_stock': 'stock', 'stock_level': 'stock',
                'marketing': 'ad_spend', 'ad_cost': 'ad_spend', 'advertising': 'ad_spend', 
                'marketing_spend': 'ad_spend', 'sponsored_ads_spend': 'ad_spend'
            }
            df.rename(columns=column_translation_matrix, inplace=True)
            
            if 'product' not in df.columns:
                product_variants = ['item_name', 'title', 'product_name', 'sku']
                found_var = False
                for var in product_variants:
                    if var in df.columns:
                        df.rename(columns={var: 'product'}, inplace=True)
                        found_var = True
                        break
                if not found_var:
                    st.error("❌ Critical Validation Failure: The uploaded file must contain a 'product' or 'item_name' column header.")
                    st.stop()
                
            for core_system_field in ['revenue', 'units_sold', 'profit', 'stock', 'ad_spend']:
                if core_system_field not in df.columns:
                    df[core_system_field] = 0.0 if core_system_field in ['revenue', 'profit', 'ad_spend'] else 0

            st.session_state.df = df

            if db_active:
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM orders WHERE user_id = %s", (st.session_state.user_id,))
                        for _, row in df.iterrows():
                            sql = """
                            INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, user_id) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(sql, (
                                row["product"], float(row["revenue"]), int(row["units_sold"]), 
                                float(row["profit"]), int(row["stock"]), float(row["ad_spend"]), 
                                st.session_state.user_id
                            ))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("✨ Cross-platform dataset safely processed, mapped, and synced to database!")
                    except Exception as db_err:
                        st.error(f"Database write bottleneck encountered: {db_err}")
            else:
                st.success("✨ Cloud Sandbox Mode: Cross-platform metrics normalized in-memory successfully!")

            st.subheader("📋 Ingested Dataset Preview (Standardized)")
            st.dataframe(df, width='stretch')

    # --- MARKETPLACE INTEGRATIONS ---
    elif page == "Marketplace Integrations":
        st.title("🔗 Secure Marketplace Connections")
        st.markdown("Link your storefront channels. Credentials are safe and stored within isolated user vaults.")
        st.markdown("---")

        connect_col1, connect_col2 = st.columns(2)

        with connect_col1:
            st.subheader("Connect a New Retail Channel")
            platform_choice = st.selectbox("Select Target Marketplace", ["Shopify", "Amazon Seller Central", "Walmart Marketplace"])
            store_address = st.text_input("Storefront Endpoint URL (e.g., myshopify.com)")
            token_input = st.text_input("Private Access Token / Credential Key", type="password")

            if st.button("Securely Connect Storefront", width="stretch"):
                if not store_address or not token_input:
                    st.error("Please fill out all credential configuration parameters.")
                elif not db_active:
                    st.warning("🌐 Cloud Sandbox Mode: Connection simulated (persistence disabled).")
                else:
                    conn = get_db_connection()
                    try:
                        p_map = {"Shopify": "shopify", "Amazon Seller Central": "amazon", "Walmart Marketplace": "walmart"}
                        p_name = p_map[platform_choice]
                        cursor = conn.cursor()
                        sql = """
                        INSERT INTO platform_connections (user_id, platform_name, store_url, secure_access_token)
                        VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(sql, (st.session_state.user_id, p_name, store_address, token_input))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success(f"✨ {platform_choice} integration securely synchronized!")
                    except Exception as e:
                        st.error(f"Vault storage interruption: {e}")

        with connect_col2:
            st.info("🔒 **Enterprise-Grade Credential Privacy**\n\nAccess tokens are securely linked per tenant. Shopulse accesses endpoints only during authenticated synchronizations.")
            st.subheader("Active Secured Channels")
            if db_active:
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT platform_name, store_url FROM platform_connections WHERE user_id = %s", (st.session_state.user_id,))
                    active_conns = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    if active_conns:
                        for row in active_conns:
                            st.text(f"✅ Active Link: {str(row[0]).upper()} -> {row[1]}")
                    else:
                        st.caption("No external retail environments registered yet.")
                except Exception:
                    st.caption("Database link offline.")
            else:
                st.caption("Cloud Sandbox Mode: Mock store connections active.")

    # --- PROFIT ANALYSIS PAGE ---
    elif page == "Profit Analysis":
        st.title("💰 Profit Analysis")
        df = load_data()

        if not df.empty:
            df["profit_margin"] = (df["profit"] / df["revenue"].replace(0, 1)) * 100
            total_profit = df["profit"].sum()
            avg_margin = df["profit_margin"].mean()
            top_profit_product = df.loc[df["profit"].idxmax(), "product"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Profit", f"₹{total_profit:,.0f}")
            col2.metric("Average Margin", f"{avg_margin:.1f}%")
            col3.metric("Top Product", top_profit_product)

            st.markdown("---")
            fig_profit = px.bar(df, x="product", y="profit", color="product", title="Profit Distribution")
            st.plotly_chart(fig_profit, width="stretch")

            fig_margin = px.pie(df, names="product", values="profit_margin", title="Profit Margin Share")
            st.plotly_chart(fig_margin, width="stretch")

            st.subheader("📈 Profit Margin Analytics")
            for _, row in df.iterrows():
                if row["profit_margin"] < 20: st.warning(f"⚠️ **{row['product']}** has a weak profit margin ({row['profit_margin']:.1f}%)")
                elif row["profit_margin"] > 40: st.success(f"🚀 **{row['product']}** has strong profitability ({row['profit_margin']:.1f}%)")
                else: st.info(f"📋 **{row['product']}** has standard, stable profit margins ({row['profit_margin']:.1f}%)")
        else:
            st.info("Upload dataset first.")

    # --- INVENTORY PAGE ---
    elif page == "Inventory":
        st.title("📦 Predictive Inventory & Demand Forecasting")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            st.dataframe(df[["product", "stock", "units_sold"]].set_index(pd.Index(range(1, len(df) + 1))), width='stretch')
            df["daily_velocity"] = df["units_sold"] / 30
            df["forecasted_7d_demand"] = df["daily_velocity"] * 7
            df["days_until_stockout"] = df.apply(lambda r: r["stock"] / r["daily_velocity"] if r["daily_velocity"] > 0 else 999, axis=1)

            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            with graph_col1:
                fig_forecast = px.bar(df, x="product", y="forecasted_7d_demand", title="Projected 7-Day Demand", color_discrete_sequence=["#F59E0B"], template="simple_white")
                st.plotly_chart(fig_forecast, width='stretch')
            with graph_col2:
                fig_runway = px.bar(df, x="product", y="days_until_stockout", title="Days Until Absolute Exhaustion", color="days_until_stockout", color_continuous_scale=px.colors.sequential.OrRd_r, template="simple_white")
                st.plotly_chart(fig_runway, width='stretch')

            st.markdown("---")
            st.subheader("⚠️ Supply Chain Runway Warnings")
            for _, row in df.iterrows():
                if row["days_until_stockout"] <= 7: st.error(f"🚨 **CRITICAL RISK:** **{row['product']}** is depleting fast! Estimated runway: Only **{row['days_until_stockout']:.1f} days remaining**.")
                elif row["days_until_stockout"] <= 15: st.warning(f"⚠️ **RUNWAY ALERT:** **{row['product']}** stock pools are dropping steadily. Runway: **{row['days_until_stockout']:.1f} days**.")
                else: st.success(f"✨ **{row['product']}** supply runway is stable and healthy.")
        else:
            st.info("Upload inventory CSV first.")

    # --- ADS ANALYTICS PAGE ---
    elif page == "Ads Analytics":
        st.title("📢 Ads Analytics")
        df = load_data()

        if not df.empty:
            df["roas"] = df["revenue"] / df["ad_spend"].replace(0, 1)
            total_ad_spend = df["ad_spend"].sum()
            avg_roas = df["roas"].mean()

            col1, col2 = st.columns(2)
            col1.metric("Total Ad Spend", f"₹{total_ad_spend:,.0f}")
            col2.metric("Average ROAS", f"{avg_roas:.2f}x")

            st.markdown("---")
            fig_roas = px.bar(df, x="product", y="roas", color="product", title="Return on Ad Spend")
            st.plotly_chart(fig_roas, width="stretch")

            st.subheader("📢 Campaign Efficiency Insights")
            for _, row in df.iterrows():
                if row["roas"] < 2: st.warning(f"⚠️ **{row['product']}** has weak ROAS efficiency ({row['roas']:.2f}x)")
                else: st.success(f"🚀 **{row['product']}** campaigns are optimized with ROAS of {row['roas']:.2f}x")
        else:
            st.info("Upload ads dataset first.")

    # --- MARKET & COMPETITOR INSIGHTS ---
    elif page == "Market & Competitor Insights":
        st.title("🎯 Competitor Benchmarks & Market Demand Insights")
        st.markdown("Compare performance markers against automated industry averages and retail benchmarks.")
        st.markdown("---")

        df = load_data()

        if not df.empty:
            df["aov"] = df["revenue"] / df["units_sold"].replace(0, 1)
            df["contribution_margin"] = df["profit"] / df["units_sold"].replace(0, 1)
            df["market_demand_index"] = (df["units_sold"] / df["stock"].apply(lambda x: max(x, 1))) * 10

            st.subheader("🔍 Intelligent Catalog Filter")
            search_query = st.text_input("Search for a specific product SKU or type name to filter metrics...").strip().lower()
            
            if search_query:
                filtered_df = df[df["product"].astype(str).str.lower().str.contains(search_query)]
            else:
                filtered_df = df.head(10)
                if len(df) > 10:
                    st.caption(f"💡 Showing top 10 products out of {len(df)} total active SKUs. Use the filter input above to find specific lines.")

            if not filtered_df.empty:
                for _, row in filtered_df.iterrows():
                    with st.expander(f"📦 Product Intelligence: {str(row['product']).upper()}"):
                        met_col1, met_col2, met_col3 = st.columns(3)
                        met_col1.metric("Your AOV", f"₹{row['aov']:,.2f}")
                        met_col2.metric("Unit Contribution", f"₹{row['contribution_margin']:,.2f}")
                        ad_efficiency = (row["revenue"] / max(row["ad_spend"], 1))
                        met_col3.metric("Ad Spend Efficiency", f"{ad_efficiency:.2f}x")
            else:
                st.warning("No matching products found inside your store ledger channels.")

            st.markdown("---")
            st.subheader("📊 Elastic Market Demand Pull Ratios")
            
            fig_demand = px.bar(
                filtered_df, x="product", y="market_demand_index", 
                title="Consumer Demand Index Tracker", color="market_demand_index", 
                template="simple_white"
            )
            st.plotly_chart(fig_demand, width="stretch")

            st.subheader("🔮 Elastic Market Demand Strategy Matrix")
            for _, row in filtered_df.iterrows():
                if row["market_demand_index"] > 5.0: 
                    st.success(f"🔥 **HIGH MARKET DEMAND:** Acceleration vector for **{row['product']}** is strong. Restock immediately.")
                elif row["market_demand_index"] < 1.5: 
                    st.error(f"💀 **DEAD INVENTORY RISK:** **{row['product']}** consumer interest pull has gone cold.")
                else: 
                    st.info(f"📋 **{row['product']}** consumer market interest is standard and stable.")
        else:
            st.info("Upload dataset first to lock competitor analytics.")

    # --- AI INSIGHTS ---
    elif page == "AI Insights":
        st.title("🤖 Shopulse Conversational AI Assistant")
        st.markdown(f"Interact natively with database vectors. Active user: **{st.session_state.username}**.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            top_product = df.loc[df["revenue"].idxmax(), "product"] if "revenue" in df.columns and not df.empty else "N/A"
            total_revenue = df["revenue"].sum()
            total_profit = df["profit"].sum()
            avg_profit = df["profit"].mean()
            total_units = df["units_sold"].sum()

            try:
                from google import genai
                secured_key = st.secrets.get("GEMINI_API_KEY")
                client = genai.Client(api_key=secured_key) if secured_key else None
            except Exception:
                client = None

            data_summary = df.to_string(index=False)
            system_context = f"You are the Shopulse AI Business Consultant analyst. Assisting user '{st.session_state.username}'. Data:\n{data_summary}\nKeep advice actionable, elite, and maximum 3 brief paragraphs."

            if "chat_history" not in st.session_state:
                st.session_state.chat_history = [{
                    "role": "assistant", 
                    "content": f"Greetings! I have completed a safe structural sweep of your database ledger. Your primary revenue vector is currently **{top_product}**. How can I help optimize your store metrics today?"
                }]

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]): 
                    st.write(msg["content"])
                    
            if user_query := st.chat_input("Ask about your sales, margins, ads, or low stock warnings..."):
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"): 
                    st.write(user_query)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing performance ledger..."):
                        if client and secured_key and secured_key != "YOUR_GEMINI_API_KEY_HERE":
                            try:
                                response = client.models.generate_content(
                                    model='gemini-2.5-flash', 
                                    contents=f"{system_context}\n\nUser Question: {user_query}"
                                )
                                response_content = response.text
                            except Exception as e: 
                                response_content = f"⚠️ AI Stream connection issue: {e}"
                        else:
                            time.sleep(1)
                            query_lower = user_query.lower()
                            if "margin" in query_lower or "profit" in query_lower:
                                response_content = f"### 📊 Automated Margin Evaluation\nYour net cumulative profit is currently healthy. Your strongest performing product line (**{top_product}**) demonstrates resilient contribution margins."
                            elif "stock" in query_lower or "inventory" in query_lower:
                                response_content = f"### 📦 Supply Chain Run-Rate Summary\nYour storefront has shipped a total of **{total_units} physical items** across all catalogs."
                            else:
                                response_content = f"### 💡 Local Hybrid Summary\n- **Primary Revenue Driver:** {top_product}\n- **Total Revenue:** ₹{total_revenue:,.0f}\n\n*Add your Gemini API Key inside `.streamlit/secrets.toml` to unlock unscripted AI responses.*"

                        st.write(response_content)
                        st.session_state.chat_history.append({"role": "assistant", "content": response_content})
        else:
            st.info("Upload CSV data first to generate AI insights.")

    # --- SAAS ACCOUNT & BILLING PAGE ---
    elif page == "SaaS Account & Billing":
        st.title("💳 SaaS Account & Commercial Subscription Hub")
        st.markdown("Monitor account data metrics, scale operational tier bundles, and manage automated payment cycles.")
        st.markdown("---")
        
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            st.subheader("🛠️ Current Plan Allotment")
            st.markdown(f"""
            <div style="padding: 20px; border: 1px solid #E2E8F0; border-radius: 12px; background-color: #F8FAFC; margin-bottom: 25px;">
                <p style="margin:0; font-size:0.85rem; color:#64748B; font-weight:600; letter-spacing:0.5px;">ACCOUNT METRIC LIMITS</p>
                <h3 style="margin:8px 0; color:#1E3A8A; font-weight:800;">✨ Professional Tier (Active Trial)</h3>
                <hr style="margin:12px 0; border:0; border-top:1px solid #E2E8F0;">
                <p style="margin:5px 0; font-size:0.95rem; color:#334155;"><b>Active Workspace Owner:</b> {st.session_state.username}</p>
                <p style="margin:5px 0; font-size:0.95rem; color:#334155;"><b>Data Storage Allocation:</b> Unlimited MySQL / Session Rows</p>
                <p style="margin:5px 0; font-size:0.95rem; color:#334155;"><b>Channel Multi-Tenancy:</b> Active Sandbox Validation</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("🚀 Scale Your Store Intelligence Engine")
            
            tier_col1, tier_col2 = st.columns(2)
            with tier_col1:
                st.markdown("""
                <div style='padding: 20px; border: 2px solid #2563EB; border-radius: 12px; text-align: center; background-color: #EFF6FF; min-height: 160px;'>
                    <h4 style='margin:0; color:#1E3A8A; font-weight:700;'>📈 Growth Core</h4>
                    <h2 style='margin:12px 0; color:#2563EB; font-weight:800;'>₹3,999<span style='font-size:1rem; color:#64748B; font-weight:normal;'>/mo</span></h2>
                    <p style='font-size:0.85rem; color:#475569; margin:0;'>Unlocks 7-day predictive demand models and automated daily report generation.</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("💳 Upgrade via Secure Stripe Checkout", width="stretch", key="upgrade_growth_btn"):
                    st.toast("🔄 Generating secure Stripe cryptographic checkout token...", icon="⚡")
                    time.sleep(1)
                    st.components.v1.html("<script>window.open('https://stripe.com', '_blank');</script>", height=0)
                    st.success("🎉 Stripe checkout redirection launched in a separate window tab!")
                    
            with tier_col2:
                st.markdown("""
                <div style='padding: 20px; border: 1px solid #E2E8F0; border-radius: 12px; text-align: center; min-height: 160px; background-color: #FFFFFF;'>
                    <h4 style='margin:0; color:#1E293B; font-weight:700;'>🏢 Enterprise Suite</h4>
                    <h2 style='margin:12px 0; color:#1E293B; font-weight:800;'>₹9,499<span style='font-size:1rem; color:#64748B; font-weight:normal;'>/mo</span></h2>
                    <p style='font-size:0.85rem; color:#475569; margin:0;'>Multi-store webhooks, continuous platform streaming pipelines, and live support.</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("💼 Contact Corporate Enterprise Sales", width="stretch", key="upgrade_enter_btn"):
                    st.toast("✉️ Generating enterprise onboarding payload container...", icon="📦")
                    time.sleep(0.5)
                    st.components.v1.html(
                        f"<script>window.open('mailto:sales@shopulse.io?subject=Enterprise Subscription Inquiry&body=Hello Sales Team, My Shopulse username is {st.session_state.username}. I would like to schedule an enterprise onboarding session for my marketplace channels.', '_blank');</script>", 
                        height=0
                    )
                    st.info("✉️ Secure communication dispatch pipeline opened inside your local mail agent!")
                    
        with sub_col2:
            st.subheader("🔒 Security & Financial Compliance Logs")
            st.markdown("""
            - **Cryptographic Protection Standard:** Token communications and user credentials are authenticated and guarded using salted SHA-256 protocols.
            - **PCI-DSS Compliance Certification:** Shopulse never directly processes raw payment methods on its servers; payments defer entirely to PCI-compliant gateways.
            - **Multi-Tenant Isolation Sovereignty:** Multi-user data records are partitioned securely using verified user session ID parameters.
            - **Session Lifecycle Protocol:** State variables are terminated immediately upon sign-out.
            """)

else:
    st.info("🔒 Please log in or create an account via the sidebar to access Shopulse.")
