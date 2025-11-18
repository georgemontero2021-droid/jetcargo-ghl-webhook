// ============================================
// JET CARGO → GOHIGHLEVEL INTEGRATION V2.0
// Versión mejorada con validación y feedback
// ============================================

// Configuración del webhook
const WEBHOOK_URL = 'https://jetcargo-ghl-webhook-production.up.railway.app/webhook/submit';

// Estado global para prevenir doble envío
const formSubmissionState = new Map();

// ============================================
// FUNCIONES DE VALIDACIÓN
// ============================================

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePhone(phone) {
    // Remover caracteres no numéricos
    const cleanPhone = phone.replace(/\D/g, '');
    // Validar que tenga al menos 10 dígitos
    return cleanPhone.length >= 10;
}

function validateName(name) {
    return name && name.trim().length >= 2;
}

function validateFormData(data) {
    const errors = [];
    
    // Validar nombre
    if (!validateName(data.name)) {
        errors.push('Por favor ingresa un nombre válido (mínimo 2 caracteres)');
    }
    
    // Validar email
    if (!data.email) {
        errors.push('El email es requerido');
    } else if (!validateEmail(data.email)) {
        errors.push('Por favor ingresa un email válido');
    }
    
    // Validar teléfono
    if (!data.phone) {
        errors.push('El teléfono es requerido');
    } else if (!validatePhone(data.phone)) {
        errors.push('Por favor ingresa un teléfono válido (mínimo 10 dígitos)');
    }
    
    return errors;
}

// ============================================
// FUNCIONES DE FEEDBACK VISUAL
// ============================================

function createNotification(message, type = 'success') {
    // Remover notificaciones existentes
    const existingNotifications = document.querySelectorAll('.jetcargo-notification');
    existingNotifications.forEach(notif => notif.remove());
    
    // Crear nueva notificación
    const notification = document.createElement('div');
    notification.className = `jetcargo-notification jetcargo-notification-${type}`;
    notification.innerHTML = `
        <div class="jetcargo-notification-content">
            <span class="jetcargo-notification-icon">${type === 'success' ? '✓' : '⚠'}</span>
            <span class="jetcargo-notification-message">${message}</span>
            <button class="jetcargo-notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Agregar estilos inline
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#f59e0b'};
        color: white;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        animation: slideInRight 0.3s ease-out;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    
    const content = notification.querySelector('.jetcargo-notification-content');
    content.style.cssText = `
        display: flex;
        align-items: center;
        gap: 12px;
    `;
    
    const icon = notification.querySelector('.jetcargo-notification-icon');
    icon.style.cssText = `
        font-size: 20px;
        font-weight: bold;
    `;
    
    const messageEl = notification.querySelector('.jetcargo-notification-message');
    messageEl.style.cssText = `
        flex: 1;
        font-size: 14px;
        line-height: 1.5;
    `;
    
    const closeBtn = notification.querySelector('.jetcargo-notification-close');
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 24px;
        cursor: pointer;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.8;
        transition: opacity 0.2s;
    `;
    closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
    closeBtn.onmouseout = () => closeBtn.style.opacity = '0.8';
    
    // Agregar animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease-out reverse';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function showSuccessMessage(message) {
    createNotification(message, 'success');
}

function showErrorMessage(message) {
    createNotification(message, 'error');
}

function showWarningMessage(message) {
    createNotification(message, 'warning');
}

function showLoadingIndicator(form) {
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.dataset.originalText = submitButton.textContent || submitButton.value;
        
        if (submitButton.tagName === 'BUTTON') {
            submitButton.textContent = 'Enviando...';
        } else {
            submitButton.value = 'Enviando...';
        }
    }
}

function hideLoadingIndicator(form) {
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitButton && submitButton.dataset.originalText) {
        submitButton.disabled = false;
        
        if (submitButton.tagName === 'BUTTON') {
            submitButton.textContent = submitButton.dataset.originalText;
        } else {
            submitButton.value = submitButton.dataset.originalText;
        }
        
        delete submitButton.dataset.originalText;
    }
}

// ============================================
// DETECCIÓN DE TIPO DE SERVICIO
// ============================================

function detectServiceType() {
    const url = window.location.href.toLowerCase();
    const pageContent = document.body.textContent.toLowerCase();
    
    if (url.includes('express-air') || pageContent.includes('express air freight')) return 'express_air_freight';
    if (url.includes('deferred-air') || pageContent.includes('deferred air freight')) return 'deferred_air_freight';
    if (url.includes('lcl-ocean') || pageContent.includes('lcl ocean')) return 'lcl_ocean_freight';
    if (url.includes('fcl-ocean') || pageContent.includes('fcl ocean')) return 'fcl_ocean_freight';
    if (url.includes('car-auction') || pageContent.includes('car auction')) return 'car_auction_transport';
    if (url.includes('procurement') || pageContent.includes('procurement')) return 'procurement_sourcing';
    if (url.includes('customs') || pageContent.includes('customs clearance')) return 'customs_clearance';
    if (url.includes('insurance') || pageContent.includes('cargo insurance')) return 'cargo_insurance';
    if (url.includes('warehousing') || pageContent.includes('warehousing')) return 'warehousing';
    
    return 'general_contact';
}

