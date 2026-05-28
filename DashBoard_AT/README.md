# Indicador de Sobre-endeudamiento (Streamlit)

Proyecto adaptado para ejecutarse con Streamlit.

Requisitos e instalación:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Ejecutar la app:

```bash
streamlit run streamlit_app.py
```

Notas:
- El script original omitía las dos primeras filas del Excel; por defecto el lector intenta usar `skiprows=2`. Si tu archivo no tiene esas filas, la app intenta leer sin `skiprows`.
- Ajusta la lista de `categorias_impulsivas` en `src/finance.py` según tus datos.
