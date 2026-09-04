[中文](README_zh.md) | [English](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [Русский](README_ru.md) | [Español](README_es.md) | [Français](README_fr.md) | [Deutsch](README_de.md) | [Português](README_pt.md)

# Instrucciones de uso de Entrada por Voz

## 1. Introducción del software

Este es un método de entrada por voz para la plataforma Windows que se conecta a una API ASR (reconocimiento de voz) de terceros. Pulse la tecla de acceso rápido para iniciar la grabación; al pulsarla de nuevo, se detiene la grabación y el texto reconocido se introduce automáticamente en la posición actual del cursor.

## 2. Funciones principales

- Voz a texto: la grabación se activa mediante una tecla de acceso rápido global y el resultado del reconocimiento se pega automáticamente en la posición del cursor
- Compatibilidad con múltiples proveedores: admite tres servicios ASR: formato compatible con OpenAI, Doubao Large Model y Volcengine
- Ventana flotante: muestra el estado en tiempo real durante la grabación (con un borde fino del color del tema); el resultado se copia automáticamente al portapapeles y se pega
- Historial: guarda automáticamente cada resultado del reconocimiento y admite formato con sangría de párrafo
- Interfaz multilingüe: incluye 35 idiomas de interfaz y selecciona automáticamente la fuente más adecuada
- Cambio de tema: admite temas claro y oscuro; los colores de todos los controles se actualizan de forma unificada
- Ajuste del tamaño de fuente: ajusta el nivel del tamaño de fuente con las flechas arriba/abajo (8 ~ 15, predeterminado 10); solo afecta a la fuente, no a los controles
- Personalización de la tecla de acceso rápido: pulse el botón "Modificar" y, en la ventana emergente, pulse la combinación de teclas para capturarla; admite combinaciones de 1 a 3 teclas
- Reemplazo por palabras activas: las palabras raras se escriben en la tabla de palabras activas y se reemplazan forzadamente mediante coincidencia fonética difusa
- Reemplazo por reglas regex: reemplaza con precisión el texto especificado mediante ecuaciones o reglas regex
- Conversión numérica ITN: convierte automáticamente "十五六个" en "15~16个"; admite rangos, fechas, porcentajes, fracciones, etc.; incluye palabras protegidas para evitar conversiones erróneas como "一会儿" o "一样"
- Eliminación de muletillas: elimina automáticamente muletillas orales como "呃", "啊", "嗯" (sin depender de LLM, procesamiento local puro)
- Procesamiento de roles LLM: cuando el resultado del reconocimiento comienza con el nombre de un rol, lo procesa el rol correspondiente del modelo de lenguaje grande (pulido, traducción, asistente, etc.); los archivos de roles se analizan de forma segura con AST y solo se permiten asignaciones literales
- Comandos de voz: diga comandos como "deshacer", "nueva línea", "retroceso" para ejecutar automáticamente la operación correspondiente
- Archivo de diario: guarda cada entrada de voz y su resultado de reconocimiento por fecha
- Inicio automático: opcional, inicia automáticamente al encender
- Bandeja del sistema: se minimiza a la bandeja; clic izquierdo abre la ventana principal, clic derecho sale

## 3. Inicio rápido

1. Tras iniciar el programa, se minimiza por defecto en la bandeja del sistema
2. Haga clic izquierdo en el icono de la bandeja para abrir la ventana principal
3. Antes del primer uso, vaya a la página "Configuración de IA" y rellene el proveedor ASR y la clave API
4. En cualquier ventana donde pueda introducir texto, coloque el cursor en la posición deseada
5. Pulse `Ctrl+Alt` para iniciar la grabación (el icono de la bandeja se pone rojo y aparece la ventana flotante)
6. Hable al micrófono
7. Pulse `Ctrl+Alt` de nuevo para detener la grabación
8. El resultado del reconocimiento se pega automáticamente en la posición del cursor

> Sugerencia: si pulsa la tecla de acceso rápido para grabar sin haber configurado la API, la ventana flotante mostrará "IA no configurada"; complete primero la configuración.

## 4. Descripción de la interfaz

La barra de navegación del lado izquierdo de la ventana principal contiene las siguientes páginas:

- Inicio: muestra el estado de grabación y el último resultado del reconocimiento, con botón de copiar
- Registro: muestra en tiempo real el registro de ejecución del programa, incluida la información de cada fase de grabación, reconocimiento y posprocesamiento
- Historial: explora los registros de reconocimiento anteriores; admite copia y visualización con sangría de párrafo
- Configuración de IA: rellene el proveedor ASR, la dirección y la clave de la API, el nombre del modelo, etc.; incluye los interruptores "Activar pulido de texto" y "Activar roles LLM"
- Caja de herramientas: centraliza los interruptores de las funciones de posprocesamiento de texto (eliminar puntuación final, ITN, eliminar muletillas, palabras activas, reglas regex, archivo de diario)
- Ajustes: configuración general, incluida la tecla de acceso rápido, el tema, el tamaño de fuente, el idioma de la interfaz, el inicio automático, la ventana flotante, etc.

## 5. Detalle de las opciones de configuración

### Relacionado con ASR (página Configuración de IA)

| Opción | Función |
| --- | --- |
| Proveedor ASR | Selecciona el servicio de reconocimiento de voz: openai_compatible (compatible con OpenAI), doubao (Doubao), volcengine (Volcengine) |
| base_url | Dirección base de la API compatible con OpenAI |
| api_key | Clave de la API compatible con OpenAI |
| model | Nombre del modelo, p. ej. whisper-1 |
| app_key | Clave de aplicación de Doubao / Volcengine |
| access_key | Clave de acceso de Doubao / Volcengine |
| resource_id | ID de recurso de Doubao |
| cluster | Nombre del clúster de Volcengine |
| asr_mode | Modo de reconocimiento ASR |
| Activar pulido de texto | Interruptor principal; al desactivarse, no se llama al LLM |
| Activar roles LLM | Solo seleccionable cuando el pulido de texto está activado; se muestra atenuado cuando está desactivado |

### Configuración general (página Ajustes)

| Opción | Función |
| --- | --- |
| Tecla de acceso rápido | Tecla de acceso rápido global que activa la grabación; predeterminada Ctrl+Alt; pulse "Modificar" para capturar una nueva combinación en la ventana emergente |
| Tema | Claro (light) u oscuro (dark); predeterminado: oscuro |
| Tamaño de fuente | Nivel del tamaño de fuente 8 ~ 15, predeterminado 10; ajuste con las flechas arriba/abajo; solo afecta a la fuente, no a los controles; surte efecto tras reiniciar |
| Idioma de la interfaz | Cambia el idioma de la interfaz; 35 idiomas disponibles |
| Inicio automático | Al activarse, el programa se inicia automáticamente al encender |
| Ventana flotante | Al activarse, muestra la ventana flotante durante la grabación (con un borde fino del color del tema); al desactivarse, el resultado solo se muestra en el cuadro de texto de la ventana principal |

### Interruptores de posprocesamiento de texto (página Caja de herramientas)

| Opción | Función | Predeterminado |
| --- | --- | --- |
| Eliminar coma y punto finales | Elimina automáticamente las comas y los puntos al final del resultado del reconocimiento | Activado |
| Conversión numérica ITN | Convierte "十五六个" en "15~16个" y otros formatos numéricos; incluye palabras protegidas para evitar conversiones erróneas como "一会儿" o "一样" | Activado |
| Eliminación de muletillas | Elimina automáticamente muletillas orales como "呃", "啊", "嗯" (procesamiento local puro, sin depender de LLM) | Activado |
| Reemplazo por palabras activas | Reemplaza forzadamente palabras raras mediante coincidencia fonética difusa | Activado |
| Umbral de coincidencia de palabras activas | Umbral de similitud de palabras activas, 0.0~1.0; cuanto mayor, más estricto | 0.85 |
| Reemplazo por reglas regex | Reemplaza con precisión el texto mediante ecuaciones o reglas regex | Activado |
| Archivo de diario | Guarda por fecha cada entrada de voz y su resultado de reconocimiento | Activado |

> Los interruptores relacionados con LLM (Activar pulido de texto, Activar roles LLM) se encuentran en la página "Configuración de IA", no en la Caja de herramientas.

### Parámetros de audio

| Opción | Función | Predeterminado |
| --- | --- | --- |
| sample_rate | Frecuencia de muestreo de audio (Hz) | 16000 |
| chunk_size | Tamaño del bloque de audio (bytes) | 3200 |

## 6. Idiomas de interfaz admitidos

El software incluye los siguientes 35 idiomas de interfaz. Cada idioma selecciona automáticamente la fuente más adecuada (chino: Microsoft YaHei; japonés: Yu Gothic; coreano: Malgun Gothic; otros idiomas: Segoe UI):

1. Chino simplificado (zh_CN)
2. Chino tradicional (zh_TW)
3. Inglés (en)
4. Español (es)
5. Árabe (ar)
6. Hindi (hi)
7. Indonesio (id)
8. Japonés (ja)
9. Francés (fr)
10. Alemán (de)
11. Ruso (ru)
12. Portugués (pt)
13. Italiano (it)
14. Turco (tr)
15. Polaco (pl)
16. Neerlandés (nl)
17. Coreano (ko)
18. Vietnamita (vi)
19. Bengalí (bn)
20. Urdu (ur)
21. Filipino (fil)
22. Malayo (ms)
23. Tailandés (th)
24. Checo (cs)
25. Húngaro (hu)
26. Sueco (sv)
27. Finés (fi)
28. Rumano (ro)
29. Ucraniano (uk)
30. Griego (el)
31. Danés (da)
32. Noruego (no)
33. Hebreo (he)
34. Búlgaro (bg)
35. Croata (hr)

En el primer inicio, el idioma de la interfaz se selecciona automáticamente según el idioma del sistema; posteriormente puede cambiarse manualmente en la página "Ajustes".

## 7. Preguntas frecuentes

### 1. ¿La tecla de acceso rápido no responde?

- Confirme que el programa se está ejecutando en la bandeja del sistema (el icono gris indica que está listo)
- Confirme que la tecla de acceso rápido no esté ocupada por otro software
- Vaya a la página "Ajustes", pulse el botón "Modificar" junto a la tecla de acceso rápido y vuelva a pulsar la combinación en la ventana emergente
- Compruebe si la página de registro muestra mensajes de error

### 2. ¿Qué hacer si falla el reconocimiento?

- Compruebe si la clave API, la dirección y el modelo rellenados en la página "Configuración de IA" son correctos
- Compruebe que la conexión de red sea correcta
- Abra la página "Registro" para ver el mensaje de error específico
- Confirme que el micrófono funcione correctamente y que el volumen de voz sea suficiente

### 3. ¿Cómo se ajusta el tamaño de fuente?

Vaya a la página "Ajustes", busque la opción "Tamaño de fuente" y ajuste el nivel con las flechas arriba/abajo de la derecha (8 ~ 15, predeterminado 10). Cuanto mayor sea el valor, mayor será la fuente. Esta opción solo afecta a la fuente y no cambia el tamaño de los controles como los botones; tras ajustarla debe reiniciar el programa para que surta efecto.

### 4. ¿Cómo se personaliza la tecla de acceso rápido?

Vaya a la página "Ajustes", busque la opción "Tecla de acceso rápido", pulse el botón "Modificar" de la derecha y, en la ventana independiente emergente, pulse la combinación de teclas deseada (admite de 1 a 3 teclas, p. ej. Ctrl+Shift+V). Tras la captura, pulse "Confirmar" para guardar; la nueva tecla de acceso rápido surte efecto tras reiniciar el programa.

### 5. ¿El resultado del reconocimiento no se pega automáticamente?

- Confirme que la ventana de destino admita la operación de pegar
- Confirme que el cursor esté colocado en una zona donde se pueda introducir texto
- Si la ventana flotante está desactivada, el resultado del reconocimiento solo se muestra en el cuadro de texto de la ventana principal y debe pulsar manualmente el botón de copiar

### 6. ¿Cómo añadir palabras raras para mejorar la precisión del reconocimiento?

Edite directamente el archivo `config/hot.txt`, una palabra activa por línea. Asimismo, en `config/hot-rule.txt` puede realizar reemplazos precisos mediante ecuaciones o reglas regex.

### 7. ¿Cómo se usan los roles LLM?

Cree archivos `.py` en el directorio `config/roles/` y, dentro del archivo, defina los atributos del rol mediante asignaciones de variables (name, trigger_words, system_prompt, output_mode, etc.). Los archivos de roles se analizan de forma segura con AST y solo se permiten asignaciones literales; no se permiten llamadas a funciones ni código arbitrario. Cuando el resultado del reconocimiento comienza con el nombre de un rol, se activa automáticamente el rol correspondiente.
