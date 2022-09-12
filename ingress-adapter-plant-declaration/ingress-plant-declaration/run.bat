@ECHO OFF

CALL E:\ingress-plant-declaration\venv\Scripts\activate.bat
PUSHD E:
CD E:\ingress-plant-declaration
CALL python -m ingress_plant_declaration.adapter
CALL E:\ingress-plant-declaration\venv\Scripts\deactivate.bat
