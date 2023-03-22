import simulatore
import json 
import argparse



def argomenti_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("testo", help =" il nome del file di testo con il codice mips ( esempio: testo.txt, Nota: deve esserci .txt).", type=str)
    parser.add_argument("-dec","--decode", help =" il booleano decode. Se inserito allora le istruzioni branch richiedono dati in fase di execute piuttosto che in fase di decode", action= "store_false")
    parser.add_argument("-f","--forwarding", help =" il booleano per stabilire se usare la tecnica di forwarding, se inserito si esegue il codice con forwarding", action= "store_true")
    parser.add_argument("-pc","--program_counter", help =" il booleano per decidere se calcolare il program counter, se inserito viene calcolato il program counter", action= "store_true")
    parser.add_argument("-m","--messaggio", help =" il booleano per decidere se visualizzare messaggi riguardanti gli stalli trovati, se inserito vengono mostrati i messaggi", action= "store_true")
    parser.add_argument("-cl", "--ciclo_clock", help =" l'intero che indica il ciclo di clock dove cercare le istruzioni nella pipeline ( deve essere maggiore o uguale a 5 oppure 0 se non si vuole eseguire la ricerca) di default è a 0", type=int)
    parser.add_argument("-exp","--excel_pipeline", help =" booleano per decidere se generare un excel con il foglio avente l'esecuzione del codice, se inserito viene generato il file excel", action= "store_true")
    parser.add_argument("-exh","--excel_hazards", help =" booleano per decidere se generare un excel con il foglio avente gli hazards trovati o le istruzioni nella pipeline, se inserito viene generato il file excel", action= "store_true")
    args = parser.parse_args()
    if not args.ciclo_clock:
        args.ciclo_clock = 0 
    print(args)
    return args

def avvia_simulatore(inputs):
    sim = simulatore.Simulatore()
    # L'ultimo valore (l'intero) serve per trovare le istruzioni in pipeline durante un certo ciclo di clock
    # Se lasciato a zero non viene eseguita la ricerca. Va inserito un numero >= 5 
    # Per jal e jalr serve program counter a True (terzo booleano)
    simulazione = sim.simula_codice_mips(inputs.testo, inputs.decode, inputs.forwarding, inputs.program_counter, inputs.messaggio, inputs.ciclo_clock)  
    # simulazione = sim.simula_codice_mips(True, False, False, True, 0)   
    json_object_pipeline = json.dumps(simulazione[0])
    json_object_hazards = json.dumps(simulazione[1])
    # Per scrivere il json file
    with open("pipeline.json", "w") as outfile:
        outfile.write(json_object_pipeline)
    with open("hazards.json", "w") as outfile:
        outfile.write(json_object_hazards)
    # Genero un file excel con uno o due fogli ( il primo booleano a True per foglio riguardante la pipeline, il secondo per gli hazards)
    simulatore.genera_excel(json_object_pipeline, json_object_hazards, sim.bool_forwarding, inputs.excel_pipeline, inputs.excel_hazards)
    


def main():
    inputs = argomenti_parse()
    avvia_simulatore(inputs)
    
    


if __name__ == "__main__":
    main()