% Viabilidad: lee supuestos.json (única fuente de cifras). Ninguna cifra se teclea aquí.
% Uso:  matlab -batch "run('analisis/matlab/viabilidad.m')"
S = jsondecode(fileread('analisis/salidas/supuestos.json'));
disp(fieldnames(S));
% TODO: punto de equilibrio, sensibilidad conjunta y Monte Carlo (rand/random del Statistics Toolbox si está licenciado)
% Escribir resultados en analisis/salidas/*.csv y citar el comando en el capítulo BP6.
