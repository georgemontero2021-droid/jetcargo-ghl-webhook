from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import logging
import os
from datetime import datetime, timedelta
import uuid
import pytz
from collections import defaultdict
from typing import Dict, Optional
import re

# ============================================
# CONFIGURACIÓN DE LOGGING MEJORADO
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# INICIALIZACIÓN DE FASTAPI
# ============================================

app = FastAPI(
    title="Jet Cargo → GoHighLevel Integration V2.0",
    description="Webhook mejorado con validación, rate limiting y mejor manejo de errores",
    version="2.0.0"
)

# CORS - permitir TODOS los orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# CONFIGURACIÓN
# ============================================

GHL_API_KEY = os.getenv("GOHIGHLEVEL_API_KEY")
GHL_LOCATION_ID = os.getenv("GOHIGHLEVEL_LOCATION_ID")
GHL_API_BASE = "https://services.leadconnectorhq.com"

# Validar configuración al inicio
if not GHL_API_KEY:
    logger.error("❌ GOHIGHLEVEL_API_KEY no está configurada")
if not GHL_LOCATION_ID:
    logger.error("❌ GOHIGHLEVEL_LOCATION_ID no está configurada")

# ============================================
# RATE LIMITING
# ============================================

# Cache simple para rate limiting (en producción usar Redis)
submission_cache: Dict[str, list] = defaultdict(list)

def check_rate_limit(client_ip: str, max_requests: int = 5, time_window: int = 3600) -> bool:
    """
    Verifica si el cliente ha excedido el límite de peticiones
    
    Args:
        client_ip: IP del cliente
        max_requests: Número máximo de peticiones permitidas
        time_window: Ventana de tiempo en segundos (default: 1 hora)
    
    Returns:
        True si está dentro del límite, False si lo excedió
    """
    now = datetime.now()
    
    # Limpiar peticiones antiguas
    submission_cache[client_ip] = [
        ts for ts in submission_cache[client_ip]
        if now - ts < timedelta(seconds=time_window)
    ]
    
    # Verificar límite
    if len(submission_cache[client_ip]) >= max_requests:
        logger.warning(f"⚠️ Rate limit excedido para IP: {client_ip}")
        return False
    
    # Agregar nueva petición
    submission_cache[client_ip].append(now)
    return True

# ============================================
# VALIDACIÓN DE DATOS
# ============================================

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    if not email:
        return False
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Valida formato de teléfono"""
    if not phone:
        return False
    # Remover caracteres no numéricos
    clean_phone = re.sub(r'\D', '', phone)
    # Validar que tenga al menos 10 dígitos
    return len(clean_phone) >= 10

def validate_name(name: str) -> bool:
    """Valida nombre"""
    if not name:
        return False
    return len(name.strip()) >= 2

def validate_form_data(data: dict) -> tuple[bool, list]:
    """
    Valida los datos del formulario
    
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    # Validar nombre
    name = data.get("name", "")
    if not validate_name(name):
        errors.append("Nombre inválido o faltante")
    
    # Validar email
    email = data.get("email", "")
    if not email:
        errors.append("Email es requerido")
    elif not validate_email(email):
        errors.append("Formato de email inválido")
    
    # Validar teléfono
    phone = data.get("phone", "")
    if not phone:
        errors.append("Teléfono es requerido")
    elif not validate_phone(phone):
        errors.append("Formato de teléfono inválido (mínimo 10 dígitos)")
    
    return (len(errors) == 0, errors)

# ============================================
# MAPEO DE SERVICIOS A PIPELINES
# ============================================

SERVICE_TO_PIPELINE = {
    "express_air_freight": "beJ4qtcdPASKoGBoTNqz",
    "deferred_air_freight": "beJ4qtcdPASKoGBoTNqz",
    "trucking_services": "zar5aTjIKP8srIK5x0qk",
    "international_courier": "zar5aTjIKP8srIK5x0qk",
    "cargo_consolidation": "zar5aTjIKP8srIK5x0qk",
    "lcl_ocean_freight": "whbJC2QacciLQBfk9fHl",
    "fcl_ocean_freight": "whbJC2QacciLQBfk9fHl",
    "car_auction_transport": "irrGZoV35EFiTMvzRhzP",
    "in_transit_cargo": "zar5aTjIKP8srIK5x0qk",
    "smart_storage": "zar5aTjIKP8srIK5x0qk",
    "warehousing": "zar5aTjIKP8srIK5x0qk",
    "procurement_sourcing": "uGs9dWTuLBzYr7cTyHjK",
    "customs_clearance": "zar5aTjIKP8srIK5x0qk",
    "cargo_insurance": "zar5aTjIKP8srIK5x0qk",
    "general_contact": "zar5aTjIKP8srIK5x0qk"
}

