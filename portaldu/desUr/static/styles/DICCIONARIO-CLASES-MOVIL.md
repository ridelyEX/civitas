# 📱 Diccionario de Clases y IDs - Versión Móvil

## 🎯 Layout Principal

### **Contenedor Principal**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `form .main` | Layout principal | Móvil (≤768px) | Flex column, margin 0.75rem, width calc(100% - 1.5rem) |
| `.left` | Sección izquierda | Móvil | Width 100%, margin-bottom 2rem, flex column |
| `.right` | Sección derecha | Móvil | Width 100%, margin-bottom 2rem, flex column |

### **Título**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.titulo` | Encabezado principal | Móvil | Width 100%, padding 1.25rem 1rem, border-radius 12px |
| `.titulo h1` | Texto del título | Móvil | Font-size 1.5rem, line-height 1.3, margin 0 |

## 📝 Elementos de Formulario

### **Contenedor de Campos**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.form` | Wrapper de campo | Móvil | Margin-bottom 1.25rem, width 100% |

### **Labels**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.form label.text` | Etiquetas de campos | Móvil | Font-size 1rem, font-weight 700, padding 0 8px |

### **Inputs de Texto**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.form input[type=text].input` | Campos de texto | Móvil | Height 3.75rem, font-size 1.1rem, border-radius 10px |
| `.form input[type=date].input` | Campos de fecha | Móvil | Height 3.75rem, font-size 1.1rem, border-radius 10px |
| `.form select.select` | Campos select | Móvil | Height 3.75rem, font-size 1.1rem, border-radius 10px |

### **Estados de Focus**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.form input:focus` | Estado activo inputs | Móvil | Border-color hover, box-shadow, transform scale(1.01) |
| `.form select:focus` | Estado activo selects | Móvil | Border-color hover, box-shadow, transform scale(1.01) |

### **Textareas**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.form textarea.tArea` | Textarea izquierda | Móvil | Height 170px, font-size 1.1rem, border-radius 10px |
| `.form textarea.tArea1` | Textarea derecha | Móvil | Height 170px, font-size 1.1rem, border-radius 10px |

## 🔲 Botones y Controles

### **Botones Principales**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.addbtn` | Botón agregar | Móvil | Min-height 3.75rem, font-size 1.1rem, border-radius 12px |
| `.next` | Botón siguiente | Móvil | Min-height 3.75rem, font-size 1.2rem, border-radius 12px |
| `.back` | Botón regresar | Móvil | Min-height 3.75rem, font-size 1.2rem, border-radius 12px |
| `.cancel` | Botón cancelar | Móvil | Min-height 3.75rem, font-size 1.2rem, border-radius 12px |

### **Estados Activos de Botones**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.addbtn:active` | Estado pressed agregar | Móvil | Transform scale(0.98) |
| `.next:active` | Estado pressed siguiente | Móvil | Transform scale(0.98) |
| `.back:active` | Estado pressed regresar | Móvil | Transform scale(0.98) |
| `.cancel:active` | Estado pressed cancelar | Móvil | Transform scale(0.98) |

### **Botones de Búsqueda**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.search.sbtn` | Botón buscar | Móvil | Height 3.75rem, font-size 1.1rem, border-radius 12px |

## 📐 Layouts y Grids

### **Grid Responsive**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.ngrid` | Grid principal | Móvil | Flex column, gap 2rem, margin-bottom 2.5rem |

### **Áreas de Botones ADD**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.left .plus` | Área botón izquierdo | Móvil | Width 100%, padding 1.25rem 0, border-radius 12px |
| `.right .plus` | Área botón derecho | Móvil | Width 100%, padding 1.25rem 0, border-radius 12px |

### **Layout de Navegación**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.bottom` | Contenedor botones navegación | Móvil | Flex column, gap 1.25rem, margin 2.5rem 0 1.5rem 0 |
| `.bottom .lBtn` | Contenedor botón izquierdo | Móvil | Width 100%, order 2 |
| `.bottom .rBtn` | Contenedor botón derecho | Móvil | Width 100%, order 1 |
| `.bottom .cBtn` | Contenedor botón centro | Móvil | Width 100%, order 3 |

## ☑️ Controles Específicos

### **Checkboxes**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.checkbox-wrapper-46` | Wrapper checkbox personalizado | Móvil | Margin 1.5rem 0, padding 1.25rem, border-radius 12px |

### **Selectores de Posición**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.nPuesto` | Selector de puesto | Móvil | Margin 1.5rem 0 |

### **Área de Fotos**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.nFoto` | Área de selección foto | Móvil | Margin 1.5rem 0 |

## 📱 Móviles Pequeños (≤480px)

### **Ajustes Específicos**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `form .main` | Layout compacto | ≤480px | Margin 0.5rem, width calc(100% - 1rem) |
| `.titulo` | Título compacto | ≤480px | Padding 1rem 0.75rem, border-radius 10px |
| `.titulo h1` | Texto compacto | ≤480px | Font-size 1.3rem |

