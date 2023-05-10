import simulatore
import json 
import argparse



# la funzione serve a passare parametri in input nella console  
def argomenti_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("testo", help =" il nome del file di testo con il codice mips (esempio: testo.txt, Nota: deve esserci .txt).", type=str)
    parser.add_argument("-dec","--decode", help =" il booleano decode. Se inserito allora le istruzioni branch decidono se è necessario eseguire il salto in fase di execute piuttosto che in fase di decode", action= "store_false")
    parser.add_argument("-f","--forwarding", help =" il booleano per stabilire se usare la tecnica di forwarding, se inserito si esegue il codice con forwarding", action= "store_true")
    parser.add_argument("-pc","--program_counter", help =" il booleano per decidere se calcolare il program counter, se inserito viene calcolato il program counter", action= "store_true")
    parser.add_argument("-m","--messaggio", help =" il booleano per decidere se visualizzare messaggi riguardanti gli stalli trovati, se inserito vengono mostrati i messaggi", action= "store_true")
    parser.add_argument("-cl", "--ciclo_clock", help =" l'intero che indica il ciclo di clock dove cercare le istruzioni nella pipeline (deve essere maggiore o uguale a 5 oppure 0 se non si vuole eseguire la ricerca) di default è a 0", type=int)
    parser.add_argument("-exp","--excel_pipeline", help =" booleano per decidere se generare un excel con due fogli. Uno ha l'esecuzione del codice e l'altro ha la rappresentazione delle istruzioni nelle fasi della pipeline, se inserito viene generato il file excel", action= "store_true")
    parser.add_argument("-exh","--excel_hazards", help =" booleano per decidere se generare altri due fogli excel con un foglio avente gli hazards trovati e l'altro foglio con numero di cicli di clock, bolle data e control hazard totali, cicli di clock in ogni parte del programma e istruzioni nella pipeline. Se inserito viene generato il file excel (Se viene inserito dopo -exp allora viene generato un unico excel con tutti e quattro i fogli). Ricorda di installare xlsxwriter (pip install xlsxwriter)", action= "store_true")
    args = parser.parse_args()
    if not args.ciclo_clock:
        args.ciclo_clock = 0 
    return args

def avvia_simulatore(inputs):
    sim = simulatore.Simulatore()
    # L'ultimo valore (l'intero) serve per trovare le istruzioni in pipeline durante un certo ciclo di clock
    # Se lasciato a zero non viene eseguita la ricerca. Va inserito un numero >= 5 (se minore non vengono generati errori, ma la ricerca non da risultati)
    # Per jal e jalr serve program counter a True (terzo booleano). Serve il program counter anche se vogliamo passare a un registro un indirizzo di testo (parte .text) (istruzione la) 
    simulazione = sim.simula_codice_mips(inputs.testo, inputs.decode, inputs.forwarding, inputs.program_counter, inputs.messaggio, inputs.ciclo_clock)     
    dizionario_hazards = {}
    chiave_data_hazards_trovati = "Data Hazards Trovati"
    chiave_control_hazards_trovati = "Control Hazards Trovati"
    # Inserisco il messaggio corretto nel momento in cui nessun data hazard e nessun control hazard venisse trovato.
    if simulazione[1][chiave_data_hazards_trovati] != []:
        dizionario_hazards[chiave_data_hazards_trovati] = simulazione[1][chiave_data_hazards_trovati]
    else:
        dizionario_hazards[chiave_data_hazards_trovati] = ["Nessun data hazard trovato"] # La lista facilita la generazione del file excel
    if simulazione[1][chiave_control_hazards_trovati] != []:
        dizionario_hazards[chiave_control_hazards_trovati] = simulazione[1][chiave_control_hazards_trovati]
    else: 
        dizionario_hazards[chiave_control_hazards_trovati] = ["Nessun control hazard trovato"] # La lista facilita la generazione del file excel
    simulazione[1].pop(chiave_data_hazards_trovati)
    simulazione[1].pop(chiave_control_hazards_trovati)
    
    lista_pipeline = [] # lista dove salvo i valori legati alla pipeline (stringhe che rappresentano le le varie fasi delle istruzioni)
    lista_righe = [] # lista dove salvo i valori numerici di ogni riga (a ogni riga corrisponde un intero)
    for chiave_esterna in simulazione[0]:
        lista_pipeline.append(simulazione[0][chiave_esterna]["Rappresentazione Pipeline"])
        lista_righe.append(simulazione[0][chiave_esterna]["Riga"])
      
    # trovo il dizionario per rappresentare la pipeline (passo le righe trovate nel codice, la riga iniziale e finale del codice, la rappresentazione pipeline di ogni riga, il valore clock finale e le righe trovate durante l'esecuzione)
    diz_rappresentazione = simulatore.rappresenta_pipeline(sim.diz_righe, simulazione[0][1]["Riga"], simulazione[0][len(simulazione[0])]["Riga"], lista_pipeline, simulazione[1]["Cicli di Clock"], lista_righe)
    
    json_object_pipeline = json.dumps(simulazione[0]) # esecuzione pipeline
    json_object_rappresentazione = json.dumps(diz_rappresentazione) # rappresentazione pipeline
    json_object_hazards = json.dumps(dizionario_hazards) # hazards
    json_object_clocks = json.dumps(simulazione[1]) # cicli di clock
    # Per scrivere i json file
    with open("pipeline.json", "w") as outfile:
        outfile.write(json_object_pipeline)
    with open("rappresentazione.json", "w") as outfile:
        outfile.write(json_object_rappresentazione)
    with open("hazards.json", "w") as outfile:
        outfile.write(json_object_hazards)
    with open("clocks.json", "w") as outfile:
        outfile.write(json_object_clocks)
        
    # Genero un file excel con da due a quattro fogli (il primo booleano a True per fogli riguardanti esecuzione e rappresentazione pipeline, il secondo per gli hazards e cicli di clock)
    simulatore.genera_excel(json_object_pipeline, json_object_rappresentazione, json_object_hazards, json_object_clocks, sim.bool_forwarding, inputs.excel_pipeline, inputs.excel_hazards)
    


def main():
    inputs = argomenti_parse()
    avvia_simulatore(inputs)
    
    


if __name__ == "__main__":
    main()