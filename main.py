import simulatore
import json 




def main():
    sim = simulatore.Simulatore()
    # L'ultimo valore (l'intero) serve per trovare le istruzioni in pipeline durante un certo ciclo di clock
    # Se lasciato a zero non viene eseguita la ricerca. Va inserito un numero >= 5 
    # Per jal e jalr serve program counter a True (terzo booleano)
    simulazione = sim.simula_codice_mips(True, False, False, True, 0)   
    json_object_pipeline = json.dumps(simulazione[0])
    json_object_hazards = json.dumps(simulazione[1])
    # Per scrivere il json file
    with open("pipeline.json", "w") as outfile:
        outfile.write(json_object_pipeline)
    with open("hazards.json", "w") as outfile:
        outfile.write(json_object_hazards)
    # Genero un file excel con uno o due fogli ( il primo booleano a True per foglio riguardante la pipeline, il secondo per gli hazards)
    simulatore.genera_excel(json_object_pipeline, json_object_hazards, sim.bool_forwarding, True, True)
    


if __name__ == "__main__":
    main()