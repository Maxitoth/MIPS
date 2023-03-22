# Considerazioni riguardo alla traduzione da mips a python

# Sconsiglio vivamente l'utilizzo del registro $at in quanto non è gestito in maniera corretta
# Il suo valore è sempre 0x1001000 dopo istruzioni load in cui è presente il nome del vettore
# Esempio : lb $s0, M($a1) ---> $at = 0x1001000
# Esempio : lb $s0, ($a1) ---> $at non cambia
# In alcuni contesti il valore di $at non dovrebbe essere 0x1001000. 
# Puo essere usato, ma non è garantita una terminazione corretta del codice.

# Il tipo float o altri non sono gestiti
# Mancano ancora molte istruzioni

# in ogni riga del testo deve esserci almeno uno spazio o una virgola tra ogni valore altrimenti il testo non
# puo essere letto correttamente

# In ogni riga del testo con parti di codice ( istruzioni, .text, .data, strutture dati...) non ci devono essere commenti 
# é possibile commentare in righe senza codice

# Le strutture dati devono avere nomi diversi dalle istruzioni mips ( non posso dire addi: o jalr: o subi: ecc...) (le maiuscole vanno bene)

# Per stringhe ascii e asciiz non ci dovrebbero essere problemi ( non possiamo usare il carattere: µ):
# Si possono usare tutti i caratteri tranne il carattere speciale e più stringhe ascii nella stessa riga di codice mips,
# tuttavia la stringa vuota va usata da sola: 
# Non vengono trovati gli indirizzi di memoria corretti o inseriti valori corretti in memoria 
# per esempio F: .ascii "ty" "as" "" o F: .asciiz "ty" "as" ""
# Funziona: F: .ascii "" o F: .asciiz ""
# Viene usato un carattere speciale definito in carattere_speciale in modifica_testo
# Il carattere speciale non va usato ma può essere cambiato, io ho scelto µ. 

# Non è gestito Exit: syscall
# Devo scrivere Exit:
#               syscall 
# La syscall va bene solo se da sola nella riga di codice ( niente labels accanto)
# (Potrebbe funzionare adesso, serve testing)

# Per quanto riguarda i data hazards trovati ( non quelli rappresentati per la pipeline durante l'esecuzione (questi '>') ma quelli trovati in totale ( questi : [10, 11, $so]) ):
# Vengono trovati tutti i possibili data hazards prendendo come riferimento il caso peggiore.
# Quindi in generale trovo tutti i data hazards come se stessi eseguendo il codice senza forwaring ( con forwarding ridurrei il numero di stalli trovati).
# Eccezione alla regola: le istruzioni branch possono eseguirsi in fase di execute e se questa funzionalità è abilitata
# allora ottengo un minor numero di stalli.


import registro
import istruzioni_mips
import program_counter
import pandas as pd


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
        # and, or, xor fanno due istruzioni (and, andi, or , ori, xor, xori)
        if nome_istruzione == stringa_and or nome_istruzione == stringa_andi: 
            nome_istruzione = "aand"
            metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
            tupla_valori = prima_posizione, seconda_posizione, terza_posizione
            return metodo(tupla_valori)
        if nome_istruzione == stringa_or or nome_istruzione == stringa_ori:
            nome_istruzione = "oor"
            metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
            tupla_valori = prima_posizione, seconda_posizione, terza_posizione
            return metodo(tupla_valori)
        if nome_istruzione == stringa_xor or nome_istruzione == stringa_xori:
            nome_istruzione = "xor"
            metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
            tupla_valori = prima_posizione, seconda_posizione, terza_posizione
            return metodo(tupla_valori)
        if nome_istruzione == stringa_jalr:
            metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
            tupla_valori = prima_posizione, seconda_posizione
            return metodo(tupla_valori)
        metodo = getattr(oggetto_classe_istruzioni, nome_istruzione)
        if seconda_posizione == "" and terza_posizione == "":
            return metodo(prima_posizione)
        elif terza_posizione == "":
            return metodo(prima_posizione, seconda_posizione)
        else:    
            return metodo(prima_posizione, seconda_posizione, terza_posizione) 
        
# Il metodo si occupa di generare un file excel con uno o due fogli
# Se i booleani sono a False il metodo non fa nulla 
# Altrimenti possono essere generati due fogli per un file excel: uno per il risultato dell'esecuzione del codice mips
# e uno per il risultato dei data hazards e control hazards possibili.
        
def genera_excel(json_object_pipeline, json_object_hazards, bool_forwarding: bool, bool_excel_pipeline: bool, bool_excel_hazards: bool):
    if bool_forwarding:
        nome_excel = 'risultato_con_forwarding.xlsx'
    else:
        nome_excel = 'risultato_senza_forwarding.xlsx'
    if bool_excel_pipeline:
        df_pipeline = pd.read_json(json_object_pipeline).transpose()
        writer_pipeline = pd.ExcelWriter(nome_excel)
        df_pipeline.to_excel(writer_pipeline, sheet_name='Pipeline', index=False, na_rep='NaN')
        
        # Per avere un excel con colonne dinamicamente aggiustate
        # set_column non funziona se non si ha installato xlswriter
        # Utilizzare pip install xlsxwriter 
        for column in df_pipeline:
            column_width = max(df_pipeline[column].astype(str).map(len).max(), len(column))
            col_idx = df_pipeline.columns.get_loc(column)
            writer_pipeline.sheets['Pipeline'].set_column(col_idx, col_idx, column_width) 
        if not bool_excel_hazards:
            writer_pipeline.close()
        
    if bool_excel_hazards:
        df_hazards = pd.read_json(json_object_hazards)
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
            writer_pipeline.close()
        

# La classe Simulatore si occupa di simulare il codice mips.

