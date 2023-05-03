import folium
import requests
import streamlit as st
from pandas import json_normalize
from sklearn.cluster import KMeans
from tabulate import tabulate

st.set_page_config(page_title="Kmeans geolocation", page_icon="📍")

st.title("Kmeans geolocation Project")
st.markdown("This project is about clustering locations based on the number of cafes, department stores and gyms near apartments around the give latitude and longitude")
st.markdown('''
    Major project by
    - [Aakash Kaushik](ak9169@srmist.edu.in)
    - [Swarnima Gupta](sg7424@srmist.edu.in)
    ''')

name = st.text_input(label="Name", placeholder="default: SRMIST")
if not name:
    name = "SRMIST"
input_long = st.text_input(label="Longitude", placeholder="default: SRMIST longitude")
input_lat = st.text_input(label="Latitude", placeholder="default: SRMIST latitude")
if not input_long or not input_lat:
    input_long = 12.82317
    input_lat = 80.04523

if st.button("Show map"):
    if not input_long or not input_lat:
        st.warning("Please enter the longitude and latitude")
    else:
        url = f"https://discover.search.hereapi.com/v1/discover?in=circle:{input_long},{input_lat};r=20000&q=apartment&apiKey=uJHMEjeagmFGldXp661-pDMf4R-PxvWIu7I68UjYC5Q"
        data = requests.get(url).json()
        d=json_normalize(data['items'])
        d.to_csv('api-data/apartment.csv')

        #Cleaning API data
        d2=d[['title','address.label','distance','access','position.lat','position.lng','address.postalCode','contacts','id']]
        d2.to_csv('api-data/cleaned_apartment.csv')

        df_final=d2[['position.lat','position.lng']]

        CafeList=[]
        DepList=[]
        GymList=[]
        latitudes = list(d2['position.lat'])
        longitudes = list( d2['position.lng'])
        for lat, lng in zip(latitudes, longitudes):    
            radius = '2000' #Set the radius to 2000 metres
            latitude=lat
            longitude=lng
            
            search_query = 'cafe' #Search for any cafes
            url = 'https://discover.search.hereapi.com/v1/discover?in=circle:{},{};r={}&q={}&apiKey=uJHMEjeagmFGldXp661-pDMf4R-PxvWIu7I68UjYC5Q'.format(latitude, longitude, radius, search_query)
            results = requests.get(url).json()
            venues=json_normalize(results['items'])
            if not venues.empty:
                CafeList.append(venues['title'].count())
            else:
                CafeList.append(0)
            
            search_query = 'gym' #Search for any gyms
            url = 'https://discover.search.hereapi.com/v1/discover?in=circle:{},{};r={}&q={}&apiKey=uJHMEjeagmFGldXp661-pDMf4R-PxvWIu7I68UjYC5Q'.format(latitude, longitude, radius, search_query)
            results = requests.get(url).json()
            venues=json_normalize(results['items'])
            if not venues.empty:
                GymList.append(venues['title'].count())
            else:
                GymList.append(0)

            search_query = 'department-store' #search for supermarkets
            url = 'https://discover.search.hereapi.com/v1/discover?in=circle:{},{};r={}&q={}&apiKey=uJHMEjeagmFGldXp661-pDMf4R-PxvWIu7I68UjYC5Q'.format(latitude, longitude, radius, search_query)
            results = requests.get(url).json()
            venues=json_normalize(results['items'])
            if not venues.empty:
                DepList.append(venues['title'].count())
            else:
                DepList.append(0)

        df_final['Cafes'] = CafeList
        df_final['Department Stores'] = DepList
        df_final['Gyms'] = GymList

        #Run K-means clustering on dataframe
        kclusters = 3

        kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(df_final)
        df_final['Cluster']=kmeans.labels_
        df_final['Cluster']=df_final['Cluster'].apply(str)

        #Plotting clustered locations on map using Folium

        #define coordinates of the college
        map_bom=folium.Map(location=[input_long, input_lat],zoom_start=12)

        # instantiate a feature group for the incidents in the dataframe
        locations = folium.map.FeatureGroup()

        # set color scheme for the clusters
        def color_producer(cluster):
            if cluster=='0':
                return 'green'
            elif cluster=='1':
                return 'orange'
            else:
                return 'red'

        latitudes = list(df_final['position.lat'])
        longitudes = list(df_final['position.lng'])
        labels = list(df_final['Cluster'])
        names=list(d2['title'])
        for lat, lng, label,names in zip(latitudes, longitudes, labels,names):
            folium.CircleMarker(
                    [lat,lng],
                    fill=True,
                    fill_opacity=1,
                    popup=folium.Popup(names, max_width = 300),
                    radius=5,
                    color=color_producer(label)
                ).add_to(map_bom)

        # add locations to map
        map_bom.add_child(locations)
        folium.Marker([input_long, input_lat],popup=name).add_to(map_bom)

        #saving the map 
        map_bom.save("map.html")

        legend_html = '''
        <div>
        <span style="display: inline-block; background-color: {}; width: 20px; height: 20px; border-radius: 50%;"></span>
        <span style="margin-left: 10px;">{}</span>
        </div>
         '''
        st.components.v1.html(open("map.html", 'r', encoding='utf-8').read(), height=600)
        st.markdown(f'''Legend: The clusters are in the descending order of their distance from the college and number of amenities available in the vicinity.
                    <ul style="list-style-type: none;">
                    <li>{legend_html.format("green", "Cluster 1")}</li>
                    <li>{legend_html.format("orange", "Cluster 2")}</li>
                    <li>{legend_html.format("red", "Cluster 3")}</li>
                    </ul>
                    ''', unsafe_allow_html=True)