// ============================================
// EXTRACCIÓN Y NORMALIZACIÓN DE DATOS
// ============================================

function extractFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        if (value && value.trim()) {
            data[key] = value.trim();
        }
    }
    
    return data;
}

function normalizeFormData(rawData) {
    const normalized = { ...rawData };
    
    // Detectar y normalizar campos comunes
    for (let [key, value] of Object.entries(rawData)) {
        const lowerKey = key.toLowerCase();
        const lowerValue = value.toLowerCase();
        
        // Email
        if (lowerKey.includes('email') || lowerKey.includes('correo') || 
            (typeof value === 'string' && value.includes('@'))) {
            normalized.email = value;
        }
        
        // Teléfono
        if (lowerKey.includes('phone') || lowerKey.includes('tel') || 
            lowerKey.includes('celular') || lowerKey.includes('movil')) {
            normalized.phone = value.replace(/\D/g, '');
        }
        
        // Nombre
        if (lowerKey.includes('name') || lowerKey.includes('nombre') || 
            lowerKey === 'deform-0') {
            normalized.name = value;
        }
        
        // Compañía
        if (lowerKey.includes('company') || lowerKey.includes('empresa') || 
            lowerKey.includes('compania')) {
            normalized.company = value;
        }
    }
    
    return normalized;
}

// ============================================
// ENVÍO AL WEBHOOK
// ============================================

async function sendToWebhook(formData, form) {
    const formId = form.id || form.name || 'form-' + Date.now();
    
    // Prevenir doble envío
    if (formSubmissionState.get(formId)) {
        console.log('⚠️ Formulario ya está siendo enviado, ignorando...');
        return;
    }
    
    formSubmissionState.set(formId, true);
    showLoadingIndicator(form);
    
    try {
        // Validar datos
        const errors = validateFormData(formData);
        if (errors.length > 0) {
            throw new Error(errors.join('\n'));
        }
        
        // Preparar payload
        const payload = {
            ...formData,
            service_type: detectServiceType(),
            page_url: window.location.href,
            page_title: document.title,
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent,
            referrer: document.referrer || 'direct'
        };
        
        console.log('📤 Enviando al webhook:', payload);
        
        // Enviar al webhook
        const response = await fetch(WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Error del servidor: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ Respuesta del webhook:', result);
        
        if (result.success) {
            showSuccessMessage('¡Gracias! Tu solicitud ha sido enviada exitosamente. Nos pondremos en contacto contigo pronto.');
        } else {
            throw new Error(result.message || 'Error al procesar la solicitud');
        }
        
    } catch (error) {
        console.error('❌ Error al enviar formulario:', error);
        showErrorMessage(error.message || 'Hubo un problema al enviar tu solicitud. Por favor intenta de nuevo o contáctanos directamente.');
    } finally {
        hideLoadingIndicator(form);
        formSubmissionState.delete(formId);
    }
}

// ============================================
// CAPTURA DE FORMULARIOS
// ============================================

function captureFormSubmit(form) {
    form.addEventListener('submit', async function(event) {
        // NO prevenir el comportamiento por defecto aquí
        // Dejar que el formulario se envíe normalmente también
        
        console.log('📋 Formulario enviado, capturando datos...');
        
        // Extraer y normalizar datos
        const rawData = extractFormData(form);
        const normalizedData = normalizeFormData(rawData);
        
        console.log('📊 Datos extraídos:', rawData);
        console.log('📊 Datos normalizados:', normalizedData);
        
        // Enviar al webhook de forma asíncrona (no bloquea el envío del formulario)
        sendToWebhook(normalizedData, form);
    });
}

// ============================================
// INICIALIZACIÓN
// ============================================

function initFormCapture() {
    console.log('🚀 Jet Cargo → GoHighLevel Integration V2.0 iniciada');
    
    // Buscar todos los formularios
    const forms = document.querySelectorAll('form');
    console.log(`📋 Formularios detectados: ${forms.length}`);
    
    if (forms.length === 0) {
        console.log('⚠️ No se encontraron formularios en esta página');
    }
    
    // Configurar captura para cada formulario
    forms.forEach((form, index) => {
        captureFormSubmit(form);
        console.log(`✅ Listener agregado a formulario #${index + 1}`);
    });
    
    console.log('✅ Integración lista');
}

// ============================================
// OBSERVADOR DE FORMULARIOS DINÁMICOS
// ============================================

function observeDynamicForms() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeName === 'FORM') {
                    captureFormSubmit(node);
                    console.log('✅ Nuevo formulario dinámico configurado');
                } else if (node.querySelectorAll) {
                    const forms = node.querySelectorAll('form');
                    forms.forEach(form => {
                        captureFormSubmit(form);
                        console.log('✅ Formulario dinámico configurado');
                    });
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('👁️ Observador de formularios dinámicos activado');
}

// ============================================
// INICIO AUTOMÁTICO
// ============================================

(function() {
    // Iniciar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initFormCapture();
            observeDynamicForms();
        });
    } else {
        initFormCapture();
        observeDynamicForms();
    }
})();
