/**
 * Jet Cargo → GoHighLevel Integration Script
 * Captura TODOS los campos del formulario y envía a GoHighLevel
 */

(function() {
    'use strict';
    
    const WEBHOOK_URL = 'https://jetcargo-ghl-integration-production.up.railway.app/webhook/submit';
    
    console.log('🚀 Jet Cargo Integration INICIADA');
    
    /**
     * Captura TODOS los datos del formulario
     */
    function getAllFormData(form) {
        const data = {};
        
        // Obtener TODOS los campos
        const fields = form.querySelectorAll('input, textarea, select');
        
        console.log(`📝 Encontrados ${fields.length} campos en el formulario`);
        
        fields.forEach((field, index) => {
            const value = field.value ? field.value.trim() : '';
            
            // Saltar campos vacíos, hidden, submit, button
            if (!value || 
                field.type === 'submit' || 
                field.type === 'button' ||
                field.type === 'hidden' ||
                field.type === 'file') {
                return;
            }
            
            // Obtener el nombre del campo
            const fieldName = field.name || field.id || field.placeholder || `field_${index}`;
            
            console.log(`Campo: ${fieldName} = ${value} (type: ${field.type})`);
            
            // Guardar el campo con su nombre original
            data[fieldName] = value;
            
            // Detectar EMAIL
            if (value.includes('@') && value.includes('.')) {
                data.email = value;
                console.log(`✅ Email detectado: ${value}`);
            }
            // Detectar TELÉFONO
            else if (/^\+?[\d\s\-\(\)]{7,}$/.test(value)) {
                data.phone = value;
                console.log(`✅ Teléfono detectado: ${value}`);
            }
            // Detectar NOMBRE - dmform-0 o primer campo de texto
            else if (!data.name) {
                if (fieldName === 'dmform-0' || fieldName === 'dmform-00' || field.type === 'text') {
                    data.name = value;
                    console.log(`✅ Nombre detectado (${fieldName}): ${value}`);
                }
            }
        });
        
        // Si no hay nombre, usar Unknown
        if (!data.name) {
            data.name = 'Unknown';
            console.log(`⚠️ No se encontró nombre, usando: Unknown`);
        }
        
        // Detectar tipo de servicio
        data.service_type = detectServiceType(form);
        
        console.log('📊 Datos finales a enviar:', data);
        
        return data;
    }
    
    /**
     * Detecta el tipo de servicio
     */
    function detectServiceType(form) {
        const modal = form.closest('[class*="modal"], [id*="modal"], .popup, [class*="popup"]');
        
        if (modal) {
            const text = modal.textContent.toLowerCase();
            
            // Orden específico para evitar conflictos
            if (text.includes('cargo consolidation') || text.includes('consolidation')) return 'cargo_consolidation';
            if (text.includes('express air freight') || text.includes('express air')) return 'express_air_freight';
            if (text.includes('ocean freight')) return 'global_ocean_freight';
            if (text.includes('trucking')) return 'trucking_services';
            if (text.includes('international courier')) return 'international_courier';
            if (text.includes('car auction')) return 'car_auction';
            if (text.includes('in-transit') || text.includes('in transit')) return 'in_transit_cargo';
            if (text.includes('storage')) return 'smart_storage';
            if (text.includes('procurement') && text.includes('usa')) return 'procurement_usa';
            if (text.includes('procurement') && text.includes('china')) return 'procurement_china';
            if (text.includes('charter')) return 'charter_flights';
            if (text.includes('car shipment')) return 'car_shipment_container';
        }
        
        return 'contact_form';
    }
    
    /**
     * Envía datos al webhook
     */
    async function sendToWebhook(data) {
        try {
            console.log('📤 Enviando a webhook:', data);
            
            const response = await fetch(WEBHOOK_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                console.error('❌ Error del servidor:', response.status, result);
                return;
            }
            
            console.log('✅ Enviado exitosamente:', result);
            
        } catch (error) {
            console.error('❌ Error al enviar:', error);
        }
    }
    
    /**
     * Maneja el envío del formulario
     */
    function handleFormSubmit(event) {
        const form = event.target;
        
        console.log('📋 Formulario enviado, capturando datos...');
        
        try {
            // Capturar TODOS los datos
            const data = getAllFormData(form);
            
            console.log('📊 Datos capturados:', data);
            
            // Enviar a webhook (en background, no bloquear)
            sendToWebhook(data).catch(err => {
                console.error('Error en background:', err);
            });
            
        } catch (error) {
            console.error('❌ Error procesando formulario:', error);
        }
        
        // NO prevenir el envío normal
    }
    
    /**
     * Agrega listeners a formularios
     */
    function attachListeners() {
        const forms = document.querySelectorAll('form');
        
        console.log(`📝 Encontrados ${forms.length} formularios`);
        
        forms.forEach((form, index) => {
            if (form.dataset.jetcargoListener) {
                return;
            }
            
            form.dataset.jetcargoListener = 'true';
            form.addEventListener('submit', handleFormSubmit);
            
            console.log(`✅ Listener agregado a formulario #${index + 1}`);
        });
    }
    
    /**
     * Observa formularios dinámicos
     */
    function observeForms() {
        const observer = new MutationObserver(() => {
            attachListeners();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('👁️ Observador activado');
    }
    
    /**
     * Inicialización
     */
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                attachListeners();
                observeForms();
            });
        } else {
            attachListeners();
            observeForms();
        }
        
        // Intentar cada 2 segundos
        setInterval(attachListeners, 2000);
    }
    
    init();
    
    console.log('✅ Integración lista');
    
})();
