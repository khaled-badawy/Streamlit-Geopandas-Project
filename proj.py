import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import folium
import leafmap.leafmap as lm
import requests 
import os
import shutil
import subprocess
from folium.plugins import Draw
from streamlit_folium import st_folium


headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
}
close = False
# ask user to upload a GeoJSON file
inputFile = st.file_uploader("upload file",type=["geojson",'gpkg'])
if  inputFile:
    gfile = gpd.read_file(inputFile)

    # checkbox to choose between converting file or do some analysis
    file_conversion = st.checkbox('File Conversion')
    show_map = st.checkbox('Show map')
    work_with_map = st.checkbox('To add features to your map and exporting it as geojson file')
    cent_route = st.checkbox('To get Centroid or Best Route')
    getcentroid ='To get centroid of polygons'
    getbestroute = "To get route between two points"

    if file_conversion:
        # dropdown list to choose the intended conversion
        option = st.selectbox(
            'Choose format you want to transform your uploaded file into ',
            ('GeoPackage', 'Shape file', 'Geo-database'))
        
        st.write('You selected:', option)

        if option == 'Shape file':
            # check if folder ShapeFiles is existed already or not , if it's i will delete the folder and create a new one
            if os.path.exists('ShapeFiles'):
                shutil.rmtree('ShapeFiles')
                os.makedirs('ShapeFiles')
            else:
                os.makedirs('ShapeFiles')
            # file conversion
            shape_file = gfile.to_file("./ShapeFiles/file.shp" , driver = 'ESRI Shapefile')
            # create new folder and zipping it to include all converted files
            shapeFolder_path = 'ShapeFiles'
            zip_shapeFile_path = 'ShapeFiles'
            zip_path = shutil.make_archive(zip_shapeFile_path,"zip",shapeFolder_path)
            # downloading the zip file
            with open("ShapeFiles.zip", "rb") as file:
                st.download_button(
                    label = 'Download file as Shape file ',
                    file_name = 'ShapeFiles.zip',
                    data = file
                )
        elif option == 'GeoPackage':
            geopackage_file = gfile.to_file("./file.gpkg" , driver = 'GPKG')
            with open("file.gpkg", "rb") as file:
                st.download_button(
                    label = 'Download file as Geopackage ',
                    file_name = 'file.gpkg',
                    data = file
                )
        else :
            if os.path.exists('geodatabase.gdb'):
                shutil.rmtree('geodatabase.gdb')
            # here i converted to GPKG because it wasn't available to convert to gdb directly
            geopackage_file = gfile.to_file("./file.gpkg" , driver = 'GPKG')
            # i used subprocess to make ogr command as it was disabled to convert to gdb using built in function
            st.write("Hint : there's a file called 'file.gpkg' that has been created in your directory please upload it to convert to geodatabase")
            gpkg_file = st.file_uploader("upload file",type=['gpkg'])
            # i used subprocess to make ogr command as it was disabled to convert to gdb using built in function
            if gpkg_file:
                st.write("HIIIII")
                subprocess.run(['ogr2ogr', '-f', 'FileGDB', 'geodatabase.gdb', f'{gpkg_file}'],shell=True)
                gdb_path = 'geodatabase.gdb'
                zip_gdb_path = 'geodatabase'
                zip_path = shutil.make_archive(zip_gdb_path,"zip",gdb_path)
                with open(zip_path, "rb") as file:
                    st.download_button(
                        label = 'Download file as Geo-database file ',
                        file_name = 'geodatabase.zip',
                        data = file,
                    )
    if show_map:
        m = leafmap.Map(
            draw_control=False,
            measure_control=False,
        )
        m.add_gdf(gfile)
        m.to_streamlit(height=500)

    if work_with_map:
        m = leafmap.Map()
        m.add_gdf(gfile)
        Draw(export=True,).add_to(m)
        drawn_features = st_folium(m, width=700, height=500)
        st.write(drawn_features)
    if cent_route:
        radio_button = st.radio(label='',options=(getcentroid,getbestroute))
        if radio_button == getcentroid :
            m = leafmap.Map(
                draw_control=False,
                measure_control=False,
            )
            m.add_gdf(gfile)
            gfile['centroid'] = gfile.centroid
            for _, r in gfile.iterrows():
                lat = r['centroid'].y
                lon = r['centroid'].x
                folium.Marker(location=[lat, lon],
                    popup='<b> longitude: {}</b> <br> <b> latitude : {}'.format([lon],[lat])).add_to(m) 
            m.to_streamlit()
        start_point = st.text_input('Start point :', placeholder='longitude,latitude')
        end_point = st.text_input('End point :', placeholder='longitude,latitude')
        if radio_button == getbestroute:      
            if st.button('Get route'):

                m = leafmap.Map(
                    draw_control=False,
                    measure_control=False,
                )
                m.add_gdf(gfile)
                #st.write('hello')
                gfile['centroid'] = gfile.centroid
                for _, r in gfile.iterrows():
                    lat = r['centroid'].y
                    lon = r['centroid'].x
                    folium.Marker(location=[lat, lon],
                        popup='<b> longitude: {}</b> <br> <b> latitude : {}'.format([lon],[lat])).add_to(m)
                key = '5b3ce3597851110001cf62486efc212f0b344436b9bb584c8d39e4af'
                call = requests.get(f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={key}&start={start_point}&end={end_point}', headers=headers)
                #st.write('hello')
                call_gdf = gpd.read_file(call.text)
                #st.write('hello')
                m.add_gdf(call_gdf)
                #st.write('hello')
                m.to_streamlit()