def get_pipeline_id(service_type: str) -> str:
    """Obtiene el ID del pipeline basado en el tipo de servicio"""
    return SERVICE_TO_PIPELINE.get(service_type, "zar5aTjIKP8srIK5x0qk")

# ============================================
# FUNCIONES DE GOHIGHLEVEL
# ============================================

def create_ghl_opportunity(contact_id: str, data: dict) -> Optional[dict]:
    """Crea una Oportunidad en GoHighLevel"""
    try:
        service_type = data.get("service_type", "general_contact")
        pipeline_id = get_pipeline_id(service_type)
        
        # Crear título descriptivo
        miami_tz = pytz.timezone('America/New_York')
        timestamp = datetime.now(miami_tz).strftime("%Y-%m-%d %H:%M")
        unique_id = str(uuid.uuid4())[:8]
        
        contact_name = data.get("name", "Unknown")
        title = f"{service_type.replace('_', ' ').title()} - {contact_name} - {timestamp}"
        
        # Preparar payload
        opportunity_payload = {
            "locationId": GHL_LOCATION_ID,
            "name": title,
            "pipelineId": pipeline_id,
            "contactId": contact_id,
            "status": "open",
            "source": "Website Form",
            "monetaryValue": 0
        }
        
        logger.info(f"📤 Creando Oportunidad: {title}")
        
        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Version": "2021-07-28",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{GHL_API_BASE}/opportunities/",
            json=opportunity_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            opp_id = result.get('opportunity', {}).get('id', 'unknown')
            logger.info(f"✅ Oportunidad creada: {opp_id}")
            return result
        else:
            logger.error(f"❌ Error creando oportunidad: {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Excepción creando oportunidad: {str(e)}")
        return None

