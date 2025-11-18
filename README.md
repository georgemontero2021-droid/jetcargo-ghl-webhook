'''
# Integración de Formularios Web de Jet Cargo con GoHighLevel CRM

**Proyecto desarrollado por:** Manus AI  
**Fecha:** 16 de noviembre de 2025  
**Versión:** 1.0.0

---

## 1. Resumen del Proyecto

Este proyecto implementa una solución completa para integrar los formularios del sitio web **www.jetcargo.us** con el CRM de **GoHighLevel**. El objetivo es automatizar la captura de leads desde todos los formularios de servicios, asegurando que cada prospecto sea registrado en GoHighLevel de manera instantánea, segmentado correctamente y asignado al pipeline de ventas sin intervención manual.

La solución se basa en una arquitectura de **servidor webhook intermedio**, que ofrece la máxima seguridad, flexibilidad y escalabilidad.

### Componentes de la Solución

1.  **Servidor Webhook (Python/FastAPI):** Una aplicación robusta que recibe los datos de los formularios, los procesa y los envía de forma segura a la API de GoHighLevel.
2.  **Script de Integración (JavaScript):** Un script ligero que se añade al sitio web para interceptar los envíos de formularios y enviarlos al servidor webhook sin afectar la funcionalidad existente.
3.  **Documentación Completa:** Guías detalladas para el despliegue, la implementación y el mantenimiento de la solución.

---

## 2. Guía de Implementación para el Desarrollador (Altech Web Design)

Esta sección contiene todos los pasos técnicos necesarios para desplegar e integrar la solución.

### Paso 1: Desplegar el Servidor Webhook

El servidor webhook está diseñado para ser desplegado en plataformas de hosting modernas como **Railway**, **Render** o **Heroku**. Recomendamos **Railway** por su facilidad de uso y su plan gratuito.

#### Despliegue en Railway (Recomendado):

1.  **Crear una cuenta** en [railway.app](https://railway.app).
2.  **Conectar tu cuenta de GitHub** a Railway.
3.  **Crear un nuevo repositorio en GitHub** y subir todos los archivos de este proyecto.
4.  En el dashboard de Railway, hacer clic en **"New Project"** y seleccionar **"Deploy from GitHub repo"**.
5.  Seleccionar el repositorio que acabas de crear.
6.  Railway detectará automáticamente la configuración y comenzará el despliegue.
7.  **Configurar las variables de entorno:**
    -   Ir a la pestaña **"Variables"** del proyecto en Railway.
    -   Añadir las siguientes variables:
        -   `GOHIGHLEVEL_API_KEY`: El Private Integration Token de GoHighLevel.
        -   `GOHIGHLEVEL_LOCATION_ID`: El Location ID (Sub-Account ID) de GoHighLevel.
8.  **Obtener la URL pública:**
    -   Una vez desplegado, Railway asignará una URL pública al servicio (ej: `https://my-project-production.up.railway.app`).
    -   Esta será la **URL del Webhook** que necesitarás en el siguiente paso.

#### Despliegue en Heroku:

El proyecto incluye un `Procfile` y `runtime.txt` para despliegue en Heroku. El proceso es similar: crear una app, conectar a GitHub y configurar las variables de entorno en la sección "Config Vars".

### Paso 2: Configurar el Script de Integración en el Sitio Web

El archivo `jetcargo_integration.js` debe ser añadido al sitio web `www.jetcargo.us`.

1.  **Subir el archivo `jetcargo_integration.js`** al servidor del sitio web (ej: en una carpeta `/js/`).

2.  **Editar el archivo `jetcargo_integration.js`** y reemplazar el placeholder `TU_URL_DEL_WEBHOOK_AQUI` con la URL pública obtenida en el paso anterior.

    ```javascript
    // Antes
    const WEBHOOK_URL = 'TU_URL_DEL_WEBHOOK_AQUI/webhook/submit';

    // Después (ejemplo)
    const WEBHOOK_URL = 'https://jetcargo-ghl-prod.up.railway.app/webhook/submit';
    ```

3.  **Añadir el script al `<head>` o al final del `<body>`** de todas las páginas del sitio web. Es crucial que se cargue en todas las páginas para asegurar que todos los formularios (incluyendo los modales) sean capturados.

    ```html
    <script src="/js/jetcargo_integration.js" defer></script>
    ```

    Añadir el atributo `defer` es importante para que el script se ejecute después de que el DOM esté completamente cargado.

### Paso 3: Verificación y Pruebas

1.  **Verificar la carga del script:**
    -   Abrir el sitio web en un navegador.
    -   Abrir la consola de desarrollador (F12).
    -   Deberías ver el mensaje: `🚀 Jet Cargo → GoHighLevel Integration iniciada`.

2.  **Probar un formulario:**
    -   Rellena y envía cualquier formulario de cotización o el formulario de contacto.
    -   En la consola del navegador, deberías ver mensajes de éxito como `✅ Formulario enviado a GoHighLevel`.

3.  **Verificar los logs del servidor:**
    -   En el dashboard de Railway (o la plataforma que uses), revisa los logs del servicio.
    -   Deberías ver entradas como: `INFO: Recibido formulario de: test@example.com - Servicio: express_air_freight` y `INFO: Contacto creado exitosamente: ...`.

4.  **Verificar en GoHighLevel:**
    -   Inicia sesión en la cuenta de GoHighLevel de Jet Cargo.
    -   Ve a la sección de **Contactos**. El nuevo contacto debería aparecer con los datos, tags y campos personalizados correctos.
    -   Ve a la sección de **Oportunidades**. Debería haberse creado una nueva oportunidad en el pipeline.

---

## 3. Guía para el Usuario (Jet Cargo)

### ¿Qué hace esta integración?

Cada vez que un cliente potencial rellena un formulario en tu sitio web, esta integración **captura automáticamente** toda esa información y la envía a tu CRM de GoHighLevel. Esto significa:

-   **No más copiar y pegar:** Los leads aparecen en tu CRM al instante.
-   **Segmentación automática:** Cada lead es etiquetado según el servicio que le interesa (ej: "Air Freight", "Car Auction").
-   **Visibilidad total:** Sabrás exactamente de dónde viene cada lead y qué necesita.

### ¿Cómo funciona?

1.  Un cliente visita `www.jetcargo.us` y solicita una cotización.
2.  Nuestro sistema intercepta los datos del formulario.
3.  Los datos se envían de forma segura a GoHighLevel.
4.  En tu CRM, verás un **nuevo contacto** con todos sus detalles y un **tag** que indica el servicio de interés.

### ¿Qué necesitas hacer tú?

¡Nada! La integración es completamente automática. Tu única tarea es:

1.  **Revisar los nuevos leads** que llegan a tu pipeline en GoHighLevel.
2.  **Contactarlos** y cerrar la venta.

### Configuración de Automatizaciones en GoHighLevel

Para sacar el máximo provecho, te recomendamos configurar **Workflows** en GoHighLevel. Por ejemplo:

-   **Workflow de Bienvenida:** Cuando un contacto con el tag "Website" es creado, envíale automáticamente un email de bienvenida.
-   **Workflow de Notificación:** Cuando se crea una nueva oportunidad, notifica al equipo de ventas por email o SMS.
-   **Workflow de Seguimiento:** Si un lead no es contactado en 24 horas, envía un recordatorio al vendedor asignado.

---

## 4. Detalles de la Arquitectura y Mantenimiento

### Servidor Webhook

-   **Framework:** FastAPI (Python)
-   **Endpoints:**
    -   `/webhook/submit`: Recibe los datos de los formularios.
    -   `/health`: Endpoint de monitoreo para verificar el estado del servicio.
    -   `/`: Información básica del servicio.
-   **Logging:** Todas las transacciones (exitosas y fallidas) se registran en el archivo `webhook_integration.log` y en los logs de la plataforma de despliegue.

### Script de Integración

-   **Lenguaje:** JavaScript (Vanilla JS)
-   **Funcionalidad:**
    -   Se adhiere a todos los formularios de la página, incluyendo los que se cargan dinámicamente (modales).
    -   Detecta el tipo de servicio basado en el contexto del formulario.
    -   Extrae los datos y los mapea a un formato estándar.
    -   Envía los datos al servidor webhook de forma asíncrona, sin interrumpir el flujo normal del formulario.

### Seguridad

-   **HTTPS:** Toda la comunicación está encriptada.
-   **Variables de Entorno:** Las credenciales de la API de GoHighLevel se gestionan de forma segura como variables de entorno en el servidor, nunca se exponen en el código del sitio web.
-   **CORS:** El servidor solo acepta peticiones desde el dominio `www.jetcargo.us`.

### Mantenimiento

-   **Monitoreo:** Revisa periódicamente los logs del servidor en la plataforma de despliegue (ej. Railway) para asegurar que todo funciona correctamente.
-   **Actualizaciones:** Si se añaden nuevos formularios o servicios al sitio web, el script de JavaScript intentará detectarlos automáticamente. Si es un servicio completamente nuevo, puede que sea necesario actualizar el `SERVICE_MAPPING` en el archivo `jetcargo_integration.js`.
-   **Dependencias:** Las dependencias de Python están fijadas en `requirements.txt` para asegurar la estabilidad. Se recomienda actualizarlas anualmente.

---

## 5. Estructura de Archivos

```
/jetcargo_ghl_integration/
├── webhook_server.py        # Lógica principal del servidor webhook (Python/FastAPI)
├── jetcargo_integration.js  # Script para integrar en el sitio web (JavaScript)
├── requirements.txt         # Dependencias de Python para el servidor
├── .env.example             # Plantilla para variables de entorno
├── railway.json             # Configuración de despliegue para Railway
├── Procfile                 # Configuración de despliegue para Heroku
├── runtime.txt              # Especifica la versión de Python para Heroku
└── README.md                # Esta documentación
```
'''
