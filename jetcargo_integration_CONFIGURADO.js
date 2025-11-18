/**
 * Jet Cargo → GoHighLevel Integration Script
 * 
 * Este script intercepta los envíos de formularios en www.jetcargo.us
 * y los envía automáticamente a GoHighLevel CRM vía webhook.
 * 
 * Autor: Manus AI
 * Fecha: 16 de noviembre de 2025
 * Versión: 1.0.0
 * 
 * INSTRUCCIONES PARA TU DESARROLLADOR:
 * 1. Reemplaza 'TU_URL_DEL_WEBHOOK_AQUI' con la URL real del servidor webhook desplegado
 * 2. Sube este archivo al servidor del sitio web
 * 3. Añade <script src="/ruta/a/este/archivo.js" defer></script> en todas las páginas
 */

(function() {
    'use strict';
    
    // ⚠️ IMPORTANTE: Reemplaza esta URL con la URL real de tu servidor webhook desplegado
    // Ejemplo: 'https://jetcargo-webhook.railway.app/webhook/submit'
    const WEBHOOK_URL = 'TU_URL_DEL_WEBHOOK_AQUI/webhook/submit';
    
    // Mapeo de servicios según el formulario
    const SERVICE_MAPPING = {
        'international_courier': 'international_courier',
        'express_air_freight': 'express_air_freight',
        'cargo_consolidation': 'cargo_consolidation',
        'global_ocean_freight': 'global_ocean_freight',
        'trucking_services': 'trucking_services',
        'car_auction': 'car_auction',
        'in_transit_cargo': 'in_transit_cargo',
        'smart_storage': 'smart_storage',
        'procurement_usa': 'procurement_usa',
        'procurement_china': 'procurement_china',
        'charter_flights': 'charter_flights',
        'car_shipment_container': 'car_shipment_container',
        'contact_form': 'contact_form'
    };
    
    /**
     * Detecta el tipo de servicio según el formulario
     * @param {HTMLFormElement} form - El formulario
     * @returns {string} - El tipo de servicio
     */
    function detectServiceType(form) {
        // Intentar detectar por ID del formulario
        if (form.id) {
            const formId = form.id.toLowerCase();
            for (const [key, value] of Object.entries(SERVICE_MAPPING)) {
                if (formId.includes(key)) {
                    return value;
                }
            }
        }
        
        // Intentar detectar por clase del formulario
        if (form.className) {
            const formClass = form.className.toLowerCase();
            for (const [key, value] of Object.entries(SERVICE_MAPPING)) {
                if (formClass.includes(key)) {
                    return value;
                }
            }
        }
        
        // Intentar detectar por el modal padre
        const modal = form.closest('[class*="modal"]');
        if (modal) {
            const modalText = modal.textContent.toLowerCase();
            if (modalText.includes('express air')) return 'express_air_freight';
            if (modalText.includes('international courier')) return 'international_courier';
            if (modalText.includes('consolidation')) return 'cargo_consolidation';
            if (modalText.includes('ocean freight')) return 'global_ocean_freight';
            if (modalText.includes('trucking')) return 'trucking_services';
            if (modalText.includes('car auction')) return 'car_auction';
            if (modalText.includes('in-transit') || modalText.includes('in transit')) return 'in_transit_cargo';
            if (modalText.includes('storage')) return 'smart_storage';
            if (modalText.includes('procurement') && modalText.includes('usa')) return 'procurement_usa';
            if (modalText.includes('procurement') && modalText.includes('china')) return 'procurement_china';
            if (modalText.includes('charter')) return 'charter_flights';
            if (modalText.includes('car shipment')) return 'car_shipment_container';
        }
        
        // Por defecto, formulario de contacto general
        return 'contact_form';
    }
    
    /**
     * Extrae datos del formulario
     * @param {HTMLFormElement} form - El formulario
     * @returns {Object} - Datos del formulario
     */
    function extractFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        // Mapeo de campos comunes
        const fieldMapping = {
            'name': ['name', 'nombre', 'full_name', 'fullname'],
            'email': ['email', 'correo', 'e-mail'],
            'phone': ['phone', 'telefono', 'tel', 'telephone'],
            'company_name': ['company', 'company_name', 'empresa', 'companyname'],
            'shipping_origin': ['origin', 'shipping_origin', 'pickup', 'pickup_address', 'origen'],
            'final_destination': ['destination', 'final_destination', 'delivery', 'delivery_address', 'destino'],
            'cargo_details': ['cargo', 'cargo_details', 'details', 'detalles'],
            'description_of_goods': ['description', 'goods', 'description_of_goods', 'descripcion'],
            'message': ['message', 'mensaje', 'comments', 'comentarios']
        };
        
        // Extraer campos
        for (const [key, possibleNames] of Object.entries(fieldMapping)) {
            for (const name of possibleNames) {
                const value = formData.get(name);
                if (value) {
                    data[key] = value;
                    break;
                }
            }
        }
        
        // Extraer manejo especial (checkboxes)
        const specialHandling = [];
        if (formData.get('fragile') || formData.get('Fragile')) {
            specialHandling.push('Fragile');
        }
        if (formData.get('refrigerated') || formData.get('Refrigerated')) {
            specialHandling.push('Refrigerated');
        }
        if (formData.get('hazardous') || formData.get('Hazardous')) {
            specialHandling.push('Hazardous');
        }
        
        if (specialHandling.length > 0) {
            data.special_handling = specialHandling;
        }
        
        return data;
    }
    
    /**
     * Envía datos al webhook
     * @param {Object} data - Datos a enviar
     * @returns {Promise} - Promesa de la petición
     */
    async function sendToWebhook(data) {
        try {
            const response = await fetch(WEBHOOK_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ Formulario enviado a GoHighLevel:', result);
            return result;
        } catch (error) {
            console.error('❌ Error al enviar formulario a GoHighLevel:', error);
            throw error;
        }
    }
    
    /**
     * Maneja el envío del formulario
     * @param {Event} event - Evento de submit
     */
    async function handleFormSubmit(event) {
        const form = event.target;
        
        // No prevenir el envío por defecto aún
        // Dejar que el formulario se envíe normalmente también
        
        try {
            // Detectar tipo de servicio
            const serviceType = detectServiceType(form);
            console.log('📋 Tipo de servicio detectado:', serviceType);
            
            // Extraer datos del formulario
            const formData = extractFormData(form);
            formData.service_type = serviceType;
            
            console.log('📤 Enviando datos a GoHighLevel:', formData);
            
            // Enviar a webhook (sin esperar para no bloquear el envío normal)
            sendToWebhook(formData)
                .then(result => {
                    console.log('✅ Datos enviados exitosamente a GoHighLevel');
                })
                .catch(error => {
                    console.error('❌ Error al enviar a GoHighLevel (el formulario se envió normalmente):', error);
                });
            
        } catch (error) {
            console.error('❌ Error en handleFormSubmit:', error);
            // No bloquear el envío normal del formulario
        }
    }
    
    /**
     * Inicializa la integración
     */
    function init() {
        console.log('🚀 Jet Cargo → GoHighLevel Integration iniciada');
        
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachFormListeners);
        } else {
            attachFormListeners();
        }
    }
    
    /**
     * Adjunta listeners a todos los formularios
     */
    function attachFormListeners() {
        // Buscar todos los formularios en la página
        const forms = document.querySelectorAll('form');
        
        console.log(`📝 ${forms.length} formulario(s) encontrado(s)`);
        
        forms.forEach((form, index) => {
            // Evitar duplicar listeners
            if (form.dataset.jetcargoIntegration === 'true') {
                return;
            }
            
            form.dataset.jetcargoIntegration = 'true';
            form.addEventListener('submit', handleFormSubmit);
            
            console.log(`✅ Listener agregado al formulario #${index + 1}`);
        });
        
        // Observer para formularios que se cargan dinámicamente (modales)
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        const newForms = node.querySelectorAll ? node.querySelectorAll('form') : [];
                        newForms.forEach((form) => {
                            if (form.dataset.jetcargoIntegration !== 'true') {
                                form.dataset.jetcargoIntegration = 'true';
                                form.addEventListener('submit', handleFormSubmit);
                                console.log('✅ Listener agregado a formulario dinámico');
                            }
                        });
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('👀 Observer de formularios dinámicos activado');
    }
    
    // Iniciar la integración
    init();
    
})();
