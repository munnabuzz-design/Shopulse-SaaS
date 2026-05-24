import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
import hashlib

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123",
    database="shopulse"
)

cursor = conn.cursor()

def load_data():

    query = "SELECT product, sales, profit, stock, ad_spend FROM orders"

    df = pd.read_sql(query, conn)

    return df

if "df" not in st.session_state:
    st.session_state.df = None

# Page config
st.set_page_config(
    page_title="Shopulse",
    page_icon="🚀",
    layout="wide"
)

# Sidebar
st.sidebar.title("🚀 Shopulse")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Upload Center",
        "Profit Analysis",
        "Inventory",
        "Ads Analytics",
        "AI Insights"
    ]
)

# Main Dashboard
if page == "Dashboard":

    st.title("📊 Ecommerce Dashboard")

    df = load_data()

    if not df.empty:

        total_sales = df["sales"].sum()
        total_profit = df["profit"].sum()
        total_products = df["product"].nunique()
        avg_profit = df["profit"].mean()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Sales", f"₹{total_sales:,.0f}")
        col2.metric("Total Profit", f"₹{total_profit:,.0f}")
        col3.metric("Products", total_products)
        col4.metric("Average Profit", f"₹{avg_profit:,.0f}")

        st.markdown("---")

        st.subheader("Sales Overview")

        fig_sales = px.bar(
            df,
            x="product",
            y="sales",
            title="Sales by Product"
        )

        st.plotly_chart(fig_sales, use_container_width=True)

        st.subheader("Profit Overview")

        fig_profit = px.pie(
            df,
            names="product",
            values="profit",
            title="Profit Distribution"
        )

        st.plotly_chart(fig_profit, use_container_width=True)

        st.subheader("Uploaded Data")

        st.dataframe(df)


    else:

        st.info("Please upload a CSV file in Upload Center.")

# Upload Center
elif page == "Upload Center":

    st.title("📂 Upload Center")

    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=["csv"]
    )

    if uploaded_file:

        df = pd.read_csv(uploaded_file)

        required_columns = ["product", "sales", "profit", "stock", "ad_spend"]

        if not all(col in df.columns for col in required_columns):
            st.error("CSV must contain: product, sales, profit, stock, ad_spend")
            st.stop()

        st.session_state.df = df

        cursor.execute("DELETE FROM orders")
        conn.commit()

        for _, row in df.iterrows():

            sql = """
            INSERT INTO orders (product, sales, profit, stock, ad_spend)
            VALUES (%s, %s, %s, %s, %s)
            """

            values = (
                row["product"],
                row["sales"],
                row["profit"],
                row["stock"],
                row["ad_spend"]
            )

            cursor.execute(sql, values)

        conn.commit()

        st.success("File uploaded successfully.")

        st.subheader("Preview Data")

        st.dataframe(df)

        st.subheader("Quick Insights")

        st.write(f"Rows: {df.shape[0]}")
        st.write(f"Columns: {df.shape[1]}")

# Profit Analysis
elif page == "Profit Analysis":

    st.title("💰 Profit Analysis")

    st.warning("Profit analytics module coming soon.")


# Inventory
elif page == "Inventory":

    st.title("📦 Inventory Management")

    df = load_data()

    if not df.empty:

        st.subheader("Inventory Overview")

        st.dataframe(df[["product", "stock"]])

        low_stock = df[df["stock"] < 10]

        df["sales_velocity"] = df["sales"] / 30

        df["days_remaining"] = (df["stock"] / df["sales_velocity"])

        st.subheader("⚠️ Low Stock Alerts")

        if not low_stock.empty:

            for _, row in low_stock.iterrows():

                st.warning(
                    f"{row['product']} stock is low "
                    f"({row['stock']} units remaining)"
                )

        else:

            st.success("All inventory levels look healthy.")

        st.subheader("🔮 Predictive Inventory Insights")

        for _, row in df.iterrows():

            if row["days_remaining"] < 7:

                st.error(
                    f"{row['product']} may stock out soon. "
                    f"Estimated remaining days: "
                    f"{row['days_remaining']:.1f}"
                )

            elif row["days_remaining"] < 15:

                st.warning(
                    f"{row['product']} inventory is declining. "
                    f"Estimated remaining days: "
                    f"{row['days_remaining']:.1f}"
                )

            else:

                st.success(
                    f"{row['product']} inventory looks stable."
                )

    else:

        st.info("Upload inventory CSV first.")


# Ads Analytics
elif page == "Ads Analytics":

    st.title("📢 Ads Analytics")

    df = load_data()

    if not df.empty:

        df["roas"] = df["sales"] / df["ad_spend"]

        total_ad_spend = df["ad_spend"].sum()

        avg_roas = df["roas"].mean()

        col1, col2 = st.columns(2)

        col1.metric(
            "Total Ad Spend",
            f"₹{total_ad_spend:,.0f}"
        )

        col2.metric(
            "Average ROAS",
            f"{avg_roas:.2f}x"
        )

        st.markdown("---")

        st.subheader("ROAS by Product")

        fig_roas = px.bar(
            df,
            x="product",
            y="roas",
            color="product",
            title="Return on Ad Spend"
        )

        st.plotly_chart(
            fig_roas,
            use_container_width=True
        )

        st.subheader("Campaign Insights")

        for _, row in df.iterrows():

            if row["roas"] < 2:

                st.warning(
                    f"{row['product']} has weak ROAS "
                    f"({row['roas']:.2f}x)"
                )

            else:

                st.success(
                    f"{row['product']} is performing well "
                    f"with ROAS of {row['roas']:.2f}x"
                )

    else:

        st.info("Upload ads dataset first.")

# AI Insights
elif page == "AI Insights":

    st.title("🤖 AI Insights")

    df = load_data()

    if not df.empty:

        top_product = df.loc[df["sales"].idxmax(), "product"]

        total_sales = df["sales"].sum()
        total_profit = df["profit"].sum()

        avg_profit = df["profit"].mean()

        st.success(f"🏆 Top Selling Product: {top_product}")

        if avg_profit > 3000:
            st.info("📈 Average profit margins look healthy.")
        else:
            st.warning("⚠️ Profit margins may need improvement.")

        if total_sales > 20000:
            st.success("🚀 Sales performance is strong.")
        else:
            st.warning("📉 Sales volume is currently low.")

        st.subheader("Business Summary")

        st.write(
            f"""
            Shopulse analyzed your ecommerce data and found that
            {top_product} is currently your strongest performing product.

            Total sales reached ₹{total_sales:,.0f}
            with total profit of ₹{total_profit:,.0f}.

            Average profit per product is ₹{avg_profit:,.0f}.
            """
        )
        st.subheader("🧠 AI Recommendations")

        for _, row in df.iterrows():

            roas = row["sales"] / row["ad_spend"]

            if row["stock"] < 10:

                st.warning(f"Consider restocking {row['product']} soon.")

            if roas < 2:

                st.error(
                    f"Reduce ad spend or optimize "
                    f"{row['product']} campaigns."
                )

            elif roas > 4:

                st.success(
                     f"Scale advertising for "
                     f"{row['product']}."
                )

    else:

        st.info("Upload CSV data first to generate AI insights.")

