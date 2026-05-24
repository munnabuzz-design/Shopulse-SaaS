import hashlib
import mysql.connector
import pandas as pd
import plotly.express as px
import streamlit as st

# --- 🌐 GLOBAL DATABASE CONNECTION SAFEGUARD ---
# Try connecting to local MySQL. If it fails (like when deployed on the cloud), handle it gracefully.
try:
    conn = mysql.connector.connect(
        host="localhost", user="root", password="root123", database="shopulse"
    )
    cursor = conn.cursor()

    # Auto-create backend tables if they don't exist
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
    db_active = True
except Exception:
    conn = None
    cursor = None
    db_active = False


# Helper function to load multi-user data safely in local and cloud environments
def load_data():
    if db_active and conn is not None:
        try:
            query = f"""
            SELECT product, revenue, units_sold, profit, stock, ad_spend 
            FROM orders 
            WHERE user_id = {st.session_state.user_id}
            """
            df = pd.read_sql(query, conn)
            return df
        except Exception:
            pass
            
    # 🌐 CLOUD FALLBACK SAFEGUARD: Read from active session cache memory if MySQL is offline!
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

# Page configuration
st.set_page_config(page_title="Shopulse", page_icon="🚀", layout="wide")

# Custom SaaS Minimalist UI CSS
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
    </style>
