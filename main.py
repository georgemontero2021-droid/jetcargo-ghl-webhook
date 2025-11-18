from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import requests
import logging
import os
from datetime import datetime
import uuid
import pytz

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Jet Cargo → GoHighLevel Integration")

# CORS - permitir TODOS los orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de GoHighLevel
GHL_API_KEY = os.getenv("GOHIGHLEVEL_API_KEY")
GHL_LOCATION_ID = os.getenv("GOHIGHLEVEL_LOCATION_ID")
GHL_API_BASE = "https://services.leadconnectorhq.com"

# Mapeo de servicios a pipelines (IDs reales de GoHighLevel)
SERVICE_TO_PIPELINE = {
    "express_air_freight": "beJ4qtcdPASKoGBoTNqz",  # Air Freight - Urgent
    "trucking_services": "zar5aTjIKP8srIK5x0qk",  # General Services
    "international_courier": "zar5aTjIKP8srIK5x0qk",  # General Services
    "cargo_consolidation": "zar5aTjIKP8srIK5x0qk",  # General Services
    "global_ocean_freight": "whbJC2QacciLQBfk9fHl",  # Ocean Freight
    "car_auction": "irrGZoV35EFiTMvzRhzP",  # Car Auction
    "in_transit_cargo": "zar5aTjIKP8srIK5x0qk",  # General Services
    "smart_storage": "zar5aTjIKP8srIK5x0qk",  # General Services
    "procurement_usa": "uGs9dWTuLBzYr7cTyHjK",  # Procurement & Sourcing
    "procurement_china": "uGs9dWTuLBzYr7cTyHjK",  # Procurement & Sourcing
    "charter_flights": "beJ4qtcdPASKoGBoTNqz",  # Air Freight - Urgent
    "car_shipment_container": "irrGZoV35EFiTMvzRhzP",  # Car Auction
    "contact_form": "zar5aTjIKP8srIK5x0qk"  # General Services
}

def get_pipeline_id(service_type: str):
    """
    Obtiene el ID del pipeline basado en el tipo de servicio
    """
    pipeline_id = SERVICE_TO_PIPELINE.get(service_type, "zar5aTjIKP8srIK5x0qk")  # Default: General Services
    return pipeline_id

def create_ghl_opportunity(contact_id: str, data: dict):
    """
    Crea una Oportunidad en GoHighLevel para un contacto existente
    """
    try:
        service_type = data.get("service_type", "contact_form")
        pipeline_id = get_pipeline_id(service_type)
        
        # Crear título descriptivo con timestamp e ID único (zona horaria Miami)
        miami_tz = pytz.timezone('America/New_York')
        timestamp = datetime.now(miami_tz).strftime("%Y-%m-%d %H:%M")
        unique_id = str(uuid.uuid4())[:8]  # Primeros 8 caracteres del UUID
        
        # Extraer nombre del contacto para el título
        contact_name = data.get("name", "")
        if not contact_name:
            for key in data.keys():
                if key.startswith('dmform-0'):
                    contact_name = data.get(key, "")
                    break
        
        # Crear título más descriptivo
        if contact_name:
            title = f"{service_type.replace('_', ' ').title()} - {contact_name} - {timestamp}"
        else:
            title = f"{service_type.replace('_', ' ').title()} - {timestamp} #{unique_id}"
        
        # Preparar notas con todos los campos del formulario
        notes = "📋 Detalles del formulario:\n\n"
        for key, value in data.items():
            if key not in ["email", "phone"] and value:
                notes += f"{key}: {value}\n"
        
        # Payload para crear oportunidad
        opportunity_payload = {
            "locationId": GHL_LOCATION_ID,
            "name": title,
            "pipelineId": pipeline_id,
            "contactId": contact_id,
            "status": "open",
            "source": "Website Form",
            "monetaryValue": 0
        }
        
        logger.info(f"📤 Creando Oportunidad: {opportunity_payload}")
        
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
        
        logger.info(f"📊 Opportunity Response Status: {response.status_code}")
        logger.info(f"📊 Opportunity Response: {response.text}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ Oportunidad creada: {result.get('opportunity', {}).get('id', 'unknown')}")
            return result
        else:
            logger.error(f"❌ Error creando oportunidad: {response.text}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error creando oportunidad: {str(e)}")
        return None

