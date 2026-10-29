# MONSTIE CHARTS — starter gratuito

Sitio fan en español para seguir charts de BABYMONSTER. Está preparado para GitHub Pages y una tarea programada de GitHub Actions.

## Qué incluye ahora
- `index.html`: interfaz responsive con estilo mixto Kworb/K-pop.
- `scripts/fetch_kworb.py`: intenta recopilar la tabla pública de canciones de BABYMONSTER en Kworb (streams totales y diarios).
- `.github/workflows/update-data.yml`: ejecuta la recopilación cada 6 horas y permite ejecutarla manualmente.
- `data/spotify-songs.json`: datos de ejemplo vacíos hasta que corra la automatización.

**Limitación honesta:** el primer recopilador solo obtiene estadísticas de canciones en Spotify publicadas por Kworb. Esos números no son posiciones oficiales del Spotify Top 200. El resto de plataformas se irán incorporando únicamente con fuentes verificables y acceso compatible. Las páginas pueden cambiar su estructura o limitar solicitudes; el workflow puede requerir ajustes.

## Publicar gratis con GitHub Pages
1. Crea una cuenta en https://github.com/ si aún no tienes.
2. Crea un repositorio **público** llamado `monstie-charts`.
3. Sube todos los archivos de esta carpeta conservando las rutas. Puedes usar **Add file → Upload files** en GitHub.
4. En el repositorio abre **Settings → Pages**.
5. En “Build and deployment”, selecciona **Deploy from a branch**, elige `main` y la carpeta `/ (root)`, y guarda.
6. Abre **Actions** y ejecuta “Actualizar datos de Kworb” con **Run workflow**. Comprueba que termine correctamente y que se haya actualizado `data/spotify-songs.json`.
7. La web quedará en `https://TU-USUARIO.github.io/monstie-charts/`.

## Activar automatización
El workflow viene configurado cada 6 horas y también admite ejecución manual. En repositorios públicos, los runners estándar de GitHub Actions son gratuitos según la documentación actual. La programación de Actions puede retrasarse ocasionalmente.
No se necesita token ni contraseña para esta fuente pública. No añadas secretos a la web.

## Cómo revisar los datos
- Fuente de estadísticas: https://kworb.net/spotify/artist/1SIocsqdEefUTE6XKGUiVS_songs.html
- Chart history: https://kworb.net/spotify/artist/1SIocsqdEefUTE6XKGUiVS.html
- YouTube Charts: https://charts.youtube.com/
- Kworb iTunes / charts multi-plataforma: https://kworb.net/itunes/artist/babymonster.html

## Aviso
Proyecto fan independiente, no afiliado a BABYMONSTER, YG Entertainment, Spotify, YouTube ni Kworb. Respeta términos y límites de cada fuente; este repositorio enlaza las fuentes originales y no pretende ser una API oficial.


## Historial centralizado (actualización)
- `scripts/snapshot_history.py` guarda capturas compartidas de Spotify y YouTube en `data/history.json`.
- El workflow actualiza la captura del día cada seis horas y conserva hasta 365 fechas; cada fecha contiene agregados y rankings Top 50 para comparar tendencias.
- El historial no es retroactivo: empieza con la primera ejecución correcta. El panel muestra las últimas 14 fechas disponibles.
- YouTube requiere el secreto opcional `YOUTUBE_API_KEY`. Si falta, el workflow conserva el último archivo de datos disponible en lugar de fallar por ese motivo.


## Calidad de datos y movimientos de ranking
- El workflow valida los JSON de Spotify, YouTube e historial antes de publicar una captura.
- La página muestra el movimiento de posición frente a la última captura de un día anterior solo si la fuente tiene una marca de actualización distinta. Si no hay histórico o la fuente no se ha actualizado, lo indica en lugar de inventar una variación.
- El historial compartido conserva hasta 365 fechas UTC; la tabla de la página muestra las 14 más recientes. No existe histórico retroactivo anterior a la primera captura correcta.
- Spotify muestra estadísticas de canciones reportadas por Kworb; YouTube muestra videos detectados por título en el canal oficial. Ninguno debe interpretarse como una clasificación oficial de charts de plataforma.
