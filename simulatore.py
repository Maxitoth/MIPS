# Considerazioni riguardo alla traduzione da mips a python

# Sconsiglio vivamente l'utilizzo del registro $at in quanto non è gestito in maniera corretta
# Il suo valore è sempre il valore dell'indirizzo dopo istruzioni load in cui è presente il nome della struttura dati
# Esempio : lb $s0, M($a1) ---> $at = 0x1001000
# Esempio : lb $s0, ($a1) ---> $at non cambia
# In alcuni contesti il valore di $at non dovrebbe essere cambiato. 
# Puo essere usato in input del testo, ma non è garantita una terminazione corretta del codice.

# Il tipo float o altri non sono gestiti
# Non sono presenti tutte le istruzioni (usate quelle trovate in self.insieme_istruzioni)

# in ogni riga del testo deve esserci almeno uno spazio o una virgola tra ogni valore altrimenti il testo non
# puo essere letto correttamente
# Non vanno lasciati spazi all'inizio di ogni riga:
# Scrivete "add $a1, $a2, 10" e non " add $a1, $a2, 10"

# In ogni riga del testo con parti di codice ( istruzioni, .text, .data, strutture dati...) non ci devono essere commenti 
# é possibile commentare in righe senza codice ( il self.commento deve essere del tipo # piu uno spazio (esempio): # Risultato e non #Risultato)
# (Lasciare uno spazio tra # e il resto della riga)

# Le strutture dati devono avere nomi diversi dalle istruzioni mips ( non posso dire addi: o jalr: o subi: ecc...) (le maiuscole vanno bene)

# Per stringhe ascii e asciiz non ci dovrebbero essere problemi ( non possiamo usare il carattere: µ):
# Si possono usare tutti i caratteri tranne il carattere speciale e più stringhe ascii nella stessa riga di codice mips,
# tuttavia la stringa vuota va usata da sola: 
# Non vengono trovati gli indirizzi di memoria corretti o inseriti valori corretti in memoria 
# per esempio F: .ascii "ty" "as" "" o F: .asciiz "ty" "as" "" non vanno bene a causa della stringa vuota
# Funziona: F: .ascii "" o F: .asciiz ""
# Viene usato un carattere speciale definito in carattere_speciale nel metodo _init_ 
# Il carattere speciale non va usato ma può essere cambiato, io ho scelto µ. 

# Ho fatto test e aggiornato il codice in modo che vengano riportati i dati corretti anche per l'istruzione syscall
# Va bene scrivere Exit: syscall 
# oppure 
# Exit:
# syscall

# Per quanto riguarda i data hazards trovati ( non quelli rappresentati per la pipeline durante l'esecuzione (non questi stalli '>') ma quelli trovati in totale ( questi : [10, 11, $so]) ):
# Vengono trovati tutti i possibili data hazards prendendo come riferimento il caso peggiore.
# Quindi in generale trovo tutti i data hazards come se stessi eseguendo il codice senza forwaring ( con forwarding ridurrei il numero di stalli trovati).
# Eccezione alla regola: le istruzioni branch possono eseguirsi in fase di execute e se questa funzionalità è abilitata
# allora ottengo un minor numero di stalli.

# Vengono trovati tutti i possibili control hazard (che siano dovuti all'esecuzione del codice o meno)

# Le lw e le lh (anche per sw e sh) funzionano anche accedendo a valori di indirizzi in memoria dispari (è scorretto e andrebbe testato il codice prima su MARS (sarebbe presente un errore) per verificare che gli indirizzi in cui si accede siano sempre pari 
# oppure aggiungere una exception nei quattro metodi (sh, sw, lh, lw))

# Da non scrivere altri indirizzi di partenza, usate quelli di default: Non inserite ".text 4194308" o ".data 268500996"
# Lasciate solo ".data" e ".text". Partire da indirizzi di partenza diversi non è gestito.

import sys
import pandas as pd
import registro
import istruzioni_mips
import program_counter


# Il metodo si occupa di chiamare il metodo della classe Istruzioni associato al nome relativo a nome_istruzione.

def chiama_istruzioni_mips(oggetto_classe_istruzioni, nome_istruzione, prima_posizione, seconda_posizione, terza_posizione):

    # le funzioni non possono chiamarsi and e or
    stringa_and = "and"
    stringa_andi = "andi"
    stringa_ori = "ori"
    stringa_or = "or"
    stringa_xor = "xor"
    stringa_xori = "xori"
    stringa_jalr = "jalr" 
    # servirebbe un insieme per istruzioni con piu input come la jalr e cosi ogni istruizione con piu
    # input la metto nel caso jalr
    # and, or, xor fanno due istruzioni (and, andi, or, ori, xor, xori)
    if nome_istruzione in (stringa_and, stringa_andi): 
        nome_istruzione = "aand"
        metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
        tupla_valori = prima_posizione, seconda_posizione, terza_posizione
        return metodo(tupla_valori)
    if nome_istruzione in (stringa_or, stringa_ori):
        nome_istruzione = "oor"
        metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
        tupla_valori = prima_posizione, seconda_posizione, terza_posizione
        return metodo(tupla_valori)
    if nome_istruzione in (stringa_xor, stringa_xori):
        nome_istruzione = "xor"
        metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
        tupla_valori = prima_posizione, seconda_posizione, terza_posizione
        return metodo(tupla_valori)
    if nome_istruzione == stringa_jalr:
        metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
        tupla_valori = prima_posizione, seconda_posizione
        return metodo(tupla_valori)
    # Caso standard
    metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
    if seconda_posizione == "" and terza_posizione == "":
        return metodo(prima_posizione)
    if terza_posizione == "":
        return metodo(prima_posizione, seconda_posizione)   
    return metodo(prima_posizione, seconda_posizione, terza_posizione) 
        
# Il metodo si occupa di generare un file excel con due o quattro fogli
# Se i booleani sono a False il metodo non fa nulla 
# Altrimenti possono essere generati quattro fogli per un file excel: uno per il risultato dell'esecuzione del codice mips,
# uno per la rappresentazione della pipeline durante l'esecuzione,
# e uno per il risultato dei data hazards e control hazards possibili, e uno per i cicli di clock trovati durante l'esecuzione.
        
def genera_excel(json_object_pipeline, json_object_rappresentazione, json_object_hazards, json_object_clocks, bool_forwarding: bool, bool_excel_pipeline: bool, bool_excel_hazards: bool):
    if bool_forwarding:
        nome_excel = 'risultato_con_forwarding.xlsx'
    else:
        nome_excel = 'risultato_senza_forwarding.xlsx'
    if bool_excel_pipeline:
        df_pipeline = pd.read_json(json_object_pipeline).transpose()
        df_rappresentazione = pd.read_json(json_object_rappresentazione)
        writer_pipeline = pd.ExcelWriter(nome_excel)
        df_pipeline.to_excel(writer_pipeline, sheet_name='Pipeline', index=False, na_rep='NaN')
        
        # Per avere un excel con colonne dinamicamente aggiustate
        # set_column non funziona se non si ha installato xlswriter
        # Utilizzare pip install xlsxwriter 
        for column in df_pipeline:
            column_width = max(df_pipeline[column].astype(str).map(len).max(), len(column))
            col_idx = df_pipeline.columns.get_loc(column)
            writer_pipeline.sheets['Pipeline'].set_column(col_idx, col_idx, column_width) 
        
        df_rappresentazione.to_excel(writer_pipeline, sheet_name='Rappresentazione', index=False, na_rep='NaN')
        for column in df_rappresentazione:
            column_width = max(df_rappresentazione[column].astype(str).map(len).max(), len(column))
            col_idx = df_rappresentazione.columns.get_loc(column)
            writer_pipeline.sheets['Rappresentazione'].set_column(col_idx, col_idx, column_width+1)
        
        if not bool_excel_hazards:
            writer_pipeline.close()
        
    if bool_excel_hazards:
        df_hazards = pd.read_json(json_object_hazards)
        df_clocks = pd.read_json(json_object_clocks, lines = True)
        if not bool_excel_pipeline:
            writer_hazards = pd.ExcelWriter(nome_excel)
            df_hazards.to_excel(writer_hazards, sheet_name='Hazards', index=False, na_rep='NaN')
        
            # Per avere un excel con colonne dinamicamente aggiustate
            # set_column non funziona se non si ha installato xlswriter
            # Utilizzare pip install xlsxwriter 
            for column in df_hazards:
                column_width = max(df_hazards[column].astype(str).map(len).max(), len(column))
                col_idx = df_hazards.columns.get_loc(column)
                writer_hazards.sheets['Hazards'].set_column(col_idx, col_idx, column_width)
                
            df_clocks.to_excel(writer_hazards, sheet_name='Clocks', index=False, na_rep='NaN') 
            for column in df_clocks:
                column_width = max(df_clocks[column].astype(str).map(len).max(), len(column))
                col_idx = df_clocks.columns.get_loc(column)
                writer_hazards.sheets['Clocks'].set_column(col_idx, col_idx, column_width)    
            writer_hazards.close()
        else:
            df_hazards.to_excel(writer_pipeline, sheet_name='Hazards', index=False, na_rep='NaN')
        
            # Per avere un excel con colonne dinamicamente aggiustate
            # set_column non funziona se non si ha installato xlswriter
            # Utilizzare pip install xlsxwriter 
            for column in df_hazards:
                column_width = max(df_hazards[column].astype(str).map(len).max(), len(column))
                col_idx = df_hazards.columns.get_loc(column)
                writer_pipeline.sheets['Hazards'].set_column(col_idx, col_idx, column_width)
                 
            df_clocks.to_excel(writer_pipeline, sheet_name='Clocks', index=False, na_rep='NaN') 
            for column in df_clocks:
                column_width = max(df_clocks[column].astype(str).map(len).max(), len(column))
                col_idx = df_clocks.columns.get_loc(column)
                writer_pipeline.sheets['Clocks'].set_column(col_idx, col_idx, column_width)    
            writer_pipeline.close()
            
# La funzione si occupa di rappresentare la pipeline (quali istruzioni o bolle sono nelle varie fasi della pipeline per ogni ciclo di clock)
            
def rappresenta_pipeline(diz_righe, riga_iniziale, riga_finale, lista_pipeline, valore_clock_finale, lista_righe):
    diz_rappresentazione = {}
    chiave_riga = "Riga"
    chiave_istruzione = "Istruzione mips"
    diz_rappresentazione[chiave_riga] = []
    diz_rappresentazione[chiave_istruzione] = []
    stringa_pipeline = ""
    posizione_valori_pipeline = 1
    stringa_rappresentazione_vuota = ' '
    intero_esecuzione = 0
    
    # Inserisco le colonne per la rappresentazione (ossia le chiavi del mio dizionario)
    for intero in range(1,valore_clock_finale+1):
        diz_rappresentazione[intero] = []
        
    # Inserisco le righe nel dizionario per la giusta visualizzazione dei dati in excel e json
    for riga, valore_diz in diz_righe.items():
        if riga >= riga_iniziale and valore_diz != "" and not valore_diz.startswith('#'):
            diz_rappresentazione[chiave_riga].append(int(riga))
            diz_rappresentazione[chiave_istruzione].append(valore_diz)
            if riga == riga_finale:
                break
    
    # Inserisco le posizioni da mostrare nella rappresentazione
    for chiave in diz_rappresentazione:
        if isinstance(chiave, int):
            diz_rappresentazione[chiave] = [stringa_rappresentazione_vuota for _ in diz_rappresentazione[chiave_riga]]
                
                
    # Inserisco infine la stringa pipeline nelle posizioni corrette          
    for stringa in lista_pipeline:
        stringa_pipeline = stringa.split(' ')
        if stringa_pipeline[-1] != 'W': # Possiamo avere messaggi tipo "Nessuna istruzione in questa riga"
            intero_esecuzione += 1
            continue
        indice_stringa_pipeline = 0
        numero_riga = lista_righe[intero_esecuzione]
        posizione_riga = 0 # le righe di ogni chiave ciclo di clock, le colonne sono i cicli di clock
        

        # Analizzo in quale posizione inserire i valori della stringa in base all'esecuzione del codice
        for intero_riga in diz_rappresentazione[chiave_riga]:
            if intero_riga == numero_riga:
                break
            posizione_riga += 1
        for _ in stringa_pipeline:
            diz_rappresentazione[posizione_valori_pipeline+indice_stringa_pipeline][posizione_riga] = stringa_pipeline[indice_stringa_pipeline]
            indice_stringa_pipeline += 1
        
        posizione_valori_pipeline += 1 + len(stringa_pipeline) - 5           
        intero_esecuzione += 1 
    
    return diz_rappresentazione
            

# La classe Simulatore si occupa di simulare il codice mips.

