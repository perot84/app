import streamlit as st
import pandas as pd
import io

def main():
    # Pedir los datos de entrada al usuario
    nif_input = st.text_input("Ingresa los NIF separados por comas: ")
    nom_input = st.text_input("Ingresa los Nombres separados por comas: ")

    # Convertir los datos de entrada a listas
    nif = nif_input.split(',')
    nom = nom_input.split(',')

    # Crear el DataFrame
    df = pd.DataFrame({'NIF': nif, 'Nom': nom})

    # Guardar el DataFrame en un archivo Excel
    excel_file = 'datos.xlsx'
    df.to_excel(excel_file, index=False)

    # Permitir que los usuarios descarguen el archivo Excel
    with open(excel_file, 'rb') as file:
        excel_data = file.read()

    st.download_button(
        label="Descarrega",
        data=excel_data,
        file_name=excel_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.write("Archivo Excel creado exitosamente.")

if __name__ == "__main__":
    main()
