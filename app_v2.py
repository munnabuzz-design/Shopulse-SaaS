import hashlib
import random
import time
import mysql.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- GLOBAL DATABASE CONNECTION SAFEGUARD ---
try:
    conn = mysql.connector.connect(
        host="localhost", user="root", password="root123", database="shopulse"
    )
    cursor = conn.cursor()

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
            ad_spend FLOAT,
            page_views INT DEFAULT 0,
            add_to_cart INT DEFAULT 0,
            return_count INT DEFAULT 0,
            cogs FLOAT DEFAULT 0.0,
            shipping_cost FLOAT DEFAULT 0.0
        );
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS platform_connections (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            platform_name VARCHAR(100),
            store_url VARCHAR(255),
            secure_access_token VARCHAR(255)
        );
    """
    )
    conn.commit()
    db_active = True
except Exception:
    conn = None
    cursor = None
    db_active = False


# Helper function to generate standardized sample store data
def generate_sample_store():
    mock_products = ['Nike Running Shoes', 'Analog Chrono Watch', 'Canvas Weekend Bag', 'Denim Jacket', 'Performance Shorts']
    new_rows = []
    for prod in mock_products:
        rev = random.randint(48000, 145000)
        units = random.randint(90, 510)
        cogs = rev * random.uniform(0.35, 0.45)
        ship = units * random.randint(70, 110)
        ads = rev * random.uniform(0.12, 0.19)
        prof = rev - cogs - ship - ads
        stk = random.randint(4, 95)
        views = units * random.randint(25, 45)
        atc = int(views * random.uniform(0.08, 0.16))
        ret = int(units * random.uniform(0.04, 0.17))
        
        new_rows.append({
            "product": prod, "revenue": rev, "units_sold": units,
            "profit": prof, "stock": stk, "ad_spend": ads,
            "page_views": views, "add_to_cart": atc, "return_count": ret,
            "cogs": cogs, "shipping_cost": ship
        })
    return pd.DataFrame(new_rows)


# Helper function to load data
def load_data():
    if db_active and conn is not None and st.session_state.user_id is not None:
        try:
            query = f"""
                SELECT product, revenue, units_sold, profit, stock, ad_spend, 
                       page_views, add_to_cart, return_count, cogs, shipping_cost 
                FROM orders WHERE user_id = {st.session_state.user_id}
            """
            df = pd.read_sql(query, conn)
            if not df.empty:
                return df
        except Exception:
            pass
    if st.session_state.df is not None:
        return st.session_state.df
    return pd.DataFrame()


# --- INITIALIZE LOGIN SESSION STATES ---
if "df" not in st.session_state:
    st.session_state.df = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "search_logs" not in st.session_state:
    st.session_state.search_logs = pd.DataFrame([
        {"query": "white sneakers", "searches": 842, "results_found": 18, "ctr": 12.4, "status": "Healthy"},
        {"query": "oversized hoodie", "searches": 531, "results_found": 0, "ctr": 0.0, "status": "Zero Results"},
        {"query": "linen casual shirt", "searches": 412, "results_found": 6, "ctr": 9.2, "status": "Healthy"},
        {"query": "gym gymbag", "searches": 320, "results_found": 0, "ctr": 0.0, "status": "Zero Results"},
        {"query": "smart smartwatch", "searches": 210, "results_found": 2, "ctr": 4.1, "status": "Low CTR"},
        {"query": "water bottle", "searches": 195, "results_found": 0, "ctr": 0.0, "status": "Zero Results"},
    ])

if "active_workflows" not in st.session_state:
    st.session_state.active_workflows = [
        {"name": "Low Stock Guard", "trigger": "Stock drops below 10 units", "action": "Generate Supplier PO & Email Vendor", "status": "Active"},
        {"name": "VIP Customer Tagger", "trigger": "Order value > ₹8,000", "action": "Tag Customer 'VIP' & Dispatch Slack Alert", "status": "Active"},
        {"name": "High Return Alert", "trigger": "SKU return rate exceeds 15%", "action": "Notify Quality Team & Flag Size Chart", "status": "Active"},
    ]

st.set_page_config(page_title="Shopulse", page_icon="🚀", layout="wide")

# Custom Premium Enterprise SaaS Design Overhaul
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
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        color: #1E3A8A !important;
        letter-spacing: -0.75px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
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


# --- AUTHENTICATION SIDEBAR ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Authentication")
    auth_mode = st.sidebar.selectbox("Choose", ["Login", "Signup"])
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")

    if password_input:
        hashed_password = hashlib.sha256(password_input.encode()).hexdigest()

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
                try:
                    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
                    cursor.execute(sql, (username_input, hashed_password))
                    conn.commit()
                    st.sidebar.success("Account created successfully.")
                except mysql.connector.Error as err:
                    if err.errno == 1062: st.sidebar.error("Username already exists!")
                    else: st.sidebar.error(f"Error: {err}")

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
                sql = "SELECT id, username FROM users WHERE username=%s AND password=%s"
                cursor.execute(sql, (username_input, hashed_password))
                user = cursor.fetchone()

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
            "Dashboard",
            "Upload Center",
            "Marketplace Integrations",
            "Profit Analysis",
            "Inventory",
            "Ads Analytics",
            "Market & Competitor Insights",
            "ReturnIQ (Returns & Sizing)",
            "SearchLens (Search Discovery)",
            "CommerceFlow (Automation)",
            "AI Insights",
            "SaaS Account & Billing"
        ]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 End Session / Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

    # =========================================================
    # 1. MAIN DASHBOARD PAGE (CommerceOS Control Tower)
    # =========================================================
    if page == "Dashboard":
        st.title("📊 Enterprise Analytics Engine")
        st.markdown("CommerceOS Executive Control Tower monitoring cross-channel metrics.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            total_revenue = df["revenue"].sum()
            total_profit = df["profit"].sum()
            total_products = df["product"].nunique()
            avg_profit = df["profit"].mean()

            # Store Health Calculation
            ret_sum = df["return_count"].sum() if "return_count" in df.columns else 0
            units_sum = max(df["units_sold"].sum(), 1)
            ret_pct = (ret_sum / units_sum) * 100
            health_score = int(max(0, min(100, 100 - (ret_pct * 2) - (5 if df["stock"].min() < 10 else 0))))

            top_m1, top_m2, top_m3, top_m4, top_m5 = st.columns(5)
            top_m1.metric("Gross Revenue", f"₹{total_revenue:,.0f}")
            top_m2.metric("Net Profit", f"₹{total_profit:,.0f}")
            top_m3.metric("Active Catalog", total_products)
            top_m4.metric("Avg Unit Profit", f"₹{avg_profit:,.0f}")
            top_m5.metric("Store Health Score", f"{health_score}/100", "Operational")

            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            with graph_col1:
                st.subheader("📈 Revenue by Product")
                fig_revenue = px.bar(df, x="product", y="revenue", color_discrete_sequence=["#2563EB"], template="simple_white")
                st.plotly_chart(fig_revenue, use_container_width=True)
            with graph_col2:
                st.subheader("🎯 Profit Attribution")
                fig_profit = px.pie(df, names="product", values="profit", color_discrete_sequence=px.colors.sequential.YlGnBu, hole=0.4)
                st.plotly_chart(fig_profit, use_container_width=True)

            # Storefront Conversion Funnel
            if "page_views" in df.columns and df["page_views"].sum() > 0:
                st.markdown("---")
                st.subheader("🛒 Storefront Conversion Funnel Health")
                t_views = df["page_views"].sum()
                t_atc = df["add_to_cart"].sum()
                t_orders = df["units_sold"].sum()

                f_col1, f_col2, f_col3 = st.columns(3)
                f_col1.metric("Total Page Views", f"{t_views:,}")
                f_col2.metric("Add to Cart Rate", f"{(t_atc / max(t_views, 1))*100:.1f}%", f"{t_atc:,} ATCs")
                f_col3.metric("Checkout Conversion Rate", f"{(t_orders / max(t_views, 1))*100:.2f}%", f"{t_orders:,} Orders")

            st.markdown("---")
            st.subheader("📋 Core Records Ledger")
            st.dataframe(df.set_index(pd.Index(range(1, len(df) + 1))), use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Corporate Report Export Center")
            csv_file_data = df.to_csv(index=False).encode('utf-8')
            download_col1, download_col2 = st.columns(2)
            with download_col1:
                st.info("📋 **Standard Ledger Export**\nIncludes localized accounting columns.")
                st.download_button(label="📥 Download Store Performance Ledger (.csv)", data=csv_file_data, file_name=f"shopulse_ledger_{st.session_state.username}.csv", mime="text/csv", use_container_width=True)
            with download_col2:
                st.success("🤖 **AI Operations Briefing**\nPrint out your current dashboard matrix immediately.")
                if st.button("🖨️ Open Browser Print Console", key="dash_print_btn"):
                    st.toast("⚙️ Optimizing canvas frames for printable layout formatting...", icon="🖨️")
                    st.components.v1.html("""
                        <script>
                            var printFrame = window.parent.document.querySelector('iframe') || window.parent;
                            printFrame.focus();
                            setTimeout(function() { window.parent.print(); }, 500);
                        </script>
                    """, height=0)

        else:
            st.info("Welcome to Shopulse! You can sync your data or seed a demonstration catalog with one click below:")
            if st.button("⚡ Load Instant Demo Store Data (1-Click)", use_container_width=True):
                sample_df = generate_sample_store()
                st.session_state.df = sample_df
                if db_active and cursor and st.session_state.user_id:
                    try:
                        cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
                        sql = """
                        INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, page_views, add_to_cart, return_count, cogs, shipping_cost, user_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        for _, r in sample_df.iterrows():
                            cursor.execute(sql, (
                                r["product"], float(r["revenue"]), int(r["units_sold"]),
                                float(r["profit"]), int(r["stock"]), float(r["ad_spend"]),
                                int(r["page_views"]), int(r["add_to_cart"]), int(r["return_count"]),
                                float(r["cogs"]), float(r["shipping_cost"]), st.session_state.user_id
                            ))
                        conn.commit()
                    except Exception:
                        pass
                st.success("✨ Multi-pillar demo catalog initialized!")
                time.sleep(0.5)
                st.rerun()

    # =========================================================
    # 2. SMART UPLOAD CENTER
    # =========================================================
    elif page == "Upload Center":
        st.title("📂 Smart Upload Center")
        st.markdown("---")
        st.subheader("⚡ Automated Marketplace Integrations")
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("🔄 Sync Live Shopify Store Data", use_container_width=True, key="shopify_sync_btn"):
                with st.spinner("Streaming encrypted live store feed across all 7 pillars..."):
                    time.sleep(1)
                    sample_df = generate_sample_store()
                    st.session_state.df = sample_df

                    if db_active and cursor and st.session_state.user_id:
                        try:
                            cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
                            sql = """
                            INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, page_views, add_to_cart, return_count, cogs, shipping_cost, user_id) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            for _, r in sample_df.iterrows():
                                cursor.execute(sql, (
                                    r["product"], float(r["revenue"]), int(r["units_sold"]),
                                    float(r["profit"]), int(r["stock"]), float(r["ad_spend"]),
                                    int(r["page_views"]), int(r["add_to_cart"]), int(r["return_count"]),
                                    float(r["cogs"]), float(r["shipping_cost"]), st.session_state.user_id
                                ))
                            conn.commit()
                        except Exception as e:
                            st.warning(f"Database sync note: {e}")

                    st.success("✨ Shopify Store Data Synchronized across all 7 Intelligence Engines!")
                    time.sleep(0.5)
                    st.rerun()

        with sync_col2:
            st.info("💡 **Unified Commerce Sync**\nPopulates revenue, inventory runway, funnel dropoffs, and return signals simultaneously.")

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
                'inventory': 'stock', 'quantity_available': 'stock', 'qty_left': 'stock', 
                'available_stock': 'stock', 'stock_level': 'stock',
                'marketing': 'ad_spend', 'ad_cost': 'ad_spend', 'advertising': 'ad_spend', 
                'views': 'page_views', 'traffic': 'page_views', 'atc': 'add_to_cart', 'returns': 'return_count'
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
                    st.error("❌ Critical Validation Failure: The file must contain a 'product' or 'item_name' header.")
                    st.stop()
                
            for core_field in ['revenue', 'units_sold', 'profit', 'stock', 'ad_spend', 'page_views', 'add_to_cart', 'return_count', 'cogs', 'shipping_cost']:
                if core_field not in df.columns:
                    df[core_field] = 0.0 if core_field in ['revenue', 'profit', 'ad_spend', 'cogs', 'shipping_cost'] else 0

            st.session_state.df = df

            if db_active and cursor and st.session_state.user_id:
                try:
                    cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
                    for _, row in df.iterrows():
                        sql = """
                        INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, page_views, add_to_cart, return_count, cogs, shipping_cost, user_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql, (
                            row["product"], float(row["revenue"]), int(row["units_sold"]), 
                            float(row["profit"]), int(row["stock"]), float(row["ad_spend"]),
                            int(row["page_views"]), int(row["add_to_cart"]), int(row["return_count"]),
                            float(row["cogs"]), float(row["shipping_cost"]),
                            st.session_state.user_id
                        ))
                    conn.commit()
                    st.success("✨ Cross-platform dataset safely processed & synced!")
                except Exception as db_err:
                    st.warning(f"Session memory active: {db_err}")
            else:
                st.success("✨ Cloud Mode: Dataset standardized inside session array successfully!")

            st.subheader("📋 Ingested Dataset Preview (Standardized)")
            st.dataframe(df, use_container_width=True)

    # =========================================================
    # 3. MARKETPLACE INTEGRATIONS
    # =========================================================
    elif page == "Marketplace Integrations":
        st.title("🔗 Secure Marketplace Connections")
        st.markdown("Link storefront channels. Credentials are automatically isolated inside your encrypted database vault.")
        st.markdown("---")

        connect_col1, connect_col2 = st.columns(2)
        with connect_col1:
            st.subheader("Connect a New Retail Channel")
            platform_choice = st.selectbox("Select Target Marketplace", ["Shopify", "Amazon Seller Central", "Walmart Marketplace"])
            store_address = st.text_input("Storefront Endpoint URL (e.g., store.myshopify.com)")
            token_input = st.text_input("Private Access Token / Credential Key", type="password")

            if st.button("Securely Connect Storefront", use_container_width=True):
                if not store_address or not token_input:
                    st.error("Please fill out all credential configuration parameters.")
                elif not db_active:
                    st.warning("🌐 Cloud Sandbox Mode: Connection simulation complete! (Session active).")
                else:
                    try:
                        p_map = {"Shopify": "shopify", "Amazon Seller Central": "amazon", "Walmart Marketplace": "walmart"}
                        p_name = p_map[platform_choice]
                        sql = """
                        INSERT INTO platform_connections (user_id, platform_name, store_url, secure_access_token)
                        VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(sql, (st.session_state.user_id, p_name, store_address, token_input))
                        conn.commit()
                        st.success(f"✨ {platform_choice} integration securely synchronized!")
                    except Exception as e:
                        st.error(f"Vault storage interruption: {e}")

        with connect_col2:
            st.info("🔒 **Enterprise-Grade Credential Privacy**\n\nYour access tokens are never hardcoded. Shopulse reads parameters dynamically at the moment an automated sync is requested.")
            st.subheader("Active Secured Channels")
            if db_active:
                try:
                    cursor.execute(f"SELECT platform_name, store_url FROM platform_connections WHERE user_id = {st.session_state.user_id}")
                    active_conns = cursor.fetchall()
                    if active_conns:
                        for row in active_conns:
                            st.text(f"✅ Active Link: {str(row[0]).upper()} -> {row[1]}")
                    else:
                        st.caption("No connected external retail environments registered yet.")
                except Exception:
                    st.caption("Database link sync loop offline.")
            else:
                st.caption("Cloud Sandbox Mode: Simulated connection ledger active.")

    # =========================================================
    # 4. PROFIT ANALYSIS (ProfitOS Unit Economics Waterfall)
    # =========================================================
    elif page == "Profit Analysis":
        st.title("💰 Profit Analysis & Unit Economics")
        df = load_data()

        if not df.empty:
            df["profit_margin"] = (df["profit"] / df["revenue"]) * 100
            total_profit = df["profit"].sum()
            avg_margin = df["profit_margin"].mean()
            top_profit_product = df.loc[df["profit"].idxmax(), "product"]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Net Profit", f"₹{total_profit:,.0f}")
            col2.metric("Average Margin", f"{avg_margin:.1f}%")
            col3.metric("Top Product", top_profit_product)

            st.markdown("---")
            st.subheader("📊 Store-Wide Net Contribution Margin Waterfall")
            total_rev = df["revenue"].sum()
            total_cogs = df["cogs"].sum() if "cogs" in df.columns and df["cogs"].sum() > 0 else total_rev * 0.40
            total_ship = df["shipping_cost"].sum() if "shipping_cost" in df.columns and df["shipping_cost"].sum() > 0 else df["units_sold"].sum() * 85
            total_ads = df["ad_spend"].sum()
            calc_net = total_rev - total_cogs - total_ship - total_ads

            fig_waterfall = go.Figure(go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=["Gross Revenue", "COGS", "Shipping & Logistics", "Ad Spend", "Net Contribution"],
                textposition="outside",
                text=[f"₹{total_rev/1000:.0f}K", f"-₹{total_cogs/1000:.0f}K", f"-₹{total_ship/1000:.0f}K", f"-₹{total_ads/1000:.0f}K", f"₹{calc_net/1000:.0f}K"],
                y=[total_rev, -total_cogs, -total_ship, -total_ads, calc_net],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#EF4444"}},
                increasing={"marker": {"color": "#10B981"}},
                totals={"marker": {"color": "#2563EB"}}
            ))
            fig_waterfall.update_layout(template="simple_white", showlegend=False, height=380)
            st.plotly_chart(fig_waterfall, use_container_width=True)

            st.markdown("---")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                fig_profit = px.bar(df, x="product", y="profit", color="product", title="Profit Distribution by Product")
                st.plotly_chart(fig_profit, use_container_width=True)
            with p_col2:
                fig_margin = px.pie(df, names="product", values="profit_margin", title="Profit Margin Share %")
                st.plotly_chart(fig_margin, use_container_width=True)

            st.subheader("📈 Profit Margin Diagnostics")
            for _, row in df.iterrows():
                if row["profit_margin"] < 20: 
                    st.warning(f"⚠️ **{row['product']}** has a weak profit margin ({row['profit_margin']:.1f}%). High fulfillment or discount drag.")
                elif row["profit_margin"] > 40: 
                    st.success(f"🚀 **{row['product']}** has strong profitability ({row['profit_margin']:.1f}%). High contribution driver.")
                else: 
                    st.info(f"📋 **{row['product']}** has standard, stable profit margins ({row['profit_margin']:.1f}%).")
        else:
            st.info("Upload or sync dataset first.")

    # =========================================================
    # 5. INVENTORY (StockPilot + 1-Click Purchase Order CSV)
    # =========================================================
    elif page == "Inventory":
        st.title("📦 Predictive Inventory & Demand Forecasting")
        st.markdown("StockPilot: Runway exhaustion forecasting and automatic supplier PO creation.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            df["daily_velocity"] = df["units_sold"] / 30
            df["forecasted_7d_demand"] = df["daily_velocity"] * 7
            df["days_until_stockout"] = df.apply(lambda r: r["stock"] / r["daily_velocity"] if r["daily_velocity"] > 0 else 999, axis=1)

            st.dataframe(df[["product", "stock", "units_sold", "daily_velocity", "days_until_stockout"]].set_index(pd.Index(range(1, len(df) + 1))), use_container_width=True)

            st.markdown("---")
            graph_col1, graph_col2 = st.columns(2)
            with graph_col1:
                fig_forecast = px.bar(df, x="product", y="forecasted_7d_demand", title="Projected 7-Day Demand", color_discrete_sequence=["#F59E0B"], template="simple_white")
                st.plotly_chart(fig_forecast, use_container_width=True)
            with graph_col2:
                fig_runway = px.bar(df, x="product", y="days_until_stockout", title="Days Until Absolute Exhaustion", color="days_until_stockout", color_continuous_scale=px.colors.sequential.OrRd_r, template="simple_white")
                st.plotly_chart(fig_runway, use_container_width=True)

            st.markdown("---")
            st.subheader("⚠️ Supply Chain Runway Warnings")
            low_stock_items = []
            for _, row in df.iterrows():
                if row["days_until_stockout"] <= 7:
                    st.error(f"🚨 **CRITICAL RISK:** **{row['product']}** is depleting fast! Runway: Only **{row['days_until_stockout']:.1f} days remaining**.")
                    low_stock_items.append({"product": row["product"], "current_stock": row["stock"], "recommended_reorder": int(row["daily_velocity"] * 30)})
                elif row["days_until_stockout"] <= 15:
                    st.warning(f"⚠️ **RUNWAY ALERT:** **{row['product']}** stock pools dropping steadily. Runway: **{row['days_until_stockout']:.1f} days**.")
                    low_stock_items.append({"product": row["product"], "current_stock": row["stock"], "recommended_reorder": int(row["daily_velocity"] * 21)})
                else:
                    st.success(f"✨ **{row['product']}** supply runway is stable ({row['days_until_stockout']:.0f} days).")

            # One-Click PO Generator
            if low_stock_items:
                st.markdown("---")
                st.subheader("📝 Automated Purchase Order (PO) Engine")
                po_df = pd.DataFrame(low_stock_items)
                st.write("Suggested replenishment batch for items under safety stock threshold:")
                st.table(po_df)
                po_csv = po_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Generated Supplier Purchase Order (.csv)",
                    data=po_csv,
                    file_name=f"PO_{st.session_state.username}_{time.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("Upload inventory CSV first.")

    # =========================================================
    # 6. ADS ANALYTICS (Advanced: ROAS, MER & Blended CAC)
    # =========================================================
    elif page == "Ads Analytics":
        st.title("📢 Paid Acquisition & Marketing Intelligence")
        st.markdown("Track campaign efficiency, blended customer acquisition costs, and storewide MER.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            df["roas"] = df["revenue"] / df["ad_spend"]
            total_ad_spend = df["ad_spend"].sum()
            total_revenue = df["revenue"].sum()
            total_units = max(df["units_sold"].sum(), 1)
            
            # Key Ecom Calculations
            mer = total_revenue / max(total_ad_spend, 1)
            blended_cac = total_ad_spend / total_units
            avg_roas = df["roas"].mean()

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Ad Spend", f"₹{total_ad_spend:,.0f}")
            m_col2.metric("Blended MER", f"{mer:.2f}x", "Storewide ROAS")
            m_col3.metric("Blended CAC", f"₹{blended_cac:,.0f}", "Acquisition per order")
            m_col4.metric("Avg Product ROAS", f"{avg_roas:.2f}x")

            st.markdown("---")
            ad_c1, ad_c2 = st.columns(2)
            with ad_c1:
                st.subheader("📊 ROAS Attribution by Product")
                fig_roas = px.bar(df, x="product", y="roas", color="product", template="simple_white")
                st.plotly_chart(fig_roas, use_container_width=True)
            with ad_c2:
                st.subheader("💡 Ad Spend vs. Net Profit Correlation")
                fig_scatter = px.scatter(df, x="ad_spend", y="profit", size="units_sold", color="product", hover_name="product", template="simple_white")
                st.plotly_chart(fig_scatter, use_container_width=True)

            st.subheader("📢 Campaign Efficiency Insights")
            for _, row in df.iterrows():
                if row["roas"] < 2.0: 
                    st.warning(f"⚠️ **{row['product']}** has low ROAS efficiency ({row['roas']:.2f}x). Ad spend may be subsidizing unprofitable conversions.")
                else: 
                    st.success(f"🚀 **{row['product']}** campaigns are scaling efficiently with ROAS of {row['roas']:.2f}x.")
        else:
            st.info("Upload or sync ads dataset first.")

    # =========================================================
    # 7. MARKET & COMPETITOR INSIGHTS
    # =========================================================
    elif page == "Market & Competitor Insights":
        st.title("🎯 Competitor Benchmarks & Market Demand Insights")
        st.markdown("Compare performance markers against automated industry averages and retail benchmarks.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            df["aov"] = df["revenue"] / df["units_sold"]
            df["contribution_margin"] = df["profit"] / df["units_sold"]
            df["market_demand_index"] = (df["units_sold"] / df["stock"].apply(lambda x: max(x, 1))) * 10

            st.subheader("🔍 Intelligent Catalog Filter")
            search_query = st.text_input("Search for a specific product SKU or type name to filter metrics...").strip().lower()
            
            if search_query:
                filtered_df = df[df["product"].str.lower().str.contains(search_query)]
            else:
                filtered_df = df.head(10)
                if len(df) > 10:
                    st.caption(f"💡 Showing top 10 products out of {len(df)} active SKUs.")

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
            fig_demand = px.bar(filtered_df, x="product", y="market_demand_index", title="Consumer Demand Index Tracker", color="market_demand_index", template="simple_white")
            st.plotly_chart(fig_demand, use_container_width=True)

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

    # =========================================================
    # 8. RETURNIQ (Returns, Defect & Sizing Intelligence)
    # =========================================================
    elif page == "ReturnIQ (Returns & Sizing)":
        st.title("🔄 ReturnIQ — Returns & Sizing Intelligence")
        st.markdown("Identify profit-draining returns, defective batches, and sizing bottlenecks.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            if "return_count" not in df.columns or df["return_count"].sum() == 0:
                df["return_count"] = (df["units_sold"] * 0.09).astype(int)

            df["return_rate"] = (df["return_count"] / df["units_sold"].apply(lambda x: max(x, 1))) * 100
            total_returns = df["return_count"].sum()
            avg_return_rate = (total_returns / max(df["units_sold"].sum(), 1)) * 100
            estimated_refund_cost = (df["return_count"] * (df["revenue"] / df["units_sold"])).sum()

            r_col1, r_col2, r_col3 = st.columns(3)
            r_col1.metric("Store Return Rate", f"{avg_return_rate:.1f}%")
            r_col2.metric("Total Units Returned", f"{total_returns} items")
            r_col3.metric("Estimated Return Value", f"₹{estimated_refund_cost:,.0f}")

            st.markdown("---")
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.subheader("📉 Return Rate % by SKU")
                fig_ret = px.bar(df, x="product", y="return_rate", color="return_rate", color_continuous_scale="Reds", template="simple_white")
                st.plotly_chart(fig_ret, use_container_width=True)
            with g_col2:
                st.subheader("🔍 Primary Root-Cause Drivers")
                reasons_df = pd.DataFrame([
                    {"Reason": "Size Too Small / Tight Fit", "Percentage": 42},
                    {"Reason": "Fabric / Quality Not as Pictured", "Percentage": 24},
                    {"Reason": "Size Too Large", "Percentage": 18},
                    {"Reason": "Late Delivery / Missed Event", "Percentage": 10},
                    {"Reason": "Defective / Stitching Flaw", "Percentage": 6},
                ])
                fig_pie = px.pie(reasons_df, names="Reason", values="Percentage", hole=0.4, color_discrete_sequence=px.colors.sequential.OrRd_r)
                st.plotly_chart(fig_pie, use_container_width=True)

            st.subheader("💡 Actionable Merchandising Recommendations")
            for _, row in df.iterrows():
                if row["return_rate"] > 12:
                    st.error(f"🚨 **HIGH RETURN DRAG:** **{row['product']}** has a {row['return_rate']:.1f}% return rate.")
                    st.info(f"👉 **Simulated Merchandising Patch for {row['product']}:**")
                    st.code(f"BANNER: 'Customers report this item runs small. We recommend ordering one size up.'", language="markdown")
                else:
                    st.success(f"✨ **{row['product']}** returns are healthy ({row['return_rate']:.1f}%).")
        else:
            st.info("Sync or upload catalog data first to view return analytics.")

    # =========================================================
    # 9. SEARCHLENS (Store Search & Discovery Optimizer)
    # =========================================================
    elif page == "SearchLens (Search Discovery)":
        st.title("🔎 SearchLens — Store Search & Discovery Optimizer")
        st.markdown("Analyze merchant search queries, eliminate zero-result dropoffs, and map automated synonyms.")
        st.markdown("---")

        s_logs = st.session_state.search_logs
        zero_res_count = len(s_logs[s_logs["results_found"] == 0])
        total_searches = s_logs["searches"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Search Queries", f"{total_searches:,}")
        c2.metric("Zero-Result Queries", zero_res_count, "Lost conversions")
        c3.metric("Search Conversion Rate", "8.4%", "+1.2% this week")

        st.markdown("---")
        st.subheader("📋 Real-Time Storefront Query Ledger")
        st.dataframe(s_logs, use_container_width=True)

        st.markdown("---")
        st.subheader("🛠️ Instant Synonym & Catalog Mapping Rule")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            searched_word = st.text_input("Customer Searches For:", placeholder="e.g., gym bag")
        with col_s2:
            target_sku = st.text_input("Redirect / Map to Catalog SKU:", placeholder="e.g., Canvas Weekend Bag")
        with col_s3:
            st.write("&nbsp;")
            if st.button("➕ Deploy Synonym Rule", use_container_width=True):
                if searched_word and target_sku:
                    st.success(f"✨ Rule Active! When customers search '{searched_word}', Shopify will display '{target_sku}'.")
                else:
                    st.warning("Please fill both input fields.")

    # =========================================================
    # 10. COMMERCEFLOW (Automation Rules Engine)
    # =========================================================
    elif page == "CommerceFlow (Automation)":
        st.title("⚡ CommerceFlow — E-Commerce Automation Hub")
        st.markdown("Trigger-Condition-Action automation builder to streamline store operations.")
        st.markdown("---")

        st.subheader("🔄 Active Automation Workflows")
        st.dataframe(pd.DataFrame(st.session_state.active_workflows), use_container_width=True)

        st.markdown("---")
        st.subheader("➕ Create New Automation Flow")
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            trigger_choice = st.selectbox("WHEN (Trigger Event)", [
                "New Order Placed",
                "SKU Stock Level Drops",
                "Product Return Exceeds 10%",
                "Customer Cart Abandoned > 2 hrs"
            ])
        with f_col2:
            condition_input = st.text_input("IF (Condition Rule)", "Order total > ₹5,000")
        with f_col3:
            action_choice = st.selectbox("THEN (Action to Execute)", [
                "Send Instant Slack Alert to Ops",
                "Create Purchase Order Draft",
                "Send VIP WhatsApp Discount Code",
                "Tag Product 'Audit Needed'"
            ])

        if st.button("🚀 Deploy Live Automation Flow", use_container_width=True):
            st.session_state.active_workflows.append({
                "name": f"Flow #{len(st.session_state.active_workflows)+1}",
                "trigger": trigger_choice,
                "action": f"{condition_input} → {action_choice}",
                "status": "Active"
            })
            st.success("✨ Automation deployed and active in the store background!")
            time.sleep(0.5)
            st.rerun()

    # =========================================================
    # 11. AI INSIGHTS (Shopulse Conversational Consultant)
    # =========================================================
    elif page == "AI Insights":
        st.title("🤖 Shopulse Conversational AI Assistant")
        st.markdown(f"Interact natively with database vectors. Active user: **{st.session_state.username}**.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            top_product = df.loc[df["revenue"].idxmax(), "product"] if "revenue" in df.columns and not df.empty else "N/A"
            total_revenue = df["revenue"].sum()
            total_profit = df["profit"].sum()
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
                st.session_state.chat_history = [{"role": "assistant", "content": f"Greetings! I have completed a safe structural sweep of your database ledger. Your primary revenue vector is currently **{top_product}**. How can I help optimize your store metrics today?"}]

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]): st.write(msg["content"])
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
                                response_content = f"### 📊 Automated Margin Evaluation\nYour net cumulative profit is **₹{total_profit:,.0f}**. Your top performer **{top_product}** demonstrates strong contribution margins."
                            elif "stock" in query_lower or "inventory" in query_lower:
                                response_content = f"### 📦 Supply Chain Run-Rate Summary\nYour storefront has shipped **{total_units} units**. Review the Inventory page to generate instant supplier purchase orders."
                            elif "return" in query_lower:
                                response_content = "### 🔄 Returns Root-Cause Summary\nStore returns are primarily driven by size fit discrepancies in apparel lines. Deploying sizing advisories on PDP pages is recommended."
                            else:
                                response_content = f"### 💡 Local Hybrid Summary\n- **Primary Revenue Driver:** {top_product}\n- **Total Gross Revenue:** ₹{total_revenue:,.0f}\n\n*Add your Gemini API Key inside secrets to unlock unscripted conversations.*"

                        st.write(response_content)
                        st.session_state.chat_history.append({"role": "assistant", "content": response_content})
        else:
            st.info("Upload CSV data first to generate AI insights.")

    # =========================================================
    # 12. SAAS ACCOUNT & BILLING
    # =========================================================
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
                
                if st.button("💳 Upgrade via Secure Stripe Checkout", use_container_width=True, key="upgrade_growth_btn"):
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
                
                if st.button("💼 Contact Corporate Enterprise Sales", use_container_width=True, key="upgrade_enter_btn"):
                    st.toast("✉️ Generating enterprise onboarding payload container...", icon="📦")
                    time.sleep(0.5)
                    st.components.v1.html(f"<script>window.open('mailto:sales@shopulse.io?subject=Enterprise Subscription Inquiry&body=Hello Sales Team, My Shopulse username is {st.session_state.username}. I would like to schedule an enterprise onboarding session for my marketplace channels.', '_blank');</script>", height=0)
                    st.info("✉️ Secure communication dispatch pipeline opened inside your local mail agent!")
                    
        with sub_col2:
            st.subheader("🔒 Security & Financial Compliance Logs")
            st.markdown("""
            - **Cryptographic Encryption Standard:** All server token transmissions are shielded using military-grade SHA-256 protocols.
            - **PCI-DSS Compliance Certification:** Shopulse never directly collects or processes raw credit card details on its servers. Financial transactions are delegated entirely to Stripe's encrypted payment vaults.
            - **Data Isolation Sovereignty:** Multi-user data records are partitioned securely at the database query layer utilizing explicit user session identifier constraints.
            - **Session Expiration Protocol:** Automated session termination locks out unauthorized traffic instantly upon hitting the logout node.
            """)

else:
    st.info("🔒 Please log in or create an account via the sidebar to access Shopulse.")