def create_ghl_contact(data: dict) -> Optional[dict]:
    """Crea un contacto en GoHighLevel"""
    try:
        email = data.get("email", "")
        phone = data.get("phone", "")
        name = data.get("name", "Unknown")
        service_type = data.get("service_type", "general_contact")
        
        # Preparar payload
        ghl_payload = {
            "locationId": GHL_LOCATION_ID,
            "source": "Website - jetcargo.us"
        }
        
        # Agregar campos básicos
        if email:
            ghl_payload["email"] = email
        
        if name:
            parts = name.split()
            ghl_payload["firstName"] = parts[0] if parts else "Unknown"
            ghl_payload["lastName"] = " ".join(parts[1:]) if len(parts) > 1 else ""
        
        if phone:
            ghl_payload["phone"] = phone
        
        # Crear tags
        tags = [service_type.replace("_", " ").title()]
        
        # Agregar campos del formulario como tags
        for key, value in data.items():
            if key not in ["email", "name", "phone", "service_type", "page_url", "page_title", "timestamp", "user_agent", "referrer"] and value:
                tag_text = f"{key.replace('_', ' ').title()}: {value}"
                if len(tag_text) > 50:
                    tag_text = tag_text[:47] + "..."
                tags.append(tag_text)
        
        ghl_payload["tags"] = tags
        
        # Custom fields
        ghl_payload["customFields"] = [{
            "key": "service_type",
            "field_value": service_type
        }]
        
        logger.info(f"📤 Creando contacto: {email}")
        
        # Enviar a GoHighLevel
        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Version": "2021-07-28",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{GHL_API_BASE}/contacts/",
            json=ghl_payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"📊 GHL Response Status: {response.status_code}")
        
        # Si es duplicado, buscar contacto existente y crear oportunidad
        if response.status_code == 400 and "duplicate" in response.text.lower():
            logger.info(f"ℹ️ Contacto duplicado detectado, buscando contacto existente...")
            
            # Buscar contacto por email
            search_response = requests.get(
                f"{GHL_API_BASE}/contacts/",
                params={"locationId": GHL_LOCATION_ID, "email": email},
                headers=headers,
                timeout=30
            )
            
            if search_response.status_code == 200:
                contacts = search_response.json().get("contacts", [])
                if contacts:
                    existing_contact_id = contacts[0].get("id")
                    logger.info(f"✅ Contacto existente encontrado: {existing_contact_id}")
                    
                    # Crear oportunidad para contacto existente
                    create_ghl_opportunity(existing_contact_id, data)
                    
                    return {
                        "contact": contacts[0],
                        "is_duplicate": True,
                        "message": "Contacto ya existe, oportunidad creada"
                    }
            
            return {
                "success": False,
                "message": "Contacto duplicado pero no se pudo crear oportunidad"
            }
        
        # Si se creó exitosamente
        if response.status_code in [200, 201]:
            result = response.json()
            contact_id = result.get("contact", {}).get("id")
            logger.info(f"✅ Contacto creado: {contact_id}")
            
            # Crear oportunidad
            create_ghl_opportunity(contact_id, data)
            
            return result
        else:
            logger.error(f"❌ Error creando contacto: {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Excepción creando contacto: {str(e)}")
        return None

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Endpoint raíz - Health check"""
    return {
        "status": "ok",
        "service": "Jet Cargo → GoHighLevel Integration",
        "version": "2.0.0",
        "features": [
            "Validación de datos",
            "Rate limiting",
            "Logging mejorado",
            "Manejo de errores robusto"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    config_status = {
        "api_key_configured": bool(GHL_API_KEY),
        "location_id_configured": bool(GHL_LOCATION_ID)
    }
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": config_status
    }

@app.post("/webhook/submit")
async def handle_webhook(request: Request):
    """
    Endpoint principal para recibir formularios
    
    Validaciones:
    - Rate limiting por IP
    - Validación de datos requeridos
    - Formato de email y teléfono
    """
    try:
        # Obtener IP del cliente
        client_ip = request.client.host
        logger.info(f"📥 Nueva petición desde IP: {client_ip}")
        
        # Verificar rate limit
        if not check_rate_limit(client_ip, max_requests=5, time_window=3600):
            raise HTTPException(
                status_code=429,
                detail="Demasiadas peticiones. Por favor intenta de nuevo más tarde."
            )
        
        # Obtener datos del formulario
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"❌ Error parseando JSON: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Datos inválidos. Por favor verifica el formato."
            )
        
        logger.info(f"📊 Datos recibidos: {data}")
        
        # Validar datos
        is_valid, errors = validate_form_data(data)
        if not is_valid:
            logger.warning(f"⚠️ Validación fallida: {errors}")
            raise HTTPException(
                status_code=400,
                detail={"errors": errors, "message": "Datos de formulario inválidos"}
            )
        
        # Verificar configuración
        if not GHL_API_KEY or not GHL_LOCATION_ID:
            logger.error("❌ Configuración de GoHighLevel faltante")
            raise HTTPException(
                status_code=500,
                detail="Error de configuración del servidor"
            )
        
        # Crear contacto en GoHighLevel
        result = create_ghl_contact(data)
        
        if result:
            logger.info("✅ Procesamiento exitoso")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Contact created successfully",
                    "ghl_contact_id": result.get("contact", {}).get("id", "unknown")
                }
            )
        else:
            logger.error("❌ Error procesando formulario")
            raise HTTPException(
                status_code=500,
                detail="Error procesando el formulario. Por favor intenta de nuevo."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

# ============================================
# STARTUP EVENT
# ============================================

@app.on_event("startup")
async def startup_event():
    """Log de inicio de la aplicación"""
    logger.info("=" * 50)
    logger.info("🚀 Jet Cargo → GoHighLevel Integration V2.0")
    logger.info("=" * 50)
    logger.info(f"✅ API Key configurada: {bool(GHL_API_KEY)}")
    logger.info(f"✅ Location ID configurada: {bool(GHL_LOCATION_ID)}")
    logger.info("✅ Rate limiting activado")
    logger.info("✅ Validación de datos activada")
    logger.info("=" * 50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
