from solvers import (
    combinaciones_lineales,
    programacion_convexa,
    pnl_general,
    prog_cuadratica_wolfe,
    programacion_estocastica,
    programacion_geometrica,
    frank_wolfe,
)

# Registro central de solvers. Agregar un solver nuevo = una línea acá.
SOLVERS = {
    combinaciones_lineales.ID:    combinaciones_lineales,
    programacion_convexa.ID:      programacion_convexa,
    pnl_general.ID:               pnl_general,
    prog_cuadratica_wolfe.ID:     prog_cuadratica_wolfe,
    programacion_estocastica.ID:  programacion_estocastica,
    programacion_geometrica.ID:   programacion_geometrica,
    frank_wolfe.ID:               frank_wolfe,
}
