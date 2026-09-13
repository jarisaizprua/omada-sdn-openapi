# Omada Controller - OpenAPI Scripts

Scripts en Python para conectarse al controlador Omada mediante su Open API (modo **authorization code**), consultar dispositivos y usuarios locales, y crear/eliminar usuarios locales de hotspot en uno, varios o todos los sites, de forma masiva desde un Excel.

## Contenido

| Archivo | Descripción |
|---|---|
| `omada_connect.py` | Realiza el flujo completo de autenticación (login, código de autorización, access token) y guarda los tokens en `tokens.json`. |
| `omada_devices.py` | Usa los tokens generados para recorrer todos los sites del controlador y mostrar los dispositivos adoptados en cada uno. |
| `omada_local_users.py` | Usa los tokens generados para recorrer todos los sites y mostrar los usuarios locales de hotspot configurados en cada uno. |
| `omada_create_local_users.py` | Lee la hoja `CrearUsuarios` de `omada_local_users_template.xlsx` y crea cada usuario en el/los site(s) indicados. |
| `omada_delete_local_users.py` | Lee la hoja `EliminarUsuarios` de `omada_local_users_template.xlsx` y elimina cada usuario del/de los site(s) indicados. |
| `omada_local_users_template.xlsx` | Plantilla de datos con las hojas `CrearUsuarios`, `EliminarUsuarios`, `Log` e `Instrucciones`. |
| `credentials_template.json` | Plantilla de credenciales de ejemplo (con placeholders, sin datos reales). Segura para subir al repositorio. |
| `credentials.json` | Archivo local con las credenciales reales de tu controlador. **No debe subirse al repositorio con datos reales.** |
| `requirements.txt` | Dependencias de Python necesarias. |
| `.gitignore` | Excluye `tokens.json`, `credentials.json` y otros archivos que no deben subirse al repositorio. |
| `Guia_Omada_OpenAPI.pdf` | Guía detallada del proyecto (flujo OAuth 2.0, explicación de cada script, referencia de endpoints y notas de seguridad). |

## Requisitos

- Python 3.9 o superior
- Un controlador Omada con Open API habilitado (Settings > Platform Integration > Open API)
- Una aplicación creada en modo **Authorization Code**, con un usuario del controlador con permisos de vista sobre sites, dispositivos y hotspot (y de **modificación** de hotspot para crear/eliminar usuarios)

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Copia `credentials_template.json` como `credentials.json` y complétalo con los datos de tu aplicación y controlador (ver detalle de campos más abajo). Coloca también `omada_local_users_template.xlsx` en la misma carpeta.

```json
{
  "oauth_login_page_address": "https://...",
  "interface_access_address": "https://...",
  "omada_id": "...",
  "client_id": "...",
  "client_secret": "...",
  "username": "...",
  "password": "..."
}
```

Dónde encontrar cada campo, en **Settings > Platform Integration > Open API**, dentro de la vista de detalle de tu aplicación:

- **Oauth Login Page Address**: página de login para flujo por navegador (se guarda para referencia, no se usa en este flujo de login directo por API).
- **Interface Access Address**: dominio base usado para todas las llamadas (login, autorización, token, API).
- **Omada ID**: identificador del MSP o customer.
- **Client ID** / **Client Secret**: credenciales de la aplicación registrada.
- **username** / **password**: credenciales del usuario del controlador con el que se hace login.

## Uso

### 1. Conectarse al controlador

```bash
python omada_connect.py
```

Ejecuta el flujo de login → código de autorización → access token, imprime cada paso en consola (con datos sensibles enmascarados) y guarda el resultado en `tokens.json`.

### 2. Consultar dispositivos adoptados

```bash
python omada_devices.py
```

Lee `tokens.json`, obtiene todos los sites del controlador y muestra automáticamente, para cada uno, sus dispositivos adoptados. No requiere selección manual.

### 3. Consultar usuarios locales (hotspot)

```bash
python omada_local_users.py
```

Lee `tokens.json`, recorre todos los sites y muestra, para cada uno, sus usuarios locales de hotspot. El campo `password` que devuelve la API **no se imprime en consola**.

### 4. Crear usuarios locales en masa

1. Abre `omada_local_users_template.xlsx` y edita la hoja **CrearUsuarios**: una fila por usuario a crear, con `site_name` y el resto de campos (ver la hoja **Instrucciones** dentro del propio archivo para el detalle de cada columna). Borra o sobrescribe la fila de ejemplo.
2. Ejecuta:

```bash
python omada_create_local_users.py
```

Cada fila se crea en el/los site(s) indicados en `site_name`, y el resultado (OK o el error devuelto por la API) queda registrado en la hoja **Log**, con fecha y hora.

### 5. Eliminar usuarios locales en masa

1. Edita la hoja **EliminarUsuarios** de `omada_local_users_template.xlsx`: una fila por usuario a eliminar, con `site_name` y `userName`.
2. Ejecuta:

```bash
python omada_delete_local_users.py
```

El script busca el usuario por `userName` en cada site indicado y lo elimina; el resultado también queda registrado en la hoja **Log**.

### Formatos admitidos en `site_name` (crear y eliminar)

- **Un solo site**: `SITE_A`
- **Varios sites**: `SITE_A, SITE_B` (separados por coma) — la operación se repite en cada uno
- **Todos los sites del controlador**: `TODOS` (también acepta `ALL` o `*`)

Cada combinación usuario + site se procesa y registra por separado en la hoja **Log**, así que un error en un site no detiene el procesamiento de los demás.

## Notas de seguridad

- Los tokens (`accessToken`, `refreshToken`), la contraseña del controlador, las MAC y los `client_secret` se muestran parcial o totalmente enmascarados en consola.
- El campo `password` de los usuarios locales **nunca se imprime en consola** en ningún script, aunque sí se envía (sin enmascarar) en el cuerpo de la solicitud de creación, como exige la API.
- El `accessToken` es válido por 2 horas; el `refreshToken` por 14 días. Pasado ese tiempo hay que repetir el flujo de `omada_connect.py`.
- `credentials.json` y `tokens.json` contienen datos sensibles y están excluidos en `.gitignore`; solo `credentials_template.json` (con placeholders) es seguro de subir al repositorio.
- `omada_create_local_users.py` y `omada_delete_local_users.py` esperan un ritmo moderado de solicitudes (hacen una pausa de 0.2s entre cada una) para no acercarse al límite de 10 solicitudes/segundo del controlador.
- Si alguna vez un token, secreto o contraseña real queda expuesto, regenera el Client Secret de la aplicación en el controlador y/o cambia la contraseña afectada de inmediato.

## Referencia

Basado en la documentación oficial del Omada Open API (Open API Guide) para el flujo de autenticación por Authorization Code y los endpoints de sites, dispositivos, y usuarios locales de hotspot (consulta, creación y eliminación). Ver `Guia_Omada_OpenAPI.pdf` para el detalle completo.
