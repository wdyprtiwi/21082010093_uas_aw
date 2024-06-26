import pandas as pd
import mysql.connector
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt
import seaborn as sns
import plotly.express as px
import matplotlib.ticker as ticker

st.set_page_config(
    page_title="Adventure Works Dashboard",
    initial_sidebar_state="expanded")

conn = st.connection("mydb", type='sql', autocommit=True)

def run_query(query, conn):
    return pd.read_sql(query, conn)

alt.themes.enable("dark")

kategori = pd.DataFrame({
    'Category': ['Comparison', 'Composition', 'Distribution', 'Relationship']
})

# Sidebar untuk memilih kategori
with st.sidebar:
    st.write('# Final Project Data Visualisasi')
    category = st.sidebar.selectbox('Pilih Kategori', kategori['Category'].unique())

# grafik untuk aspek comparasion
if category == 'Comparison':
    query_comp = """
    SELECT dsc.EnglishProductSubcategoryName as "subcategory", SUM(f.OrderQuantity) AS "Penjualan"
    FROM factinternetsales f 
    JOIN dimproduct dp ON f.ProductKey = dp.ProductKey 
    JOIN dimproductsubcategory dsc ON dp.ProductSubcategoryKey = dsc.ProductSubcategoryKey 
    GROUP BY dsc.EnglishProductSubcategoryName
    """

    # Fetch data from database
    df_comp = conn.query(query_comp)

    # Convert 'jumlahPenjualan' to float
    df_comp['Penjualan'] = df_comp['Penjualan'].astype(float)

    # Display bar chart using
    st.subheader('Perbandingan Penjualan Subcategory')
    st.bar_chart(data=df_comp, x='subcategory', y='Penjualan')
    st.write("""
    Berdasarkan grafik tersebut dapat dilihat bahwa top 3 penjualan produk yang paling laris ada pada subcategory Tires and Tubes dengan total 17322,
    kemudian Road Bikes dengan total 8068, dan Bottles and Cages dengan total 7981.
    """)

    query_comp2 = """
    SELECT d.CalendarQuarter, d.CalendarYear, SUM(f.TotalProductCost) AS Total
    FROM factinternetsales f
    JOIN dimtime d ON f.OrderDateKey = d.TimeKey
    GROUP BY d.CalendarYear, d.CalendarQuarter
    ORDER BY d.CalendarYear, d.CalendarQuarter
    """

    df_comp2 = conn.query(query_comp2)

    st.subheader('Trend Penjualan per Kuartal di Setiap Tahun')

    fig, ax = plt.subplots(figsize=(10, 6))

    # Memplot data untuk setiap tahun
    for year in df_comp2['CalendarYear'].unique():
        year_data = df_comp2[df_comp2['CalendarYear'] == year]
        ax.plot(year_data['CalendarQuarter'], year_data['Total'], label=str(year))

    plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, pos: '{:,.0f}'.format(y)))

    ax.set_xlabel('Kuartal')
    ax.set_ylabel('Total')
    ax.set_xticks(range(1, 5))
    ax.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'])
    ax.set_title('Trend Penjualan per Kuartal di Setiap Tahun')
    ax.legend()
    ax.grid(True)
    ax.set_ylim(bottom=0)

    # menampilkan plot
    st.pyplot(fig)

    # Narasi
    st.write("""
    Line chart di atas menampilkan trend penjualan per kuartal di setiap tahunnya dimana data dimulai 
    dari kuartal 3 tahun 2001 hingga kuartal 3 2024. Dari trend tersebut dapat dilihat pada kuartal 
    1 tahun 2024 menuju kuartal 2 mengalami kenaikan yang lebih tinggi dibandingkan di kuartal pada tahun yang lainnya.
    """)

