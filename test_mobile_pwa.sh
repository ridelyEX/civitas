# Script de Pruebas para DesUr Mobile PWA
# Ejecutar desde la raíz del proyecto

echo "🚀 Iniciando pruebas de DesUr Mobile PWA..."

# 1. Verificar archivos críticos
echo "📁 Verificando archivos PWA..."
if [ -f "portaldu/desUr/static/sw.js" ]; then
    echo "✅ Service Worker encontrado"
else
    echo "❌ Service Worker faltante"
fi

if [ -f "portaldu/desUr/static/sripts/mobile-offline.js" ]; then
    echo "✅ Script offline encontrado"
else
    echo "❌ Script offline faltante"
fi

# 2. Verificar configuración Django
echo "⚙️ Verificando configuración Django..."
python manage.py check --deploy

# 3. Probar rutas PWA
echo "🌐 Iniciando servidor de desarrollo..."
python manage.py runserver 127.0.0.1:8000 &
SERVER_PID=$!

sleep 5

# Verificar rutas PWA
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/desur/sw.js
if [ $? -eq 0 ]; then
    echo "✅ Service Worker accesible"
else
    echo "❌ Error accediendo Service Worker"
fi

curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/desur/manifest.json
if [ $? -eq 0 ]; then
    echo "✅ Manifest accesible"
else
    echo "❌ Error accediendo Manifest"
fi

# Detener servidor
kill $SERVER_PID

echo "✅ Pruebas básicas completadas"
echo ""
echo "📱 INSTRUCCIONES DE PRUEBA MANUAL:"
echo ""
echo "1. INSTALACIÓN EN MÓVIL:"
echo "   - Abre Chrome/Safari en tu móvil"
echo "   - Ve a http://[tu-ip]:8000/desur/"
echo "   - Busca el prompt 'Agregar a pantalla de inicio'"
echo "   - Instala la aplicación"
echo ""
echo "2. PRUEBAS OFFLINE:"
echo "   - Con la app instalada, activa modo avión"
echo "   - Abre la app desde la pantalla de inicio"
echo "   - Navega por las páginas (deben cargar)"
echo "   - Llena formularios (se guardan offline)"
echo "   - Reactiva conexión (se sincroniza automáticamente)"
echo ""
echo "3. FUNCIONALIDADES A VERIFICAR:"
echo "   ✓ Navegación sin conexión"
echo "   ✓ Formularios offline"
echo "   ✓ Indicador de estado de conexión"
echo "   ✓ Sincronización automática"
echo "   ✓ Notificaciones de estado"
echo "   ✓ Botón de sincronización manual"
echo ""
echo "4. HERRAMIENTAS DE DESARROLLO:"
echo "   - Chrome DevTools > Application > Service Workers"
echo "   - Chrome DevTools > Application > Storage"
echo "   - Chrome DevTools > Network > Throttling (para simular offline)"
echo ""
echo "🎯 CRITERIOS DE ÉXITO:"
echo "   ✅ App funciona completamente sin conexión"
echo "   ✅ Formularios se guardan offline"
echo "   ✅ Sincronización automática al reconectar"
echo "   ✅ UI responsive y nativa"
echo "   ✅ Instalable como PWA"