class Simulatore:
    
    def __init__(self):
        self.testo = "" # testo preso in input
        self.righe = [] # lista che conterrà le righe del testo
        self.testo_modificato = [] # lista che conterrà liste per ogni riga del testo
        self.insieme_istruzioni = {"or","and","ori","andi","xor","xori","subi","sub","add","addi","addiu","addu","slt","sle","j","jal","jalr","beq","beqz","bne","bnez","bge","bgez","blt","bltz","move","lui","srl","sll","li","la","lh","lhu","lw","lb","lbu","sw","sh","sb"} # da aggiungere ogni istruzione MIPS necessaria
        # Per ogni istruzione serve un metodo definito nella classe Istruzioni nel file istruzioni_mips.py
        self.istruzioni_save = {"sw","sb","sh"}
        self.istruzioni_load = {"la","lw","lb","lbu","lh","lhu"}
        self.istruzioni_branch = {"bne","bnez","bge","bgez","beq","beqz","blt","bltz"}
        self.istruzioni_jump = {"j","jal","jalr"}
        self.iniziali_registri = {'a','s','t','v','r','k','1','2','3','4','5','6','7','8','9'} # Iniziali dei possibili registri (ho escluso la f che servirebbe per i floating point registers)
        self.iniziali_registri_numerici = {'1','2','3','4','5','6','7','8','9'} # per segnare registri numerici come $1
        # diz_numero_registri serve per assegnare i valori numerici ai corrispettivi registri
        self.diz_numero_registri = {"$1": "$at", "$2": "$v0", "$3": "$v1", "$4": "$a0", "$5": "$a1","$6": "$a2","$7": "$a3","$8": "$t0","$9": "$t1","$10": "$t2","$11": "$t3","$12": "$t4","$13": "$t5","$14": "$t6","$15": "$t7","$16": "$s0","$17": "$s1","$18": "$s2","$19": "$s3","$20": "$s4","$21": "$s5","$22": "$s6","$23": "$s7", "$24": "$t8","$25": "$t9","$26": "$k0","$27": "$k1","$28": "$gp","$29": "$sp","$30": "$fp","$31": "$ra"}
        self.insieme_registri = set() # L'insieme che conterrà tutti i registri inizializzati
        self.diz_salti = {} # Per controllare a che indice saltare
        self.diz_loops = {} # Per segnare tutti i possibili loop e info associate
        self.insieme_data_hazards = set() # L'insieme che conterrà tutti i data hazard possibili
        self.insieme_control_hazards = set() # L'insieme che conterrà tutti i control hazard possibili
        self.istruzioni = istruzioni_mips.Istruzioni() # Oggetto di classe Istruzioni usato per ottenere per esempio il dizionario che simula la memoria
        self.program_counter = program_counter.ProgramCounter() # Oggetto di classe ProgramCounter usato per ottenere il dizionario che contiene gli indirizzi del testo
        self.diz_indirizzi = {} # dizionario che conterrà tutti gli indirizzi iniziali delle strutture dati trovate in input (parte .data)
        self.diz_righe = {} # dizionario che conterrà come chiave indice riga e come valore la riga del testo
        self.bool_forwarding = False # booleano per salvare il fatto che si applica forwarding o meno
        self.ciclo_di_clock = 0 # valore che indica il ciclo di clock in cui cercare i valori nella pipeline (a 0 non si esegue la ricerca)
        self.diz_hazards = {} # dizionario che conterrà tutti i data hazard e control hazards (uno degli output utilizzato per generare il file hazards.json e l'excel associato)
        self.bool_clock_trovato = False # booleano che indica se abbiamo trovato il ciclo di clock richiesto in input
        self.bool_pipeline_wb = False # booleano che indica se bisogna inserire l'istruzione o la bolla nella fase di WB della pipeline
        self.bool_pipeline_mem = False # booleano che indica se bisogna inserire l'istruzione o la bolla nella fase di MEM della pipeline
        self.bool_pipeline_ex = False # booleano che indica se bisogna inserire l'istruzione o la bolla nella fase di EX della pipeline
        self.bool_pipeline_id = False # booleano che indica se bisogna inserire l'istruzione o la bolla nella fase di ID della pipeline
        self.bool_pipeline_if = False # booleano che indica se bisogna inserire l'istruzione o la bolla nella fase di IF della pipeline
        self.conta_clocks = 0 # valore utilizzato per calcolare i cicli di clock in ogni parte del testo (Esempio semplice: parte prima del loop, parte del loop, parte dopo il loop. Tuttavia vengono valutati anche più loop e loop dentro a loop)
        self.valore_loop = "(Nessun loop trovato)" # Stringa che indicherà il nome del testo da cui inizia un possibile loop (Esempio: "Cycl: beq $s1, $s2, Exit", Cycl sarà il valore loop)
        self.stringa_clocks_pre_loops = "Cicli di clock prima del loop " # Stringa usata prima di un possibile loop. Viene usata per creare una chiave in diz_hazards per salvare i dati riguardanti la parte del testo prima del loop (o prima del secondo loop ecc...)
        self.reset_calcolo_loop = False # booleano che indica se il loop ha terminato un ciclo di esecuzione (quindi sta cominciando il prossimo ciclo o il loop è finito)
        self.aggiorna_pre_loop = False # booleano che indica se il loop è stato appena trovato e quindi bisogna segnare i cicli di clock presenti precedentemente
        self.conta_control_hazards = 0 # valore che indicherà le bolle dovute a control hazard in una parte del testo
        self.conta_data_hazards = 0 # valore che indicherà le bolle dovute a data hazard in una parte del testo
        self.carattere_speciale = 'µ' # Importante per la gestione delle stringhe ascii (il valore non deve presentarsi in input)
    
    # Valori da non cambiare
    piu = '+'
    aperta_tonda = "("
    chiusa_tonda = ")"
    text = ".text"
    data = ".data"
    punto  = '.'
    dollaro = "$"
    meno = '-'
    meno_zero_x = "-0x"
    zero_x = "0x"
    piu_zero_x = "+0x"
    carattere_virgoletta = "'"
    syscall = "syscall"
    zero = "0"
    stringa_bolla = "> "
    stringa_pipeline = "F D X M W"
    commento = '#'
        
    # Il metodo si occupa di modificare il file di testo associato per ottenere una lista di liste (ogni lista é una riga del testo)
    # Il dizionario diz_righe viene aggiornato con numero riga e riga del testo associata.
    
    def modifica_testo(self) :
        with open(self.testo, encoding='utf-8') as testo:
            self.righe = testo.readlines()
        due_punti = ':'
        virgola = ','
        due_spazi = '  '
        spazio = ' '
        invio = '\n'
        virgolette = '"'
        stringa_spazio_piu_spazio = " + "
        stringa_spazio_piu = " +"
        stringa_piu_spazio = "+ "
        stringa_tonda_aperta_spazio = "( "
        stringa_tonda_chiusa_spazio = ") "
        stringa_spazio_tonda_chiusa = " )"
        fine_riga_textarea = '\r'
        bool_stringhe_data = False
        bool_virgolette = False
        bool_dati_ascii = False
        riga_ascii = ""
        numero_riga = 1
        riga_corretta = []
        # Analizzo riga per riga, rimpiazzo doppi spazi, virgole, due punti
        # e altri casi particolari possibilmente trovati in input 
        for riga, istruzione in enumerate(self.righe, 1): 
            riga_modificata = istruzione.strip()
            self.diz_righe[riga] = riga_modificata
            if riga_modificata.startswith(self.data):
                bool_stringhe_data = True
            if riga_modificata.startswith(self.text):
                bool_stringhe_data = False
            if virgolette in riga_modificata and bool_stringhe_data: # Trovata stringa ascii
                # Analizzo la stringa ascii e trovo la riga ascii corretta (se ho S: .ascii "stringa " " trovata" --> stringaµ µtrovata --> ['S','.ascii', 'stringa ', ' trovata'])
                for carattere in riga_modificata: 
                    if carattere == virgolette:
                        bool_virgolette = not bool(bool_virgolette)
                    if carattere == spazio and bool_virgolette:
                        riga_ascii += self.carattere_speciale
                    elif carattere == due_punti and not bool_virgolette:
                        riga_ascii += spazio
                    elif carattere == virgola and not bool_virgolette:
                        riga_ascii += spazio  
                    elif carattere == fine_riga_textarea and not bool_virgolette: # Pensato per textarea da web (non viene trovato)
                        riga_ascii += '' 
                    elif carattere == invio and not bool_virgolette: # Pensato per textarea da web (non viene trovato)
                        riga_ascii += ''
                    else:
                        riga_ascii += carattere    
                bool_dati_ascii = True
                riga_modificata = riga_ascii                  
                riga_modificata = riga_modificata.replace(virgolette, spazio)
                riga_ascii = ""
            else:
                if due_punti in riga_modificata:
                    riga_modificata = riga_modificata.replace(due_punti, spazio)
                if virgola in riga_modificata:
                    riga_modificata = riga_modificata.replace(virgola, spazio)
                if fine_riga_textarea in riga_modificata: # Pensato per textarea da web
                    riga_modificata = riga_modificata.replace(fine_riga_textarea, '')
                if invio in riga_modificata: # Pensato per textarea da web 
                    riga_modificata = riga_modificata.replace(invio, '')        
            while due_spazi in riga_modificata: # tolgo i doppi spazi
                riga_modificata = riga_modificata.replace(due_spazi, spazio)
            if not bool_stringhe_data: # check semplice per capire se sono in una riga di .text o in .data
                if stringa_spazio_piu in riga_modificata and self.aperta_tonda in riga_modificata: # Si fa solo per load o store instruction
                    riga_modificata = riga_modificata.replace(stringa_spazio_piu, self.piu)
                if stringa_piu_spazio in riga_modificata and self.aperta_tonda in riga_modificata: # Si fa solo per load o store instruction
                    riga_modificata = riga_modificata.replace(stringa_piu_spazio, self.piu)
                if stringa_spazio_piu_spazio in riga_modificata: # Si fa per tutte le istruzioni
                    riga_modificata = riga_modificata.replace(stringa_spazio_piu_spazio, self.piu)
                if stringa_tonda_aperta_spazio in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_tonda_aperta_spazio, self.aperta_tonda)
                if stringa_tonda_chiusa_spazio in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_tonda_chiusa_spazio, self.chiusa_tonda)
                if stringa_spazio_tonda_chiusa in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_spazio_tonda_chiusa, self.chiusa_tonda)
            riga_modificata = riga_modificata.split()
            if bool_dati_ascii:
                riga_corretta = [val.replace(self.carattere_speciale, spazio) if self.carattere_speciale in val else val for val in riga_modificata]
                        
            # I modi di scrivere istruzioni load o store portano a dover modificare la riga
            # Basti pensare a "la $a0, M + -1000 ($zero )" -> [la, $a0, M+-1000, ($zero)]
            # è possibile scrivere anche in quel modo e in molti altri.
            # Dopo questa parte ottengo [la, $a0, M+-1000($zero)], ossia la giusta rappresentazione
            if len(riga_modificata) == 4 and not bool_stringhe_data: # Per caso particolare 
                if riga_modificata[0] in self.istruzioni_load or riga_modificata[0] in self.istruzioni_save:
                    riga_modificata[-1] = riga_modificata[-2] + riga_modificata[-1]
                    riga_modificata.pop(-2)
            elif len(riga_modificata) == 5 and not bool_stringhe_data: # Per caso particolare (con nome di testo)
                if riga_modificata[1] in self.istruzioni_load or riga_modificata[1] in self.istruzioni_save:
                    riga_modificata[-1] = riga_modificata[-2] + riga_modificata[-1]
                    riga_modificata.pop(-2)  
            elif len(riga_modificata) == 3 and not bool_stringhe_data: # Per caso particolare (con nome di testo)
                if riga_modificata[1] in self.istruzioni_load or riga_modificata[1] in self.istruzioni_save:
                    lista_stringa_corretta = riga_modificata[-1].split(self.piu)
                    riga_modificata.pop(-1) 
                    riga_modificata.append(lista_stringa_corretta[0])
                    riga_modificata.append(lista_stringa_corretta[1])
            elif len(riga_modificata) == 2 and not bool_stringhe_data: # Per caso particolare
                if riga_modificata[0] in self.istruzioni_load or riga_modificata[0] in self.istruzioni_save:
                    lista_stringa_corretta = riga_modificata[-1].split(self.piu)
                    riga_modificata.pop(-1) 
                    riga_modificata.append(lista_stringa_corretta[0])
                    riga_modificata.append(lista_stringa_corretta[1]) 
            numero_riga += 1
            if bool_dati_ascii:
                self.testo_modificato.append(riga_corretta)
                bool_dati_ascii = False 
                riga_corretta = []
            else:
                self.testo_modificato.append(riga_modificata)
        testo.close()
    
    # Il metodo si occupa di trovare gli indirizzi legati al .text in mars usando due dizionari
    # I dati trovati servono a simulare il program counter.
    # Tuttavia qui viene anche chiamato il metodo crea registri per inizializzare registri e il metodo trova_valori_per_pipeline per
    # trovare alcuni dei possibili data hazards 
    
    def trova_indirizzi_text_e_salti(self, bool_decode: bool):
        chiave = ""
        diz_indirizzi_text = self.program_counter.diz_indirizzi_text # Valori program counter nel testo (tutti gli indirizzi)
        diz_text = self.istruzioni.diz_text # Valori program counter per i nomi del testo (indirizzi)
        indirizzo_text = self.program_counter.indirizzo_text # Valore dell'indirizzo (si incrementa di 4 per ogni istruzione)
        indice_riga_pre_precedente = -1
        indice_riga_precedente = -1
        nome_at = "$at"
        registro_at = registro.Registro(nome_at, 0, "$1") # instanzio $at
        registro_at.write_back = True
        registro_at.fetch = False
        registro_at.stato_fase = 5
        registro_ra = self.istruzioni.ra
        registro_ra.write_back = True
        registro_ra.fetch = False
        registro_ra.stato_fase = 5
        self.insieme_registri.add(registro_at)
        self.insieme_registri.add(registro_ra)
        istruzione_trovata = False
        indice_lista = 0
        istruzione = ""
        istruzione_precedente = ""
        for indice, lista in enumerate(self.testo_modificato):
            for elem in lista:
                if lista[0].startswith(self.punto):
                    break
                if len(lista) == 1: # Per evitare out of range
                    if lista[0] == self.syscall:
                        indirizzo_text += 4
                        diz_indirizzi_text[indirizzo_text] = indice
                        indice_riga_pre_precedente = indice_riga_precedente
                        indice_riga_precedente = indice
                    else: 
                        chiave = elem
                        diz_text[chiave] = indirizzo_text+4
                        self.diz_salti[chiave] = indice # ci dice dove dobbiamo saltare (per beq, j ecc...)
                    break
                if lista[1] in self.insieme_istruzioni:
                    istruzione_precedente = istruzione
                    istruzione = lista[1]
                    ultimo_valore = lista[-1:][0]
                    indice_lista = 1
                    istruzione_trovata = True
                    chiave = elem
                    indirizzo_text += 4
                    diz_indirizzi_text[indirizzo_text] = indice
                    diz_text[chiave] = indirizzo_text
                    self.diz_salti[chiave] = indice # ci dice dove dobbiamo saltare (per beq, j ecc...) 
                elif lista[0] in self.insieme_istruzioni:
                    istruzione_precedente = istruzione
                    istruzione = lista[0]
                    indice_lista = 0  
                    istruzione_trovata = True 
                    indirizzo_text += 4
                    diz_indirizzi_text[indirizzo_text] = indice
                else:
                    if lista[1] == self.syscall:
                        indirizzo_text += 4
                        diz_indirizzi_text[indirizzo_text] = indice
                        chiave = elem
                        diz_text[chiave] = indirizzo_text+4
                        self.diz_salti[chiave] = indice # ci dice dove dobbiamo saltare (per beq, j ecc...)
                        indice_riga_pre_precedente = indice_riga_precedente
                        indice_riga_precedente = indice
                    break
                if istruzione_trovata:
                    ultimo_valore = lista[-1:][0] # Se è un nome di testo allora potrebbe creare loop
                    # Per trovare i possibili loop
                    if istruzione in self.istruzioni_jump or istruzione in self.istruzioni_branch:
                        if ultimo_valore in self.diz_salti:
                            self.diz_loops[ultimo_valore] = [indice, False, 0, [], set()]
                    valore = True
                    carattere_trovato = False
                    valore_con_tonda_trovato = False
                    ultimo_elemento = lista[-1]
                    penultimo_elemento = lista[-2]
                    skip = False
                    nome_registro = Simulatore.crea_registri(self, lista[indice_lista:])
                    Simulatore.trova_valori_per_pipeline(self,istruzione_precedente,indice_riga_precedente,indice_riga_pre_precedente,0,0,nome_registro,indice,lista,False,False,0,0,0,bool_decode,False,False,False)
                    indice_riga_pre_precedente = indice_riga_precedente
                    indice_riga_precedente = indice
                    istruzione_trovata = False
                # Qui sotto parte necessaria al calcolo corretto del program counter
                if istruzione in self.program_counter.insieme_istruzioni_semplici:
                    break
                # Da qui comincia l'analisi dell'input per simulare il numero di pseudo-istruzioni generate, quindi
                # un corretto valore del program counter e indirizzi del text
                if self.istruzioni.bool_program_counter: # Da farsi solo se richiesto
                    if self.aperta_tonda in ultimo_elemento:
                        skip = True
                        if ultimo_elemento.startswith(self.piu): # Se scrivo +60 lo leggo come intero positivo
                            ultimo_elemento = ultimo_elemento[1:]
                        if self.piu in ultimo_elemento:
                            valore = self.program_counter.range_sessanta + 1 # vado oltre il range
                            if self.aperta_tonda in ultimo_elemento: # Per caso W+100($a0)
                                valore_con_tonda_trovato = True
                        elif ultimo_elemento[0] != self.aperta_tonda:
                            valore_con_tonda_trovato = True
                            valore = ultimo_elemento[0:ultimo_elemento.index(self.aperta_tonda)]
                            if valore.isdigit() or valore.startswith(self.zero_x) or valore.startswith(self.meno_zero_x) or valore.startswith(self.meno):
                                if valore.startswith(self.zero_x) or valore.startswith(self.meno_zero_x):
                                    valore = istruzioni_mips.toint(int(valore,16))
                                else:
                                    valore = int(valore)
                            elif not valore.startswith(self.carattere_virgoletta):
                                valore = self.program_counter.range_sessanta + 1 # vado oltre il range
                            else:
                                carattere_trovato = True
                    elif ultimo_elemento.isdigit() or ultimo_elemento.startswith(self.zero_x) or ultimo_elemento.startswith(self.meno_zero_x) or ultimo_elemento.startswith(self.meno):
                        skip = True
                        if ultimo_elemento.startswith(self.zero_x) or ultimo_elemento.startswith(self.meno_zero_x):
                            valore = istruzioni_mips.toint(int(ultimo_elemento,16))
                        else:
                            valore = int(ultimo_elemento)
                    elif ultimo_elemento.startswith(self.carattere_virgoletta):
                        skip = True
                        carattere_trovato = True
                    elif istruzione in self.program_counter.insieme_save_load or istruzione == self.program_counter.istruzione_la:
                        valore = self.program_counter.range_sessanta + 1 # vado oltre il range
                        skip = True
                    if not skip: # Per branch
                        if penultimo_elemento.startswith(self.piu): # Se scrivo +60 lo leggo come intero positivo
                            penultimo_elemento = penultimo_elemento[1:]
                        if penultimo_elemento.isdigit() or penultimo_elemento.startswith(self.zero_x) or penultimo_elemento.startswith(self.meno_zero_x) or penultimo_elemento.startswith(self.meno):
                            if penultimo_elemento.startswith(self.zero_x) or penultimo_elemento.startswith(self.meno_zero_x):
                                valore = istruzioni_mips.toint(int(penultimo_elemento,16))
                            else:
                                valore = int(penultimo_elemento)
                        elif penultimo_elemento.startswith(self.carattere_virgoletta):
                            carattere_trovato = True
                    indirizzo_text = self.program_counter.simula_program_counter(istruzione, indirizzo_text, carattere_trovato, valore, valore_con_tonda_trovato)
                break
        indirizzo_text += 4 # esecuzione ultima istruzione
        diz_indirizzi_text[indirizzo_text] = ""
        self.istruzioni.pc_finale = indirizzo_text 
        self.istruzioni.diz_indirizzi_text = self.program_counter.diz_indirizzi_text
        
    # Il metodo si occupa di trovare le istruzioni o le bolle nelle varie fasi della pipeline (IF, ID, EX, MEM e WB)
    # in un determinato ciclo di clock
    def trova_istruzioni_e_bolle_in_pipeline(self, indice: int, indice_riga_precedente: int, istruzione_precedente: str, totale_clocks: int, riga: str, lista_valori_diz: dict, bool_decode: bool):
        if totale_clocks >= self.ciclo_di_clock and not self.bool_clock_trovato:
            if self.ciclo_di_clock == totale_clocks: # caso standard
                self.bool_clock_trovato = True
                self.diz_hazards["WB"] = "("+str(indice+1)+") "+riga
                self.bool_pipeline_wb = True
            elif self.ciclo_di_clock == totale_clocks - 1: # è presente uno stallo
                self.bool_clock_trovato = True
                self.diz_hazards["WB"] = "bolla"
                self.bool_pipeline_wb = True
                self.diz_hazards["MEM"] = "("+str(indice+1)+") "+riga
                self.bool_pipeline_mem = True
            elif self.ciclo_di_clock == totale_clocks - 2: # sono presenti due stalli
                self.bool_clock_trovato = True
                self.diz_hazards["WB"] = "bolla"
                self.bool_pipeline_wb = True
                self.diz_hazards["MEM"] = "bolla"
                self.bool_pipeline_mem = True
                self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                self.bool_pipeline_ex = True
        elif self.bool_clock_trovato:
            if lista_valori_diz["Numero Bolle Control Hazard"] == 1 or lista_valori_diz["Numero Bolle Data Hazard"] == 1:
                if self.bool_pipeline_if:
                    self.ciclo_di_clock = 0 # ho finito la ricerca
                elif self.bool_pipeline_id:
                    if istruzione_precedente in self.istruzioni_branch: # Controllo caso particolare branch
                        riga_successiva_a_precedente = indice_riga_precedente+2
                        if riga_successiva_a_precedente in self.diz_righe:
                            for _ in self.diz_righe:
                                if riga_successiva_a_precedente in self.diz_righe:
                                    if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                        self.diz_hazards["IF"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"
                                        break 
                                riga_successiva_a_precedente += 1       
                        else:
                            self.diz_hazards["IF"] = "bolla"   
                    else:
                        self.diz_hazards["IF"] = "bolla"
                    self.bool_pipeline_if = True
                elif self.bool_pipeline_ex:
                    self.diz_hazards["ID"] = "bolla"
                    self.bool_pipeline_id = True
                    self.diz_hazards["IF"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_if = True
                elif self.bool_pipeline_mem:
                    self.diz_hazards["EX"] = "bolla"
                    self.bool_pipeline_ex = True
                    self.diz_hazards["ID"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_id = True
                elif self.bool_pipeline_wb:
                    self.diz_hazards["MEM"] = "bolla"
                    self.bool_pipeline_mem = True
                    self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_ex = True
            elif lista_valori_diz["Numero Bolle Data Hazard"] == 2 or lista_valori_diz["Numero Bolle Control Hazard"] == 2:
                if self.bool_pipeline_if:
                    self.ciclo_di_clock = 0 # ho finito la ricerca
                elif self.bool_pipeline_id:
                    # Questa parte non dovrebbe mai succedere
                    # Se ho due bolle control hazard allora la branch è in EX
                    # Quindi partirei da self.bool_pipeline_ex
                    if istruzione_precedente in self.istruzioni_branch: # Non funzionerà, serve l'istruzione pre-precedente
                        riga_successiva_a_precedente = indice_riga_precedente+2
                        if riga_successiva_a_precedente in self.diz_righe:
                            for _ in self.diz_righe:
                                if riga_successiva_a_precedente in self.diz_righe:
                                    if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                        self.diz_hazards["IF"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"
                                        break 
                                riga_successiva_a_precedente += 1
                        else:
                            self.diz_hazards["IF"] = "bolla"  
                    else:
                        self.diz_hazards["IF"] = "bolla"
                    self.bool_pipeline_if = True
                elif self.bool_pipeline_ex:
                    if istruzione_precedente in self.istruzioni_branch and not bool_decode: # Controllo caso particolare branch analizzata in fase EX
                        jalr_trovata = False
                        riga_successiva_a_precedente = indice_riga_precedente+2
                        if riga_successiva_a_precedente in self.diz_righe:
                            for _ in self.diz_righe:
                                if riga_successiva_a_precedente in self.diz_righe:
                                    if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                        self.diz_hazards["ID"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"
                                        lista_riga_successiva = self.testo_modificato[riga_successiva_a_precedente-1]
                                        if lista_riga_successiva[1] in self.insieme_istruzioni:
                                            lista_riga_successiva = lista_riga_successiva[1:]
                                        if lista_riga_successiva[0] in self.istruzioni_jump:
                                            # da vedere jalr
                                            if lista_riga_successiva[0] == "jalr":
                                               jalr_trovata = True
                                            else: 
                                                riga_successiva_a_precedente = self.diz_salti[lista_riga_successiva[-1]] + 1
                                        else:
                                            riga_successiva_a_precedente += 1
                                        break 
                                riga_successiva_a_precedente += 1
                            if jalr_trovata:
                                self.diz_hazards["IF"] = "Caso jalr non implementato, istruzione successiva non trovata (bolla)"  
                                self.bool_pipeline_if = True
                            else:  
                                for _ in self.diz_righe:
                                    if riga_successiva_a_precedente in self.diz_righe:
                                        if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                            self.diz_hazards["IF"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"  
                                            self.bool_pipeline_if = True                                              
                                            break 
                                    riga_successiva_a_precedente += 1
                        else:
                            self.diz_hazards["ID"] = "bolla" 
                            self.diz_hazards["IF"] = "bolla"
                            self.bool_pipeline_if = True  
                    else:
                        self.diz_hazards["ID"] = "bolla"
                        self.diz_hazards["IF"] = "bolla"
                        self.bool_pipeline_if = True
                    self.bool_pipeline_id = True
                elif self.bool_pipeline_mem:
                    self.diz_hazards["EX"] = "bolla"
                    self.bool_pipeline_ex = True
                    self.diz_hazards["ID"] = "bolla"
                    self.bool_pipeline_id = True
                    self.diz_hazards["IF"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_if = True
                elif self.bool_pipeline_wb:
                    self.diz_hazards["MEM"] = "bolla"
                    self.bool_pipeline_mem = True
                    self.diz_hazards["EX"] = "bolla"
                    self.bool_pipeline_ex = True
                    self.diz_hazards["ID"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_id = True
            else:
                if self.bool_pipeline_if:
                    self.ciclo_di_clock = 0 # ho finito la ricerca
                elif self.bool_pipeline_id: # Controllo caso particolare branch
                    if istruzione_precedente in self.istruzioni_branch:
                        riga_successiva_a_precedente = indice_riga_precedente+2
                        if riga_successiva_a_precedente in self.diz_righe:
                            for _ in self.diz_righe:
                                if riga_successiva_a_precedente in self.diz_righe:
                                    if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                        self.diz_hazards["IF"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"
                                        break 
                                riga_successiva_a_precedente += 1
                        else:
                            self.diz_hazards["IF"] = "("+str(indice+1)+") "+riga   
                    else:
                        self.diz_hazards["IF"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_if = True
                elif self.bool_pipeline_ex:
                    if istruzione_precedente in self.istruzioni_branch and not bool_decode: # Controllo caso particolare branch analizzata in fase EX
                        jalr_trovata = False
                        riga_successiva_a_precedente = indice_riga_precedente+2
                        if riga_successiva_a_precedente in self.diz_righe:
                            for _ in self.diz_righe:
                                if riga_successiva_a_precedente in self.diz_righe:
                                    if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                        self.diz_hazards["ID"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"
                                        lista_riga_successiva = self.testo_modificato[riga_successiva_a_precedente-1]
                                        if lista_riga_successiva[1] in self.insieme_istruzioni:
                                            lista_riga_successiva = lista_riga_successiva[1:]
                                        if lista_riga_successiva[0] in self.istruzioni_jump:
                                            # da vedere jalr
                                            if lista_riga_successiva[0] == "jalr":
                                                jalr_trovata = True
                                            else:
                                                riga_successiva_a_precedente = self.diz_salti[lista_riga_successiva[-1]] + 1
                                        else:
                                            riga_successiva_a_precedente += 1
                                        break 
                                riga_successiva_a_precedente += 1
                            if jalr_trovata:
                                self.diz_hazards["IF"] = "Caso jalr non implementato, istruzione successiva non trovata (bolla)"  
                                self.bool_pipeline_if = True
                            else: 
                                for _ in self.diz_righe:
                                    if riga_successiva_a_precedente in self.diz_righe:
                                        if self.diz_righe[riga_successiva_a_precedente][:-1] not in self.istruzioni.diz_text:
                                            self.diz_hazards["IF"] = "("+str(riga_successiva_a_precedente)+") "+self.diz_righe[riga_successiva_a_precedente]+" (bolla)"  
                                            self.bool_pipeline_if = True                                              
                                            break 
                                    riga_successiva_a_precedente += 1
                        else:
                            self.diz_hazards["ID"] = "("+str(indice+1)+") "+riga   
                    else:
                        self.diz_hazards["ID"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_id = True
                elif self.bool_pipeline_mem:
                    self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_ex = True
                elif self.bool_pipeline_wb:
                    self.diz_hazards["MEM"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_mem = True 
    
    # Il metodo si occupa di aggiornare i valori mostrati in output (Vengono aggiornati i valori riguardanti la riga di codice mips analizzata)                
    def aggiorna_valori_pipeline(self, lista_valori_diz: dict, control_hazards: int, stalli_registro: int, data_hazards_totali: int, totale_clocks: int, conta_clocks: int):
        lista_valori_diz["Rappresentazione Pipeline"] = self.stringa_bolla*(control_hazards+stalli_registro)+self.stringa_pipeline # rappresentazione pipeline 
        data_hazards_totali += stalli_registro
        numero_hazards = stalli_registro+control_hazards
        totale_clocks += numero_hazards
        conta_clocks += numero_hazards
        lista_valori_diz["Numero Bolle Data Hazard"] = stalli_registro # stalli data hazards per quella istruzione
        lista_valori_diz["Numero Bolle Control Hazard"] = control_hazards # stalli control hazards per quella istruzione
        lista_valori_diz["Valore Clock"] = totale_clocks # Valore clock finale per quella istruzione
        return lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards
    
    # Il metodo si occupa di mostrare il valore dell'hazard trovato e di dare un messaggio per i
    # data hazard trovati se i messaggi sono richiesti (messaggi per control hazard aggiornati in simula_codice_mips)
    def aggiorna_hazard_e_messaggi(self, lista_valori_diz: dict, tupla_hazard: tuple, registro_da_controllare: registro.Registro, stalli_registro: int, bool_messaggi_hazards: bool, bool_forwarding: bool, bool_branch: bool, bool_decode: bool, messaggio_data_hazards: str):
        lista_valori_diz["Hazard Trovato"] = tupla_hazard # Hazard trovato in quella riga
        nome_registro = tupla_hazard[2]
        riga_registro = str(tupla_hazard[0])
        riga_attuale = str(tupla_hazard[1])
        if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
            if bool_forwarding: # Parte forwarding
                if registro_da_controllare.istruzione_mips in self.istruzioni_load and registro_da_controllare.istruzione_mips != "la": # istruzione la non passa per la memory
                    if bool_branch and bool_decode: # Caso particolare per le branch
                        if stalli_registro == 2:
                            messaggio_data_hazards = "Ci sono due stalli dovuti a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" ha già superato la fase di decode (è in fase di execute)."
                        else:
                            messaggio_data_hazards = "C'è uno stallo dovuto a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                    else: # Caso standard
                        messaggio_data_hazards = "C'è uno stallo dovuto a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di execute."       
                else: # Caso particolare per le altre istruzioni, si ha uno stallo solo con branch eseguite a fase di decode
                    messaggio_data_hazards = "C'è uno stallo dovuto a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di execute per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di decode."       
            else: # Parte not forwarding
                if bool_branch and not bool_decode:
                    messaggio_data_hazards = "C'è uno stallo dovuto a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di execute."
                else:
                    if stalli_registro == 2:
                        messaggio_data_hazards = "Ci sono due stalli dovuti a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di execute l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                    else:
                        messaggio_data_hazards = "C'è uno stallo dovuto a un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di decode."
            lista_valori_diz["Messaggio"] = messaggio_data_hazards
        return lista_valori_diz
    
    # Il metodo si occupa di calcolare i cicli di clock per ogni parte di ogni loop trovato
    # Ogni parte di un loop di codice (tramite jump e branch) ha un numero di bolle dovute a data hazard e control hazard,
    # un insieme di istruzioni, cicli di clock di quella parte e il numero di volte in cui troviamo quella parte durante l'esecuzione
    # Se l'insieme di istruzioni trovate (righe) e il numero di cicli di clock trovati è lo stesso, allora abbiamo ritrovato la stessa parte di codice nel loop  
    def calcola_clocks_per_parte_loops(self, conta_clocks: int, indice: int):
        for valore_diz in self.diz_loops.values(): # Aggiungo cicli di clock e righe istruzioni per ogni loop trovato
            if valore_diz[1]:
                valore_diz[2] += conta_clocks
                valore_diz[4].add(indice+1) 
        if self.reset_calcolo_loop: # Aggiungo i valori trovati (l'iterazione del loop è terminata o il loop è cominciato)
            if self.diz_loops[self.valore_loop][1]: # loop già cominciato, iterazione terminata
                self.diz_loops[self.valore_loop][2] = self.diz_loops[self.valore_loop][2] - 1
                lista_cercata = [self.diz_loops[self.valore_loop][2],self.diz_loops[self.valore_loop][4],1] # [cicli di clock, insieme righe, numero di iterazioni (prima volta 1)] 
                bool_lista_trovata = False
                for indice_lista in range(0,len(self.diz_loops[self.valore_loop][3])):
                    if self.diz_loops[self.valore_loop][3][indice_lista][0] == lista_cercata[0] and self.diz_loops[self.valore_loop][3][indice_lista][1] == lista_cercata[1]: 
                        self.diz_loops[self.valore_loop][3][indice_lista][2] += 1
                        bool_lista_trovata = True
                        break
                if not bool_lista_trovata:
                    lista_cercata.append(self.conta_data_hazards)
                    lista_cercata.append(self.conta_control_hazards)
                    self.diz_loops[self.valore_loop][3] += [lista_cercata] 
                self.conta_data_hazards = 0
                self.conta_control_hazards = 0 
                self.conta_clocks = 1
                self.diz_loops[self.valore_loop][2] = 1
                self.diz_loops[self.valore_loop][4] = set() # Reset dell'insieme di righe trovate
            else: # loop appena trovato, comincia l'analisi
                self.diz_loops[self.valore_loop][1] = True
                self.aggiorna_pre_loop = True
                self.conta_clocks = self.conta_clocks - 1 
                self.diz_loops[self.valore_loop][2] = 1  
                self.diz_loops[self.valore_loop][4].add(indice+1)
      
    # Il metodo si occupa di trovare i data hazard tra la riga attuale analizzata e le righe precedenti in cui 
    # è presente il registro coinvolto nell'istruzione attuale            
    def trova_data_hazard(self, indice: int, lista_indice: list, istruzione_precedente: str, bool_saltato: bool, registro_da_controllare: registro.Registro, indice_riga_precedente: int, indice_riga_pre_precedente: int, bool_decode: bool, bool_analizza_con_esecuzione: bool):
        tupla_hazard = ""
        # Se l'istruzione precedente è di tipo branch e il salto si è fatto, allora
        # so che nella pipeline è presente almeno un control hazard e ancora prima l'istruzione branch. Le istruzioni branch analizzate
        # non cambiano i valori dei registri quindi non si verificano data hazard.
        if not (istruzione_precedente in self.istruzioni_branch and bool_saltato): # Escludo questo caso.
            if registro_da_controllare.istruzione_mips != "": # Trova dove sono gli stalli (riga a riga con registro)
                if indice_riga_precedente+1 == registro_da_controllare.riga_registro: # Cerca stalli causati da istruzione precedente
                    tupla_hazard = (registro_da_controllare.riga_registro,indice+1,registro_da_controllare.nome)
                    self.insieme_data_hazards.add(tupla_hazard)
                elif (lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch: # Caso standard con riga pre-precedente o con branch che decide il salto in fase di ID
                    # Evito di trovare stalli con jump se sto facendo l'analisi del testo in "trova_indirizzi_text" 
                    if indice_riga_pre_precedente+1 == registro_da_controllare.riga_registro and not (istruzione_precedente in self.istruzioni_jump and not bool_analizza_con_esecuzione): # Cerca stalli causati da istruzione pre-precedente
                        tupla_hazard = (registro_da_controllare.riga_registro,indice+1,registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard)
            if registro_da_controllare.istruzione_precedente != "" and ((lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch) :
                if indice_riga_pre_precedente+1 == registro_da_controllare.riga_precedente: # Cerca stalli causati da istruzione pre-precedente
                    if tupla_hazard != "": # nuovo data hazard trovato, ma non è quello trovato durante l'esecuzione 
                        tupla_hazard_aggiuntiva = (registro_da_controllare.riga_precedente,indice+1,registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard_aggiuntiva)
                    else:
                        tupla_hazard = (registro_da_controllare.riga_precedente,indice+1,registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard)
        return tupla_hazard
        
        # Il metodo si occupa di trovare data hazards, control hazards e mostrare come si comporta la pipeline (dizionario che viene usato per generare vari json file).
        # è influenzato da vari booleani precedentemente stabiliti (forwarding o meno, ecc...)
    def trova_valori_per_pipeline(self,istruzione_precedente: str, indice_riga_precedente: int, indice_riga_pre_precedente: int, valore_program_counter: int,totale_clocks: int, nome_registro_tonde: str, indice: int, lista_indice: list, 
                                  bool_salto: bool, bool_saltato: bool, data_hazards_totali: int, control_hazards_totali: int, control_hazards: int, bool_decode: bool, bool_forwarding: bool, bool_messaggi_hazards: bool, bool_analizza_con_esecuzione: bool):
        lista_valori_diz = {"Riga": 0, "Program Counter": 0, "Istruzione Mips": "", "Rappresentazione Pipeline": "", "Numero Bolle Data Hazard": 0, "Numero Bolle Control Hazard": 0, "Valore Clock": 0, "Hazard Trovato": [] }
        if bool_messaggi_hazards:
            lista_valori_diz["Messaggio"] = ""
        istruzione = ""
        riga = ""
        primo_registro_da_controllare = ""
        secondo_registro_da_controllare = ""
        registro_principale =""
        intero_stato_not_forwarding = 0
        intero_stato_forwarding = 0
        stalli_primo_registro_not_forwarding = 0
        stalli_secondo_registro_not_forwarding = 0
        stalli_primo_registro_forwarding = 0 
        stalli_secondo_registro_forwarding = 0
        tupla_hazard_primo_registro = ""
        tupla_hazard_secondo_registro = ""
        messaggio_data_hazards = ""
        conta_clocks = 0 # per numero clock a istruzione e non totali
        numero_hazards = 0 # per numero stalli
        for reg in self.insieme_registri:
            reg.cambia_fase()
            if control_hazards == 1:
                reg.cambia_fase() 
            if control_hazards == 2: # Caso branch in fase EX
                reg.cambia_fase()
                reg.cambia_fase() 
        totale_clocks += 1
        conta_clocks += 1
        riga = self.diz_righe[indice+1]
        lista_valori_diz["Riga"] = indice+1 # valore riga del codice mips
        lista_valori_diz["Program Counter"] = valore_program_counter # valore program counter (corretto solo se program counter abilitato)
        lista_valori_diz["Istruzione Mips"] = riga # codice mips in quella riga
        bool_branch = False
        if lista_indice[0] not in self.insieme_istruzioni:
            lista_indice = lista_indice[1:]
        # Controllo i casi jump e casi particolari come l'istruzione "jal" e "jalr"
        if lista_indice[0] in self.istruzioni_jump: # caso jump
            # Analisi casi jump
            if lista_indice[0] == "jal":
                for reg in self.insieme_registri:
                    if reg.nome == "$ra":
                        reg.decode = True
                        reg.execute = False
                        reg.memory = False
                        reg.write_back = False
                        if reg.istruzione_mips != "":
                            reg.istruzione_precedente = reg.istruzione_mips
                            reg.riga_precedente = reg.riga_registro
                        reg.istruzione_mips = lista_indice[0] # Passa per la memoria?
                        reg.riga_registro = indice+1
                        break
            if lista_indice[0] == "jalr": # Caso estremamente particolare
                if len(lista_indice) == 2:
                    jalr_len_due = True
                    for reg in self.insieme_registri:
                        if reg.nome == lista_indice[1] or reg.nome_numerico == lista_indice[1]:
                            primo_registro_da_controllare = reg
                            break
                else:
                    jalr_len_due = False
                    for reg in self.insieme_registri:
                        if reg.nome == lista_indice[2] or reg.nome_numerico == lista_indice[2]:
                            primo_registro_da_controllare = reg
                            break
                if primo_registro_da_controllare != "":                 
                    if not bool_forwarding:
                        if primo_registro_da_controllare.istruzione_mips != "":
                            stalli_primo_registro_not_forwarding = primo_registro_da_controllare.stato_write_back - primo_registro_da_controllare.stato_fase - intero_stato_not_forwarding
                            stalli_primo_registro_not_forwarding = max(stalli_primo_registro_not_forwarding, 0)
                    # Parte forwarding
                    else:
                        if primo_registro_da_controllare.istruzione_mips != "":
                            istruzione_registro = primo_registro_da_controllare.istruzione_mips
                            if  istruzione_registro in self.istruzioni_load and istruzione_registro != "la": # la si fa prima della memoria
                                stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 1 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding
                            else:
                                stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 2 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding
                            stalli_primo_registro_forwarding = max(stalli_primo_registro_forwarding, 0)
                                    
                    tupla_hazard_primo_registro = Simulatore.trova_data_hazard(self, indice, lista_indice, istruzione_precedente, bool_saltato, primo_registro_da_controllare, indice_riga_precedente, indice_riga_pre_precedente, bool_decode, bool_analizza_con_esecuzione)
                        
                    for reg in self.insieme_registri:
                        if not bool_forwarding:
                            if stalli_primo_registro_not_forwarding > 0:
                                for _ in range(0,stalli_primo_registro_not_forwarding):
                                    reg.cambia_fase()
                            else:
                                break
                        else:
                            if stalli_primo_registro_forwarding > 0:
                                for _ in range(0,stalli_primo_registro_not_forwarding):
                                    reg.cambia_fase()
                            else:
                                break
                if jalr_len_due:
                    for reg in self.insieme_registri:
                        if reg.nome == "$ra": # reset registro
                            reg.decode = True
                            reg.execute = False
                            reg.memory = False
                            reg.write_back = False
                            if reg.istruzione_mips != "":
                                reg.istruzione_precedente = reg.istruzione_mips
                                reg.riga_precedente = reg.riga_registro
                            reg.istruzione_mips = lista_indice[0]
                            reg.riga_registro = indice+1
                            break
                else:
                    for reg in self.insieme_registri:
                        if reg.nome == lista_indice[1]: # reset registro
                            reg.decode = True
                            reg.execute = False
                            reg.memory = False
                            reg.write_back = False
                            if reg.istruzione_mips != "":
                                reg.istruzione_precedente = reg.istruzione_mips
                                reg.riga_precedente = reg.riga_registro
                            reg.istruzione_mips = lista_indice[0]
                            reg.riga_registro = indice+1
                            break
            if not bool_forwarding:
                lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards = Simulatore.aggiorna_valori_pipeline(self, lista_valori_diz, control_hazards, stalli_primo_registro_not_forwarding, data_hazards_totali, totale_clocks, conta_clocks)
                
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_not_forwarding > 0:
                    lista_valori_diz = Simulatore.aggiorna_hazard_e_messaggi(self, lista_valori_diz, tupla_hazard_primo_registro, primo_registro_da_controllare, stalli_primo_registro_not_forwarding, bool_messaggi_hazards, bool_forwarding, bool_branch, bool_decode, messaggio_data_hazards)
                    
            else:
                lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards = Simulatore.aggiorna_valori_pipeline(self, lista_valori_diz, control_hazards, stalli_primo_registro_forwarding, data_hazards_totali, totale_clocks, conta_clocks)
                
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_forwarding > 0:
                    lista_valori_diz = Simulatore.aggiorna_hazard_e_messaggi(self, lista_valori_diz, tupla_hazard_primo_registro, primo_registro_da_controllare, stalli_primo_registro_forwarding, bool_messaggi_hazards, bool_forwarding, bool_branch, bool_decode, messaggio_data_hazards)
                        
            # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
            if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
                Simulatore.trova_istruzioni_e_bolle_in_pipeline(self, indice, indice_riga_precedente, istruzione_precedente, totale_clocks, riga, lista_valori_diz, bool_decode)
            
            self.conta_clocks += conta_clocks
            if control_hazards == 0 and bool_analizza_con_esecuzione:
                self.conta_data_hazards += numero_hazards
            else:
                if bool_analizza_con_esecuzione:
                    self.conta_control_hazards += control_hazards 
                    
            Simulatore.calcola_clocks_per_parte_loops(self, conta_clocks, indice)           
                                 
            return lista_valori_diz, totale_clocks, data_hazards_totali, control_hazards_totali
        
        # Controllo normale
        valore_tre = ""
        valore_due = ""
        valore_uno = ""
        if len(lista_indice) == 4:
            valore_tre = lista_indice[3]
            valore_due = lista_indice[2]
            valore_uno = lista_indice[1]
            istruzione = lista_indice[0]
        if len(lista_indice) == 3:
            valore_due = lista_indice[2]
            valore_uno = lista_indice[1]
            istruzione = lista_indice[0]
        if len(lista_indice) == 2:
            valore_uno = lista_indice[1]
            istruzione = lista_indice[0]
        # Controllo che tipo di istruzione viene trovata e i registri in prima e seconda posizione 
        # (da controllare perchè potrebbero causare data hazard, quindi stalli nella pipeline) 
        if istruzione in self.istruzioni_save:
            for reg in self.insieme_registri:
                if primo_registro_da_controllare != "" and secondo_registro_da_controllare != "":
                    break
                if reg.nome == nome_registro_tonde: # il nome è già cambiato al registro corretto
                    secondo_registro_da_controllare = reg
                if valore_uno in (reg.nome, reg.nome_numerico):
                    primo_registro_da_controllare = reg
        elif istruzione in self.istruzioni_load:
            for reg in self.insieme_registri:
                if registro_principale != "" and primo_registro_da_controllare != "":
                    break
                if reg.nome == nome_registro_tonde: # il nome è già cambiato al registro corretto
                    primo_registro_da_controllare = reg
                if valore_uno in (reg.nome, reg.nome_numerico):
                    registro_principale = reg
        elif istruzione in self.istruzioni_branch:
            bool_branch = True
            for reg in self.insieme_registri:
                if primo_registro_da_controllare != "" and secondo_registro_da_controllare != "":
                    break
                if valore_uno in (reg.nome, reg.nome_numerico):
                    primo_registro_da_controllare = reg
                if valore_due in (reg.nome, reg.nome_numerico):
                    secondo_registro_da_controllare = reg
            if bool_salto:
                if bool_decode:
                    control_hazards_totali += 1
                else:
                    control_hazards_totali += 2
        else:
            for reg in self.insieme_registri:
                if primo_registro_da_controllare != "" and secondo_registro_da_controllare != "" and registro_principale != "":
                    break
                if valore_uno in (reg.nome, reg.nome_numerico):
                    registro_principale = reg
                if valore_due in (reg.nome, reg.nome_numerico):
                    primo_registro_da_controllare = reg
                if valore_tre in (reg.nome, reg.nome_numerico):
                    secondo_registro_da_controllare = reg
                    
        if primo_registro_da_controllare != "": # Potrebbe succedere che abbiamo add $s1, $zero, $s2
            # Nel caso del registro $zero o $0 questi registri non sono inizializzati prima
            # In generale anche se avessi prima l'istruzione add $zero, $zero, $s2 in $zero rimane lo zero
            # e non si scrive di solito proprio perchè non cambia nulla
            # Quindi suppongo non crei stalli
            if bool_branch:
                if bool_decode:
                    intero_stato_forwarding = -1 # causa piu stalli
                else:
                    intero_stato_not_forwarding = 1 # causa meno stalli  
            # Parte not forwarding
            if not bool_forwarding:
                if primo_registro_da_controllare.istruzione_mips != "": # lo stato write back è lo stato in cui l'istruzione deve stare (write back deve essere allineata con decode della istruzione attuale), 
                    # quindi questo - lo stato del registro (stato dell'istruzione in cui faceva parte il registro l'ultima volta) ci dice quanti stalli ottengo. Se è una istruzione branch
                    # potrebbe essere write back allineata con execute (in sostanza meno stalli).
                    stalli_primo_registro_not_forwarding = primo_registro_da_controllare.stato_write_back - primo_registro_da_controllare.stato_fase - intero_stato_not_forwarding
                    stalli_primo_registro_not_forwarding = max(stalli_primo_registro_not_forwarding, 0)
            # Parte forwarding
            else:
                if primo_registro_da_controllare.istruzione_mips != "": # lo stato write back non è piu lo stato in cui l'istruzione deve stare (execute o memory devono essere allineati con decode della istruzione attuale), 
                    # quindi questo - lo stato del registro (stato dell'istruzione in cui faceva parte il registro l'ultima volta) ci dice quanti stalli ottengo. Se è una istruzione branch
                    # potrebbe essere execute o memory allineata con decode o fetch (in sostanza più stalli).
                    istruzione_registro = primo_registro_da_controllare.istruzione_mips
                    if istruzione_registro in self.istruzioni_load and istruzione_registro != "la": # la si fa prima della memoria
                        stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 1 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding 
                        if istruzione in self.istruzioni_save: # riduco di 1 in quanto passo direttamente il valore alla memoria per le istruzioni store
                            stalli_primo_registro_forwarding -= 1 
                    else:
                        stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 2 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding
                    stalli_primo_registro_forwarding = max(stalli_primo_registro_forwarding, 0)
    
            tupla_hazard_primo_registro = Simulatore.trova_data_hazard(self, indice, lista_indice, istruzione_precedente, bool_saltato, primo_registro_da_controllare, indice_riga_precedente, indice_riga_pre_precedente, bool_decode, bool_analizza_con_esecuzione)
                        
                        
        if secondo_registro_da_controllare != "": # Potrebbe succedere che abbiamo add $s1, $zero, $s2
            # Nel caso del registro $zero o $0 questi registri non sono inizializzati prima
            # In generale anche se avessi prima l'istruzione add $zero, $zero, $s2 in $zero rimane lo zero
            # e non si scrive di solito proprio perchè non cambia nulla
            # Quindi suppongo non crei stalli
            if bool_branch:
                if bool_decode:
                    intero_stato_forwarding = -1
                else:
                    intero_stato_not_forwarding = 1
            # Parte not forwarding
            if not bool_forwarding:
                if secondo_registro_da_controllare.istruzione_mips != "":
                    stalli_secondo_registro_not_forwarding = secondo_registro_da_controllare.stato_write_back - secondo_registro_da_controllare.stato_fase - intero_stato_not_forwarding
                    stalli_secondo_registro_not_forwarding = max(stalli_secondo_registro_not_forwarding, 0)
            # Parte forwarding
            else:
                if secondo_registro_da_controllare.istruzione_mips != "":
                    istruzione_registro = secondo_registro_da_controllare.istruzione_mips
                    if  istruzione_registro in self.istruzioni_load:
                        stalli_secondo_registro_forwarding = secondo_registro_da_controllare.stato_write_back - 1 - secondo_registro_da_controllare.stato_fase - intero_stato_forwarding  
                    else:
                        stalli_secondo_registro_forwarding = secondo_registro_da_controllare.stato_write_back - 2 - secondo_registro_da_controllare.stato_fase - intero_stato_forwarding
                    stalli_secondo_registro_forwarding = max(stalli_secondo_registro_forwarding, 0)
                        
            tupla_hazard_secondo_registro = Simulatore.trova_data_hazard(self, indice, lista_indice, istruzione_precedente, bool_saltato, secondo_registro_da_controllare, indice_riga_precedente, indice_riga_pre_precedente, bool_decode, bool_analizza_con_esecuzione)
            
        if not bool_forwarding:
            if stalli_primo_registro_not_forwarding >= stalli_secondo_registro_not_forwarding:
                lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards = Simulatore.aggiorna_valori_pipeline(self, lista_valori_diz, control_hazards, stalli_primo_registro_not_forwarding, data_hazards_totali, totale_clocks, conta_clocks)
                
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_not_forwarding > 0:
                    lista_valori_diz = Simulatore.aggiorna_hazard_e_messaggi(self, lista_valori_diz, tupla_hazard_primo_registro, primo_registro_da_controllare, stalli_primo_registro_not_forwarding, bool_messaggi_hazards, bool_forwarding, bool_branch, bool_decode, messaggio_data_hazards)
                              
            else:
                lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards = Simulatore.aggiorna_valori_pipeline(self, lista_valori_diz, control_hazards, stalli_secondo_registro_not_forwarding, data_hazards_totali, totale_clocks, conta_clocks)
                
                if tupla_hazard_secondo_registro != "" and stalli_secondo_registro_not_forwarding > 0:
                    lista_valori_diz = Simulatore.aggiorna_hazard_e_messaggi(self, lista_valori_diz, tupla_hazard_secondo_registro, secondo_registro_da_controllare, stalli_secondo_registro_not_forwarding, bool_messaggi_hazards, bool_forwarding, bool_branch, bool_decode, messaggio_data_hazards)
                    
        else:    
            if stalli_primo_registro_forwarding >= stalli_secondo_registro_forwarding:
                lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards = Simulatore.aggiorna_valori_pipeline(self, lista_valori_diz, control_hazards, stalli_primo_registro_forwarding, data_hazards_totali, totale_clocks, conta_clocks)
                
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_forwarding > 0:
                    lista_valori_diz = Simulatore.aggiorna_hazard_e_messaggi(self, lista_valori_diz, tupla_hazard_primo_registro, primo_registro_da_controllare, stalli_primo_registro_forwarding, bool_messaggi_hazards, bool_forwarding, bool_branch, bool_decode, messaggio_data_hazards)
                    
            else:
                lista_valori_diz, data_hazards_totali, totale_clocks, conta_clocks, numero_hazards = Simulatore.aggiorna_valori_pipeline(self, lista_valori_diz, control_hazards, stalli_secondo_registro_forwarding, data_hazards_totali, totale_clocks, conta_clocks)
                
                if tupla_hazard_secondo_registro != "" and stalli_secondo_registro_forwarding > 0:
                    lista_valori_diz = Simulatore.aggiorna_hazard_e_messaggi(self, lista_valori_diz, tupla_hazard_secondo_registro, secondo_registro_da_controllare, stalli_secondo_registro_forwarding, bool_messaggi_hazards, bool_forwarding, bool_branch, bool_decode, messaggio_data_hazards)
                    
        for reg in self.insieme_registri:
            if not bool_forwarding:
                if stalli_primo_registro_not_forwarding >= stalli_secondo_registro_not_forwarding and stalli_primo_registro_not_forwarding > 0:
                    for _ in range(0,stalli_primo_registro_not_forwarding):
                        reg.cambia_fase()
                elif stalli_secondo_registro_not_forwarding > stalli_primo_registro_not_forwarding:
                    for _ in range(0,stalli_secondo_registro_not_forwarding):
                        reg.cambia_fase()
                else:
                    break
            else:
                if stalli_primo_registro_forwarding >= stalli_secondo_registro_forwarding and stalli_primo_registro_forwarding > 0:
                    for _ in range(0,stalli_primo_registro_forwarding):
                        reg.cambia_fase()
                elif stalli_secondo_registro_forwarding > stalli_primo_registro_forwarding:
                    for _ in range(0,stalli_secondo_registro_forwarding):
                        reg.cambia_fase()
                else:
                    break
        if registro_principale != "": # reset per il registro modificato in questa istruzione
            # non c'é necessita di cambiare lo stato in quanto cambiera alla prossima istruzione
            registro_principale.decode = True
            registro_principale.execute = False
            registro_principale.memory = False
            registro_principale.write_back = False
            if registro_principale.istruzione_mips != "":
                registro_principale.istruzione_precedente = registro_principale.istruzione_mips
                registro_principale.riga_precedente = registro_principale.riga_registro
            registro_principale.istruzione_mips = lista_indice[0] 
            registro_principale.riga_registro = indice+1
            
         # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
        if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
            Simulatore.trova_istruzioni_e_bolle_in_pipeline(self, indice, indice_riga_precedente, istruzione_precedente, totale_clocks, riga, lista_valori_diz, bool_decode)
                 
        self.conta_clocks += conta_clocks
        if control_hazards == 0 and bool_analizza_con_esecuzione:
            self.conta_data_hazards += numero_hazards
        else:
            if bool_analizza_con_esecuzione:
                self.conta_control_hazards += control_hazards 
                       
        Simulatore.calcola_clocks_per_parte_loops(self, conta_clocks, indice)             
        
        return lista_valori_diz, totale_clocks, data_hazards_totali, control_hazards_totali   
    
    # Il metodo si occupa di instanziare i registri, ovvero inizializzare i registri che sono effettivamente nel testo di codice.
    # Potrei crearli direttamente tutti, ma siccome potrebbero non essere usati preferisco questo approccio.
    # Viene inoltre restituito il nome del registro dentro alle parentesi tonde (se non viene trovato si restituisce la stringa vuota)
    
    def crea_registri(self, lista_riga: list):
        registro_trovato = False
        nome_registro = ""
        nome_numerico = ""
        if len(lista_riga) == 3:
            if lista_riga[1].startswith(self.dollaro) and lista_riga[1][1] in self.iniziali_registri:
                registro_trovato = any(reg.nome == lista_riga[1] or reg.nome_numerico == lista_riga[1] for reg in self.insieme_registri)
                if not registro_trovato:
                    if lista_riga[1][1] in self.iniziali_registri_numerici:
                        nuovo_registro = registro.Registro(self.diz_numero_registri[lista_riga[1]], 0, lista_riga[1])
                    else:
                        for chiave, valore_diz in self.diz_numero_registri.items():
                            if valore_diz == lista_riga[1]:
                                nome_numerico = chiave
                                break 
                        nuovo_registro = registro.Registro(lista_riga[1], 0, nome_numerico)
                        nome_numerico = ""
                    self.insieme_registri.add(nuovo_registro)
            if lista_riga[2].startswith(self.dollaro) and lista_riga[2][1] in self.iniziali_registri: # in posizione superiore a 1
                # il registro non è stato usato prima e quindi lo stato corretto è write back 
                registro_trovato = any(reg.nome == lista_riga[2] or reg.nome_numerico == lista_riga[2] for reg in self.insieme_registri)
                if not registro_trovato:
                    if lista_riga[2][1] in self.iniziali_registri_numerici:
                        nuovo_registro = registro.Registro(self.diz_numero_registri[lista_riga[2]], 0, lista_riga[2])
                    else:
                        for chiave, valore_diz in self.diz_numero_registri.items():
                            if valore_diz == lista_riga[2]:
                                nome_numerico = chiave
                                break 
                        nuovo_registro = registro.Registro(lista_riga[2], 0, nome_numerico)
                        nome_numerico = ""
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro)
            elif self.aperta_tonda in lista_riga[2]: # Caso ($a0)
                registro_trovato = False
                nome_registro = lista_riga[2][lista_riga[2].index(self.aperta_tonda)+1: lista_riga[2].index(self.chiusa_tonda)]
                for reg in self.insieme_registri:
                    if nome_registro in (reg.nome, reg.nome_numerico):
                        registro_trovato = True
                        if reg.nome_numerico == nome_registro:
                            nome_registro = reg.nome # Voglio che sia il nome del registro (non valore numerico)
                        break
                if not registro_trovato:
                    if nome_registro[1] in self.iniziali_registri_numerici:
                        nuovo_registro = registro.Registro(self.diz_numero_registri[nome_registro], 0, nome_registro)
                        nome_registro = self.diz_numero_registri[nome_registro]
                    else:
                        for chiave, valore_diz  in self.diz_numero_registri.items():
                            if valore_diz == nome_registro:
                                nome_numerico = chiave
                                break 
                        nuovo_registro = registro.Registro(nome_registro, 0, nome_numerico)
                        nome_numerico = ""
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro)       
        if len(lista_riga) == 4: # al massimo ci sono 4 posizioni --> add $t1, $t2, $t3
            if lista_riga[1].startswith(self.dollaro) and lista_riga[1][1] in self.iniziali_registri:
                registro_trovato = any(reg.nome == lista_riga[1] or reg.nome_numerico == lista_riga[1] for reg in self.insieme_registri)
                if not registro_trovato:
                    if lista_riga[1][1] in self.iniziali_registri_numerici:
                        nuovo_registro = registro.Registro(self.diz_numero_registri[lista_riga[1]], 0, lista_riga[1])
                    else:
                        for chiave, valore_diz in self.diz_numero_registri.items():
                            if valore_diz == lista_riga[1]:
                                nome_numerico = chiave
                                break 
                        nuovo_registro = registro.Registro(lista_riga[1], 0, nome_numerico)
                        nome_numerico = ""
                    self.insieme_registri.add(nuovo_registro)
            if lista_riga[2].startswith(self.dollaro) and lista_riga[2][1] in self.iniziali_registri: # in posizione superiore a 1
                # il registro non è stato usato prima e quindi lo stato corretto è write back 
                registro_trovato = any(reg.nome == lista_riga[2] or reg.nome_numerico == lista_riga[2] for reg in self.insieme_registri)
                if not registro_trovato:
                    if lista_riga[2][1] in self.iniziali_registri_numerici:
                        nuovo_registro = registro.Registro(self.diz_numero_registri[lista_riga[2]], 0, lista_riga[2])
                    else:
                        for chiave, valore_diz in self.diz_numero_registri.items():
                            if valore_diz == lista_riga[2]:
                                nome_numerico = chiave
                                break 
                        nuovo_registro = registro.Registro(lista_riga[2], 0, nome_numerico)
                        nome_numerico = ""
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro)
            if lista_riga[3].startswith(self.dollaro) and lista_riga[3][1] in self.iniziali_registri: # in posizione superiore a 1
                # il registro è stato usato prima e quindi lo stato corretto è write back 
                registro_trovato = any(reg.nome == lista_riga[3] or reg.nome_numerico == lista_riga[3] for reg in self.insieme_registri)
                if not registro_trovato:
                    if lista_riga[3][1] in self.iniziali_registri_numerici: 
                        nuovo_registro = registro.Registro(self.diz_numero_registri[lista_riga[3]], 0, lista_riga[3])
                    else:
                        for chiave, valore_diz in self.diz_numero_registri.items():
                            if valore_diz == lista_riga[3]:
                                nome_numerico = chiave
                                break 
                        nuovo_registro = registro.Registro(lista_riga[3], 0, nome_numerico)
                        nome_numerico = "" 
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro)
        return nome_registro    
        
    # Il metodo si occupa di passare i valori dei caratteri delle stringhe ascii nel dizionario che simula la memoria
    # Sono stati valutati certi caratteri speciali (esempio '\n' o \t' ecc....) che non venivano letti correttamente
    # viene restituita la chiave (ossia l'indirizzo attuale del dizionario che simula la memoria)
    def aggiorna_diz_memoria_ascii_asciiz(self, stringa_valore, chiave, carattere_slash, diz_slash):
        conta_slash = 0
        for carattere in stringa_valore:
            if carattere == carattere_slash:
                conta_slash += 1
                if conta_slash == 2 or carattere == stringa_valore[-1]:
                    chiave += 1
                    self.istruzioni.diz_dati[chiave] = ord(carattere_slash)
                    conta_slash = 1
                continue
            if conta_slash == 1:
                conta_slash = 0
                chiave += 1
                if carattere in diz_slash:
                    self.istruzioni.diz_dati[chiave] = diz_slash[carattere] # funzione ord passata al dizionario
                else: # Se non riesco allora non do errore, ma il valore non sarà corretto, dipende dai valori del dizionario
                    self.istruzioni.diz_dati[chiave] = ord(carattere)      
            else:
                chiave += 1
                self.istruzioni.diz_dati[chiave] = ord(carattere) 
        return chiave
    
    # Il metodo si occupa di aggiornare il dizionario che simula la memoria con i dati passati in input (parte .data)
    # I dati analizzati per questo metodo sono di tipo word
    # viene restituita la chiave (ossia l'indirizzo attuale del dizionario che simula la memoria)
    def aggiorna_diz_memoria_word(self, valore_in_lista: str, chiave: int):
        aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
        valore_in_lista = self.zero*aggiungi_zeri + valore_in_lista 
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-2:],16)
        chiave += 1
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-4:-2],16)
        chiave += 1
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-6:-4],16)
        chiave += 1
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-8:-6],16)
        return chiave
    
    # Il metodo si occupa di aggiornare il dizionario che simula la memoria con i dati passati in input (parte .data)
    # I dati analizzati per questo metodo sono di tipo half
    # viene restituita la chiave (ossia l'indirizzo attuale del dizionario che simula la memoria)
    def aggiorna_diz_memoria_half(self, valore_in_lista: str, chiave: int):
        aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
        valore_in_lista = self.zero*aggiungi_zeri + valore_in_lista
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-2:],16)
        chiave += 1
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-4:-2],16) 
        return chiave
    
    # Il metodo si occupa di aggiornare il dizionario che simula la memoria con i dati passati in input (parte .data)
    # I dati analizzati per questo metodo sono di tipo byte
    def aggiorna_diz_memoria_byte(self, valore_in_lista: str, chiave: int):
        self.istruzioni.diz_dati[chiave] = int(valore_in_lista[-2:],16)
        
 
    # Il metodo si occupa di simulare l'esecuzione del codice mips.
    # Viene simulata la memoria tramite un dizionario inizializzato nella classe Istruzioni.
    # Qui viene aggiornato tale dizionario con gli indirizzi trovati nella sezione .data di mars.
    # Ma istruzioni save o load possono pure aumentare la dimensione del dizionario.
    # Ogni lista associata alla lista di liste ottenuta con modifica_testo viene analizzata.
    # In particolare ogni elemento della lista viene analizzato per capire se è un istruzione, un registro o un nome di testo ("Cycl", "main", "Exit").
    # Viene poi chiamata l'istruzione della classe Istruzioni corrispondente all'istruzione mips trovata.
    # E infine viene simulata la pipeline per quella specifica riga.
    # Otteniamo cosi due dizionari con tutti i dati.
    # (Il valore del program counter viene aggiornato per ogni istruzione trovata)
     
    def simula_codice_mips(self, testo: str, bool_decode: bool, bool_forwarding: bool, bool_program_counter: bool, bool_messaggi_hazards: bool, ciclo_di_clock: int):
        self.testo = testo
        Simulatore.modifica_testo(self)
        # print(self.testo_modificato)
        self.istruzioni.bool_program_counter = bool_program_counter
        self.bool_forwarding = bool_forwarding
        self.ciclo_di_clock = ciclo_di_clock
        # i reset dei registri at e ra avvengono nel seguente metodo (non serve farlo prima)
        Simulatore.trova_indirizzi_text_e_salti(self, bool_decode)
        diz_pipeline = {}
        diz_hazards = {}
        if ciclo_di_clock != 0:
            diz_hazards = {"IF": "Nessuna istruzione", "ID": "Nessuna istruzione", "EX": "Nessuna istruzione", "MEM": "Nessuna istruzione", "WB": "Nessuna istruzione"}
        self.diz_hazards = diz_hazards
        chiave_diz_ris = 1
        indice = 0
        aggiungi_dati = False
        diz_dati = self.istruzioni.diz_dati
        chiave = 268500991
        indirizzo_iniziale = 268500992 
        indirizzo_finale = 268500992
        intero_at = indirizzo_iniziale
        intero_at_text = 4194304
        nome_at = "$at"
        pc = self.istruzioni.pc
        diz_indirizzi_text = self.istruzioni.diz_indirizzi_text
        diz_text = self.istruzioni.diz_text
        nome_registro = "" 
        valore_posizione = 0
        istruzione_mips = ""
        not_in_range = True
        prima_posizione = ""
        seconda_posizione = ""
        terza_posizione = ""
        stringa_salto = ""
        self.carattere_virgoletta = "'"
        stringa_valore_intero = ""
        registro_trovato = False
        stringa_tipo = ""
        valore_program_counter = ""
        tipo_word = ".word"
        tipo_half = ".half"
        tipo_asciiz = ".asciiz"
        tipo_ascii = ".ascii"
        insieme_byte_ascii = {".byte",".ascii",".asciiz"}
        carattere_slash = '\\'
        dizionario_slash = {'n':ord('\n'),'r':ord('\r'),'t':ord('\t'),'b':ord('\b'),'f':ord('\f')}
        chiave_indirizzi = ""
        controlla_len = 0
        istruzione_precedente = ""
        indice_riga_precedente = -1
        indice_riga_pre_precedente = -1
        bool_salto = False
        bool_saltato = False
        bool_analizza_con_esecuzione = True
        totale_clocks = 4
        self.conta_clocks = 4 # Reset necessario
        data_hazards_totali = 0
        control_hazards = 0
        control_hazards_totali = 0 
        tupla_control_hazards = ""
        messaggio_hazards = ""
        messaggio_hazard_inizio = "È presente uno stallo dovuto a un control hazard perchè la condizione dell'istruzione branch '"
        messaggio_due_hazard_inizio = "Sono presenti due stalli dovuti a un control hazard perchè la condizione dell'istruzione branch '"
        aggiorna_loops_prossima_riga = False
        stringa_loops = "" # Usata per i loops se si salta (non fa lo stesso di stringa_salto)
        
        for reg in self.insieme_registri: # Faccio un reset dei registri in quanto ho generato i registri e simulato 
            # il ritrovamento di possibili stalli durante la lettura del testo. 
            reg.vai_a_writeback()
            reg.riga_registro = ""
            reg.riga_precedente = ""
            reg.istruzione_mips = ""
            reg.istruzione_precedente = ""
        
        # Comincia la simulazione del codice
        while indice < len(self.testo_modificato):
            indice_secondario = 0
            for valore in self.testo_modificato[indice]:
                if self.testo_modificato[indice][0].startswith(self.commento):
                    break
                if self.testo_modificato[indice][0].startswith(self.punto):
                    if valore == self.data:
                        aggiungi_dati = True
                    if valore == self.text:
                        aggiungi_dati = False
                        if chiave != indirizzo_iniziale - 1: # se avessi .text senza parte .data il valore 268500991 non va usato in indirizzo finale
                            indirizzo_finale = chiave
                        self.istruzioni.diz_dati = diz_dati
                    break
                # Aggiungo i valori dei dati trovati in .data
                if aggiungi_dati:  
                    if indice_secondario == 0:
                        chiave_vettori = valore
                        valore_in_lista = 0
                        if stringa_tipo != "":
                            if stringa_tipo in insieme_byte_ascii and self.testo_modificato[indice][1] == tipo_word:
                                
                                # L'allineamento dei dati in memoria è importante
                                # Le word e half vogliono indirizzi pari (multiplo di 4 per word) mentre ascii,asciiz e byte possono avere indirizzi dispari
                                # La differenza tra l'indirizzo attuale e l'indirizzo iniziale deve risultare un multiplo di quattro (4 byte a parola per un allineamento corretto)
                                # Aumento da una a tre chiavi se la differenza non risulta un multiplo 
                                if (chiave + 1) % 2 != 0: # Voglio che il valore sia sempre dispari
                                    chiave += 1
                                    diz_dati[chiave] = 0 
                                controlla_len = (chiave - indirizzo_iniziale)% 4
                                if controlla_len != 0:
                                    controlla_len = 4 - controlla_len
                                for _ in range(0,controlla_len):
                                    chiave += 1 
                                    diz_dati[chiave] = 0
                            elif stringa_tipo in insieme_byte_ascii and self.testo_modificato[indice][1] == tipo_half:
                                if (chiave + 1) % 2 != 0: 
                                    chiave += 1
                                    diz_dati[chiave] = 0
                            elif stringa_tipo == tipo_half and self.testo_modificato[indice][1] == tipo_word:
                                if (chiave + 1) % 2 != 0: 
                                    chiave += 1
                                    diz_dati[chiave] = 0 
                                controlla_len = (chiave - indirizzo_iniziale)% 4
                                if controlla_len != 0:
                                    controlla_len = 4 - controlla_len
                                for _ in range(0,controlla_len):
                                    chiave += 1 
                                    diz_dati[chiave] = 0
                                     
                            if stringa_tipo in insieme_byte_ascii and self.testo_modificato[indice][1] in insieme_byte_ascii: 
                                self.diz_indirizzi[chiave_vettori] = chiave + 1 # Si possono avere anche valori dispari
                            else:
                                if (chiave) % 2 != 0:    
                                    self.diz_indirizzi[chiave_vettori] = chiave + 1  # Per indirizzo corretto
                                else:    
                                    self.diz_indirizzi[chiave_vettori] = chiave  # Per indirizzo corretto 
                                    chiave = chiave - 1 # Per inserire i valori nelle giuste posizioni in memoria (la chiave viene incrementata di uno quando aggiungo il valore)
                        else:
                            self.diz_indirizzi[chiave_vettori] = indirizzo_iniziale
                    # I valori in .data vengono convertiti in esadecimali e inseriti nel dizionario diz_dati
                    # l'esadecimale trovato potrebbe avere al massimo 8 posizioni
                    # Partendo da destra vengono inseriti , a coppie di due, i valori nel dizionario (un valore viene passato come intero che rappresenta il byte trovato)
                    # Non è un caso che siano due: un byte è rappresentabile con due valori esadecimali
                    # Si parte da destra perchè a destra sono presenti i valori più piccoli
                    elif indice_secondario > 1: 
                        # Considero ogni valore possibile in input:
                        # Interi positivi e negativi, esadecimali positivi e negativi, caratteri e il tipo di dato (byte, ascii, asciiz, half, word)
                        # Ricordo che i valori interi positivi possono essere scritti seguiti dal + (+1 o +0x1) 
                        # Viene applicata la giusta conversione dei valori per avere numeri di al massimo 8 esadecimali
                        if len(valore) == 1:
                            if stringa_tipo == tipo_word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_word(self, valore_in_lista, chiave)
                            elif stringa_tipo == tipo_half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_half(self, valore_in_lista, chiave)             
                            elif stringa_tipo == tipo_asciiz:
                                chiave += 1
                                diz_dati[chiave] = ord(valore)
                                chiave += 1
                                diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == tipo_ascii:
                                chiave += 1
                                diz_dati[chiave] = ord(valore)
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                Simulatore.aggiorna_diz_memoria_byte(self, valore_in_lista, chiave)
                        elif valore.startswith(self.zero_x) or valore.startswith(self.meno_zero_x) or valore.startswith(self.piu_zero_x):
                            if stringa_tipo == tipo_word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore,16),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_word(self, valore_in_lista, chiave)
                            elif stringa_tipo == tipo_half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore,16),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_half(self, valore_in_lista, chiave)             
                            elif stringa_tipo == tipo_asciiz:
                                chiave = Simulatore.aggiorna_diz_memoria_ascii_asciiz(self, valore, chiave, carattere_slash, dizionario_slash)
                                chiave += 1
                                diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == tipo_ascii:
                                chiave = Simulatore.aggiorna_diz_memoria_ascii_asciiz(self, valore, chiave, carattere_slash, dizionario_slash)
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore,16),32)[2:] # escludo 0x
                                Simulatore.aggiorna_diz_memoria_byte(self, valore_in_lista, chiave)               
                        elif valore.isdigit() or valore[1:].isdigit(): # Per interi sia positivi che negativi
                            if stringa_tipo == tipo_word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_word(self, valore_in_lista, chiave)
                            elif stringa_tipo == tipo_half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_half(self, valore_in_lista, chiave)             
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                Simulatore.aggiorna_diz_memoria_byte(self, valore_in_lista, chiave)
                        elif valore[0] == self.carattere_virgoletta and valore[-1] == self.carattere_virgoletta: # è un carattere
                            if stringa_tipo == tipo_word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(ord(valore[1]),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_word(self, valore_in_lista, chiave)
                            elif stringa_tipo == tipo_half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(ord(valore[1]),32)[2:] # escludo 0x
                                chiave = Simulatore.aggiorna_diz_memoria_half(self, valore_in_lista, chiave)             
                            elif stringa_tipo == tipo_asciiz: # Potrebbe succedere 
                                chiave = Simulatore.aggiorna_diz_memoria_ascii_asciiz(self, valore, chiave, carattere_slash, dizionario_slash)
                                chiave += 1
                                diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == tipo_ascii: # Potrebbe succedere 
                                chiave = Simulatore.aggiorna_diz_memoria_ascii_asciiz(self, valore, chiave, carattere_slash, dizionario_slash)
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(ord(valore[1]),32)[2:] # escludo 0x
                                Simulatore.aggiorna_diz_memoria_byte(self, valore_in_lista, chiave)
                        else:
                            if stringa_tipo == tipo_asciiz:
                                chiave = Simulatore.aggiorna_diz_memoria_ascii_asciiz(self, valore, chiave, carattere_slash, dizionario_slash)
                                chiave += 1
                                diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == tipo_ascii: 
                                chiave = Simulatore.aggiorna_diz_memoria_ascii_asciiz(self, valore, chiave, carattere_slash, dizionario_slash)
                    else:
                        stringa_tipo = valore
                        if stringa_tipo == tipo_asciiz and indice_secondario == len(self.testo_modificato[indice])-1:
                            chiave += 1
                            diz_dati[chiave] = 0 # Per stringa vuota aggiungiamo il terminatore 0 
                    indice_secondario += 1 
                    continue
                if aggiorna_loops_prossima_riga: # loop caso particolare
                    self.reset_calcolo_loop = True
                    aggiorna_loops_prossima_riga = False
                if valore in self.diz_salti and indice_secondario != len(self.testo_modificato[indice])-1 or len(self.testo_modificato[indice]) == 1:
                     # Risolviamo possibili problemi legati ai salti
                     # Analizzo l'istruzione particolare syscall
                     # Aggiungo un ciclo di clock (Si suppone che l'istruzione syscall non causi stalli)
                     # Dopo controllo se la syscall é da inserire nella pipeline (soluzione d'esercizio di esame, punto 5)
                    if len(self.testo_modificato[indice]) == 1: 
                        if valore == self.syscall:
                            totale_clocks += 1
                            totale_clocks += control_hazards
                            self.conta_clocks += 1
                            conta_clocks = 1+control_hazards
                            Simulatore.calcola_clocks_per_parte_loops(self, conta_clocks, indice)
                            pc.intero += 4
                            valore_program_counter = pc.intero
                            
                            diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": valore_program_counter, "Istruzione Mips": valore, "Rappresentazione Pipeline": self.stringa_bolla*control_hazards+self.stringa_pipeline, "Numero Bolle Data Hazard": 0, "Numero Bolle Control Hazard": control_hazards, "Valore Clock": totale_clocks, "Hazard Trovato": [] }
                            # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
                            if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
                                Simulatore.trova_istruzioni_e_bolle_in_pipeline(self, indice, indice_riga_precedente, istruzione_mips, totale_clocks, self.syscall, diz_pipeline[chiave_diz_ris], bool_decode)
                                
                            if bool_messaggi_hazards:
                                diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                            if tupla_control_hazards != "":
                                diz_pipeline[chiave_diz_ris]["Hazard Trovato"] = tupla_control_hazards
                                riga_branch = str(tupla_control_hazards[0])
                                tupla_control_hazards = ""
                                if bool_messaggi_hazards:
                                    if bool_decode:
                                        messaggio_hazards = messaggio_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta"
                                    else:
                                        messaggio_hazards = messaggio_due_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta. L'istruzione branch ha deciso il salto in fase di EX e non in fase di ID quindi ci sono due stalli."
                                    diz_pipeline[chiave_diz_ris]["Messaggio"] = messaggio_hazards
                            control_hazards = 0 # Reset perchè non eseguo il resto del codice
                            indice_riga_pre_precedente = indice_riga_precedente
                            indice_riga_precedente = indice
                        else:
                            diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": 0, "Istruzione Mips": valore, "Rappresentazione Pipeline": "Nessuna istruzione in questa riga", "Numero Bolle Data Hazard": 0, "Numero Bolle Control Hazard": 0, "Valore Clock": 0, "Hazard Trovato": [] } # riga come Q: (nessuna riga di codice)
                            if bool_messaggi_hazards:
                                diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                            if valore in self.diz_loops:
                                if (stringa_loops == "" and not self.diz_loops[valore][1]) or (valore == stringa_loops):
                                    self.valore_loop = valore # dovrebbe essere il label di testo
                                    aggiorna_loops_prossima_riga = True
                            else:
                                stringa_loops = "" # Reset necessario in certi casi
                        chiave_diz_ris += 1
                    else:
                        if self.testo_modificato[indice][1] not in self.insieme_istruzioni: # Caso syscall ma del tipo "Cycl: syscall", con nome di testo accanto
                            # Stesso ragionamento utilizzato nel caso syscall normale , analizzo la syscall
                            # Uso self.diz_righe[indice+1] per la riga corretta (in questo caso è del tipo "Cycl: syscall" e non solo "syscall")
                            if self.testo_modificato[indice][1] == self.syscall:
                                totale_clocks += 1
                                totale_clocks += control_hazards
                                self.conta_clocks += 1
                                conta_clocks = 1+control_hazards
                                Simulatore.calcola_clocks_per_parte_loops(self, conta_clocks, indice)
                                pc.intero += 4
                                valore_program_counter = pc.intero
                                
                                diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": valore_program_counter, "Istruzione Mips": self.diz_righe[indice+1], "Rappresentazione Pipeline": self.stringa_bolla*control_hazards+self.stringa_pipeline, "Numero Bolle Data Hazard": 0, "Numero Bolle Control Hazard": control_hazards, "Valore Clock": totale_clocks, "Hazard Trovato": [] }
                                # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
                                if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
                                    Simulatore.trova_istruzioni_e_bolle_in_pipeline(self, indice, indice_riga_precedente, istruzione_mips, totale_clocks, self.diz_righe[indice+1], diz_pipeline[chiave_diz_ris], bool_decode)
                                    
                                if bool_messaggi_hazards:
                                    diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                                if tupla_control_hazards != "":
                                    diz_pipeline[chiave_diz_ris]["Hazard Trovato"] = tupla_control_hazards
                                    riga_branch = str(tupla_control_hazards[0])
                                    tupla_control_hazards = ""
                                    if bool_messaggi_hazards:
                                        if bool_decode:
                                            messaggio_hazards = messaggio_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta"
                                        else:
                                            messaggio_hazards = messaggio_due_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta. L'istruzione branch ha deciso il salto in fase di EX e non in fase di ID quindi ci sono due stalli"
                                        diz_pipeline[chiave_diz_ris]["Messaggio"] = messaggio_hazards
                                if valore in self.diz_loops: # loop syscall
                                    if (stringa_loops == "" and not self.diz_loops[valore][1]) or (valore == stringa_loops):
                                        self.reset_calcolo_loop = True
                                        self.valore_loop = valore
                                control_hazards = 0 # Reset perchè non eseguo il resto del codice
                                indice_riga_pre_precedente = indice_riga_precedente
                                indice_riga_precedente = indice
                                chiave_diz_ris += 1
                                break
                            else: # Caso non implementato correttamente (non dovrebbe mai succedere)
                                # diz_pipeline[chiave_diz_ris] = [indice+1,valore] # riga come Q: (nessuna riga di codice)
                                diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": 0, "Istruzione Mips": valore, "Rappresentazione Pipeline": "Nessuna istruzione in questa riga", "Numero Bolle Data Hazard": 0, "Numero Bolle Control Hazard": 0, "Valore Clock": 0, "Hazard Trovato": [] } # riga come Q: (nessuna riga di codice)
                                if bool_messaggi_hazards:
                                    diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                                # if valore in self.diz_loops:
                                    # aggiorna_loops_prossima_riga = True
                                    # self.valore_loop = valore # potrebbe essere errato, non so cosa viene trovato qua
                            chiave_diz_ris += 1
                        else: # abbiamo nome testo più istruzione (per i loop nel codice)
                            if valore in self.diz_loops: # loop normalmente
                                # Considero se il loop è già iniziato e sta ricominciando (iterazione successiva) o se sta cominciando la prima iterazione
                                if (stringa_loops == "" and not self.diz_loops[valore][1]) or (valore == stringa_loops):
                                    self.reset_calcolo_loop = True
                                    self.valore_loop = valore
                    indice_secondario += 1 
                    continue
                # Se abbiamo una istruzione allora salvo l'istruzione
                # Successivamente verrà controllata la prima posizione
                # Consideriamo add $s1, $s2, $s3:
                # Salvo add, poi analizzo $s1, poi $s2 e poi $s3
                # Ogni posizione viene analizzata (gli input possono essere registri, interi, ecc...)
                if valore in self.insieme_istruzioni: # Controllo istruzione
                    istruzione_precedente = istruzione_mips
                    istruzione_mips = valore
                    valore_posizione = 1
                    indice_secondario += 1 
                    continue
                if valore.startswith(self.dollaro): # Controllo registri
                    if valore[1] in self.iniziali_registri:
                        for reg in self.insieme_registri:
                            if valore in (reg.nome, reg.nome_numerico): # Se il registro esiste già lo prendiamo dall'insieme
                                if valore_posizione == 1:
                                    prima_posizione = reg
                                    valore_posizione += 1
                                    break
                                if valore_posizione == 2:
                                    seconda_posizione = reg
                                    valore_posizione += 1
                                    break
                                if valore_posizione == 3:
                                    terza_posizione = reg
                                    break
                    else: # consideriamo $zero o $0 come valore numerico 0
                        if valore_posizione == 1:
                            prima_posizione = 0
                            valore_posizione += 1
                        elif valore_posizione == 2:
                            seconda_posizione = 0
                            valore_posizione += 1
                        elif valore_posizione == 3:
                            terza_posizione = 0
                else:
                    if valore_posizione == 1: # per istruzione j che vuole solo una stringa
                        if valore[0].isdigit(): # Da vedere se ci sono solo sempre registri
                            print("errore: numero in prima posizione")
                        else:
                            prima_posizione = valore
                            valore_posizione += 1 # mmm non credo serva ma per ora lascio stare
                    elif valore_posizione == 2: # Controllo seconda posizione
                        if (valore[0].isdigit() or valore[0] == self.meno or valore[0] == self.piu) and self.aperta_tonda not in valore: # Trovo un intero esadecimale o decimale 
                            stringa_corretta = valore
                            if stringa_corretta.startswith(self.piu):
                                stringa_corretta = stringa_corretta[1:] # rimuovo il + fastidioso
                            if stringa_corretta.startswith(self.zero_x) or stringa_corretta.startswith(self.meno_zero_x): # per esadecimali
                                seconda_posizione = istruzioni_mips.toint(int(stringa_corretta, 16))
                            else:
                                seconda_posizione = int(stringa_corretta)
                            # Vedo se si cerca di accedere alla memoria solo con un intero
                            if (istruzione_mips in self.istruzioni_load or istruzione_mips in self.istruzioni_save) and istruzione_mips != "la":       
                                if seconda_posizione <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                    not_in_range = False  
                                if not_in_range: # Simulo la memoria
                                    chiave = indirizzo_finale
                                    try:
                                        assert(seconda_posizione <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                    except AssertionError as messaggio_errore:
                                        print(messaggio_errore)
                                        sys.exit(1)  
                                    for _ in range(0,seconda_posizione - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                        chiave += 1
                                        diz_dati[chiave] = 0
                                    indirizzo_finale = chiave
                        else:
                            if valore in self.diz_indirizzi: # Caso indirizzi in .data
                                seconda_posizione = self.diz_indirizzi[valore] # passo l'indirizzo 
                                if seconda_posizione not in diz_dati: # Caso particolare dovuto ad avere una struttura dati ascii come ultimo valore. (potrebbe non essere più necessaria la condizione)
                                    diz_dati[seconda_posizione] = 0
                                    indirizzo_finale = seconda_posizione 
                                chiave_indirizzi = valore
                            elif valore in diz_text and istruzione_mips == "la": # deve accadere solo quando passo indirizzi a registri, altrimenti causa problemi con branch (branch tipo beqz che ha nome di testo in seconda posizione)
                                seconda_posizione = diz_text[valore]
                                chiave_indirizzi = valore
                            elif self.aperta_tonda in valore: # Caso con ()
                                nome_registro = valore[valore.index(self.aperta_tonda)+1: valore.index(self.chiusa_tonda)]
                                if nome_registro in self.diz_numero_registri:
                                    nome_registro = self.diz_numero_registri[nome_registro]
                                if valore[0] == self.aperta_tonda: # Consideriamo ($s7) per esempio
                                    registro_trovato = False 
                                    for reg in self.insieme_registri:
                                        if reg.nome == nome_registro:
                                            if reg.intero in diz_dati:         
                                                seconda_posizione = reg.intero
                                                if reg.intero <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                    not_in_range = False
                                            if not_in_range: # Simulo la memoria
                                                chiave = indirizzo_finale
                                                try:
                                                    assert(reg.intero <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                except AssertionError as messaggio_errore:
                                                    print(messaggio_errore)
                                                    sys.exit(1) 
                                                for _ in range(0,reg.intero - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                    chiave += 1
                                                    diz_dati[chiave] = 0
                                                seconda_posizione = reg.intero
                                                indirizzo_finale = chiave 
                                            registro_trovato = True
                                            break
                                    if not registro_trovato: # caso estremo (Non dovrebbe mai succedere)
                                        seconda_posizione = 0 # potrebbe essere $zero o un registro non inizializzato prima
                                else: # consideriamo array($s7) o 1($s7) o 'r'($s7) per esempio
                                    registro_trovato = False
                                    for elem in valore:
                                        if elem == self.aperta_tonda:
                                            break
                                        stringa_valore_intero += elem
                                    if stringa_valore_intero.startswith(self.piu): # potrei avere +5($s7), quel piu lo rimuovo
                                        stringa_valore_intero = stringa_valore_intero[1:]
                                    chiave_vettori = valore[0:valore.index(self.aperta_tonda)]
                                    for reg in self.insieme_registri:
                                        if reg.nome == nome_registro:
                                            if stringa_valore_intero.isdigit() or stringa_valore_intero[0] == self.carattere_virgoletta or stringa_valore_intero[0] == self.meno or stringa_valore_intero.startswith(self.zero_x): # ho trovato 1($s7)
                                                if stringa_valore_intero.startswith(self.zero_x) or stringa_valore_intero.startswith(self.meno_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == self.carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if reg.intero + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potrei simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = reg.intero + intero_stringa
                                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                                elif reg.intero + intero_stringa in diz_dati:
                                                    seconda_posizione = reg.intero + intero_stringa
                                                    if reg.intero + intero_stringa <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                        not_in_range = False
                                                if not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    try:
                                                        assert(reg.intero + intero_stringa <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                    except AssertionError as messaggio_errore:
                                                        print(messaggio_errore)
                                                        sys.exit(1)            
                                                    for _ in range(0,reg.intero + intero_stringa - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = reg.intero + intero_stringa
                                                    indirizzo_finale = chiave
                                            elif self.piu in stringa_valore_intero: # ho trovato array+100($s7)
                                                chiave_vettori = stringa_valore_intero[0:stringa_valore_intero.index(self.piu)]
                                                stringa_valore_intero = stringa_valore_intero[stringa_valore_intero.index(self.piu)+1:]
                                                if stringa_valore_intero.startswith(self.zero_x) or stringa_valore_intero.startswith(self.meno_zero_x) or stringa_valore_intero.startswith(self.piu_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == self.carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi .text prima del piu
                                                # Potrebbe essere ridondante questo elif
                                                elif reg.intero + intero_indirizzo + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potrei simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                                elif reg.intero + intero_indirizzo + intero_stringa in diz_dati:
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    if reg.intero + intero_indirizzo + intero_stringa <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                        not_in_range = False
                                                if not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    try:
                                                        assert(reg.intero + intero_indirizzo + intero_stringa <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                    except AssertionError as messaggio_errore:
                                                        print(messaggio_errore)
                                                        sys.exit(1) 
                                                    for _ in range(0,reg.intero + intero_indirizzo + intero_stringa - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    indirizzo_finale = chiave
                                            else: # ho trovato array($s7)
                                                # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi .text prima del piu
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                elif reg.intero + intero_indirizzo in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                                elif reg.intero + intero_indirizzo in diz_dati:
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                    if reg.intero + intero_indirizzo <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                        not_in_range = False
                                                if not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    try:
                                                        assert(reg.intero + intero_indirizzo <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                    except AssertionError as messaggio_errore:
                                                        print(messaggio_errore)
                                                        sys.exit(1)
                                                    for _ in range(0,reg.intero + intero_indirizzo - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                    indirizzo_finale = chiave 
                                            registro_trovato = True
                                            break
                                    if not registro_trovato:
                                        if stringa_valore_intero == "": # Caso $zero o $0 e da errori in mars
                                            seconda_posizione = 0 # Andrà in out of range
                                        else: # Permetto l'uso di registri come $zero o $0, se i valori sono corretti non si hanno problemi sul simulatore Mars e quindi nemmeno qui
                                            # Altrimenti si avranno eccezioni su python o risultati indesiderati. 
                                            if stringa_valore_intero.isdigit() or stringa_valore_intero[0] == self.carattere_virgoletta or stringa_valore_intero[0] == self.meno or stringa_valore_intero.startswith(self.zero_x): # ho trovato 1($zero)
                                                if stringa_valore_intero.startswith(self.zero_x) or stringa_valore_intero.startswith(self.meno_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == self.carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = intero_stringa
                                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                                elif intero_stringa in diz_dati:
                                                    seconda_posizione = intero_stringa
                                                    if intero_stringa <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                        not_in_range = False
                                                if not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    try:
                                                        assert(intero_stringa <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                    except AssertionError as messaggio_errore:
                                                        print(messaggio_errore)
                                                        sys.exit(1)
                                                    for _ in range(0,intero_stringa - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = intero_stringa
                                                    indirizzo_finale = chiave
                                            elif self.piu in stringa_valore_intero: # ho trovato array+100($zero)
                                                chiave_vettori = stringa_valore_intero[0:stringa_valore_intero.index(self.piu)]
                                                stringa_valore_intero = stringa_valore_intero[stringa_valore_intero.index(self.piu)+1:]
                                                if stringa_valore_intero.startswith(self.zero_x) or stringa_valore_intero.startswith(self.meno_zero_x) or stringa_valore_intero.startswith(self.piu_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == self.carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi .text prima del piu
                                                elif intero_indirizzo + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                                elif intero_indirizzo + intero_stringa in diz_dati:
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    if intero_indirizzo + intero_stringa <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                        not_in_range = False
                                                if not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    try:
                                                        assert(intero_indirizzo + intero_stringa <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                    except AssertionError as messaggio_errore:
                                                        print(messaggio_errore)
                                                        sys.exit(1)
                                                    for _ in range(0,intero_indirizzo + intero_stringa - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    indirizzo_finale = chiave
                                            else: # ho trovato array($zero)
                                                # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi .text prima del piu
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = intero_indirizzo
                                                elif intero_indirizzo in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = intero_indirizzo
                                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                                elif intero_indirizzo in diz_dati:
                                                    seconda_posizione = intero_indirizzo
                                                    if intero_indirizzo <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                                        not_in_range = False
                                                if not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    try:
                                                        assert(intero_indirizzo <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                                    except AssertionError as messaggio_errore:
                                                        print(messaggio_errore)
                                                        sys.exit(1)
                                                    for _ in range(0,intero_indirizzo - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = intero_indirizzo
                                                    indirizzo_finale = chiave          
                            elif self.piu in valore: # il piu è almeno in seconda posizione 
                                chiave_vettori = valore[0:valore.index(self.piu)]
                                stringa_valore_intero = valore[valore.index(self.piu)+1:]
                                if stringa_valore_intero.startswith(self.zero_x) or stringa_valore_intero.startswith(self.meno_zero_x) or stringa_valore_intero.startswith(self.piu_zero_x):
                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                elif stringa_valore_intero[0] == self.carattere_virgoletta:
                                    intero_stringa = ord(stringa_valore_intero[1])
                                else:
                                    intero_stringa = int(stringa_valore_intero)
                                if chiave_vettori in self.diz_indirizzi:
                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                if chiave_vettori in diz_text: # per istruzione la puo succedere
                                    intero_indirizzo = diz_text[chiave_vettori]
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi .text prima del piu     
                                elif intero_indirizzo + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                    not_in_range = False # Simulo istruzione la, non passo per la memoria
                                elif intero_indirizzo + intero_stringa in diz_dati:
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                    if intero_indirizzo + intero_stringa <= indirizzo_finale - 4: # -4 per evitare out of range in lw
                                        not_in_range = False
                                if not_in_range: # Simulo la memoria
                                    chiave = indirizzo_finale
                                    try:
                                        assert(intero_indirizzo + intero_stringa <= self.istruzioni.ultimo_valore_possibile), "Errore, il calcolo dell'indirizzo in memoria supera i limiti permessi (indirizzo 272629759 superato), riga: "+str(indice+1)+", "+self.diz_righe[indice+1]
                                    except AssertionError as messaggio_errore:
                                        print(messaggio_errore)
                                        sys.exit(1)
                                    for _ in range(0, intero_indirizzo + intero_stringa - indirizzo_finale + 4): # +4 per evitare out of range in lw
                                        chiave += 1
                                        diz_dati[chiave] = 0
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                    indirizzo_finale = chiave
                            elif self.carattere_virgoletta in valore: # per caratteri ascii  
                                seconda_posizione = ord(valore[1])
                            else:
                                seconda_posizione = valore
                        valore_posizione += 1
                    elif valore_posizione == 3: # potrebbe essere un else... Controllo terza posizione
                        if valore[0].isdigit() or valore[0] == self.meno or valore[0] == self.piu:
                            stringa_corretta = valore
                            if stringa_corretta.startswith(self.piu):
                                stringa_corretta = stringa_corretta[1:] # rimuovo il + fastidioso
                            if stringa_corretta.startswith(self.zero_x) or stringa_corretta.startswith(self.meno_zero_x): # per esadecimali
                                terza_posizione = istruzioni_mips.toint(int(stringa_corretta, 16))
                            else:
                                terza_posizione = int(stringa_corretta)
                        elif self.carattere_virgoletta in valore: # per caratteri ascii  
                            terza_posizione = ord(valore[1])
                        else:
                            if valore in self.diz_indirizzi: # da capire se succede (probabilmente non possibile)
                                terza_posizione = self.diz_indirizzi[valore]
                            else:
                                terza_posizione = valore           
                indice_secondario += 1
                if indice_secondario == len(self.testo_modificato[indice]): # Simulo l'esecuzione dell'istruzione
                    pc.intero += 4 # incremento il program counter
                    valore_program_counter = pc.intero
                    stringa_loops = ""
                    # Simulo l'istruzione 
                    operazione = chiama_istruzioni_mips(self.istruzioni, istruzione_mips, prima_posizione, seconda_posizione, terza_posizione)
                    if isinstance(operazione, tuple): # se sono tuple allora si fa un salto
                        if(operazione[1]): # se booleano a True
                            bool_salto = True # Indico che si verifica il salto a un'altra istruzione
                            stringa_loops = operazione[0] # aggiorno la stringa_loops con il nome del testo trovato
                        stringa_salto = operazione[0]   
                    # Cerco i valori legati alla pipeline (stalli, data e control hazard, cicli di clock, ecc...)
                    risultato_per_pipeline = Simulatore.trova_valori_per_pipeline(self,istruzione_precedente,indice_riga_precedente,indice_riga_pre_precedente,valore_program_counter,totale_clocks,nome_registro,indice,self.testo_modificato[indice],
                                                                                bool_salto,bool_saltato,data_hazards_totali,control_hazards_totali,control_hazards,bool_decode,bool_forwarding,bool_messaggi_hazards,bool_analizza_con_esecuzione) 
                    # Salvo il valore di cicli di clock ottenuto per ogni parte del codice (parte prima del ciclo loop, parti nel ciclo loop, parte finale dopo i loop aggiornata alla fine del codice) 
                    if self.reset_calcolo_loop: # reset loops
                        stringa_aggiornamento = "( "+str(self.conta_clocks - (self.conta_control_hazards+self.conta_data_hazards))+"(I) "+str(self.conta_data_hazards)+"(DH) "+str(self.conta_control_hazards)+"(CH) )"
                        if self.stringa_clocks_pre_loops+self.valore_loop+stringa_aggiornamento not in diz_hazards and self.aggiorna_pre_loop:
                            diz_hazards[self.stringa_clocks_pre_loops+self.valore_loop+stringa_aggiornamento] = self.conta_clocks
                        self.conta_data_hazards = 0
                        self.conta_control_hazards = 0
                        self.conta_clocks = 1
                        self.reset_calcolo_loop = False
                        self.aggiorna_pre_loop = False
                    # Aggiorno i valori trovati
                    diz_pipeline[chiave_diz_ris] = risultato_per_pipeline[0]
                    totale_clocks = risultato_per_pipeline[1]
                    data_hazards_totali = risultato_per_pipeline[2]
                    control_hazards_totali = risultato_per_pipeline[3]
                    # Salvo il control hazard trovato per quella istruzione
                    if tupla_control_hazards != "":
                        diz_pipeline[chiave_diz_ris]["Hazard Trovato"] = tupla_control_hazards
                        riga_branch = str(tupla_control_hazards[0])
                        tupla_control_hazards = ""
                        # Se i messaggi sono abilitati aggiungo un messaggio
                        if bool_messaggi_hazards:
                            if bool_decode:
                                messaggio_hazards = messaggio_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta"
                            else:
                                messaggio_hazards = messaggio_due_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta. L'istruzione branch ha deciso il salto in fase di EX e non in fase di ID quindi ci sono due stalli"
                            diz_pipeline[chiave_diz_ris]["Messaggio"] = messaggio_hazards
                    chiave_diz_ris += 1
                    
                    # Verifico se il salto a un altra riga è stato eseguito
                    bool_saltato = bool(bool_salto)
                    
                    indice_riga_pre_precedente = indice_riga_precedente
                    indice_riga_precedente = indice
                    
                    if istruzione_mips not in self.istruzioni_jump and bool_salto: # caso jump non causa control hazards
                        if bool_decode:
                            control_hazards = 1
                        else:
                            control_hazards = 2
                    else:
                        control_hazards = 0 
                    if isinstance(stringa_salto, int) and bool_salto:
                        indice = stringa_salto - 1 
                        # il pc é modificato nella jalr
                    elif bool_salto: 
                        indice = self.diz_salti[stringa_salto] - 1 # -1 perchè si incrementa di 1 alla fine del ciclo
                        pc.intero = diz_text[stringa_salto] - 4
                    # Simulo il possibile salto anche se non si dovesse verificare per ottenere tutti i control hazard possibili
                    if stringa_salto != "" and istruzione_mips not in self.istruzioni_jump:
                        indice_possibile_salto = self.diz_salti[stringa_salto] - 1
                        tupla_control_hazards = indice_riga_precedente+1, indice_possibile_salto+2
                        if not tupla_control_hazards in self.insieme_control_hazards:
                            self.insieme_control_hazards.add(tupla_control_hazards)
                        if not bool_salto:
                            tupla_control_hazards = ""
                    # Provo a simulare $at quando eseguo una istruzione load con nome di testo
                    if istruzione_mips in self.istruzioni_load and (chiave_indirizzi in self.diz_indirizzi or chiave_indirizzi in diz_text):   
                        for reg in self.insieme_registri:
                            if reg.nome == nome_at:
                                if chiave_indirizzi in diz_text:
                                    reg.intero = intero_at_text
                                else:
                                    reg.intero = intero_at
                                break
                            
                    stringa_valore_intero = ""
                    chiave_indirizzi = ""
                    chiave_vettori = ""
                    not_in_range = True
                    bool_salto = False
                    nome_registro = ""
                    chiave = ""
                    prima_posizione = ""
                    seconda_posizione = ""
                    terza_posizione = ""
                    stringa_salto = ""   
            indice += 1
        pc.intero = self.istruzioni.pc_finale
        chiave_loop = "Cicli di clock nel loop "
        # Aggiorno il calcolo dei cicli di clock per ogni parte dei cicli loop trovata (do una migliore visualizzione dei dati)
        for chiave, valore_diz in self.diz_loops.items():
            intero = 1
            for indice_lista in range(0,len(valore_diz[3])):
                stringa_aggiornamento = "( "+str(valore_diz[3][indice_lista][0] - (valore_diz[3][indice_lista][3]+valore_diz[3][indice_lista][4]))+"(I) "+str(valore_diz[3][indice_lista][3])+"(DH) "+str(valore_diz[3][indice_lista][4])+"(CH) )"
                diz_hazards[chiave_loop+chiave+" ("+str(intero)+") "+"(x"+str(valore_diz[3][indice_lista][2])+") "+stringa_aggiornamento] = valore_diz[3][indice_lista][0]
                intero += 1
        # Se non trovo cicli loop allora spiego che non sono stati trovati loop
        if self.valore_loop == "(Nessun loop trovato)":
            stringa_aggiornamento = "( "+str(self.conta_clocks - (self.conta_control_hazards+self.conta_data_hazards))+"(I) "+str(self.conta_data_hazards)+"(DH) "+str(self.conta_control_hazards)+"(CH) )"
            diz_hazards["Nessun loop trovato, cicli di click trovati "+stringa_aggiornamento] = self.conta_clocks 
        # Inserisco l'ultima parte del codice 
        if self.conta_clocks != 0 and self.valore_loop != "(Nessun loop trovato)":  
            stringa_aggiornamento = "( "+str(self.conta_clocks - (self.conta_control_hazards+self.conta_data_hazards))+"(I) "+str(self.conta_data_hazards)+"(DH) "+str(self.conta_control_hazards)+"(CH) )"     
            diz_hazards["Cicli di clock dopo i loop "+stringa_aggiornamento] = self.conta_clocks
        # Inserisco alcuni dati nel dizionario diz_hazards (usato come output, quindi aggiorno output)
        diz_hazards["Bolle Data Hazard Totali"] = data_hazards_totali
        diz_hazards["Bolle Control Hazard Totali"] = control_hazards_totali
        diz_hazards["Cicli di Clock"] = totale_clocks
        # Aggiorno output con istruzione o bolla in pipeline (caso ciclo di clock troppo grande)
        if ciclo_di_clock > totale_clocks:
            diz_hazards["IF"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["ID"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["EX"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["MEM"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["WB"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
        # Ordino gli insiemi con i possibili data hazard e control hazard usando liste
        lista_data_hazards = list(self.insieme_data_hazards)
        lista_data_hazards.sort()
        lista_control_hazards = list(self.insieme_control_hazards)
        lista_control_hazards.sort()
        # Aggiungo liste vuote per una corretta rappresentazione excel tramite pandas
        if len(lista_control_hazards) > len(lista_data_hazards):
            differenza = len(lista_control_hazards) - len(lista_data_hazards)
            for _ in range(0,differenza):
                lista_data_hazards.append([])
        elif len(lista_data_hazards) > len(lista_control_hazards):
            differenza = len(lista_data_hazards) - len(lista_control_hazards)
            for _ in range(0,differenza):
                lista_control_hazards.append([])
        # Aggiorno output
        diz_hazards["Data Hazards Trovati"] = lista_data_hazards
        diz_hazards["Control Hazards Trovati"] = lista_control_hazards
        # Controllo il valore del registro (usato nel testing per capire se i registri hanno i valori corretti alla fine dell'esecuzione) 
        for reg in self.insieme_registri:
            if reg.nome == "$a0":
                print("qua")
                print(reg.intero)
                break
        # rimuovo il program counter se il program counter è disabilitato
        # infatti il program counter calcolato è errato perchè non calcola le pseudoistruzioni in questo caso
        # Il codice funziona sempre tranne se si usano istruzioni che lo necessitano (per esempio jal, jalr, la con nomi del testo(della parte .text))
        # In quel caso il program counter deve essere corretto e quindi per ogni istruzione il calcolo delle pseudoistruzioni generate deve essere corretto
        # Ogni istruzione nuova aggiunta dovrebbe avere questi calcoli (altrimenti è bene non fare uso di jal e jalr e disattivare il program counter)
        if not bool_program_counter: 
            for diz in diz_pipeline:
                del diz_pipeline[diz]["Program Counter"]
        
        # Tanti print usati per testing 
                  
        # print(pc.intero)
        # print(diz_text)
        # print(self.diz_loops)
        # print(self.testo_modificato)
        # print(diz_dati)
        # print(self.diz_righe)
        # print(self.istruzioni.diz_text)
        # print(lista_data_hazards)
        # print(self.righe)
        # print(self.testo_modificato)
        
        # Restituisco i due dizionari con tutte le informazioni trovate
        return diz_pipeline, diz_hazards
       
