# Adaptación al español y al registro académico

Las listas originales están en inglés. Estas son las equivalencias en español y las reglas
que cambian cuando el texto es un proyecto de tesis o un artículo.

## Reglas originales que se relajan en texto académico

| Regla original | En texto académico |
|---|---|
| Sin voz pasiva | Se admite «se calculará», «se excluirán» en metodología (el agente es la investigadora y ya consta en la portada). Evitar pasiva cuando oculta quién decide algo. |
| Sin adverbios | Se conservan los que cumplen función técnica: «significativamente» sólo si hay prueba con valor p; «estrictamente» en criterios de inclusión. Se cortan los de énfasis. |
| «Tú» al lector | No aplica. Se escribe en tercera persona o futuro impersonal, como pide el formato. |
| Sin comas largas / rayas | Evitar la raya (—) como muletilla; se admite en incisos breves. |
| Sin números redondos vagos | Toda cifra lleva fuente; no se inventa ninguna para sonar concreto. |

## Muletillas de IA en español (cortar o reescribir)

**Aperturas de relleno:** «Cabe destacar que», «Es importante señalar que», «Vale la pena mencionar»,
«En el contexto actual», «En la actualidad», «En un mundo donde», «No es un secreto que»,
«Sin lugar a dudas», «Hoy más que nunca».

**Cierres grandilocuentes:** «En definitiva», «En conclusión, es evidente que», «Solo así se podrá…»,
«un paso fundamental hacia», «sentar las bases de un futuro».

**Vocabulario inflado:** «crucial», «fundamental», «clave» (como adjetivo de relleno), «multifacético»,
«panorama», «tejido social», «entramado», «sinergia», «abordaje integral», «paradigma»,
«desafíos y oportunidades», «a lo largo y ancho», «pilar».

**Estructuras:** contraste binario («no solo X sino también Y», «no es X, es Y»); tríadas
automáticas («A, B y C») cuando sólo hay dos cosas; frase corta y dramática para cerrar párrafo;
párrafos que arrancan todos con conector («Asimismo», «Además», «Por otro lado», «Finalmente»);
pregunta retórica seguida de su respuesta; «Esto no es solo… es…».

**Personificación de lo inanimado:** «los datos hablan», «la pandemia dejó al descubierto»,
«las cifras revelan», «el sistema falló» sin decir quién o dónde. Nombrar el sujeto real.

**Afirmaciones vagas:** «la situación es grave», «las implicaciones son significativas»,
«existen múltiples factores». Nombrar el factor, el número o la fuente.

## Lo que no se toca al limpiar

Términos técnicos, citas numeradas, definiciones operacionales, cifras y su fuente, y el orden de
las secciones que exige el formato de la universidad. Limpiar estilo no cambia contenido.

## Símbolos y formato que delatan una redacción de IA (añadido 2026-10-02)

Medido sobre una tesis real: la autora los marcó como «claramente IA» y los quitó a mano. Cortar
todos, en cualquier texto de tesis, informe o artículo.

| Qué aparece | Por qué delata | Qué escribir |
|---|---|---|
| `§4.9a`, `§5.5a`, «en la §3» | Notación de manual jurídico/técnico; ningún formato universitario la pide | «sección 4.9a», «el apartado 4.9a», o nombrar el contenido («en el análisis con ENDES») |
| Expresiones regulares o código en la prosa: `^O[0-7]`, `^O9[89]`, `TB_X.csv` | Filtración del código al texto | El rango en lenguaje de investigación: «códigos O00–O79» |
| Nombres de archivo, rutas y comandos: `.csv`, `.py`, `.png`, `outputs/`, `workflows/`, `make reproducir` | El documento es publicable; los archivos son del repositorio | Describir el dato («la base consolidada de defunciones»); la ruta y los comandos van una sola vez, en la declaración de disponibilidad del código |
| Identificadores del tablero interno (`INC-006`), «prueba golden verde», «limitación registrada internamente» | Jerga del flujo de trabajo, ilegible para el jurado | Decir la limitación en palabras: «5 registros no se unieron a la grilla del INEI» |
| Negrita decorativa: nombres de autor al inicio de párrafo, títulos incrustados («**Macrorregión:**»), énfasis a mitad de frase, números destacados | Parece resaltador de chat | Negrita solo en rótulos formales del formato (Palabras clave, OE1, HE1, términos del glosario, títulos de figura). Nunca a mitad de oración |
| Marcas markdown o LaTeX filtradas: `**`, `` ` ``, `$$`, `\frac` | Salen literales al pasar a Word | Texto plano o ecuación real de Word |
| Flechas `→` en la prosa o en hipótesis | Taquigrafía de notas | Redactar la relación: «a mayor X, mayor Y» |
| Párrafos o títulos unidos sin espacio: «Nota:Texto», «(Top 10).Gráfico» | Resto de fusionar bloques | Revisar el espacio tras `:` y `.` al unir párrafos |

Regla general: **si un lector humano de la universidad no escribiría ese símbolo a mano en Word,
sobra.** Tras limpiar, buscar con grep `§`, `\^O`, `\.csv`, `\.py`, `INC-`, `\*\*` antes de entregar.
