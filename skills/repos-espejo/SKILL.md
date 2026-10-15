---
name: repos-espejo
description: Mantiene y verifica los espejos `bare` de los repos de trabajo en F:\REPOSITORIOS\espejos\, que son el único respaldo local del historial de git. Úsala cuando haya que respaldar código, comprobar qué repos están sin respaldar o sin commitear, tras crear un repo nuevo, o antes de cualquier operación arriesgada sobre un repo (rebase, filter-branch, borrado de ramas). Prohíbe crear segundas copias de trabajo: un espejo bare no se puede editar y por eso no puede divergir.
---

# Espejos de repositorios

`F:\REPOSITORIOS\espejos\<nombre>.git` guarda el **historial** de cada repo de
trabajo. No es una segunda copia editable: eso es exactamente la avería que se
evita (ver `wiki/SISTEMA/Espejos de Repositorios en el Disco F.md`).

## Comandos

```bash
E=/mnt/f/skills/_personales/repos-espejo/scripts/espejar.py
python3 $E                      # simulacro: qué se crearía/actualizaría
python3 $E --aplicar            # crea o refresca todos los espejos
python3 $E --trabajo ~/otro --espejos /ruta --aplicar
```

Desde una copia de trabajo concreta:

```bash
git push local --all && git push local --tags
```

## Reglas

- **Nunca crear una copia de trabajo en F:.** Si hace falta el código en
  Windows, se clona *desde* el espejo a un sitio nuevo y se trata como
  desechable, o se trabaja en WSL. Dos árboles editables del mismo repo
  divergen; ya pasó con la skill `run-element` y con `sapyria-platform`.
- **El script descubre los repos**, no lleva lista. Un repo nuevo entra solo.
- **Verifica siempre**: tras espejar compara las refs de la copia con las del
  espejo y falla si falta alguna. Un espejo que no se comprueba no es respaldo.
- **0 refs = no hay respaldo posible.** El script lo reporta en vez de crear un
  espejo vacío que aparente estar bien. Hay que commitear primero.
- Un espejo en el mismo disco protege contra borrado accidental y contra perder
  la máquina WSL. **No** protege contra un fallo de F:.

## Salida que importa

`⚠️ N sin commitear` en un repo significa que ese trabajo **no está en el
espejo**: `git push` solo mueve commits. Commitear antes de dar el respaldo por
bueno.
