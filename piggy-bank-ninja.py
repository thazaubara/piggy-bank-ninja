import logger


def greeting():

    string = """                       _                      __                __            _         _      
    _____       ____  (_)___ _____ ___  __   / /_  ____ _____  / /__   ____  (_)___    (_)___ _
^..^     \9    / __ \/ / __ `/ __ `/ / / /  / __ \/ __ `/ __ \/ //_/  / __ \/ / __ \  / / __ `/
(oo)_____/    / /_/ / / /_/ / /_/ / /_/ /  / /_/ / /_/ / / / / ,<    / / / / / / / / / / /_/ / 
   WW  WW    / .___/_/\__, /\__, /\__, /  /_.___/\__,_/_/ /_/_/|_|  /_/ /_/_/_/ /_/_/ /\__,_/  
            /_/      /____//____//____/                zaubara 2023              /___/      """
    logger.log(string)
    logger.highlight("Welcome to piggy bank ninja!")

greeting()