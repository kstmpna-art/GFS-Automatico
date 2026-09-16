#!/usr/bin/env python3
"""Reproduce el contenido del GRIB2 GFS P25 + WW3 de referencia."""

import argparse
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


URL_ATMOS = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
URL_OLAS = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfswave.pl"
PAUSA_NOMADS = 10


def parametros_region(limites):
    norte, sur, oeste, este = limites
    return {
        "subregion": "",
        "toplat": norte,
        "bottomlat": sur,
        "leftlon": oeste,
        "rightlon": este,
    }


def construir_urls_atmos(fecha, ciclo, plazo, limites):
    """Dos consultas evitan campos extra por cruces variable/nivel."""
    base = {
        "file": f"gfs.t{ciclo:02d}z.pgrb2.0p25.f{plazo:03d}",
        "dir": f"/gfs.{fecha:%Y%m%d}/{ciclo:02d}/atmos",
        **parametros_region(limites),
    }

    # PRMSL; HGT/T/RH/U/V a 700 hPa; T2m; U/V a 10 m.
    grupo_1 = {
        "lev_10_m_above_ground": "on",
        "lev_2_m_above_ground": "on",
        "lev_mean_sea_level": "on",
        "lev_700_mb": "on",
        "var_UGRD": "on",
        "var_VGRD": "on",
        "var_PRMSL": "on",
        "var_HGT": "on",
        "var_TMP": "on",
    }

    # CAPE, CIN y ráfagas en superficie; humedad relativa a 700 hPa.
    grupo_2 = {
        "lev_surface": "on",
        "lev_700_mb": "on",
        "var_CAPE": "on",
        "var_CIN": "on",
        "var_GUST": "on",
        "var_RH": "on",
    }

    return (
        URL_ATMOS + "?" + urlencode({**base, **grupo_1}),
        URL_ATMOS + "?" + urlencode({**base, **grupo_2}),
    )


def construir_url_olas(fecha, ciclo, plazo, limites):
    parametros = {
        "file": (
            f"gfswave.t{ciclo:02d}z.global.0p25."
            f"f{plazo:03d}.grib2"
        ),
        # Oleaje combinado, mar de viento y swell primario.
        "var_HTSGW": "on",
        "var_WVHGT": "on",
        "var_WVDIR": "on",
        "var_WVPER": "on",
        "var_SWELL": "on",
        "var_SWDIR": "on",
        "var_SWPER": "on",
        "lev_surface": "on",
        "lev_1_in_sequence": "on",
        "dir": f"/gfs.{fecha:%Y%m%d}/{ciclo:02d}/wave/gridded",
        **parametros_region(limites),
    }
    return URL_OLAS + "?" + urlencode(parametros)


def es_grib(datos):
    return len(datos) > 16 and datos[:4] == b"GRIB" and datos[-4:] == b"7777"


def descargar(url, intentos=3):
    solicitud = Request(
        url,
        headers={
            "User-Agent": "GFS-XyGrib-Downloader/2.0",
            "Accept": "application/octet-stream",
        },
    )
    ultimo_error = None

    for intento in range(1, intentos + 1):
        try:
            with urlopen(solicitud, timeout=180) as respuesta:
                datos = respuesta.read()
            if not es_grib(datos):
                muestra = datos[:120].decode("utf-8", errors="replace")
                raise RuntimeError(f"respuesta no GRIB: {muestra!r}")
            return datos
        except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
            ultimo_error = error
            if intento < intentos:
                espera = intento * 10
                print(f"    Falló el intento {intento}: {error}")
                print(f"    Reintentando en {espera} segundos...")
                time.sleep(espera)

    raise RuntimeError(str(ultimo_error))


def encontrar_corrida_comun(limites):
    """Busca la corrida más reciente que tenga atmósfera y olas."""
    ahora = datetime.now(dt_timezone.utc)

    for retroceso in range(3):
        fecha = (ahora - timedelta(days=retroceso)).date()
        for ciclo in (18, 12, 6, 0):
            inicio = datetime.combine(
                fecha, datetime.min.time(), tzinfo=dt_timezone.utc
            ).replace(hour=ciclo)
            if inicio > ahora:
                continue

            etiqueta = f"{fecha:%Y-%m-%d} {ciclo:02d} UTC"
            print(f"Probando corrida común {etiqueta}...")
            try:
                url_atmos_1, _ = construir_urls_atmos(
                    fecha, ciclo, 0, limites
                )
                descargar(url_atmos_1, 1)
                time.sleep(PAUSA_NOMADS)
                descargar(construir_url_olas(fecha, ciclo, 0, limites), 1)
                return fecha, ciclo
            except RuntimeError:
                time.sleep(PAUSA_NOMADS)

    raise RuntimeError(
        "No se encontró una corrida común de GFS Atmos y GFS-Wave "
        "en las últimas 72 horas."
    )


