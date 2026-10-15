---
name: clean-architecture
description: Reglas de arquitectura en capas (Clean/Hexagonal) — la Regla de Dependencia, entidades vs casos de uso, puertos/adaptadores, SOLID y límites (boundaries). Cargar al diseñar la estructura de un proyecto nuevo, al decidir dónde va una clase/módulo, al revisar si la lógica de negocio se está filtrando hacia el framework/DB/HTTP, o al discutir si algo necesita una interfaz.
metadata:
  origen: "F:\\skills\\Programacion y matematicas\\clean-architecture-1.0.0 + principle-clean-architecture-1.0.0"
  extraido: 2026-09-05
---

# Arquitectura en capas (Clean / Hexagonal)

> Síntesis de dos skills de la librería local (Robert C. Martin, *Clean Architecture*,
> más la variante "principle-clean-architecture"). No se copian verbatim: son reglas
> operativas para aplicar en este workspace.

## La regla que manda sobre todas las demás

**Las dependencias del código fuente apuntan siempre hacia adentro.** Un círculo
interior no puede conocer nada de un círculo exterior (ni sus clases, ni sus
tipos de datos, ni su formato).

```
[ Frameworks & Drivers ]   ← HTTP, DB, UI, CLI, SDKs de terceros
  [ Interface Adapters ]   ← controllers, presenters, gateways/repos concretos
    [ Casos de uso ]       ← reglas de negocio de la aplicación
      [ Entidades ]        ← reglas de negocio de la empresa/dominio
```

Si un caso de uso importa el ORM, ya se rompió la regla — no importa cuán
pequeño sea el import.

## Reglas duras

1. **Los frameworks son un detalle, no la arquitectura.** La base de datos es un
   detalle. El transporte HTTP es un detalle. Ninguno debe dictar la estructura
   de carpetas ni forzar tipos en el dominio.
2. **Puerto vs adaptador.** El *puerto* es una interfaz que define el dominio/caso
   de uso (`UserRepository.find(id)`); el *adaptador* es la implementación externa
   (`PostgresUserRepository`). El dominio depende del puerto; el composition root
   (el `main()`/entrypoint) conecta el adaptador al puerto en el arranque.
3. **El dominio se mantiene puro.** Nada de imports de HTTP, SQL, tipos de ORM,
   librerías JSON, ni reloj de pared (`datetime.now()`) directamente en el
   dominio. Esas dependencias entran como interfaces (`Clock`, `IdGenerator`,
   `Repository`) inyectadas desde afuera.
4. **Los datos que cruzan un límite (boundary) usan la forma que le conviene al
   círculo interior**, nunca la del exterior. Un caso de uso nunca recibe ni
   devuelve un objeto de ORM o un `Request`/`Response` de HTTP — solo DTOs/tipos
   planos que el propio caso de uso define.
5. **Un caso de uso, una operación de aplicación.** `PlaceOrder`, `CancelOrder`,
   `RefundOrder` como unidades separadas — no un `OrderService` gigante que hace
   de todo.
6. **SOLID es el nivel medio que hace posible la Regla de Dependencia:**
   - **SRP**: un módulo tiene una sola razón para cambiar — sirve a un solo actor,
     no "hace una sola cosa" en sentido literal.
   - **OCP**: extender agregando código nuevo (strategy/plugin), no editando el
     existente.
   - **LSP**: un subtipo debe poder sustituir al tipo base sin que el cliente note
     diferencia — si una subclase lanza excepciones inesperadas o ignora
     métodos, está rota (ver ejemplo clásico `Square extends Rectangle`).
   - **ISP**: no forzar a un cliente a depender de métodos que no usa — partir
     interfaces gordas en interfaces de rol.
   - **DIP**: los módulos de alto nivel no dependen de los de bajo nivel; ambos
     dependen de una abstracción que define el módulo de alto nivel.

## Dónde va cada cosa (regla de import por capa)

| Capa | Puede importar | NO puede importar |
|---|---|---|
| Dominio/Entidades | librería estándar | Aplicación, Infraestructura, Framework |
| Aplicación (casos de uso) | Dominio | Infraestructura, Framework |
| Infraestructura (adapters/gateways) | Dominio, Aplicación | Framework (salvo su propio SDK) |
| Framework/UI (controllers, CLI, HTTP) | todas | — |

No hace falta multi-módulo: un directorio por capa alcanza
(`domain/`, `app/`/`usecase/`, `infra/`, `ui/`).

## Cómo decidir si algo necesita boundary/interfaz

Preguntar: **"si cambiáramos la base de datos / el framework web / el bus de
mensajes, ¿qué archivos cambian?"** — solo los adaptadores deberían cambiar. Si
la respuesta toca el dominio o los casos de uso, falta un límite.

Otra prueba rápida: si una dependencia **cruza una capa**, necesita interfaz —
sin negociación. Si no cruza capa, no hace falta.

## Cuándo NO aplicar esto

- Scripts desechables y prototipos: una estructura plana está bien.
- CRUD obvio sin lógica de negocio real: un solo archivo de servicio es más
  claro que cuatro capas.
- Herramientas internas pequeñas donde el costo de la ceremonia supera el costo
  del cambio.

Aplicar de forma proporcional: un directorio por capa no cuesta nada; forzar
puertos/adaptadores completos en un script de 50 líneas sí es sobre-ingeniería.

## Señales de que la arquitectura se está desviando (drift smells)

- Un repositorio devuelve objetos de ORM en vez de tipos de dominio.
- Un caso de uso importa tipos de request/response de HTTP.
- El presenter contiene reglas de negocio.
- Un paquete `utils` es importado desde el dominio.
- Una función de dominio recibe una conexión de base de datos como parámetro.
- Hay dependencias circulares entre componentes (romperlas con DIP o
  extrayendo un componente nuevo — ver ADP).

## Excusas comunes — y por qué no aplican

| Excusa | Realidad |
|---|---|
| "Todo en un paquete es más simple" | Más simple de escribir, más difícil de mantener: cuando cambia la lógica de DB, los tests de dominio se rompen — ese es el costo del acoplamiento. |
| "Separar en directorios es sobre-ingeniería" | Los directorios son gratis. La carga cognitiva de no saber dónde vive la lógica no lo es. |
| "El framework exige esta estructura" | Los frameworks solo restringen la capa más externa. Las capas internas no le deben nada al framework. |
| "Esto es solo un prototipo" | Si hay chance de que llegue a producción, aplicar la regla ahora — retroadaptar capas sobre código plano es el refactor más caro que existe. |

## Diagnóstico rápido antes de dar algo por bueno

- [ ] ¿Se pueden testear las reglas de negocio sin DB, sin servidor web, sin framework?
- [ ] ¿Todos los imports del dominio apuntan hacia adentro?
- [ ] ¿Se puede cambiar la base de datos sin tocar la lógica de negocio?
- [ ] ¿Los casos de uso son independientes del mecanismo de entrega (HTTP/CLI/cola)?
- [ ] ¿El framework está confinado al círculo más externo?
- [ ] ¿El composition root (`main`) es el único lugar que instancia clases concretas?
