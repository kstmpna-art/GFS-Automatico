# GFS marítimo automático por Gmail

Este paquete descarga dos veces al día un pronóstico marítimo reducido de
GFS/GFS-Wave y lo envía como archivo GRIB2 adjunto mediante Gmail.

## Configuración incluida

- Horarios: 06:00 y 18:00 de Argentina.
- Región: norte -40°, sur -46°, oeste -66°, este -59°.
- Horizonte: cinco días.
- Intervalo: seis horas.
- Variables: viento a 10 m, presión al nivel del mar, altura significativa,
  dirección y período del oleaje total.

## 1. Crear el repositorio

1. Crear un repositorio **privado** en GitHub.
2. Subir todo el contenido de esta carpeta, incluida la carpeta oculta
   `.github`.
3. Verificar que la rama predeterminada sea `main`.

## 2. Preparar Gmail

1. Activar la verificación en dos pasos de la cuenta de Google remitente.
2. Crear una contraseña de aplicación para este proceso.
3. No escribir esa contraseña en ningún archivo del repositorio.

## 3. Agregar los secretos

En GitHub abrir:

`Settings > Secrets and variables > Actions > New repository secret`

Crear exactamente estos tres secretos:

| Secreto | Contenido |
|---|---|
| `MAIL_USER` | Dirección completa de Gmail que enviará el mensaje |
| `MAIL_PASSWORD` | Contraseña de aplicación de 16 caracteres |
| `MAIL_DESTINO` | Dirección que recibirá el GRIB2 |

La contraseña puede pegarse con o sin los espacios visuales que muestra
Google; si hubiera un error de autenticación, guardarla sin espacios.

## 4. Hacer la primera prueba

1. Abrir la pestaña `Actions` del repositorio.
2. Seleccionar **Enviar GRIB marítimo**.
3. Pulsar `Run workflow`.
4. Revisar el registro de ejecución y confirmar la llegada del correo.

Después de esa prueba, GitHub ejecutará el flujo automáticamente a las 06:00
y 18:00, usando la zona `America/Argentina/Buenos_Aires`.

## Seguridad y recuperación

- El flujo nunca imprime la contraseña en pantalla.
- Solo envía el archivo si supera la validación básica de GRIB.
- Usa un límite conservador de 18 MiB para el adjunto.
- Conserva cada GRIB durante tres días como artefacto descargable en GitHub,
  incluso después de enviarlo por correo.
- También puede ejecutarse manualmente desde la pestaña `Actions`.
