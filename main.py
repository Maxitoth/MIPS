import simulatore
import json 



def main():
    sim = simulatore.Simulatore()
    simulazione = sim.simula_codice_mips(True, False, False, False)   
    json_object = json.dumps(simulazione)
    # Writing to sample.json
    with open("risultato.json", "w") as outfile:
        outfile.write(json_object) 


if __name__ == "__main__":
    main()