# grafik untuk aspek composition
elif category == 'Composition':
    query_cps = """
    SELECT dc.EnglishProductCategoryName, SUM(f.OrderQuantity) AS "Penjualan"
    FROM factinternetsales f 
    JOIN dimproduct dp ON f.ProductKey = dp.ProductKey 
    JOIN dimproductsubcategory dsc ON dp.ProductSubcategoryKey = dsc.ProductSubcategoryKey 
    JOIN dimproductcategory dc ON dsc.ProductCategoryKey = dc.ProductCategoryKey
    GROUP BY dc.EnglishProductCategoryName
    """

    df_cps = conn.query(query_cps)

    st.subheader("Komposisi Penjualan Per Kategori")

    if st.get_option("theme.base") == "dark":
        background_color = "#0e1117"  # Background default untuk tema dark
        text_color = "white"
    else:
        background_color = "white"  # Background default untuk tema light
        text_color = "black"

    # donut chart
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(df_cps['Penjualan'], labels=df_cps['EnglishProductCategoryName'], autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
    ax.axis('equal')

    # Menyesuaikan warna background dan teks
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(background_color)
    for text in texts + autotexts:
        text.set_color(text_color)

    st.pyplot(fig)

    # Narasi
    st.write("""
    Donut chart di atas menampilkan bagaimana komposisi penjualan produk di setiap kategorinya. 
    Dapat dilihat bahwa komposisi kategori Accessories memiliki nilai yang paling besar, yaitu 59.8% 
    yang artinya produk pada kategori Accessories mengalami penjualan yang banyak.
    """)

    # Stacked 100%
    query_cps2 = """
    SELECT
        dc.EnglishProductCategoryName AS Category,
        ds.EnglishProductSubcategoryName AS Subcategory,
        COUNT(f.SalesOrderNumber) AS TotalOrders
    FROM 
        factinternetsales f
        INNER JOIN dimproduct d ON f.ProductKey = d.ProductKey
        INNER JOIN dimproductsubcategory ds ON d.ProductSubcategoryKey = ds.ProductSubcategoryKey 
        INNER JOIN dimproductcategory dc ON ds.ProductCategoryKey = dc.ProductCategoryKey 
    GROUP BY
        dc.EnglishProductCategoryName , ds.EnglishProductSubcategoryName 
    ORDER BY
        dc.EnglishProductCategoryName , ds.EnglishProductSubcategoryName
    """

    df_cps2 = conn.query(query_cps2)

    st.header("Komposisi Penjualan Produk Berasarkan Subcategory")

    # Group data berdasarkan Category dan Subcategory, kemudian hitung total orders
    df_grouped = df_cps2.groupby(['Category', 'Subcategory'])['TotalOrders'].sum().reset_index()

    # Hitung total orders per Category untuk normalisasi ke 100%
    df_grouped['TotalCategoryOrders'] = df_grouped.groupby('Category')['TotalOrders'].transform('sum')
    df_grouped['Percent'] = df_grouped['TotalOrders'] / df_grouped['TotalCategoryOrders'] * 100

    # Buat stacked 100% column chart dengan Plotly
    fig = px.bar(df_grouped, x='Category', y='Percent', color='Subcategory', 
                barmode='stack', labels={'Percent': 'Percentage (%)', 'Category': 'Category'})

    # Konfigurasi tampilan grafik
    fig.update_layout(
        xaxis_title='Category',
        yaxis_title='Percentage (%)',
        legend_title='Subcategory',
        bargap=0.2  # Jarak antara kolom
    )

    st.plotly_chart(fig)

    # Narasi
    st.write("""
    Grafik di atas merupakan tampilan komposisi penjualan produk berdasarkan subcategory dalam persentase. 
    Dengan grafik tersebut kita dapat melihat komposisi persentase penjualan produk berdasarkan sub category 
    dan kategorinya. Pada produk category Accessories komposisi top 3 penjualan yang paling besar adalah Tires 
    and Tubes dengan persentase 48%, Bottles and Cages dengan persentase 22.1%, dan Helmets dengan persentase 17.8%. 
    Kemudian pada produk category Bikes, komposisi top 3 penjualan yang paling besar adalah Road and Bikes dengan 
    persentase 53%, Mountain Bikes dengan persentase 32.6%, dan Touring Bikes dengan persentase 14.2%. Dan yang 
    terakhir pada produk category Clothing, komposisi top 3 penjualan yang paling besar adalah Jerseys dengan persentase 36.6%, 
    Caps dengan persentase 24.1%, dan Gloves dengan persentase 15.7%
    """)

# grafik untuk aspek distribusi
elif category == 'Distribution':

    query_dsb = """
    SELECT DISTINCT 
        TIMESTAMPDIFF(YEAR, d.BirthDate, CURDATE()) AS Age, COUNT(*) as Jumlah
    FROM factinternetsales f 
    INNER JOIN dimcustomer d ON f.CustomerKey = d.CustomerKey
    GROUP BY Age
    """

    df_dsb = conn.query(query_dsb)

    st.header("Distribusi Umur Customer")

    fig, ax = plt.subplots()
    ax.bar(df_dsb['Age'], df_dsb['Jumlah'])
    ax.set_xlabel('Age')
    ax.set_ylabel('Jumlah')

    st.pyplot(fig)

    # Narasi
    st.write("""
    Histogram yang menampilkan umur pelanggan yang melakukan transaksi. 
    Dapat dilihat bahwa mayoritas pelanggan adventure works yang melakukan transaksi ada pada rentang umur 50-60 an.
    Selain itu, pada umur lansia masih banyak yang melakukan transaksi di adventure works. Hal ini menandakan bahwa
    produk adventure works banyak diminati oleh masyarakat di umur 50 hingga lanjut.
    """)

# grafik untuk aspek relationship
elif category == 'Relationship':
    query_rlt = """
    SELECT ListPrice, TaxAmt 
    FROM factinternetsales f
    inner join dimproduct d on f.ProductKey = d.ProductKey
    """

    df_rlt = conn.query(query_rlt)
    st.header("Hubungan Antara Harga Produk dan Pajak")

    fig, ax = plt.subplots()
    ax.scatter(data=df_rlt, x='ListPrice', y='TaxAmt')
    ax.set_xlabel('List Price')
    ax.set_ylabel('Tax')

    st.pyplot(fig)

    # Narasi
    st.write("""
    Scatter plot di atas menampilkan apakah terdapat hubungan antara harga produk dengan pajak yang harus dibayar oleh customer. 
    Grafik tersebut menunjukkan bahwa adanya hubungan dari kedua variabel tersebut. Jadi, semakin mahal barang yang dibeli oleh customer
    maka tax yang dibayar oleh customer semakin tinggi juga.
    """)
