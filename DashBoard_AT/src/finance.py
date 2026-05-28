import pandas as pd
import numpy as np

categorias_impulsivas = [
    'Tecnolog\u00eda',
    'Entretenimiento',
    'Indumentaria',
    'Viajes'
]


def calcular_cuota(monto, tasa, cuotas):
    # Manejar valores faltantes o no numéricos
    try:
        monto = float(monto)
    except Exception:
        return 0.0

    # cuotas puede venir como float/NaN
    try:
        cuotas = float(cuotas)
    except Exception:
        return 0.0

    if cuotas == 0 or np.isnan(cuotas):
        return 0.0

    try:
        tasa = float(tasa)
    except Exception:
        tasa = 0.0

    if tasa == 0:
        return monto / cuotas

    cuota = monto * (
        tasa * (1 + tasa) ** cuotas
    ) / (
        ((1 + tasa) ** cuotas) - 1
    )
    return float(cuota)


def process_dataframe(df: pd.DataFrame, ingreso_mensual: float):
    df = df.copy()
    df = df.dropna(how='all')

    # Normalizar columnas de forma robusta: soporta dataframes con columnas extra
    expected = [
        'numero_operacion',
        'usuario',
        'categoria',
        'descripcion',
        'monto',
        'cuotas',
        'tna'
    ]

    cols = df.columns.tolist()
    ncols = len(cols)

    # Si ya tiene exactamente 7 columnas, reemplazamos por los nombres esperados
    if ncols == len(expected):
        df.columns = expected

    else:
        lower = [str(c).lower() for c in cols]

        # Intentar localizar columnas clave por palabra en el nombre
        def find_idx(keywords):
            for i, c in enumerate(lower):
                for kw in keywords:
                    if kw in c:
                        return i
            return None

        idx_num = find_idx(['oper', 'numero', 'id'])
        idx_user = find_idx(['usuario', 'cliente', 'user'])
        idx_categoria = find_idx(['categoria', 'cat'])
        idx_descripcion = find_idx(['descripcion', 'desc', 'detalle'])
        idx_monto = find_idx(['monto', 'amount', 'importe'])
        idx_cuotas = find_idx(['cuotas', 'plazo'])
        idx_tna = find_idx(['tna', 'tea', 'tasa'])

        found_indices = [idx_num, idx_user, idx_categoria, idx_descripcion, idx_monto, idx_cuotas, idx_tna]
        # Si encontramos al menos las columnas financieras mínimas, reordenamos
        if idx_monto is not None and idx_cuotas is not None and idx_tna is not None and idx_categoria is not None and idx_descripcion is not None:
            # Rellenar con índices disponibles, y si faltan `numero_operacion` o `usuario`, tomar columnas restantes al inicio
            selected = []
            for ix in [idx_num, idx_user, idx_categoria, idx_descripcion, idx_monto, idx_cuotas, idx_tna]:
                if ix is not None and ix not in selected:
                    selected.append(ix)

            # Si faltan posiciones para completar 7, añadir columnas desde el inicio hasta completar
            if len(selected) < len(expected):
                for i in range(ncols):
                    if i not in selected:
                        selected.insert(len(selected) if len(selected) < len(expected) else len(selected), i)
                    if len(selected) >= len(expected):
                        break

            selected = selected[:len(expected)]
            df = df.iloc[:, selected]
            df.columns = expected

        else:
            # Fallback: tomar las últimas 7 columnas si hay más, o lanzar error si hay menos
            if ncols >= len(expected):
                df = df.iloc[:, -len(expected):]
                df.columns = expected
            else:
                raise ValueError(f"El DataFrame tiene {ncols} columnas; se requieren al menos {len(expected)} columnas para procesar")

    # Normalizar columnas numéricas: `monto`, `cuotas`, `tna`
    def to_numeric_series(s: pd.Series) -> pd.Series:
        s = s.astype(str).str.strip()
        # eliminar caracteres no numéricos excepto . , -
        s = s.str.replace(r"[^0-9,\.\-]", "", regex=True)

        has_comma = s.str.contains(",").any()
        has_dot = s.str.contains("\.").any()

        # Si sólo tiene comas, tratar coma como separador decimal
        if has_comma and not has_dot:
            s = s.str.replace(",", ".")

        # Si tiene ambos, asumimos que '.' es separador de miles y ',' decimal
        if has_comma and has_dot:
            s = s.str.replace("\.", "", regex=False)
            s = s.str.replace(",", ".", regex=False)

        return pd.to_numeric(s, errors='coerce')

    # Aplicar conversiones y rellenar NaN razonables
    if 'monto' in df.columns:
        df['monto'] = to_numeric_series(df['monto']).fillna(0.0)
    if 'cuotas' in df.columns:
        df['cuotas'] = to_numeric_series(df['cuotas']).fillna(0.0)
    if 'tna' in df.columns:
        df['tna'] = to_numeric_series(df['tna']).fillna(0.0)

    df['tasa_mensual'] = (df['tna'] / 100) / 12

    df['cuota_mensual'] = df.apply(
        lambda fila: calcular_cuota(
            fila['monto'], fila['tasa_mensual'], fila['cuotas']
        ),
        axis=1
    )

    total_cuotas = df['cuota_mensual'].sum()
    ratio_endeudamiento = total_cuotas / ingreso_mensual if ingreso_mensual else np.nan

    gastos_impulsivos = df[df['categoria'].isin(categorias_impulsivas)]
    total_impulsivos = gastos_impulsivos['monto'].sum()
    ratio_impulsivos = total_impulsivos / ingreso_mensual if ingreso_mensual else np.nan

    riesgo = 0
    if ratio_endeudamiento >= 0.50:
        riesgo += 3
    elif ratio_endeudamiento >= 0.35:
        riesgo += 2
    elif ratio_endeudamiento >= 0.20:
        riesgo += 1

    if ratio_impulsivos >= 1:
        riesgo += 3
    elif ratio_impulsivos >= 0.50:
        riesgo += 2
    elif ratio_impulsivos >= 0.25:
        riesgo += 1

    if riesgo <= 1:
        nivel = "BAJO"
        alerta = "Situaci\u00f3n financiera estable"

    elif riesgo <= 3:
        nivel = "MEDIO"
        alerta = "Atenci\u00f3n: el nivel de deuda comienza a ser elevado"

    else:
        nivel = "ALTO"
        alerta = "ALERTA: posible sobreendeudamiento"

    return {
        'df': df,
        'total_cuotas': total_cuotas,
        'ratio_endeudamiento': ratio_endeudamiento,
        'gastos_impulsivos': gastos_impulsivos,
        'total_impulsivos': total_impulsivos,
        'ratio_impulsivos': ratio_impulsivos,
        'riesgo': riesgo,
        'nivel': nivel,
        'alerta': alerta
    }