### **Campos Compactos**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.form input[type=text].input` | Input compacto | ≤480px | Height 3.5rem, font-size 1rem, padding 12px 14px |
| `.form input[type=date].input` | Fecha compacta | ≤480px | Height 3.5rem, font-size 1rem, padding 12px 14px |
| `.form select.select` | Select compacto | ≤480px | Height 3.5rem, font-size 1rem, padding 12px 14px |
| `.form textarea.tArea` | Textarea compacta | ≤480px | Height 150px, font-size 1rem |
| `.form textarea.tArea1` | Textarea1 compacta | ≤480px | Height 150px, font-size 1rem |

### **Botones Compactos**
| Selector | Uso | Breakpoint | Descripción |
|----------|-----|------------|-------------|
| `.addbtn` | Agregar compacto | ≤480px | Min-height 3.5rem, font-size 1rem |
| `.next` | Siguiente compacto | ≤480px | Min-height 3.5rem, font-size 1.1rem |
| `.back` | Regresar compacto | ≤480px | Min-height 3.5rem, font-size 1.1rem |
| `.cancel` | Cancelar compacto | ≤480px | Min-height 3.5rem, font-size 1.1rem |
| `.search.sbtn` | Buscar compacto | ≤480px | Height 3.5rem, font-size 1rem |

## ♿ Accesibilidad

### **Tamaños Táctiles Mínimos**
| Selector | Uso | Descripción |
|----------|-----|-------------|
| `button` | Botones generales | Min-height 44px, min-width 44px |
| `.addbtn` | Botón agregar | Min-height 44px, min-width 44px |
| `.next` | Botón siguiente | Min-height 44px, min-width 44px |
| `.back` | Botón regresar | Min-height 44px, min-width 44px |
| `.cancel` | Botón cancelar | Min-height 44px, min-width 44px |
| `.search.sbtn` | Botón buscar | Min-height 44px, min-width 44px |

### **Estados de Focus Accesibles**
| Selector | Uso | Descripción |
|----------|-----|-------------|
| `.form input:focus` | Focus inputs | Outline 2px, outline-offset 2px, box-shadow 4px |
| `.form select:focus` | Focus selects | Outline 2px, outline-offset 2px, box-shadow 4px |
| `.form textarea:focus` | Focus textareas | Outline 2px, outline-offset 2px, box-shadow 4px |
| `button:focus` | Focus botones | Outline 2px, outline-offset 2px, box-shadow 4px |

### **Reducción de Movimiento**
| Media Query | Uso | Descripción |
|-------------|-----|-------------|
| `@media (prefers-reduced-motion: reduce)` | Accesibilidad | Animation-duration 0.01ms, transition-duration 0.01ms |

### **Prevención de Zoom iOS**
| Media Query | Uso | Descripción |
|-------------|-----|-------------|
| `@media screen and (max-width: 768px)` | iOS Safari | Font-size 16px !important en inputs |

## 🎨 Estados de Validación

### **Estados Invalid**
| Selector | Uso | Descripción |
|----------|-----|-------------|
| `.form input:invalid:not(:focus):not(:placeholder-shown)` | Input inválido | Border-color #e74c3c, box-shadow rojo |
| `.form select:invalid:not(:focus)` | Select inválido | Border-color #e74c3c, box-shadow rojo |
| `.form textarea:invalid:not(:focus):not(:placeholder-shown)` | Textarea inválido | Border-color #e74c3c, box-shadow rojo |

### **Estados Valid**
| Selector | Uso | Descripción |
|----------|-----|-------------|
| `.form input:valid:not(:placeholder-shown)` | Input válido | Border-color #27ae60 |
| `.form select:valid` | Select válido | Border-color #27ae60 |
| `.form textarea:valid:not(:placeholder-shown)` | Textarea válido | Border-color #27ae60 |

## 🖱️ Interacciones Hover (Solo Desktop)

### **Estados Hover**
| Selector | Media Query | Descripción |
|----------|-------------|-------------|
| `.form input:hover` | `@media (hover: hover) and (pointer: fine)` | Border-color hover, box-shadow sutil |
| `.form select:hover` | `@media (hover: hover) and (pointer: fine)` | Border-color hover, box-shadow sutil |
| `.form textarea:hover` | `@media (hover: hover) and (pointer: fine)` | Border-color hover, box-shadow sutil |
| `.addbtn:hover` | `@media (hover: hover) and (pointer: fine)` | Transform translateY(-1px), box-shadow |

## 🎯 Variables CSS Utilizadas

### **Colores**
| Variable | Valor | Uso |
|----------|-------|-----|
| `--primary-color` | #005194 | Bordes, textos principales |
| `--primary-hover` | #004dff | Estados hover/focus |
| `--primary-dark` | #00396e | Variaciones oscuras |
| `--secondary-color` | #286496 | Títulos, fondos secundarios |
| `--cancel-color` | #ca0000 | Botones de cancelar |
| `--gray-color` | #666d7e | Textos secundarios |

### **Radios**
| Variable | Valor | Uso |
|----------|-------|-----|
| `--border-radius` | 5px | Bordes estándar |
| `--border-radius-large` | 10px | Bordes grandes |

### **Sombras**
| Variable | Descripción | Uso |
|----------|-------------|-----|
| `--shadow-light` | Sombra sutil | Elementos elevados |
| `--shadow-hover` | Sombra hover | Estados interactivos |

---

*📱 Diccionario completo de clases y selectores CSS para implementación móvil optimizada*
