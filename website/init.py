"""
Ficher initialisation (eg, constantes chargées au démarrage dans la session)
"""

from datetime import datetime
from os import path

SESSION['APP'] = "Serial Critique"
SESSION['BASELINE'] = "Critiquez vos séries !"
SESSION['DIR_HISTORIQUE'] = path.join(SESSION['DIRECTORY'], "historiques")
SESSION['HISTORIQUE'] = dict()
SESSION['CURRENT_YEAR'] = datetime.now().year