def generar_plazos(horizonte, paso):
    return list(range(0, horizonte + 1, paso))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Crea un GRIB2 con la misma selección de campos, dominio y "
            "plazos que el archivo de referencia GFS P25 + WW3."
        )
    )
    parser.add_argument("--norte", type=float, default=-18.0)
    parser.add_argument("--sur", type=float, default=-65.0)
    parser.add_argument("--oeste", type=float, default=-85.0)
    parser.add_argument("--este", type=float, default=-25.0)
    parser.add_argument("--horas", type=int, default=168)
    parser.add_argument("--paso", type=int, default=3)
    parser.add_argument("--salida", type=Path)

    # Colab/Jupyter añade "-f kernel.json". Ignoramos solo argumentos ajenos.
    args, desconocidos = parser.parse_known_args()
    if desconocidos and not any(x == "-f" or "kernel-" in x for x in desconocidos):
        print(f"Aviso: argumentos ignorados: {desconocidos}")

    print("\nGFS P25 + GFS-WAVE: PRODUCTO DE REFERENCIA")
    print("=" * 46)

    norte, sur = args.norte, args.sur
    oeste, este = args.oeste, args.este

    if norte <= sur:
        raise SystemExit("La latitud norte debe ser mayor que la latitud sur.")
    if oeste >= este:
        raise SystemExit("Esta versión requiere oeste < este.")
    if not 0 <= args.horas <= 384:
        raise SystemExit("El horizonte debe estar entre 0 y 384 horas.")
    if args.paso <= 0:
        raise SystemExit("El paso debe ser mayor que cero.")
    if args.horas > 240 and args.paso % 12 != 0:
        raise SystemExit("Para superar 240 h usá un paso múltiplo de 12.")

    limites = (norte, sur, oeste, este)
    fecha, ciclo = encontrar_corrida_comun(limites)
    salida = args.salida or Path(
        f"gfs_p25_ww3_{fecha:%Y%m%d}_{ciclo:02d}z_"
        f"f000-f{args.horas:03d}.grb2"
    )
    temporal = salida.with_suffix(salida.suffix + ".parcial")
    plazos = generar_plazos(args.horas, args.paso)

    print(f"\nCorrida: {fecha:%Y-%m-%d} {ciclo:02d} UTC")
    print(f"Dominio: N={norte}, S={sur}, O={oeste}, E={este}")
    print(f"Salida: {salida.resolve()}\n")

    total = 0
    try:
        with temporal.open("wb") as archivo:
            for numero, plazo in enumerate(plazos, 1):
                etiqueta = f"[{numero:02d}/{len(plazos):02d}] f{plazo:03d}"

                print(f"{etiqueta}: atmósfera (grupo 1/2)...")
                url_atmos_1, url_atmos_2 = construir_urls_atmos(
                    fecha, ciclo, plazo, limites
                )
                atmosferico_1 = descargar(url_atmos_1)
                archivo.write(atmosferico_1)
                total += len(atmosferico_1)
                time.sleep(PAUSA_NOMADS)

                print(f"{etiqueta}: atmósfera (grupo 2/2)...")
                atmosferico_2 = descargar(url_atmos_2)
                archivo.write(atmosferico_2)
                total += len(atmosferico_2)
                time.sleep(PAUSA_NOMADS)

                print(f"{etiqueta}: olas...")
                olas = descargar(
                    construir_url_olas(fecha, ciclo, plazo, limites)
                )
                archivo.write(olas)
                total += len(olas)

                print(
                    f"    Atmos {(len(atmosferico_1)+len(atmosferico_2))/1024:.1f} KiB | "
                    f"Olas {len(olas)/1024:.1f} KiB"
                )
                if numero < len(plazos):
                    time.sleep(PAUSA_NOMADS)

        temporal.replace(salida)
    except KeyboardInterrupt:
        raise SystemExit(f"Descarga cancelada. Parcial: {temporal}")
    except Exception:
        print(f"Descarga incompleta conservada en: {temporal}")
        raise

    print("\nDescarga terminada.")
    print(f"Tamaño: {total/(1024*1024):.2f} MiB")
    print(f"Archivo para XyGrib: {salida.resolve()}")


if __name__ == "__main__":
    main()