def extract_form_data(data: dict):
    """
    Extrae y organiza los datos del formulario para campos específicos
    """
    # Mapeo de campos del formulario a nombres legibles
    destination = ""
    origin = ""
    weight = ""
    
    # Buscar destino en varios campos posibles
    for key in data.keys():
        value = str(data.get(key, "")).lower()
        if "destination" in key.lower() or "destino" in key.lower():
            destination = data.get(key, "")
        elif "origin" in key.lower() or "shipping" in key.lower() and "origin" in value:
            origin = data.get(key, "")
        elif "cargo" in key.lower() or "weight" in key.lower() or "package" in key.lower() or "pallet" in key.lower():
            if not weight:  # Solo tomar el primero
                weight = data.get(key, "")
    
    return {
        "destination": destination,
        "origin": origin,
        "weight": weight
    }

def create_ghl_contact(data: dict):
    """
    Crea un contacto en GoHighLevel con CUALQUIER dato que venga
    Si el contacto ya existe, crea una Oportunidad
    """
    try:
        # Extraer campos básicos si existen
        email = data.get("email", "")
        phone = data.get("phone", "")
        service_type = data.get("service_type", "contact_form")
        
        # Extraer NOMBRE - buscar en múltiples campos posibles
        name = data.get("name", "")
        if not name:
            # Buscar en dmform-0, dmform-00, dmform-1, etc.
            for key in data.keys():
                if key.startswith('dmform-0') or key == 'dmform-0' or key == 'dmform-00':
                    name = data.get(key, "")
                    logger.info(f"📝 Nombre extraído de {key}: {name}")
                    break
        
        # Si aún no hay nombre, usar Unknown
        if not name:
            name = "Unknown"
            logger.warning("⚠️ No se encontró nombre en los datos")
        
        # Preparar payload mínimo para GoHighLevel
        ghl_payload = {
            "locationId": GHL_LOCATION_ID,
            "source": "Website - jetcargo.us"
        }
        
        # Agregar campos solo si existen y no están vacíos
        if email:
            ghl_payload["email"] = email
        if name:
            # Dividir nombre en firstName y lastName
            parts = name.split()
            ghl_payload["firstName"] = parts[0] if parts else "Unknown"
            ghl_payload["lastName"] = " ".join(parts[1:]) if len(parts) > 1 else ""
        if phone:
            ghl_payload["phone"] = phone
        
        # Convertir TODOS los campos del formulario en TAGS
        tags = []
        
        # Tag principal: Servicio
        service_tag = service_type.replace("_", " ").title()
        tags.append(service_tag)
        
        # Mapeo de nombres de campos a etiquetas legibles
        field_labels = {
            "destination": "Destino",
            "origin": "Origen",
            "weight": "Peso",
            "kilo": "Kilos",
            "lb": "Lbs",
            "cargo": "Carga",
            "package": "PCS",
            "pallet": "Pallets",
            "pcs": "PCS",
            "pieces": "PCS",
            "company": "Empresa",
            "shipping": "Envío",
            "description": "Descripción",
            "goods": "Mercancía",
            "handling": "Handling",
            "special": "Especial",
            "hub": "Hub",
            "consolidation": "Consolidación"
        }
        
        # Si hay all_fields, expandirlo primero
        all_fields_data = {}
        if "all_fields" in data and isinstance(data["all_fields"], dict):
            all_fields_data = data["all_fields"]
            # Remover all_fields de data para no procesarlo como tag
            data_to_process = {k: v for k, v in data.items() if k != "all_fields"}
            # Agregar los campos de all_fields a data_to_process
            data_to_process.update(all_fields_data)
        else:
            data_to_process = data
        
        # Convertir cada campo del formulario en un tag individual
        for key, value in data_to_process.items():
            if key not in ["email", "name", "phone", "service_type"] and value:
                # Buscar etiqueta legible
                label = None
                for field_key, field_label in field_labels.items():
                    if field_key in key.lower():
                        label = field_label
                        break
                
                # Si no hay etiqueta, usar el key original limpio
                if not label:
                    label = key.replace("_", " ").replace("-", " ").replace("dmform", "Campo").title()
                
                # Crear tag en formato "Label: Valor"
                tag_text = f"{label}: {value}"
                # Limitar longitud del tag (GoHighLevel tiene límites)
                if len(tag_text) > 50:
                    tag_text = tag_text[:47] + "..."
                tags.append(tag_text)
        
        ghl_payload["tags"] = tags
        
        # También guardar service_type como custom field para referencia
        custom_fields = [{
            "key": "service_type",
            "field_value": service_type
        }]
        
        ghl_payload["customFields"] = custom_fields
        
        logger.info(f"📤 Enviando a GoHighLevel: {ghl_payload}")
        
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
        logger.info(f"📊 GHL Response: {response.text}")
        
        # Si es duplicado (400), crear Oportunidad en su lugar
        if response.status_code == 400 and "duplicate" in response.text.lower():
            logger.warning("⚠️ Contacto duplicado detectado - Creando Oportunidad")
            
            # Extraer el ID del contacto duplicado de la respuesta
            try:
                import json
                error_data = json.loads(response.text)
                contact_id = error_data.get("meta", {}).get("contactId")
                
                if contact_id:
                    logger.info(f"✅ Contacto ya existe en GHL: {contact_id}")
                    
                    # CREAR OPORTUNIDAD para el contacto existente
                    opportunity_result = create_ghl_opportunity(contact_id, data)
                    
                    if opportunity_result:
                        logger.info(f"✅ Oportunidad creada para contacto existente")
                        return {
                            "contact": {
                                "id": contact_id
                            },
                            "opportunity": opportunity_result,
                            "status": "duplicate_opportunity_created",
                            "message": "Contact already exists, new opportunity created"
                        }
                    else:
                        logger.warning("⚠️ No se pudo crear oportunidad, pero formulario registrado")
                        return {
                            "contact": {
                                "id": contact_id
                            },
                            "status": "duplicate_ignored",
                            "message": "Contact already exists, form submission recorded"
                        }
                else:
                    logger.warning("⚠️ No se pudo extraer contactId")
                    return {
                        "status": "duplicate_ignored",
                        "message": "Duplicate contact, form submission recorded"
                    }
            except Exception as e:
                logger.warning(f"⚠️ Error procesando duplicado: {str(e)}")
                return {
                    "status": "duplicate_ignored",
                    "message": "Duplicate contact, form submission recorded"
                }
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"✅ Contacto creado: {result.get('contact', {}).get('id', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error creando contacto: {str(e)}")
        raise

@app.post("/webhook/submit")
async def webhook_submit(request: Request):
    """
    Endpoint que acepta CUALQUIER dato en formato JSON
    """
    try:
        # Obtener datos raw
        data = await request.json()
        
        logger.info(f"📥 Datos recibidos: {data}")
        
        # Si no hay datos, rechazar
        if not data:
            logger.error("❌ No se recibieron datos")
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "No data received"}
            )
        
        # Crear contacto en GoHighLevel (o Oportunidad si es duplicado)
        result = create_ghl_contact(data)
        
        logger.info("✅ Formulario procesado exitosamente")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Contact created successfully",
                "ghl_response": result
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error procesando formulario: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "Jet Cargo → GoHighLevel Integration",
        "version": "3.0-with-opportunities"
    }

@app.get("/jetcargo_integration.js")
async def serve_integration_script():
    """Sirve el script de integración"""
    script_path = os.path.join(os.path.dirname(__file__), "jetcargo_integration.js")
    return FileResponse(
        script_path,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
