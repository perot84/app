import streamlit as st
import pandas as pd

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
    df.to_excel('datos.xlsx', index=False)

    st.write("Archivo Excel creado exitosamente.")

if __name__ == "__main__":
    main()

