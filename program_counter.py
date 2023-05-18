
# La classe del program counter, con vari insiemi.
# Ogni insieme ha istruzioni che hanno valori in comune.
# Il valore in comune sono il numero di pseudoistruzioni in base alla casistica x trovata.
# Ogni istruzione puo avere un numero di pseudoistruzioni variabile.
# Se avessi tutte le casistiche avrei tutti gli insiemi possibili, tuttavia per averle dovrei avere
# un grande numero di istruzioni simulabili.
# Se non si vuole simulare il program counter, cio si puo fare ma allora non sara possibile saltare
# su una riga di testo (parte .text in mars) perche i vari dizionari che tengono conto della posizione della riga avranno dati errati.
# Serve sempre uno studio approfondito su ogni istruzione per poter simulare il program counter.

class ProgramCounter:
    
    def __init__(self) -> None:
        self.indirizzo_text = 4194300
        self.diz_indirizzi_text = {}
    
    insieme_istruzioni_semplici = {"lui", "srl", "sll", "slt", "j", "jal", "jalr", "move", "xor", "or", "and", "beqz","bgez","bnez","bltz"}
    insieme_ori = {"ori", "xori", "andi"} # range identico 65535 a 0, nessun problema con chars 
    insieme_addi = {"addi", "addiu", "add"} # range identico 32767 a -32768, nessun problema con chars
    insieme_beq_subi = {"beq", "bne", "sub", "subi"} # range identico 32767 a -32768
    insieme_save_load = {"sb","sh","sw","lb","lbu","lh","lhu","lw"} # range identico 32767 a -32768, nessun problema con chars
    insieme_bge = {"bge","blt"}
    istruzione_addu = "addu"
    istruzione_li = "li" # range identico 65535 a -32768, nessun problema con chars
    istruzione_la = "la" # range identico 65535 a -32768, nessun problema con chars
    
    range_sessanta = 65535
    range_piu_trenta = 32767
    range_meno_trenta = -32768
    zero = 0
    
    # Il metodo rende possibile simulare il program counter (il dizionario diz_indirizzi_text viene modificato)
    
    def simula_program_counter(self, istruzione: str, indirizzo_text: int, carattere_trovato: bool, valore, valore_con_tonda_trovato: bool):
        bool_non_aggiungere_altro = False
        if istruzione in self.insieme_addi: # Simulo program counter
            bool_non_aggiungere_altro = bool(carattere_trovato or isinstance(valore,bool) or (self.range_meno_trenta <= valore <= self.range_piu_trenta)) 
            if not bool_non_aggiungere_altro:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 2)
        elif istruzione == self.istruzione_addu:
            bool_non_aggiungere_altro = bool(isinstance(valore,bool) and not carattere_trovato)
            if not bool_non_aggiungere_altro:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 2)
        elif istruzione in self.insieme_beq_subi: # Simulo program counter
            if carattere_trovato:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1)
                bool_non_aggiungere_altro = True
            elif isinstance(valore,bool):
                bool_non_aggiungere_altro = True
            elif self.range_meno_trenta <= valore <= self.range_piu_trenta:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1)
                bool_non_aggiungere_altro = True
            if not bool_non_aggiungere_altro:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 2) 
        elif istruzione == self.istruzione_la: # Simulo program counter
            if carattere_trovato or isinstance(valore,bool):
                bool_non_aggiungere_altro = True
            if not bool_non_aggiungere_altro:
                if self.range_meno_trenta <= valore <= self.range_sessanta:
                    if valore_con_tonda_trovato:
                        indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1) 
                else:
                    if valore_con_tonda_trovato:
                        indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 2)
                    else:
                        indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1) 
        elif istruzione in self.insieme_ori: # Simulo program counter
            bool_non_aggiungere_altro = bool(carattere_trovato or isinstance(valore,bool) or (self.zero <= valore <= self.range_sessanta)) 
            if not bool_non_aggiungere_altro:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 2)
        elif istruzione in self.insieme_save_load: # Simulo program counter
            bool_non_aggiungere_altro = bool(carattere_trovato or isinstance(valore,bool) or (self.range_meno_trenta <= valore <= self.range_piu_trenta))
            if not bool_non_aggiungere_altro:
                if valore_con_tonda_trovato:
                    indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 2)
                else:
                    indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1) 
        elif istruzione == self.istruzione_li: # Simulo program counter
            bool_non_aggiungere_altro = bool(carattere_trovato or isinstance(valore,bool) or (self.range_meno_trenta <= valore <= self.range_sessanta)) 
            if not bool_non_aggiungere_altro:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1)
        elif istruzione in self.insieme_bge: # Simulo program counter
            bool_non_aggiungere_altro = bool(carattere_trovato or isinstance(valore,bool) or (self.range_meno_trenta <= valore <= self.range_piu_trenta))
            if bool_non_aggiungere_altro:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 1)
            else:
                indirizzo_text = ProgramCounter.trova_indirizzo_testo_corretto(self, indirizzo_text, 3)
        return indirizzo_text
       
    # Il metodo si occupa di aggiungere gli indirizzi corretti, dovuti alle pseudo-istruzioni,
    # nel dizionario contenente gli indirizzi del testo (program counter per quella istruzione)   
    # Si aggiunge una stringa vuota nelle posizioni in cui sono presenti pseudo-istruzioni  
    def trova_indirizzo_testo_corretto(self, indirizzo_text, numero_pseudo_istruzioni):
        for _ in range(0,numero_pseudo_istruzioni):
            indirizzo_text += 4
            self.diz_indirizzi_text[indirizzo_text] = "" 
        return indirizzo_text