class Simulatore() :
    
    def __init__(self):
        self.testo = ""
        self.righe = []
        self.testo_modificato = []
        self.insieme_istruzioni = {"or","and","ori","andi","xor","xori","subi","sub","add","addi","addiu","addu","slt","j","jal","jalr","beq","beqz","bne","bge","blt","move","lui","srl","sll","li","la","lh","lhu","lw","lb","lbu","sw","sh","sb"} # da aggiungere ogni istruzione MIPS necessaria
        # Per ogni istruzione serve un metodo definito nella classe Istruzioni nel file istruzioni_mips.py
        self.istruzioni_save = {"sw","sb","sh"}
        self.istruzioni_load = {"la","lw","lb","lbu","lh","lhu"}
        self.istruzioni_branch = {"bne","bge","beq","beqz","blt"}
        self.istruzioni_jump = {"j","jal","jalr"}
        self.iniziali_registri = {'a','s','t','v','r','k','1','2','3','4','5','6','7','8','9'} # Iniziali dei possibili registri ( ho escluso la f che servirebbe per i floating point registers)
        self.insieme_registri = set()
        self.diz_salti = {} # Per controllare a che indice saltare
        self.diz_loops = {} # Per segnare tutti i possibili loop e info associate
        self.insieme_data_hazards = set()
        self.insieme_control_hazards = set()
        self.istruzioni = istruzioni_mips.Istruzioni()
        self.program_counter = program_counter.Program_counter()
        self.diz_indirizzi = {}
        self.diz_righe = {}
        self.bool_forwarding = False
        self.ciclo_di_clock = 0
        self.diz_hazards = {}
        self.bool_clock_trovato = False
        self.bool_pipeline_wb = False
        self.bool_pipeline_mem = False
        self.bool_pipeline_ex = False
        self.bool_pipeline_id = False
        self.bool_pipeline_if = False
        self.conta_clocks = 0
        self.valore_loop = "(Nessun loop trovato)"
        self.stringa_clocks_pre_loops = "Cicli di clock prima del possibile loop "
        self.reset_calcolo_loop = False
        self.aggiorna_pre_loop = False
        self.istruzione_pre_precedente = ""
        
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
        piu = '+'
        stringa_spazio_piu = " +"
        stringa_piu_spazio = "+ "
        dollaro = "$"
        aperta_tonda = "("
        chiusa_tonda = ")"
        stringa_tonda_aperta_spazio = "( "
        stringa_tonda_chiusa_spazio = ") " # Non dovrebbe presentarsi
        stringa_spazio_tonda_chiusa = " )"
        fine_riga_textarea = '\r'
        punto_data = ".data"
        punto_text = ".text"
        bool_stringhe_data = False
        bool_virgolette = False
        bool_dati_ascii = False
        riga_ascii = ""
        carattere_speciale = 'µ' # Importante per la gestione delle stringhe ascii
        numero_riga = 1
        riga_corretta = []
        for riga in range(0,len(self.righe)): 
            riga_modificata = self.righe[riga].strip()
            self.diz_righe[numero_riga] = riga_modificata
            if riga_modificata.startswith(punto_data):
                bool_stringhe_data = True
            if riga_modificata.startswith(punto_text):
                bool_stringhe_data = False
            if virgolette in riga_modificata and bool_stringhe_data:
                for carattere in riga_modificata:
                    if carattere == virgolette:
                        if bool_virgolette == False:
                            bool_virgolette = True
                        else:
                            bool_virgolette = False
                    if carattere == spazio and bool_virgolette:
                        riga_ascii += carattere_speciale
                    elif carattere == due_punti and not bool_virgolette:
                        riga_ascii += spazio
                    elif carattere == virgola and not bool_virgolette:
                        riga_ascii += spazio  
                    elif carattere == fine_riga_textarea and not bool_virgolette:
                        riga_ascii += '' 
                    elif carattere == invio and not bool_virgolette:
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
                if fine_riga_textarea in riga_modificata:
                    riga_modificata = riga_modificata.replace(fine_riga_textarea, '')
                if invio in riga_modificata:
                    riga_modificata = riga_modificata.replace(invio, '')
            while due_spazi in riga_modificata:
                riga_modificata = riga_modificata.replace(due_spazi, spazio)
            if not bool_stringhe_data: # check semplice per capire se sono in una riga di .text o in .data
                if stringa_spazio_piu in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_spazio_piu, piu)
                if stringa_piu_spazio in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_piu_spazio, piu)
                if stringa_tonda_aperta_spazio in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_tonda_aperta_spazio, aperta_tonda)
                if stringa_tonda_chiusa_spazio in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_tonda_chiusa_spazio, chiusa_tonda)
                if stringa_spazio_tonda_chiusa in riga_modificata:
                    riga_modificata = riga_modificata.replace(stringa_spazio_tonda_chiusa, chiusa_tonda)
            riga_modificata = riga_modificata.split()
            if bool_dati_ascii:
                for val in riga_modificata:
                    if carattere_speciale in val:
                        riga_corretta.append(val.replace(carattere_speciale, spazio))
                    else:
                        riga_corretta.append(val)
            if len(riga_modificata) == 4 and not bool_stringhe_data: # Per caso particolare
                if aperta_tonda in riga_modificata[-1]:
                    if not dollaro in riga_modificata[-2]:
                        riga_modificata[-1] = riga_modificata[-2] + riga_modificata[-1]
                        riga_modificata.pop(-2)
            numero_riga += 1
            if bool_dati_ascii:
               self.testo_modificato.append(riga_corretta)
               bool_dati_ascii = False 
               riga_corretta = []
            else:
                self.testo_modificato.append(riga_modificata)
        testo.close()
        return
    
    # Il metodo si occupa di trovare gli indirizzi legati al .text in mars usando due dizionari
    # I dati trovati servono a simulare il program counter.
    # Tuttavia qui viene anche chiamato il metodo crea registri per inizializzare registri e il metodo trova_valori_per_pipeline per
    # trovare alcuni dei possibili data hazards 
    
    def trova_indirizzi_text_e_salti(self, bool_decode: bool):
        chiave = ""
        punto = '.'
        diz_indirizzi_text = self.program_counter.diz_indirizzi_text
        diz_text = self.istruzioni.diz_text
        indirizzo_text = self.program_counter.indirizzo_text
        aperta_tonda = "("
        zero_x = "0x"
        meno_zero_x= "-0x"
        piu = "+"
        meno = "-"
        carattere_virgoletta = "'"
        syscall = "syscall"
        indice_riga_pre_precedente = -1
        indice_riga_precedente = -1
        nome_at = "$at"
        intero_at = 268500992
        registro_at = registro.Registro(nome_at, intero_at)
        registro_at.write_back = True
        registro_at.fetch = False
        registro_at.stato_fase = 5
        registro_ra = self.istruzioni.ra
        registro_ra.write_back = True
        registro_ra.fetch = False
        registro_ra.stato_fase = 5
        self.insieme_registri.add(registro_at)
        self.insieme_registri.add(registro_ra)
        istruzione = ""
        for indice in range(0,len(self.testo_modificato)):
            lista = self.testo_modificato[indice]
            for elem in lista:
                if lista[0].startswith(punto):
                    break
                if len(lista) == 1: # Per evitare out of range
                    if lista[0] == syscall:
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
                    # Per trovare i possibili loop
                    if istruzione in self.istruzioni_jump or istruzione in self.istruzioni_branch:
                        if ultimo_valore in self.diz_salti: 
                            self.diz_loops[ultimo_valore] = [indice, False, 0, [], set()]
                    valore = True
                    chiave = elem
                    carattere_trovato = False
                    valore_con_tonda_trovato = False
                    indirizzo_text += 4
                    diz_indirizzi_text[indirizzo_text] = indice
                    diz_text[chiave] = indirizzo_text
                    self.diz_salti[chiave] = indice # ci dice dove dobbiamo saltare (per beq, j ecc...)
                    ultimo_elemento = lista[-1]
                    penultimo_elemento = lista[-2]
                    skip = False   
                    nome_registro = Simulatore.crea_registri(self, lista[1:]) 
                    Simulatore.trova_valori_per_pipeline(self,istruzione_precedente,indice_riga_precedente,indice_riga_pre_precedente,0,0,nome_registro,indice,lista,False,False,0,0,0,bool_decode,False,False,False)
                    indice_riga_pre_precedente = indice_riga_precedente
                    indice_riga_precedente = indice 
                elif lista[0] in self.insieme_istruzioni:
                    istruzione_precedente = istruzione
                    istruzione = lista[0]
                    ultimo_valore = lista[-1:][0]
                    # Per trovare i possibili loop
                    # Per trovare i possibili loop
                    if istruzione in self.istruzioni_jump or istruzione in self.istruzioni_branch:
                        if ultimo_valore in self.diz_salti: 
                            self.diz_loops[ultimo_valore] = [indice, False, 0, [], set()] # indice indica la riga - 1 dove finisce il loop ( non utilizzata)
                    valore = True
                    carattere_trovato = False
                    valore_con_tonda_trovato = False
                    indirizzo_text += 4
                    diz_indirizzi_text[indirizzo_text] = indice
                    ultimo_elemento = lista[-1]
                    penultimo_elemento = lista[-2]
                    skip = False
                    nome_registro = Simulatore.crea_registri(self, lista)
                    Simulatore.trova_valori_per_pipeline(self,istruzione_precedente,indice_riga_precedente,indice_riga_pre_precedente,0,0,nome_registro,indice,lista,False,False,0,0,0,bool_decode,False,False,False)
                    indice_riga_pre_precedente = indice_riga_precedente
                    indice_riga_precedente = indice
                else:
                    if lista[1] == syscall:
                        indirizzo_text += 4
                        diz_indirizzi_text[indirizzo_text] = indice
                        chiave = elem
                        diz_text[chiave] = indirizzo_text+4
                        self.diz_salti[chiave] = indice # ci dice dove dobbiamo saltare (per beq, j ecc...)
                        indice_riga_pre_precedente = indice_riga_precedente
                        indice_riga_precedente = indice
                    break
                # Qui sotto parte necessaria al calcolo corretto del program counter
                if istruzione in self.program_counter.insieme_istruzioni_semplici:
                    break
                if aperta_tonda in ultimo_elemento:
                    skip = True
                    if ultimo_elemento.startswith(piu): # Se scrivo +60 lo leggo come intero positivo
                        ultimo_elemento = ultimo_elemento[1:]
                    if piu in ultimo_elemento:
                        valore = self.program_counter.range_sessanta + 1 # vado oltre il range
                    elif ultimo_elemento[0] != aperta_tonda:
                        valore_con_tonda_trovato = True
                        valore = ultimo_elemento[0:ultimo_elemento.index(aperta_tonda)]
                        if valore.isdigit() or valore.startswith(zero_x) or valore.startswith(meno_zero_x) or valore.startswith(meno):
                            if valore.startswith(zero_x) or valore.startswith(meno_zero_x):
                                    valore = istruzioni_mips.toint(int(valore,16))
                            else:
                                valore = int(valore)
                        elif not valore.startswith(carattere_virgoletta):
                            valore = self.program_counter.range_sessanta + 1 # vado oltre il range
                        else:
                            carattere_trovato = True
                elif ultimo_elemento.isdigit() or ultimo_elemento.startswith(zero_x) or ultimo_elemento.startswith(meno_zero_x) or ultimo_elemento.startswith(meno):
                    skip = True
                    if ultimo_elemento.startswith(zero_x) or ultimo_elemento.startswith(meno_zero_x):
                        valore = istruzioni_mips.toint(int(ultimo_elemento,16))
                    else:
                        valore = int(ultimo_elemento)
                elif ultimo_elemento.startswith(carattere_virgoletta):
                    skip = True
                    carattere_trovato = True
                elif istruzione in self.program_counter.insieme_save_load or istruzione == self.program_counter.istruzione_la:
                    valore = self.program_counter.range_sessanta + 1 # vado oltre il range
                    skip = True
                if not skip:
                    if penultimo_elemento.startswith(piu): # Se scrivo +60 lo leggo come intero positivo
                        penultimo_elemento = penultimo_elemento[1:]
                    if penultimo_elemento.isdigit() or penultimo_elemento.startswith(zero_x) or penultimo_elemento.startswith(meno_zero_x) or penultimo_elemento.startswith(meno):
                        if penultimo_elemento.startswith(zero_x) or penultimo_elemento.startswith(meno_zero_x):
                            valore = istruzioni_mips.toint(int(penultimo_elemento,16))
                        else:
                            valore = int(penultimo_elemento)
                    elif penultimo_elemento.startswith(carattere_virgoletta):
                        carattere_trovato = True
                if self.istruzioni.bool_program_counter:
                    indirizzo_text = self.program_counter.simula_program_counter(istruzione, indirizzo_text, carattere_trovato, valore, valore_con_tonda_trovato)
                break
        indirizzo_text += 4 # esecuzione ultima istruzione
        diz_indirizzi_text[indirizzo_text] = ""
        self.istruzioni.pc_finale = indirizzo_text 
        self.istruzioni.diz_indirizzi_text = self.program_counter.diz_indirizzi_text
        #print(diz_text)
        
        # Il metodo si occupa di trovare data hazards, control hazards e mostrare come si comporta la pipeline ( a livello testuale).
        # è influenzato da vari booleani precedentemente stabiliti ( forwarding o meno, ecc...)
   
    def trova_valori_per_pipeline(self,istruzione_precedente: str, indice_riga_precedente: int, indice_riga_pre_precedente: int, program_counter: int,totale_clocks: int, nome_registro_tonde: str, indice: int, lista_indice: list, 
                                  bool_salto: bool, bool_saltato: bool, data_hazards_totali: int, control_hazards_totali: int, control_hazards: int, bool_decode: bool, bool_forwarding: bool, bool_messaggi_hazards: bool, bool_analizza_con_esecuzione: bool):
        # lista_valori_diz = []
        lista_valori_diz = {"Riga": 0, "Program Counter": 0, "Istruzione Mips": "", "Rappresentazione Pipeline": "", "Numero Data Hazards": 0, "Numero Control Hazards": 0, "Valore Clock": 0, "Hazard Trovato": [] }
        if bool_messaggi_hazards:
            lista_valori_diz["Messaggio"] = ""
        istruzione = ""
        riga = ""
        primo_registro_da_controllare = ""
        secondo_registro_da_controllare = ""
        registro_principale =""
        intero_stato_not_forwarding = 0
        intero_stato_forwarding = 0
        stringa_pipeline = "F D X M W" # potrei passarli direttamente al metodo
        data_hazards = "> " # potrei passarli direttamente al metodo 
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
        totale_clocks += 1
        conta_clocks += 1
        riga = self.diz_righe[indice+1]
        # lista_valori_diz.append(indice+1) # valore riga del codice mips
        # lista_valori_diz.append(program_counter)
        # lista_valori_diz.append(riga) # codice mips in quella riga
        lista_valori_diz["Riga"] = indice+1 # valore riga del codice mips
        lista_valori_diz["Program Counter"] = program_counter # valore program counter ( corretto solo se program counter abilitato)
        lista_valori_diz["Istruzione Mips"] = riga # codice mips in quella riga
        if lista_indice[0] not in self.insieme_istruzioni:
            lista_indice = lista_indice[1:]
        if lista_indice[0] in self.istruzioni_jump: # caso jump
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
                        if reg.nome == lista_indice[1]:
                            primo_registro_da_controllare = reg
                            break
                else:
                    jalr_len_due = False
                    for reg in self.insieme_registri:
                        if reg.nome == lista_indice[2]:
                            primo_registro_da_controllare = reg
                            break
                if primo_registro_da_controllare != "":                 
                    if not bool_forwarding:
                        if primo_registro_da_controllare.istruzione_mips != "":
                            stalli_primo_registro_not_forwarding = primo_registro_da_controllare.stato_write_back - primo_registro_da_controllare.stato_fase - intero_stato_not_forwarding
                            if stalli_primo_registro_not_forwarding < 0:
                                stalli_primo_registro_not_forwarding = 0
                    # Parte forwarding
                    else:
                        if primo_registro_da_controllare.istruzione_mips != "":
                            istruzione_registro = primo_registro_da_controllare.istruzione_mips
                            if  istruzione_registro in self.istruzioni_load and istruzione_registro != "la": # la si fa prima della memoria
                                stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 1 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding  
                            else:
                                stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 2 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding
                            if stalli_primo_registro_forwarding < 0:
                                stalli_primo_registro_forwarding = 0
                    if not (istruzione_precedente in self.istruzioni_branch and bool_saltato):
                        if primo_registro_da_controllare.istruzione_mips != "": # Trova dove sono gli stalli( riga a riga con registro)
                            if indice_riga_precedente+1 == primo_registro_da_controllare.riga_registro:
                                tupla_hazard_primo_registro = (primo_registro_da_controllare.riga_registro,indice+1,primo_registro_da_controllare.nome)
                                self.insieme_data_hazards.add(tupla_hazard_primo_registro)
                            elif (lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch:
                                if indice_riga_pre_precedente+1 == primo_registro_da_controllare.riga_registro and not (istruzione_precedente in self.istruzioni_jump and not bool_analizza_con_esecuzione):
                                    tupla_hazard_primo_registro = (primo_registro_da_controllare.riga_registro,indice+1,primo_registro_da_controllare.nome)
                                    self.insieme_data_hazards.add(tupla_hazard_primo_registro)
                        if primo_registro_da_controllare.istruzione_precedente != "" and ((lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch):
                            if indice_riga_pre_precedente+1 == primo_registro_da_controllare.riga_precedente:
                                tupla_hazard_primo_registro = (primo_registro_da_controllare.riga_precedente,indice+1,primo_registro_da_controllare.nome)
                                self.insieme_data_hazards.add(tupla_hazard_primo_registro)
                    for reg in self.insieme_registri:
                        if not bool_forwarding:
                            if stalli_primo_registro_not_forwarding > 0:
                                for val in range(0,stalli_primo_registro_not_forwarding):
                                    reg.cambia_fase()
                            else:
                                break
                        else:
                            if stalli_primo_registro_forwarding > 0:
                                for val in range(0,stalli_primo_registro_not_forwarding):
                                    reg.cambia_fase()
                            else:
                                break
                if jalr_len_due:
                    for reg in self.insieme_registri:
                        if reg.nome == "$ra": # reset
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
                else:
                    for reg in self.insieme_registri:
                        if reg.nome == lista_indice[1]: # reset
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
            if not bool_forwarding:
                # lista_valori_diz.append(data_hazards*(control_hazards+stalli_primo_registro_not_forwarding)+stringa_pipeline) # rappresentazione pipeline
                lista_valori_diz["Rappresentazione Pipeline"] = data_hazards*(control_hazards+stalli_primo_registro_not_forwarding)+stringa_pipeline # rappresentazione pipeline
                data_hazards_totali += stalli_primo_registro_not_forwarding
                numero_hazards = stalli_primo_registro_not_forwarding+control_hazards 
                totale_clocks += numero_hazards 
                conta_clocks += numero_hazards 
                # lista_valori_diz.append(stalli_primo_registro_not_forwarding) # data hazards per quella istruzione
                # lista_valori_diz.append(control_hazards) # control hazards per quella istruzione
                # lista_valori_diz.append(totale_clocks) # valore clock per quella istruzione
                lista_valori_diz["Numero Data Hazards"] = stalli_primo_registro_not_forwarding # data hazards per quella istruzione
                lista_valori_diz["Numero Control Hazards"] = control_hazards # control hazards per quella istruzione
                lista_valori_diz["Valore Clock"] = totale_clocks # valore clock per quella istruzione
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_not_forwarding > 0:
                    # lista_valori_diz.append(tupla_hazard_primo_registro)
                    lista_valori_diz["Hazard Trovato"] = tupla_hazard_primo_registro 
                    nome_registro = tupla_hazard_primo_registro[2]
                    riga_registro = str(tupla_hazard_primo_registro[0])
                    riga_attuale = str(tupla_hazard_primo_registro[1])
                    if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
                        if bool_branch and not bool_decode:
                            messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di execute."
                        else:
                            if stalli_primo_registro_not_forwarding == 2:
                                messaggio_data_hazards = "Ci sono due data hazards perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di execute l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                            else:
                                messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                        # lista_valori_diz.append(messaggio_data_hazards)
                        lista_valori_diz["Messaggio"] = messaggio_data_hazards
            else:
                # lista_valori_diz.append(data_hazards*(control_hazards+stalli_primo_registro_forwarding)+stringa_pipeline) # rappresentazione pipeline
                lista_valori_diz["Rappresentazione Pipeline"] = data_hazards*(control_hazards+stalli_primo_registro_forwarding)+stringa_pipeline # rappresentazione pipeline
                data_hazards_totali += stalli_primo_registro_forwarding
                numero_hazards = stalli_primo_registro_forwarding+control_hazards 
                totale_clocks += numero_hazards 
                conta_clocks += numero_hazards
                # lista_valori_diz.append(stalli_primo_registro_forwarding) # data hazards per quella istruzione
                # lista_valori_diz.append(control_hazards) # control hazards per quella istruzione
                # lista_valori_diz.append(totale_clocks) # valore clock per quella istruzione
                lista_valori_diz["Numero Data Hazards"] = stalli_primo_registro_forwarding # data hazards per quella istruzione
                lista_valori_diz["Numero Control Hazards"] = control_hazards # control hazards per quella istruzione
                lista_valori_diz["Valore Clock"] = totale_clocks # valore clock per quella istruzione
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_forwarding > 0:
                    # lista_valori_diz.append(tupla_hazard_primo_registro) 
                    lista_valori_diz["Hazard Trovato"] = tupla_hazard_primo_registro
                    nome_registro = tupla_hazard_primo_registro[2]
                    riga_registro = str(tupla_hazard_primo_registro[0])
                    riga_attuale = str(tupla_hazard_primo_registro[1])
                    if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
                        if primo_registro_da_controllare.istruzione_mips in self.istruzioni_load and primo_registro_da_controllare.istruzione_mips != "la": # istruzione la non passa per la memory
                            if bool_branch and bool_decode: # Caso particolare per le branch
                                if stalli_primo_registro_forwarding == 2:
                                    messaggio_data_hazards = "Ci sono due data hazards perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" ha già superato la fase di decode (è in fase di execute)."
                                else:
                                    messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                            else: # Caso standard
                                messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di execute."       
                        else: # Caso particolare per le altre istruzioni, si ha uno stallo solo con branch eseguite a fase di decode
                            messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di execute per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di decode."       
                        # lista_valori_diz.append(messaggio_data_hazards)    
                        lista_valori_diz["Messaggio"] = messaggio_data_hazards
                        
            # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
            if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
                if totale_clocks >= self.ciclo_di_clock and not self.bool_clock_trovato:
                    if self.ciclo_di_clock == totale_clocks: # caso standard
                        self.bool_clock_trovato = True
                        self.diz_hazards["WB"] = "("+str(indice+1)+") "+riga
                        self.bool_pipeline_wb = True
                    elif self.ciclo_di_clock == totale_clocks - 1:
                        self.bool_clock_trovato = True
                        self.diz_hazards["WB"] = "bolla"
                        self.bool_pipeline_wb = True
                        self.diz_hazards["MEM"] = "("+str(indice+1)+") "+riga
                        self.bool_pipeline_mem = True
                    elif self.ciclo_di_clock == totale_clocks - 2:
                        self.bool_clock_trovato = True
                        self.diz_hazards["WB"] = "bolla"
                        self.bool_pipeline_wb = True
                        self.diz_hazards["MEM"] = "bolla"
                        self.bool_pipeline_mem = True
                        self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                        self.bool_pipeline_ex = True
                elif self.bool_clock_trovato:
                    if lista_valori_diz["Numero Control Hazards"] == 1 or lista_valori_diz["Numero Data Hazards"] == 1:
                        if self.bool_pipeline_if:
                            self.ciclo_di_clock = 0 # ho finito la ricerca
                        elif self.bool_pipeline_id:
                            if istruzione_precedente in self.istruzioni_branch: # Non si sa ancora se si è effettuato il salto o meno
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
                    elif lista_valori_diz["Numero Data Hazards"] == 2:
                        if self.bool_pipeline_if:
                            self.ciclo_di_clock = 0 # ho finito la ricerca
                        elif self.bool_pipeline_id:
                            self.diz_hazards["IF"] = "bolla"
                            self.bool_pipeline_if = True
                        elif self.bool_pipeline_ex:
                            self.diz_hazards["ID"] = "bolla"
                            self.bool_pipeline_id = True
                            self.diz_hazards["IF"] = "bolla"
                            self.bool_pipeline_if = True
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
                        elif self.bool_pipeline_id:
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
                            self.diz_hazards["ID"] = "("+str(indice+1)+") "+riga
                            self.bool_pipeline_id = True
                        elif self.bool_pipeline_mem:
                            self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                            self.bool_pipeline_ex = True
                        elif self.bool_pipeline_wb:
                            self.diz_hazards["MEM"] = "("+str(indice+1)+") "+riga
                            self.bool_pipeline_mem = True 
            
            self.conta_clocks += conta_clocks
            for chiave in self.diz_loops:
                if self.diz_loops[chiave][1] == True:
                    self.diz_loops[chiave][2] += conta_clocks
                    self.diz_loops[chiave][4].add(indice+1) 
            if self.reset_calcolo_loop:
                if self.diz_loops[self.valore_loop][1] == True: 
                    self.diz_loops[self.valore_loop][2] = self.diz_loops[self.valore_loop][2] - 1
                    lista_cercata = [self.diz_loops[self.valore_loop][2],self.diz_loops[self.valore_loop][4],1]
                    bool_lista_trovata = False
                    for indice_lista in range(0,len(self.diz_loops[self.valore_loop][3])):
                        if self.diz_loops[self.valore_loop][3][indice_lista][0] == lista_cercata[0] and self.diz_loops[self.valore_loop][3][indice_lista][1] == lista_cercata[1]: 
                            self.diz_loops[self.valore_loop][3][indice_lista][2] += 1
                            bool_lista_trovata = True
                            break
                    if not bool_lista_trovata:
                        self.diz_loops[self.valore_loop][3] += [lista_cercata]   
                    self.conta_clocks = 1
                    self.diz_loops[self.valore_loop][2] = 1
                    self.diz_loops[self.valore_loop][4] = set()
                else:
                    self.diz_loops[self.valore_loop][1] = True
                    self.aggiorna_pre_loop = True
                    self.conta_clocks = self.conta_clocks - 1 
                    self.diz_loops[self.valore_loop][2] = 1  
                    self.diz_loops[self.valore_loop][4].add(indice+1)        
                                 
            return lista_valori_diz, totale_clocks, data_hazards_totali, control_hazards_totali
        
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
        bool_branch = False
        if istruzione in self.istruzioni_save:
            for reg in self.insieme_registri:
                if primo_registro_da_controllare != "":
                    break
                if reg.nome == valore_uno:
                    primo_registro_da_controllare = reg
        elif istruzione in self.istruzioni_load:
            for reg in self.insieme_registri:
                if registro_principale != "" and primo_registro_da_controllare != "":
                    break
                if reg.nome == nome_registro_tonde:
                    primo_registro_da_controllare = reg
                if reg.nome == valore_uno:
                    registro_principale = reg
        elif istruzione in self.istruzioni_branch:
            bool_branch = True
            for reg in self.insieme_registri:
                if primo_registro_da_controllare != "" and secondo_registro_da_controllare != "":
                    break
                if reg.nome == valore_uno:
                    primo_registro_da_controllare = reg
                if reg.nome == valore_due:
                    secondo_registro_da_controllare = reg
            if bool_salto:
                control_hazards_totali += 1
        else:
            for reg in self.insieme_registri:
                if primo_registro_da_controllare != "" and secondo_registro_da_controllare != "" and registro_principale != "":
                    break
                if reg.nome == valore_uno:
                    registro_principale = reg
                if reg.nome == valore_due:
                    primo_registro_da_controllare = reg
                if reg.nome == valore_tre:
                    secondo_registro_da_controllare = reg
        #print(lista_indice)
        #print(primo_registro_da_controllare)
        #print(secondo_registro_da_controllare)
        #print(registro_principale)
        #print(indice+1)
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
                if primo_registro_da_controllare.istruzione_mips != "": # lo stato write back è lo stato in cui l'istruzione deve stare ( write back deve essere allineata con decode della istruzione attuale), 
                    # quindi questo - lo stato del registro ( stato dell'istruzione in cui faceva parte il registro l'ultima volta) ci dice quanti stalli ottengo. Se è una istruzione branch
                    # potrebbe essere write back allineata con execute ( in sostanza meno stalli).
                    stalli_primo_registro_not_forwarding = primo_registro_da_controllare.stato_write_back - primo_registro_da_controllare.stato_fase - intero_stato_not_forwarding
                    if stalli_primo_registro_not_forwarding < 0:
                        stalli_primo_registro_not_forwarding = 0
            # Parte forwarding
            else:
                if primo_registro_da_controllare.istruzione_mips != "": # lo stato write back non è piu lo stato in cui l'istruzione deve stare ( execute o memory devono essere allineati con decode della istruzione attuale), 
                    # quindi questo - lo stato del registro ( stato dell'istruzione in cui faceva parte il registro l'ultima volta) ci dice quanti stalli ottengo. Se è una istruzione branch
                    # potrebbe essere execute o memory allineata con decode o fetch ( in sostanza più stalli).
                    istruzione_registro = primo_registro_da_controllare.istruzione_mips
                    if  istruzione_registro in self.istruzioni_load and istruzione_registro != "la": # la si fa prima della memoria
                        stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 1 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding  
                    else:
                        stalli_primo_registro_forwarding = primo_registro_da_controllare.stato_write_back - 2 - primo_registro_da_controllare.stato_fase - intero_stato_forwarding
                    if stalli_primo_registro_forwarding < 0:
                        stalli_primo_registro_forwarding = 0
            if not (istruzione_precedente in self.istruzioni_branch and bool_saltato):
                if primo_registro_da_controllare.istruzione_mips != "": # Trova dove sono gli stalli( riga a riga con registro)
                    if indice_riga_precedente+1 == primo_registro_da_controllare.riga_registro:
                        tupla_hazard_primo_registro = (primo_registro_da_controllare.riga_registro,indice+1,primo_registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard_primo_registro)
                    elif (lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch:
                        if indice_riga_pre_precedente+1 == primo_registro_da_controllare.riga_registro and not (istruzione_precedente in self.istruzioni_jump and not bool_analizza_con_esecuzione):
                            tupla_hazard_primo_registro = (primo_registro_da_controllare.riga_registro,indice+1,primo_registro_da_controllare.nome)
                            self.insieme_data_hazards.add(tupla_hazard_primo_registro)
                if primo_registro_da_controllare.istruzione_precedente != "" and ((lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch) :
                    if indice_riga_pre_precedente+1 == primo_registro_da_controllare.riga_precedente:
                        tupla_hazard_primo_registro = (primo_registro_da_controllare.riga_precedente,indice+1,primo_registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard_primo_registro)
                        
                        
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
                    if stalli_secondo_registro_not_forwarding < 0:
                        stalli_secondo_registro_not_forwarding = 0
            # Parte forwarding
            else:
                if secondo_registro_da_controllare.istruzione_mips != "":
                    istruzione_registro = secondo_registro_da_controllare.istruzione_mips
                    if  istruzione_registro in self.istruzioni_load:
                        stalli_secondo_registro_forwarding = secondo_registro_da_controllare.stato_write_back - 1 - secondo_registro_da_controllare.stato_fase - intero_stato_forwarding  
                    else:
                        stalli_secondo_registro_forwarding = secondo_registro_da_controllare.stato_write_back - 2 - secondo_registro_da_controllare.stato_fase - intero_stato_forwarding
                    if stalli_secondo_registro_forwarding < 0:
                        stalli_secondo_registro_forwarding = 0
            if not (istruzione_precedente in self.istruzioni_branch and bool_saltato):
                if secondo_registro_da_controllare.istruzione_mips != "": # Trova dove sono gli stalli( riga a riga con registro)
                    if indice_riga_precedente+1 == secondo_registro_da_controllare.riga_registro:
                        tupla_hazard_secondo_registro = (secondo_registro_da_controllare.riga_registro,indice+1,secondo_registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard_secondo_registro)
                    elif (lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch:
                        if indice_riga_pre_precedente+1 == secondo_registro_da_controllare.riga_registro and not (istruzione_precedente in self.istruzioni_jump and not bool_analizza_con_esecuzione):
                            tupla_hazard_secondo_registro = (secondo_registro_da_controllare.riga_registro,indice+1,secondo_registro_da_controllare.nome)
                            self.insieme_data_hazards.add(tupla_hazard_secondo_registro)
                if secondo_registro_da_controllare.istruzione_precedente != "" and ((lista_indice[0] in self.istruzioni_branch and bool_decode) or not lista_indice[0] in self.istruzioni_branch) :
                    if indice_riga_pre_precedente+1 == secondo_registro_da_controllare.riga_precedente:
                        tupla_hazard_secondo_registro = (secondo_registro_da_controllare.riga_precedente,indice+1,secondo_registro_da_controllare.nome)
                        self.insieme_data_hazards.add(tupla_hazard_secondo_registro)
        if not bool_forwarding:
            if stalli_primo_registro_not_forwarding >= stalli_secondo_registro_not_forwarding:
                # lista_valori_diz.append(data_hazards*(control_hazards+stalli_primo_registro_not_forwarding)+stringa_pipeline) # rappresentazione pipeline
                lista_valori_diz["Rappresentazione Pipeline"] = data_hazards*(control_hazards+stalli_primo_registro_not_forwarding)+stringa_pipeline # rappresentazione pipeline
                data_hazards_totali += stalli_primo_registro_not_forwarding
                numero_hazards = stalli_primo_registro_not_forwarding+control_hazards
                totale_clocks += numero_hazards
                conta_clocks += numero_hazards 
                # lista_valori_diz.append(stalli_primo_registro_not_forwarding) # data hazards per quella istruzione
                # lista_valori_diz.append(control_hazards) # control hazards per quella istruzione
                # lista_valori_diz.append(totale_clocks) # Valore clock per quella istruzione
                lista_valori_diz["Numero Data Hazards"] = stalli_primo_registro_not_forwarding # data hazards per quella istruzione
                lista_valori_diz["Numero Control Hazards"] = control_hazards # control hazards per quella istruzione
                lista_valori_diz["Valore Clock"] = totale_clocks # Valore clock per quella istruzione
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_not_forwarding > 0:
                    # lista_valori_diz.append(tupla_hazard_primo_registro)
                    lista_valori_diz["Hazard Trovato"] = tupla_hazard_primo_registro
                    nome_registro = tupla_hazard_primo_registro[2]
                    riga_registro = str(tupla_hazard_primo_registro[0])
                    riga_attuale = str(tupla_hazard_primo_registro[1])
                    if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
                        if bool_branch and not bool_decode:
                            messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di execute."
                        else:
                            if stalli_primo_registro_not_forwarding == 2:
                                messaggio_data_hazards = "Ci sono due data hazards perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di execute l'istruzione in riga "+riga_attuale+" è già in fase di decode." 
                            else:
                                messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                        # lista_valori_diz.append(messaggio_data_hazards)
                        lista_valori_diz["Messaggio"] = messaggio_data_hazards           
            else:
                # lista_valori_diz.append(data_hazards*(control_hazards+stalli_secondo_registro_not_forwarding)+stringa_pipeline) # rappresentazione pipeline
                lista_valori_diz["Rappresentazione Pipeline"] = data_hazards*(control_hazards+stalli_secondo_registro_not_forwarding)+stringa_pipeline # rappresentazione pipeline
                data_hazards_totali += stalli_secondo_registro_not_forwarding
                numero_hazards = stalli_secondo_registro_not_forwarding+control_hazards
                totale_clocks += numero_hazards
                conta_clocks += numero_hazards 
                # lista_valori_diz.append(stalli_secondo_registro_not_forwarding) # data hazards per quella istruzione
                # lista_valori_diz.append(control_hazards) # control hazards per quella istruzione
                # lista_valori_diz.append(totale_clocks) # Valore clock per quella istruzione
                lista_valori_diz["Numero Data Hazards"] = stalli_secondo_registro_not_forwarding # data hazards per quella istruzione
                lista_valori_diz["Numero Control Hazards"] = control_hazards # control hazards per quella istruzione
                lista_valori_diz["Valore Clock"] = totale_clocks # Valore clock per quella istruzione
                if tupla_hazard_secondo_registro != "" and stalli_secondo_registro_not_forwarding > 0:
                    # lista_valori_diz.append(tupla_hazard_secondo_registro)
                    lista_valori_diz["Hazard Trovato"] = tupla_hazard_secondo_registro
                    nome_registro = tupla_hazard_secondo_registro[2]
                    riga_registro = str(tupla_hazard_secondo_registro[0])
                    riga_attuale = str(tupla_hazard_secondo_registro[1])
                    if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
                        if bool_branch and not bool_decode:
                            messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di execute."
                        else:
                            if stalli_secondo_registro_not_forwarding == 2:
                                messaggio_data_hazards = "Ci sono due data hazards perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di execute l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                            else:
                                messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di write back per poter passare il nuovo valore del registro, ma raggiunta la fase di memory l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                        # lista_valori_diz.append(messaggio_data_hazards)
                        lista_valori_diz["Messaggio"] = messaggio_data_hazards
        else:    
            if stalli_primo_registro_forwarding >= stalli_secondo_registro_forwarding:
                # lista_valori_diz.append(data_hazards*(control_hazards+stalli_primo_registro_forwarding)+stringa_pipeline) # rappresentazione pipeline
                lista_valori_diz["Rappresentazione Pipeline"] = data_hazards*(control_hazards+stalli_primo_registro_forwarding)+stringa_pipeline # rappresentazione pipeline
                data_hazards_totali += stalli_primo_registro_forwarding
                numero_hazards = stalli_primo_registro_forwarding+control_hazards
                totale_clocks += numero_hazards
                conta_clocks += numero_hazards
                # lista_valori_diz.append(stalli_primo_registro_forwarding) # data hazards per quella istruzione
                # lista_valori_diz.append(control_hazards) # control hazards per quella istruzione
                # lista_valori_diz.append(totale_clocks) # Valore clock per quella istruzione
                lista_valori_diz["Numero Data Hazards"] = stalli_primo_registro_forwarding # data hazards per quella istruzione
                lista_valori_diz["Numero Control Hazards"] = control_hazards # control hazards per quella istruzione
                lista_valori_diz["Valore Clock"] = totale_clocks # Valore clock per quella istruzione
                if tupla_hazard_primo_registro != "" and stalli_primo_registro_forwarding > 0:
                    # lista_valori_diz.append(tupla_hazard_primo_registro)
                    lista_valori_diz["Hazard Trovato"] = tupla_hazard_primo_registro
                    nome_registro = tupla_hazard_primo_registro[2]
                    riga_registro = str(tupla_hazard_primo_registro[0])
                    riga_attuale = str(tupla_hazard_primo_registro[1])
                    if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
                        if primo_registro_da_controllare.istruzione_mips in self.istruzioni_load and primo_registro_da_controllare.istruzione_mips != "la": # istruzione la non passa per la memory
                            if bool_branch and bool_decode: # Caso particolare per le branch
                                if stalli_primo_registro_forwarding == 2:
                                    messaggio_data_hazards = "Ci sono due data hazards perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" ha già superato la fase di decode (è in fase di execute)."
                                else:
                                    messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                            else: # Caso standard
                                messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di execute."       
                        else: # Caso particolare per le altre istruzioni, si ha uno stallo solo con branch eseguite a fase di decode
                            messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di execute per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di decode."       
                        # lista_valori_diz.append(messaggio_data_hazards)
                        lista_valori_diz["Messaggio"] = messaggio_data_hazards
            else:
                # lista_valori_diz.append(data_hazards*(control_hazards+stalli_secondo_registro_forwarding)+stringa_pipeline) # rappresentazione pipeline 
                lista_valori_diz["Rappresentazione Pipeline"] = data_hazards*(control_hazards+stalli_secondo_registro_forwarding)+stringa_pipeline # rappresentazione pipeline 
                data_hazards_totali += stalli_secondo_registro_forwarding
                numero_hazards = stalli_secondo_registro_forwarding+control_hazards
                totale_clocks += numero_hazards
                conta_clocks += numero_hazards
                # lista_valori_diz.append(stalli_secondo_registro_forwarding) # data hazards per quella istruzione
                # lista_valori_diz.append(control_hazards) # control hazards per quella istruzione
                # lista_valori_diz.append(totale_clocks) # Valore clock per quella istruzione
                lista_valori_diz["Numero Data Hazards"] = stalli_secondo_registro_forwarding # data hazards per quella istruzione
                lista_valori_diz["Numero Control Hazards"] = control_hazards # control hazards per quella istruzione
                lista_valori_diz["Valore Clock"] = totale_clocks # Valore clock per quella istruzione
                if tupla_hazard_secondo_registro != "" and stalli_secondo_registro_forwarding > 0:
                    # lista_valori_diz.append(tupla_hazard_secondo_registro)
                    lista_valori_diz["Hazard Trovato"] = tupla_hazard_secondo_registro
                    nome_registro = tupla_hazard_secondo_registro[2]
                    riga_registro = str(tupla_hazard_secondo_registro[0])
                    riga_attuale = str(tupla_hazard_secondo_registro[1])
                    if bool_messaggi_hazards: # Se i messaggi sono abilitati allora verranno inseriti nella soluzione
                        if secondo_registro_da_controllare.istruzione_mips in self.istruzioni_load and secondo_registro_da_controllare.istruzione_mips != "la": # istruzione la non passa per la memory
                            if bool_branch and bool_decode: # Caso particolare per le branch
                                if stalli_secondo_registro_forwarding == 2:
                                    messaggio_data_hazards = "Ci sono due data hazards perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" ha già superato la fase di decode (è in fase di execute)."
                                else:
                                    messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione eseguita precedentemente in riga "+riga_registro+". L'istruzione è in fase di execute e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è già in fase di decode."
                            else: # Caso standard
                                messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di memory per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di execute."       
                        else: # Caso particolare per le altre istruzioni, si ha uno stallo solo con branch eseguite a fase di decode
                            messaggio_data_hazards = "C'è un data hazard perchè il registro "+nome_registro+" ha cambiato valore nell'istruzione precedente in riga "+riga_registro+". L'istruzione è in fase di decode e deve raggiungere la fase di execute per poter passare il nuovo valore del registro, ma una volta raggiunta questa fase l'istruzione in riga "+riga_attuale+" è gia in fase di decode."       
                        # lista_valori_diz.append(messaggio_data_hazards)
                        lista_valori_diz["Messaggio"] = messaggio_data_hazards
        for reg in self.insieme_registri:
            if not bool_forwarding:
                if stalli_primo_registro_not_forwarding >= stalli_secondo_registro_not_forwarding and stalli_primo_registro_not_forwarding > 0:
                    for val in range(0,stalli_primo_registro_not_forwarding):
                        reg.cambia_fase()
                elif stalli_secondo_registro_not_forwarding > stalli_primo_registro_not_forwarding:
                    for val in range(0,stalli_secondo_registro_not_forwarding):
                        reg.cambia_fase()
                else:
                    break
            else:
                if stalli_primo_registro_forwarding >= stalli_secondo_registro_forwarding and stalli_primo_registro_forwarding > 0:
                    for val in range(0,stalli_primo_registro_forwarding):
                        reg.cambia_fase()
                elif stalli_secondo_registro_forwarding > stalli_primo_registro_forwarding:
                    for val in range(0,stalli_secondo_registro_forwarding):
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
            if totale_clocks >= self.ciclo_di_clock and not self.bool_clock_trovato:
                if self.ciclo_di_clock == totale_clocks: # caso standard
                    self.bool_clock_trovato = True
                    self.diz_hazards["WB"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_wb = True
                elif self.ciclo_di_clock == totale_clocks - 1:
                    self.bool_clock_trovato = True
                    self.diz_hazards["WB"] = "bolla"
                    self.bool_pipeline_wb = True
                    self.diz_hazards["MEM"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_mem = True
                elif self.ciclo_di_clock == totale_clocks - 2:
                    self.bool_clock_trovato = True
                    self.diz_hazards["WB"] = "bolla"
                    self.bool_pipeline_wb = True
                    self.diz_hazards["MEM"] = "bolla"
                    self.bool_pipeline_mem = True
                    self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                    self.bool_pipeline_ex = True
            elif self.bool_clock_trovato:
                if lista_valori_diz["Numero Control Hazards"] == 1 or lista_valori_diz["Numero Data Hazards"] == 1:
                    if self.bool_pipeline_if:
                        self.ciclo_di_clock = 0 # ho finito la ricerca
                    elif self.bool_pipeline_id:
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
                elif lista_valori_diz["Numero Data Hazards"] == 2:
                    if self.bool_pipeline_if:
                        self.ciclo_di_clock = 0 # ho finito la ricerca
                    elif self.bool_pipeline_id:
                        self.diz_hazards["IF"] = "bolla"
                        self.bool_pipeline_if = True
                    elif self.bool_pipeline_ex:
                        self.diz_hazards["ID"] = "bolla"
                        self.bool_pipeline_id = True
                        self.diz_hazards["IF"] = "bolla"
                        self.bool_pipeline_if = True
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
                    elif self.bool_pipeline_id:
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
                        self.diz_hazards["ID"] = "("+str(indice+1)+") "+riga
                        self.bool_pipeline_id = True
                    elif self.bool_pipeline_mem:
                        self.diz_hazards["EX"] = "("+str(indice+1)+") "+riga
                        self.bool_pipeline_ex = True
                    elif self.bool_pipeline_wb:
                        self.diz_hazards["MEM"] = "("+str(indice+1)+") "+riga
                        self.bool_pipeline_mem = True 
        self.conta_clocks += conta_clocks
        for chiave in self.diz_loops:
            if self.diz_loops[chiave][1] == True:
                self.diz_loops[chiave][2] += conta_clocks
                self.diz_loops[chiave][4].add(indice+1) 
        if self.reset_calcolo_loop:
            if self.diz_loops[self.valore_loop][1] == True: 
                self.diz_loops[self.valore_loop][2] = self.diz_loops[self.valore_loop][2] - 1
                lista_cercata = [self.diz_loops[self.valore_loop][2],self.diz_loops[self.valore_loop][4],1]
                bool_lista_trovata = False
                for indice_lista in range(0,len(self.diz_loops[self.valore_loop][3])):
                    if self.diz_loops[self.valore_loop][3][indice_lista][0] == lista_cercata[0] and self.diz_loops[self.valore_loop][3][indice_lista][1] == lista_cercata[1]: 
                        self.diz_loops[self.valore_loop][3][indice_lista][2] += 1
                        bool_lista_trovata = True
                        break
                if not bool_lista_trovata:
                    self.diz_loops[self.valore_loop][3] += [lista_cercata] 

                self.conta_clocks = 1
                self.diz_loops[self.valore_loop][2] = 1
                self.diz_loops[self.valore_loop][4] = set()
            else:
                self.diz_loops[self.valore_loop][1] = True
                self.aggiorna_pre_loop = True
                self.conta_clocks = self.conta_clocks - 1 
                self.diz_loops[self.valore_loop][2] = 1  
                self.diz_loops[self.valore_loop][4].add(indice+1) 
        
        return lista_valori_diz, totale_clocks, data_hazards_totali, control_hazards_totali   
    
    # Il metodo si occupa di creare registri, ovvero inizializzare i registri che sono effettivamente nel testo di codice.
    # Potrei crearli direttamente tutti, ma siccome potrebbero non essere usati preferisco questo approccio.
    
    def crea_registri(self, lista_riga: list):
        dollaro = "$"
        aperta_tonda = "("
        chiusa_tonda = ")"
        registro_non_trovato = True
        nome_registro = ""
        if len(lista_riga) == 3:
            if lista_riga[1].startswith(dollaro) and lista_riga[1][1] in self.iniziali_registri:
                for reg in self.insieme_registri:
                    if reg.nome == lista_riga[1]:
                        registro_non_trovato = False
                        break
                if registro_non_trovato:
                    nuovo_registro = registro.Registro(lista_riga[1], 0)
                    self.insieme_registri.add(nuovo_registro)
            if lista_riga[2].startswith(dollaro) and lista_riga[2][1] in self.iniziali_registri: # in posizione superiore a 1
                # il registro è stato usato prima e quindi lo stato corretto è write back 
                registro_non_trovato = True
                for reg in self.insieme_registri:
                    if reg.nome == lista_riga[2]:
                        registro_non_trovato = False
                        break
                if registro_non_trovato:
                    nuovo_registro = registro.Registro(lista_riga[2], 0)
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro)
            elif aperta_tonda in lista_riga[2]:
                nome_registro = lista_riga[2][lista_riga[2].index(aperta_tonda)+1: lista_riga[2].index(chiusa_tonda)]          
        if len(lista_riga) == 4: # al massimo ci sono 4 posizioni --> add $t1, $t2, $t3
            if lista_riga[1].startswith(dollaro) and lista_riga[1][1] in self.iniziali_registri:
                for reg in self.insieme_registri:
                    if reg.nome == lista_riga[1]:
                        registro_non_trovato = False
                        break
                if registro_non_trovato:
                    nuovo_registro = registro.Registro(lista_riga[1], 0)
                    self.insieme_registri.add(nuovo_registro)
            if lista_riga[2].startswith(dollaro) and lista_riga[2][1] in self.iniziali_registri: # in posizione superiore a 1
                # il registro è stato usato prima e quindi lo stato corretto è write back 
                registro_non_trovato = True
                for reg in self.insieme_registri:
                    if reg.nome == lista_riga[2]:
                        registro_non_trovato = False
                        break
                if registro_non_trovato:
                    nuovo_registro = registro.Registro(lista_riga[2], 0)
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro)
            if lista_riga[3].startswith(dollaro) and lista_riga[3][1] in self.iniziali_registri: # in posizione superiore a 1
                # il registro è stato usato prima e quindi lo stato corretto è write back 
                registro_non_trovato = True
                for reg in self.insieme_registri:
                    if reg.nome == lista_riga[3]:
                        registro_non_trovato = False
                        break
                if registro_non_trovato:
                    nuovo_registro = registro.Registro(lista_riga[3], 0)
                    nuovo_registro.write_back = True
                    nuovo_registro.fetch = False
                    nuovo_registro.stato_fase = 5
                    self.insieme_registri.add(nuovo_registro) 
            return nome_registro     
 
    # Il metodo si occupa di simulare l'esecuzione del codice mips.
    # Viene simulata la memoria tramite un dizionario inizializzato nella classe Istruzioni.
    # Qui viene aggiornato tale dizionario con gli indirizzi trovati nella sezione .data di mars.
    # Ma istruzioni save o load possono pure aumentare la dimensione del dizionario.
    # Ogni lista associata alla lista di liste ottenuta con modifica_testo viene analizzata.
    # In particolare ogni elemento della lista viene analizzato per capire se è un istruzione, un registro o un label.
    # Viene poi chiamata l'istruzione della classe Istruzioni corrispondente all'istruzione mips trovata.
    # E infine viene simulata la pipeline per quella specifica riga.
    # Otteniamo cosi un dizionario con tutti i dati.
    # ( Il program counter viene aggiornato per ogni istruzione trovata)
     
    def simula_codice_mips(self, testo: str, bool_decode: bool, bool_forwarding: bool, bool_program_counter: bool, bool_messaggi_hazards: bool, ciclo_di_clock: int):
        self.testo = testo
        Simulatore.modifica_testo(self)
        # print(self.testo_modificato)
        self.istruzioni.bool_program_counter = bool_program_counter
        self.bool_forwarding = bool_forwarding
        self.ciclo_di_clock = ciclo_di_clock
        Simulatore.trova_indirizzi_text_e_salti(self, bool_decode)
        diz_pipeline = {}
        diz_hazards = {}
        if ciclo_di_clock != 0:
            diz_hazards = {"IF": "Nessuna istruzione", "ID": "Nessuna istruzione", "EX": "Nessuna istruzione", "MEM": "Nessuna istruzione", "WB": "Nessuna istruzione"}
        self.diz_hazards = diz_hazards
        chiave_diz_ris = 1
        indice = 0
        punto = '.'
        dollaro = "$"
        text = ".text"
        data = ".data"
        aggiungi_dati = False
        diz_dati = self.istruzioni.diz_dati
        chiave = 268500991
        indirizzo_iniziale = 268500992 
        indirizzo_finale = 0
        intero_at = indirizzo_iniziale
        intero_at_text = 4194304
        nome_at = "$at"
        pc = self.istruzioni.pc
        diz_indirizzi_text = self.istruzioni.diz_indirizzi_text
        diz_text = self.istruzioni.diz_text
        meno = '-'
        meno_zero_x = "-0x"
        zero_x = "0x"
        aperta_tonda = '('
        chiusa_tonda = ')'
        nome_registro = "" 
        valore_posizione = 0
        intero_byte_memoria = 0
        istruzione_mips = ""
        not_in_range = True
        prima_posizione = ""
        seconda_posizione = ""
        terza_posizione = ""
        stringa_salto = ""
        carattere_virgoletta = "'"
        stringa_valore_intero = ""
        registro_trovato = False
        stringa_tipo = ""
        byte = ".byte"
        word = ".word"
        half = ".half"
        asciiz = ".asciiz"
        ascii = ".ascii"
        insieme_byte_ascii = {".byte",".ascii",".asciiz"}
        syscall = "syscall"
        zero = "0"
        chiave_indirizzi = ""
        aggiungi_zeri = 0
        controlla_len = 0
        stringa_pipeline_syscall = "F D X M W"
        commento = '#'
        piu = '+'
        indice_riga_precedente = -1
        indice_riga_pre_precedente = -1
        bool_salto = False
        bool_saltato = False
        bool_analizza_con_esecuzione = True
        totale_clocks = 4
        self.conta_clocks = 4
        data_hazards_totali = 0
        control_hazards = 0
        control_hazards_totali = 0 
        tupla_control_hazards = ""
        messaggio_hazards = ""
        messaggio_hazard_inizio = "È presente un control hazard perchè la condizione dell'istruzione branch '"
        aggiorna_loops_prossima_riga = False
        stringa_loops = "" # Usata per i loops se si salta ( non fa lo stesso di stringa_salto)
        
        for reg in self.insieme_registri: # Faccio un reset dei registri in quanto ho generato i registri e simulato 
            # il ritrovamento di possibili stalli durante la lettura del testo. 
            reg.vai_a_writeback()
            reg.riga_registro = ""
            reg.riga_precedente = ""
            reg.istruzione_mips = ""
            reg.istruzione_precedente = ""

        
        while indice < len(self.testo_modificato):
            indice_secondario = 0
            for valore in self.testo_modificato[indice]:
                if self.testo_modificato[indice][0].startswith(commento):
                    break
                if self.testo_modificato[indice][0].startswith(punto):
                    if valore == data:
                        aggiungi_dati = True
                    if valore == text:
                        aggiungi_dati = False
                        indirizzo_finale = chiave
                        self.istruzioni.diz_dati = diz_dati
                    break
                if aggiungi_dati:
                    if indice_secondario == 0:
                        chiave_vettori = valore
                        valore_in_lista = 0
                        if stringa_tipo != "":
                            if stringa_tipo in insieme_byte_ascii and self.testo_modificato[indice][1] == word:
                                controlla_len = intero_byte_memoria%4 
                                if controlla_len != 0:
                                    controlla_len = 4 - controlla_len
                                for _ in range(0,controlla_len):
                                    chiave += 1 
                                    diz_dati[chiave] = 0
                            elif stringa_tipo in insieme_byte_ascii and self.testo_modificato[indice][1] == half:
                                controlla_len = intero_byte_memoria%2 
                                for _ in range(0,controlla_len):
                                    chiave += 1 
                                    diz_dati[chiave] = 0
                            elif stringa_tipo == half and self.testo_modificato[indice][1] == word:   
                                controlla_len = intero_byte_memoria%4 
                                if controlla_len != 0 and controlla_len != 2:
                                    controlla_len = 3 - controlla_len  # 3 e non 4 perchè 2 (non una) posizioni già aggiunte dall'half
                                for _ in range(0,controlla_len):
                                    chiave += 1 
                                    diz_dati[chiave] = 0
                            self.diz_indirizzi[chiave_vettori] = chiave + 1  # Per indirizzo corretto 
                        else:
                            self.diz_indirizzi[chiave_vettori] = indirizzo_iniziale
                    elif indice_secondario > 1:
                        if stringa_tipo == half:
                            intero_byte_memoria += 2
                        elif stringa_tipo == word:
                            intero_byte_memoria += 4
                        else:
                            intero_byte_memoria += 1
                        if len(valore) == 1:
                            if stringa_tipo == word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista 
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-6:-4],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-8:-6],16))
                            elif stringa_tipo == half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))              
                            elif stringa_tipo == asciiz:
                                chiave += 1
                                diz_dati[chiave] = ord(valore)
                                intero_byte_memoria += 1
                                chiave += 1
                                diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == ascii:
                                chiave += 1
                                diz_dati[chiave] = ord(valore)
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                        elif valore.startswith(zero_x) or valore.startswith(meno_zero_x):
                            if stringa_tipo == word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore,16),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista 
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-6:-4],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-8:-6],16))
                            elif stringa_tipo == half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore,16),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))              
                            elif stringa_tipo == asciiz:
                                    for carattere in valore:
                                        chiave += 1
                                        diz_dati[chiave] = ord(carattere)
                                        intero_byte_memoria += 1
                                    chiave += 1
                                    diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == ascii:
                                for carattere in valore:
                                        chiave += 1
                                        diz_dati[chiave] = ord(carattere)
                                        intero_byte_memoria += 1
                                intero_byte_memoria -= 1 # perche incrementato prima
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore,16),32)[2:] # escludo 0x
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))               
                        elif valore.isdigit() or valore[1:].isdigit(): # Per interi sia positivi che negativi
                            if stringa_tipo == word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista 
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-6:-4],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-8:-6],16))
                            elif stringa_tipo == half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))              
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(int(valore),32)[2:] # escludo 0x
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                        elif valore[0] == carattere_virgoletta and valore[-1] == carattere_virgoletta: # è un carattere
                            if stringa_tipo == word:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(ord(valore[1]),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista 
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-6:-4],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-8:-6],16))
                            elif stringa_tipo == half:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(ord(valore[1]),32)[2:] # escludo 0x
                                aggiungi_zeri = 8 - len(valore_in_lista) # Non dovrebbe superare 8 di len
                                valore_in_lista = zero*aggiungi_zeri + valore_in_lista
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                                chiave += 1
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-4:-2],16))              
                            elif stringa_tipo == asciiz: # Non dovrebbe succedere 
                                    chiave += 1
                                    diz_dati[chiave] = ord(valore[1])
                                    chiave += 1
                                    diz_dati[chiave] = 0
                                    intero_byte_memoria += 1
                            elif stringa_tipo == ascii: # Non dovrebbe succedere 
                                chiave += 1
                                diz_dati[chiave] = ord(valore[1])
                            else:
                                chiave += 1
                                valore_in_lista = istruzioni_mips.tohex(ord(valore[1]),32)[2:] # escludo 0x
                                diz_dati[chiave] = istruzioni_mips.toint(int(valore_in_lista[-2:],16))
                        else:
                            if stringa_tipo == asciiz:
                                for carattere in valore:
                                    chiave += 1
                                    diz_dati[chiave] = ord(carattere)
                                    intero_byte_memoria += 1
                                chiave += 1
                                diz_dati[chiave] = 0 # terminatore 0
                            elif stringa_tipo == ascii: 
                                for carattere in valore:
                                    chiave += 1
                                    diz_dati[chiave] = ord(carattere)
                                    intero_byte_memoria += 1
                                intero_byte_memoria -= 1 # perche incrementato prima
                    else:
                        stringa_tipo = valore
                        if stringa_tipo == asciiz and indice_secondario == len(self.testo_modificato[indice])-1:
                            chiave += 1
                            diz_dati[chiave] = 0 # Per stringa vuota aggiungiamo il terminatore 0
                            intero_byte_memoria += 1  
                    indice_secondario += 1 
                    continue
                if aggiorna_loops_prossima_riga: # loop caso particolare
                    self.reset_calcolo_loop = True
                    aggiorna_loops_prossima_riga = False
                if valore in self.diz_salti and indice_secondario != len(self.testo_modificato[indice])-1 or len(self.testo_modificato[indice]) == 1:
                     # Risolviamo possibili problemi legati ai salti
                    if len(self.testo_modificato[indice]) == 1: 
                        if valore == syscall:
                            totale_clocks += 1
                            self.conta_clocks += 1
                            for chiave in self.diz_loops:
                                if self.diz_loops[chiave][1] == True:
                                    self.diz_loops[chiave][2] += 1
                            pc.intero += 4
                            program_counter = pc.intero
                            # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
                            if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
                                if totale_clocks == self.ciclo_di_clock and not self.bool_clock_trovato:
                                    self.bool_clock_trovato = True
                                    self.diz_hazards["WB"] = "("+str(indice+1)+") "+syscall
                                    self.bool_pipeline_wb = True
                                elif self.bool_clock_trovato:
                                    if self.bool_pipeline_if:
                                        self.ciclo_di_clock = 0 # ho finito la ricerca
                                    elif self.bool_pipeline_id:
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
                                                self.diz_hazards["IF"] = "("+str(indice+1)+") "+syscall   
                                        else:
                                            self.diz_hazards["IF"] = "("+str(indice+1)+") "+syscall
                                        self.bool_pipeline_if = True
                                    elif self.bool_pipeline_ex:
                                        self.diz_hazards["ID"] = "("+str(indice+1)+") "+syscall
                                        self.bool_pipeline_id = True
                                    elif self.bool_pipeline_mem:                            
                                        self.diz_hazards["EX"] = "("+str(indice+1)+") "+syscall
                                        self.bool_pipeline_ex = True
                                    elif self.bool_pipeline_wb:
                                        self.diz_hazards["MEM"] = "("+str(indice+1)+") "+syscall
                                        self.bool_pipeline_mem = True
                            # diz_pipeline[chiave_diz_ris] = [indice+1,program_counter,valore,stringa_pipeline_syscall,0,control_hazards,totale_clocks]
                            diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": program_counter, "Istruzione Mips": valore, "Rappresentazione Pipeline": stringa_pipeline_syscall, "Numero Data Hazards": 0, "Numero Control Hazards": control_hazards, "Valore Clock": totale_clocks, "Hazard Trovato": [] }
                            if bool_messaggi_hazards:
                                diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                            indice_riga_pre_precedente = indice_riga_precedente
                            indice_riga_precedente = indice
                        else:
                            # diz_pipeline[chiave_diz_ris] = [indice+1,valore] # riga come Q: (nessuna riga di codice)
                            diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": 0, "Istruzione Mips": valore, "Rappresentazione Pipeline": "Nessuna istruzione in questa riga", "Numero Data Hazards": 0, "Numero Control Hazards": 0, "Valore Clock": 0, "Hazard Trovato": [] } # riga come Q: (nessuna riga di codice)
                            if bool_messaggi_hazards:
                                diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                            if valore in self.diz_loops:
                                if (stringa_loops == "" and self.diz_loops[valore][1] == False)  or (valore == stringa_loops and self.diz_loops[valore][1] == True):
                                    self.valore_loop = valore # dovrebbe essere il label di testo
                                    aggiorna_loops_prossima_riga = True
                        chiave_diz_ris += 1
                    else:
                        if self.testo_modificato[indice][1] not in self.insieme_istruzioni:
                            if self.testo_modificato[indice][1] == syscall:
                                totale_clocks += 1
                                self.conta_clocks += 1
                                for chiave in self.diz_loops:
                                    if self.diz_loops[chiave][1] == True:
                                        self.diz_loops[chiave][2] += 1
                                pc.intero += 4
                                program_counter = pc.intero
                                # Analizzo le istruzioni nella pipeline durante un determinato ciclo di clock
                                if self.ciclo_di_clock != 0: # Non vengono risolti i casi con clock minore di 5
                                    if totale_clocks == self.ciclo_di_clock and not self.bool_clock_trovato:
                                        self.bool_clock_trovato = True
                                        self.diz_hazards["WB"] = "("+str(indice+1)+") "+syscall
                                        self.bool_pipeline_wb = True
                                    elif self.bool_clock_trovato:
                                        if self.bool_pipeline_if:
                                            self.ciclo_di_clock = 0 # ho finito la ricerca
                                        elif self.bool_pipeline_id:
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
                                                    self.diz_hazards["IF"] = "("+str(indice+1)+") "+syscall   
                                            else:
                                                self.diz_hazards["IF"] = "("+str(indice+1)+") "+syscall
                                            self.bool_pipeline_if = True
                                        elif self.bool_pipeline_ex:
                                            self.diz_hazards["ID"] = "("+str(indice+1)+") "+syscall
                                            self.bool_pipeline_id = True
                                        elif self.bool_pipeline_mem:                            
                                            self.diz_hazards["EX"] = "("+str(indice+1)+") "+syscall
                                            self.bool_pipeline_ex = True
                                        elif self.bool_pipeline_wb:
                                            self.diz_hazards["MEM"] = "("+str(indice+1)+") "+syscall
                                            self.bool_pipeline_mem = True
                                # diz_pipeline[chiave_diz_ris] = [indice+1,program_counter,valore,stringa_pipeline_syscall,0,control_hazards,totale_clocks]
                                diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": program_counter, "Istruzione Mips": self.diz_righe[indice+1], "Rappresentazione Pipeline": stringa_pipeline_syscall, "Numero Data Hazards": 0, "Numero Control Hazards": control_hazards, "Valore Clock": totale_clocks, "Hazard Trovato": [] }
                                if bool_messaggi_hazards:
                                    diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                                if valore in self.diz_loops: # loop syscall
                                    if (stringa_loops == "" and self.diz_loops[valore][1] == False)  or (valore == stringa_loops and self.diz_loops[valore][1] == True):
                                        self.reset_calcolo_loop = True
                                        self.valore_loop = valore
                                indice_riga_pre_precedente = indice_riga_precedente
                                indice_riga_precedente = indice
                                chiave_diz_ris += 1
                                break
                            else: # Caso non implementato correttamente ( non dovrebbe mai succedere)
                                # diz_pipeline[chiave_diz_ris] = [indice+1,valore] # riga come Q: (nessuna riga di codice)
                                diz_pipeline[chiave_diz_ris] = {"Riga": indice+1, "Program Counter": 0, "Istruzione Mips": valore, "Rappresentazione Pipeline": "Nessuna istruzione in questa riga", "Numero Data Hazards": 0, "Numero Control Hazards": 0, "Valore Clock": 0, "Hazard Trovato": [] } # riga come Q: (nessuna riga di codice)
                                if bool_messaggi_hazards:
                                    diz_pipeline[chiave_diz_ris]["Messaggio"] = ""
                                # if valore in self.diz_loops:
                                    # aggiorna_loops_prossima_riga = True
                                    # self.valore_loop = valore # potrebbe essere errato, non so cosa viene trovato qua
                            chiave_diz_ris += 1
                        else: # abbiamo label più istruzione
                            if valore in self.diz_loops: # loop normalmente
                                if (stringa_loops == "" and self.diz_loops[valore][1] == False)  or (valore == stringa_loops and self.diz_loops[valore][1] == True):
                                    self.reset_calcolo_loop = True
                                    self.valore_loop = valore
                    indice_secondario += 1 
                    continue
                if valore in self.insieme_istruzioni: # Controllo istruzione
                     istruzione_precedente = istruzione_mips
                     istruzione_mips = valore
                     valore_posizione = 1
                     indice_secondario += 1 
                     continue
                if valore.startswith(dollaro): # Controllo registri
                    if valore[1] in self.iniziali_registri:
                        for reg in self.insieme_registri:
                            if reg.nome == valore: # Se il registro esiste già lo prendiamo dall'insieme
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
                                # in seconda e terza posizione potremmo star usando registri $1,$2,$3 ecc...
                    else: # consideriamo $zero come valore numerico 0
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
                            assert("errore: numero in prima posizione")
                            print("errore: numero in prima posizione")
                        else:
                            prima_posizione = valore
                            valore_posizione += 1 # mmm non credo serva ma per ora lascio stare
                    elif valore_posizione == 2: 
                        if (valore[0].isdigit() or valore[0] == meno or valore[0] == piu) and aperta_tonda not in valore: # Potremmo avere 100($s7), e vari casi particolari
                            stringa_corretta = valore
                            if stringa_corretta.startswith(piu):
                                stringa_corretta = stringa_corretta[1:] # rimuovo il + fastidioso
                            if stringa_corretta.startswith(zero_x) or stringa_corretta.startswith(meno_zero_x): # per esadecimali
                                seconda_posizione = istruzioni_mips.toint(int(stringa_corretta, 16))
                            else:
                                seconda_posizione = int(stringa_corretta)
                        else:
                            if valore in self.diz_indirizzi:
                                seconda_posizione = self.diz_indirizzi[valore] # passo l'indirizzo 
                                if seconda_posizione not in diz_dati: # Caso particolare dovuto ad avere una struttura dati ascii come ultimo valore.
                                    diz_dati[seconda_posizione] = 0
                                    indirizzo_finale = seconda_posizione 
                                chiave_indirizzi = valore
                            elif valore in diz_text:
                                seconda_posizione = diz_text[valore]
                                chiave_indirizzi = valore
                            elif aperta_tonda in valore:
                                nome_registro = valore[valore.index(aperta_tonda)+1: valore.index(chiusa_tonda)] 
                                if valore[0] == aperta_tonda: # Consideriamo ($s7) per esempio
                                    registro_trovato = False 
                                    for reg in self.insieme_registri:
                                        if reg.nome == nome_registro:
                                            if reg.intero in diz_dati:         
                                                seconda_posizione = reg.intero
                                                not_in_range = False
                                            if not_in_range: # Simulo la memoria
                                                chiave = indirizzo_finale
                                                for chiavi in range(0,reg.intero - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
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
                                        if elem == aperta_tonda:
                                            break
                                        else:
                                            stringa_valore_intero += elem
                                    if stringa_valore_intero.startswith(piu): # potrei avere +5($s7), quel piu lo rimuovo
                                        stringa_valore_intero = stringa_valore_intero[1:]
                                    chiave_vettori = valore[0:valore.index(aperta_tonda)]
                                    for reg in self.insieme_registri:
                                        if reg.nome == nome_registro:
                                            if stringa_valore_intero.isdigit() or stringa_valore_intero[0] == carattere_virgoletta or stringa_valore_intero[0] == meno or stringa_valore_intero.startswith(zero_x): # ho trovato 1($s7)
                                                if stringa_valore_intero.startswith(zero_x) or stringa_valore_intero.startswith(meno_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if reg.intero + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = reg.intero + intero_stringa
                                                    not_in_range = False
                                                elif reg.intero + intero_stringa in diz_dati:
                                                    seconda_posizione = reg.intero + intero_stringa
                                                    not_in_range = False
                                                elif not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    for chiavi in range(0,reg.intero + intero_stringa - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = reg.intero + intero_stringa
                                                    indirizzo_finale = chiave
                                            elif piu in stringa_valore_intero: # ho trovato array+100($s7)
                                                chiave_vettori = stringa_valore_intero[0:stringa_valore_intero.index(piu)]
                                                stringa_valore_intero = stringa_valore_intero[stringa_valore_intero.index(piu)+1:]
                                                if stringa_valore_intero.startswith(zero_x) or stringa_valore_intero.startswith(meno_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi text prima del piu
                                                # Potrebbe essere rindondante questo elif
                                                elif reg.intero + intero_indirizzo + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    not_in_range = False
                                                elif reg.intero + intero_indirizzo + intero_stringa in diz_dati:
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    not_in_range = False
                                                elif not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    for chiavi in range(0,reg.intero + intero_indirizzo + intero_stringa - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = reg.intero + intero_indirizzo + intero_stringa
                                                    indirizzo_finale = chiave
                                            else: # ho trovato array($s7)
                                                # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi text prima del piu
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                # Potrebbe essere rindondante questo elif
                                                elif reg.intero + intero_indirizzo in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                    not_in_range = False
                                                elif reg.intero + intero_indirizzo in diz_dati:
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                    not_in_range = False
                                                elif not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    for chiavi in range(0,reg.intero + intero_indirizzo - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = reg.intero + intero_indirizzo
                                                    indirizzo_finale = chiave 
                                            registro_trovato = True
                                            break
                                    if not registro_trovato:
                                        if stringa_valore_intero == "": # Caso $zero o $0 e da errori in mars
                                            seconda_posizione = 0 # Andra in out of range
                                        else: # Permetto l'uso di registri come $zero o $0 ecc... se i valori sono corretti non si hanno problemi sul simulatore Mars e quindi nemmeno qui
                                            # Altrimenti si avranno eccezioni su python o risultati indesiderati. 
                                            if stringa_valore_intero.isdigit() or stringa_valore_intero[0] == carattere_virgoletta or stringa_valore_intero[0] == meno or stringa_valore_intero.startswith(zero_x): # ho trovato 1($zero)
                                                if stringa_valore_intero.startswith(zero_x) or stringa_valore_intero.startswith(meno_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = intero_stringa
                                                    not_in_range = False
                                                elif intero_stringa in diz_dati:
                                                    seconda_posizione = intero_stringa
                                                    not_in_range = False
                                                elif not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    for chiavi in range(0,intero_stringa - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = intero_stringa
                                                    indirizzo_finale = chiave
                                            elif piu in stringa_valore_intero: # ho trovato array+100($zero)
                                                chiave_vettori = stringa_valore_intero[0:stringa_valore_intero.index(piu)]
                                                stringa_valore_intero = stringa_valore_intero[stringa_valore_intero.index(piu)+1:]
                                                if stringa_valore_intero.startswith(zero_x) or stringa_valore_intero.startswith(meno_zero_x):
                                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                                elif stringa_valore_intero[0] == carattere_virgoletta:
                                                    intero_stringa = ord(stringa_valore_intero[1])
                                                else:
                                                    intero_stringa = int(stringa_valore_intero)
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi text prima del piu
                                                elif intero_indirizzo + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    not_in_range = False
                                                elif intero_indirizzo + intero_stringa in diz_dati:
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    not_in_range = False
                                                elif not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    for chiavi in range(0,intero_indirizzo + intero_stringa - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = intero_indirizzo + intero_stringa
                                                    indirizzo_finale = chiave
                                            else: # ho trovato array($zero)
                                                # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi text prima del piu
                                                if chiave_vettori in self.diz_indirizzi:
                                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                                if chiave_vettori in diz_text: # per la puo succedere
                                                    intero_indirizzo = diz_text[chiave_vettori]
                                                    seconda_posizione = intero_indirizzo
                                                # Potrebbe essere rindondante questo elif
                                                elif intero_indirizzo in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                                    seconda_posizione = intero_indirizzo
                                                    not_in_range = False
                                                elif intero_indirizzo in diz_dati:
                                                    seconda_posizione = intero_indirizzo
                                                    not_in_range = False
                                                elif not_in_range: # Simulo la memoria
                                                    chiave = indirizzo_finale
                                                    for chiavi in range(0,intero_indirizzo - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                                        chiave += 1
                                                        diz_dati[chiave] = 0
                                                    seconda_posizione = intero_indirizzo
                                                    indirizzo_finale = chiave          
                            elif piu in valore: # il piu è almeno in seconda posizione 
                                chiave_vettori = valore[0:valore.index(piu)]
                                stringa_valore_intero = valore[valore.index(piu)+1:]
                                if stringa_valore_intero.startswith(zero_x) or stringa_valore_intero.startswith(meno_zero_x):
                                    intero_stringa = istruzioni_mips.toint(int(stringa_valore_intero,16))
                                elif stringa_valore_intero[0] == carattere_virgoletta:
                                    intero_stringa = ord(stringa_valore_intero[1])
                                else:
                                    intero_stringa = int(stringa_valore_intero)
                                if chiave_vettori in self.diz_indirizzi:
                                    intero_indirizzo = self.diz_indirizzi[chiave_vettori]
                                if chiave_vettori in diz_text: # per istruzione la puo succedere
                                    intero_indirizzo = diz_text[chiave_vettori]
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                # intero_indirizzo viene sempre trovato in quanto c'é un nome di indirizzi data o indirizzi text prima del piu     
                                elif intero_indirizzo + intero_stringa in diz_indirizzi_text: # Funziona, ma causera problemi se vogliamo fare per esempio una jalr in una pseudo istruzione
                                    # non presente quindi nel testo. Potremmo simularlo facendo una jump piu avanti ma non traduce l'esecuzione corretta
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                    not_in_range = False
                                elif intero_indirizzo + intero_stringa in diz_dati:
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                    not_in_range = False
                                elif not_in_range: # Simulo la memoria
                                    chiave = indirizzo_finale
                                    for chiavi in range(0, intero_indirizzo + intero_stringa - indirizzo_finale + 3): # +3 per evitare out of ranges nelle istruzioni
                                        chiave += 1
                                        diz_dati[chiave] = 0
                                    seconda_posizione = intero_indirizzo + intero_stringa
                                    indirizzo_finale = chiave
                            elif carattere_virgoletta in valore: # per caratteri ascii  
                                seconda_posizione = ord(valore[1])
                            else:
                                seconda_posizione = valore
                        valore_posizione += 1
                    elif valore_posizione == 3: #potrebbe essere un else...
                        if valore[0].isdigit() or valore[0] == meno or valore[0] == piu:
                            stringa_corretta = valore
                            if stringa_corretta.startswith(piu):
                                stringa_corretta = stringa_corretta[1:] # rimuovo il + fastidioso
                            if stringa_corretta.startswith(zero_x) or stringa_corretta.startswith(meno_zero_x): # per esadecimali
                                terza_posizione = istruzioni_mips.toint(int(stringa_corretta, 16))
                            else:
                                terza_posizione = int(stringa_corretta)
                        elif carattere_virgoletta in valore: # per caratteri ascii  
                                terza_posizione = ord(valore[1])
                        else:
                            if valore in self.diz_indirizzi: # da capire se succede ( forse per le istruzioni branch)
                                terza_posizione = self.diz_indirizzi[valore]
                            else:
                                terza_posizione = valore           
                indice_secondario += 1
                if(indice_secondario == len(self.testo_modificato[indice])): # Simuliamo l'istruzione
                    pc.intero += 4 # incremento il program counter
                    #print(pc.intero)
                    program_counter = pc.intero
                    stringa_loops = ""
                    operazione = chiama_istruzioni_mips(self.istruzioni, istruzione_mips, prima_posizione, seconda_posizione, terza_posizione)
                    if type(operazione) == tuple: # se sono tuple allora si fa un salto
                        if(operazione[1]): # se booleano a True
                            bool_salto = True  
                            stringa_loops = operazione[0]
                        stringa_salto = operazione[0]
                        if istruzione_mips in self.istruzioni_branch:
                            self.istruzione_pre_precedente = istruzione_mips   
                    # Qua trova_valori_pipeline
                    risultato_per_pipeline = Simulatore.trova_valori_per_pipeline(self,istruzione_precedente,indice_riga_precedente,indice_riga_pre_precedente,program_counter,totale_clocks,nome_registro,indice,self.testo_modificato[indice],
                                                                                bool_salto,bool_saltato,data_hazards_totali,control_hazards_totali,control_hazards,bool_decode,bool_forwarding,bool_messaggi_hazards,bool_analizza_con_esecuzione)
                    if self.reset_calcolo_loop: # reset loops
                        if self.stringa_clocks_pre_loops+self.valore_loop not in diz_hazards and self.aggiorna_pre_loop:
                            diz_hazards[self.stringa_clocks_pre_loops+self.valore_loop] = self.conta_clocks
                        self.conta_clocks = 1
                        self.reset_calcolo_loop = False
                        self.aggiorna_pre_loop = False
                    diz_pipeline[chiave_diz_ris] = risultato_per_pipeline[0]
                    totale_clocks = risultato_per_pipeline[1]
                    data_hazards_totali = risultato_per_pipeline[2]
                    control_hazards_totali = risultato_per_pipeline[3]
                    if tupla_control_hazards != "":
                        # diz_risultato[chiave_diz_ris].append(tupla_control_hazards)
                        diz_pipeline[chiave_diz_ris]["Hazard Trovato"] = tupla_control_hazards
                        riga_branch = str(tupla_control_hazards[0])
                        tupla_control_hazards = ""
                        if bool_messaggi_hazards:
                            messaggio_hazards = messaggio_hazard_inizio+istruzione_precedente+"' a riga "+riga_branch+" è soddisfatta"
                            # diz_risultato[chiave_diz_ris].append(messaggio_hazards)
                            diz_pipeline[chiave_diz_ris]["Messaggio"] = messaggio_hazards
                    chiave_diz_ris += 1
                    if bool_salto:
                        bool_saltato = True
                    else:
                        bool_saltato = False
                    
                    indice_riga_pre_precedente = indice_riga_precedente
                    indice_riga_precedente = indice
                    
                    # if stringa_salto != "":
                    if istruzione_mips not in self.istruzioni_jump and bool_salto: # caso jump non causa control hazards
                        control_hazards = 1
                    else:
                        control_hazards = 0 
                    if type(stringa_salto) == int and bool_salto:
                        indice = stringa_salto - 1 
                        # il pc é modificato nella jalr
                    elif bool_salto: 
                        indice = self.diz_salti[stringa_salto] - 1 # -1 perchè si incrementa di 1 alla fine del ciclo
                        pc.intero = diz_text[stringa_salto] - 4
                    if stringa_salto != "" and istruzione_mips not in self.istruzioni_jump:
                        indice_possibile_salto = self.diz_salti[stringa_salto] - 1
                        tupla_control_hazards = indice_riga_precedente+1, indice_possibile_salto+2
                        if not tupla_control_hazards in self.insieme_control_hazards:
                            self.insieme_control_hazards.add(tupla_control_hazards)
                        if not bool_salto:
                            tupla_control_hazards = ""
                    if istruzione_mips in self.istruzioni_load and (chiave_indirizzi in self.diz_indirizzi or chiave_indirizzi in diz_text): # Simulo at quando eseguo una istruzione load con label  
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
        #print(diz_dati)
        #print(diz_indirizzi)
        #print(diz_indirizzi_text)
        chiave_loop = "Cicli di clock nel loop "
        for chiave in self.diz_loops:
            intero = 1
            for indice_lista in range(0,len(self.diz_loops[chiave][3])):
                diz_hazards[chiave_loop+chiave+" ("+str(intero)+") "+"(x"+str(self.diz_loops[chiave][3][indice_lista][2])+")"] = self.diz_loops[chiave][3][indice_lista][0]
                intero += 1
    
        if self.valore_loop == "(Nessun loop trovato)":
            diz_hazards["Nessun loop trovato, cicli di click trovati"] = self.conta_clocks  
        if self.conta_clocks != 0 and self.valore_loop != "(Nessun loop trovato)":       
            diz_hazards["Cicli di clock dopo i possibili loop "] = self.conta_clocks
        diz_hazards["Data Hazards Totali"] = data_hazards_totali
        diz_hazards["Control Hazards Totali"] = control_hazards_totali
        diz_hazards["Cicli di Clock"] = totale_clocks
        if ciclo_di_clock > totale_clocks:
            diz_hazards["IF"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["ID"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["EX"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["MEM"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
            diz_hazards["WB"] = "Nessuna istruzione trovata perchè l'esecuzione del codice è terminata. Inserire un ciclo di clock più piccolo"
        lista_data_hazards = list(self.insieme_data_hazards)
        lista_data_hazards.sort()
        lista_control_hazards = list(self.insieme_control_hazards)
        lista_control_hazards.sort()
        if len(lista_control_hazards) > len(lista_data_hazards):
            differenza = len(lista_control_hazards) - len(lista_data_hazards)
            for _ in range(0,differenza):
                lista_data_hazards.append([])
        elif len(lista_data_hazards) > len(lista_control_hazards):
            differenza = len(lista_data_hazards) - len(lista_control_hazards)
            for _ in range(0,differenza):
                lista_control_hazards.append([])
        diz_hazards["Data Hazards Trovati"] = lista_data_hazards
        diz_hazards["Control Hazards Trovati"] = lista_control_hazards 
        for reg in self.insieme_registri:
            if reg.nome == "$a0":
                print("qua")
                print(reg.intero)
                break
        # rimuovo il program counter se il program counter è disabilitato
        # infatti il program counter calcolato è errato  perchè non calcola le pseudoistruzioni in questo caso
        # Il codice funziona sempre tranne se si usano istruzioni che lo necessitano ( per esempio jal, jalr)
        # In quel caso il program counter deve essere corretto e quindi per ogni istruzione il calcolo delle pseudoistruzioni generate deve essere corretto
        # Ogni istruzione nuova aggiunta dovrebbe avere questi calcoli ( altrimenti è bene non fare uso di jal e jalr e disattivare il program counter)
        if not bool_program_counter: 
            for diz in diz_pipeline:
                del diz_pipeline[diz]["Program Counter"]
        #print(pc.intero)
        #print(diz_text)
        # print(self.diz_indirizzi)
        # print(self.testo_modificato)
        #print(diz_dati)
        #print(lista_data_hazards)
        
        return diz_pipeline, diz_hazards # Bisogna ritornare la soluzione pipeline
       