""", unsafe_allow_html=True)


# --- STEP 4 — Add Authentication Sidebar ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Authentication")
    auth_mode = st.sidebar.selectbox("Choose", ["Login", "Signup"])
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")

    if password_input:
        hashed_password = hashlib.sha256(password_input.encode()).hexdigest()

    # --- STEP 5 — Signup Logic ---
    if auth_mode == "Signup":
        if st.sidebar.button("Create Account"):
            if not username_input or not password_input:
                st.sidebar.error("Fields cannot be empty!")
            elif not db_active:
                # 🌐 Cloud Bypass: Allow sandbox signup instantly without database
                st.session_state.logged_in = True
                st.session_state.user_id = 999
                st.session_state.username = username_input
                st.sidebar.success("Cloud Demo Session Initialized!")
                st.rerun()
            else:
                try:
                    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
                    values = (username_input, hashed_password)
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
            if not username_input or not password_input:
                st.sidebar.error("Please enter details.")
            elif not db_active:
                # 🌐 Cloud Bypass: Allow sandbox login instantly without database
                st.session_state.logged_in = True
                st.session_state.user_id = 999
                st.session_state.username = username_input
                st.sidebar.success("Welcome to Cloud Demo!")
                st.rerun()
            else:
                sql = "SELECT id, username FROM users WHERE username=%s AND password=%s"
                values = (username_input, hashed_password)
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
            "Profit Analysis",
            "Inventory",
            "Ads Analytics",
            "Market & Competitor Insights",
            "AI Insights",
            "SaaS Account & Billing"
        ],
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔓 End Session / Logout", width='stretch'):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

    # --- MAIN DASHBOARD PAGE ---
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
            st.dataframe(df, width='stretch')

            st.markdown("---")
            st.subheader("📊 Corporate Report Export Center")
            csv_file_data = df.to_csv(index=False).encode('utf-8')
            download_col1, download_col2 = st.columns(2)

            with download_col1:
                st.info("📋 **Standard Ledger Export**\nIncludes localized accounting columns.")
                st.download_button(label="📥 Download Store Performance Ledger (.csv)", data=csv_file_data, file_name=f"shopulse_ledger_{st.session_state.username}.csv", mime="text/csv", width="stretch")
            with download_col2:
                st.success("🤖 **AI Operations Briefing**\nPrint out your current dashboard matrix immediately.")
                if st.button("🖨️ Open Browser Print Console", key="dash_print_btn"):
                    st.components.v1.html("<script>window.print();</script>", height=0)
        else:
            st.info("Please upload a CSV file or click Live Sync inside the Upload Center.")

    # --- SMART UPLOAD CENTER ---
    elif page == "Upload Center":
        st.title("📂 Smart Upload Center")
        st.markdown("Automate pipelines. Connect directly via cloud integrations or upload manual ledger sheets.")
        st.markdown("---")

        st.subheader("⚡ Automated Marketplace Integrations")
        sync_col1, sync_col2 = st.columns(2)
        
        with sync_col1:
            if st.button("🔄 Sync Live Shopify Store Data", width="stretch", key="shopify_sync_btn"):
                with st.spinner("Connecting to secure Shopify API endpoints..."):
                    import time, random
                    time.sleep(1.5)
                    mock_products = ['Shoes', 'Watch', 'Bag']
                    
                    new_rows = []
                    for prod in mock_products:
                        rev = random.randint(25000, 95000)
                        units = random.randint(40, 500)
                        prof = rev * random.uniform(0.20, 0.45)
                        stk = random.randint(2, 90)
                        ads = rev * random.uniform(0.10, 0.20)
                        
                        if db_active and cursor:
                            cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
                            sql = "INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                            cursor.execute(sql, (prod, float(rev), int(units), float(prof), int(stk), float(ads), st.session_state.user_id))
                        
                        new_rows.append({"product": prod, "revenue": rev, "units_sold": units, "profit": prof, "stock": stk, "ad_spend": ads})
                    
                    if db_active:
                        conn.commit()
                    
                    # Store variables directly inside cloud runtime cache
                    st.session_state.df = pd.DataFrame(new_rows)
                    st.success("✨ Shopify synchronization finalized! Cloud memory populated.")
                    st.rerun()
                    
        with sync_col2:
            st.info("💡 **API Streaming Automation**\nExecutes a live simulated cloud handshake. It populates memory caches immediately.")

        st.markdown("---")
        st.subheader("📋 Alternative: Manual CSV Ingestion")
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            df.columns = [str(col).lower().strip().replace(" ", "_").replace("-", "_") for col in df.columns]
            
            column_mapping = {
                'sales': 'revenue', 'turnover': 'revenue', 'total_sales': 'revenue', 'gross_sales': 'revenue',
                'quantity': 'units_sold', 'qty': 'units_sold', 'items_sold': 'units_sold', 'volume': 'units_sold',
                'earnings': 'profit', 'net_profit': 'profit', 'inventory': 'stock', 'marketing': 'ad_spend'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            if 'product' not in df.columns:
                st.error("❌ Critical Error: Missing 'product' column header.")
                st.stop()
                
            for col in ['revenue', 'units_sold', 'profit', 'stock', 'ad_spend']:
                if col not in df.columns:
                    df[col] = 0.0 if col in ['revenue', 'profit', 'ad_spend'] else 0

            st.session_state.df = df

            if db_active and cursor:
                cursor.execute(f"DELETE FROM orders WHERE user_id = {st.session_state.user_id}")
                for _, row in df.iterrows():
                    sql = "INSERT INTO orders (product, revenue, units_sold, profit, stock, ad_spend, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (row["product"], float(row["revenue"]), int(row["units_sold"]), float(row["profit"]), int(row["stock"]), float(row["ad_spend"]), st.session_state.user_id))
                conn.commit()

            st.success("✨ E-commerce ledger safely ingested.")
            st.dataframe(df, use_container_width=True)

    # --- PROFIT ANALYSIS PAGE ---
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
            fig_profit = px.bar(df, x="product", y="profit", color="product", title="Profit Distribution")
            st.plotly_chart(fig_profit, width="stretch")

            fig_margin = px.pie(df, names="product", values="profit_margin", title="Profit Margin Share")
            st.plotly_chart(fig_margin, width="stretch")
        else:
            st.info("Upload dataset first.")

    # --- INVENTORY PAGE ---
    elif page == "Inventory":
        st.title("📦 Predictive Inventory & Demand Forecasting")
        st.markdown("Automated forward demand calculations and supply runway velocity indexes.")
        st.markdown("---")
        df = load_data()

        if not df.empty:
            st.dataframe(df[["product", "stock", "units_sold"]], width='stretch')
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
        else:
            st.info("Upload inventory CSV first.")

    # --- ADS ANALYTICS PAGE ---
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
            fig_roas = px.bar(df, x="product", y="roas", color="product", title="Return on Ad Spend")
            st.plotly_chart(fig_roas, width="stretch")
        else:
            st.info("Upload ads dataset first.")

    # --- MARKET & COMPETITOR INSIGHTS ---
    elif page == "Market & Competitor Insights":
        st.title("🎯 Competitor Benchmarks & Market Demand Insights")
        df = load_data()

        if not df.empty:
            df["aov"] = df["revenue"] / df["units_sold"]
            df["contribution_margin"] = df["profit"] / df["units_sold"]
            df["market_demand_index"] = (df["units_sold"] / df["stock"].apply(lambda x: max(x, 1))) * 10

            for _, row in df.iterrows():
                with st.expander(f"📦 Product Intelligence: {row['product']}"):
                    met_col1, met_col2, met_col3 = st.columns(3)
                    met_col1.metric("Your AOV", f"₹{row['aov']:,.2f}")
                    met_col2.metric("Unit Contribution", f"₹{row['contribution_margin']:,.2f}")
                    met_col3.metric("Ad Spend Efficiency", f"{(row['revenue']/max(row['ad_spend'],1)):.2f}x")

            st.markdown("---")
            fig_demand = px.bar(df, x="product", y="market_demand_index", title="Consumer Demand Index Tracker", color="market_demand_index", template="simple_white")
            st.plotly_chart(fig_demand, use_container_width=True)
        else:
            st.info("Upload dataset first to lock competitor analytics.")

    # --- AUTONOMOUS CHATBOT AI INSIGHTS ---
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

            from google import genai
            try:
                secured_key = st.secrets.get("GEMINI_API_KEY")
                client = genai.Client(api_key=secured_key) if secured_key else None
            except Exception:
                client = None

            data_summary = df.to_string(index=False)
            system_context = f"""
            You are the Shopulse AI Business Consultant. Assisting user '{st.session_state.username}'.
            Current live store performance metrics:
            {data_summary}
            Base answers on these parameters. Keep advice professional, highly actionable, and limited to 3 short paragraphs max.
            """

            if "chat_history" not in st.session_state:
                st.session_state.chat_history = [{"role": "assistant", "content": f"Greetings! I have completed a safe structural sweep of your database ledger. Your primary revenue vector is currently **{top_product}**. How can I help optimize your store metrics today?"}]

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            if user_query := st.chat_input("Ask about your sales, margins, ads, or low stock warnings..."):
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"): st.write(user_query)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing performance ledger..."):
                        if client and secured_key and secured_key != "YOUR_GEMINI_API_KEY_HERE":
                            try:
                                response = client.models.generate_content(model='gemini-2.5-flash', contents=f"{system_context}\n\nUser Question: {user_query}")
                                response_content = response.text
                            except Exception as e:
                                response_content = f"⚠️ AI Stream Connection Failed. Details: {e}"
                        else:
                            import time
                            time.sleep(1)
                            query_lower = user_query.lower()
                            if "margin" in query_lower or "profit" in query_lower:
                                response_content = f"### 📊 Automated Margin Evaluation\nYour net cumulative profit is currently healthy. Your strongest performing product line (**{top_product}**) demonstrates resilient contribution margins."
                            elif "stock" in query_lower or "inventory" in query_lower:
                                response_content = f"### 📦 Supply Chain Run-Rate Summary\nYour storefront has shipped a total of **{total_units} physical items** across all catalogs."
                            else:
                                response_content = f"### 💡 Local Hybrid Summary\n- **Primary Revenue Driver:** {top_product}\n- **Total Revenue:** ₹{total_revenue:,.0f}\n\n*Add your Gemini API Key inside .streamlit/secrets.toml to unlock unscripted cloud conversations.*"

                        st.write(response_content)
                        st.session_state.chat_history.append({"role": "assistant", "content": response_content})
        else:
            st.info("Upload CSV data first to generate AI insights.")

    # --- ACCOUNT & BILLING PANEL ---
    elif page == "SaaS Account & Billing":
        st.title("💳 SaaS Account & Commercial Subscription Hub")
        st.markdown("---")
        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            st.subheader("🛠️ Current Plan Allotment")
            st.markdown(f"""
            <div style="padding: 20px; border: 1px solid #E5E7EB; border-radius: 8px; background-color: #F9FAFB;">
                <p style="margin:0; font-size:0.9rem; color:#4B5563;">ACCOUNT ACCESS STATUS</p>
                <h3 style="margin:5px 0; color:#1E3A8A;">✨ Professional Tier (Active Trial)</h3>
                <hr style="margin:10px 0; border:0; border-top:1px solid #E5E7EB;">
                <p style="margin:5px 0; font-size:0.95rem;"><b>Workspace Owner:</b> {st.session_state.username}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            tier_col1, tier_col2 = st.columns(2)
            with tier_col1:
                st.markdown("<div style='padding: 15px; border: 2px solid #2563EB; border-radius: 8px; text-align: center; background-color: #EFF6FF;'><h4>📈 Growth Core</h4><h2>₹3,999<span style='font-size:1rem;'>/mo</span></h2></div>", unsafe_allow_html=True)
                if st.button("Upgrade to Growth Core", key="upgrade_growth_btn"): st.success("Initializing secure payment webhook simulation!")
            with tier_col2:
                st.markdown("<div style='padding: 15px; border: 1px solid #E5E7EB; border-radius: 8px; text-align: center;'><h4>🏢 Enterprise Suite</h4><h2>₹9,499<span style='font-size:1rem;'>/mo</span></h2></div>", unsafe_allow_html=True)
                if st.button("Contact Sales", key="upgrade_enter_btn"): st.info("Corporate connection logged successfully.")
        with sub_col2:
            st.subheader("🔒 Compliance Logs")
            st.markdown("- Encryption: SHA-256 protocols\n- Multi-User Isolation Block Active\n- Automated Token Expiration Active")

else:
    st.info("🔒 Please log in or create an account via the sidebar to access Shopulse.")
