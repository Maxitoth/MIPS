
# La classe del program counter, con vari insiemi.
# Ogni insieme ha istruzioni che hanno valori in comune.
# Il valore in comune sono il numero di pseudoistruzioni in base alla casistica x trovata.
# Ogni istruzione puo avere un numero di pseudoistruzioni variabile.
# Se avessi tutte le casistiche avrei tutti gli insiemi possibili, tuttavia per averle dovrei avere
# un grande numero di istruzioni simulabili.
# Se non si vuole simulare il program counter, cio si puo fare ma allora non sara possibile saltare
# su una riga di testo (parte .text in mars) perche i vari dizionari che tengono conto della posizione della riga avranno dati errati.
# Serve sempre uno studio approfondito su ogni istruzione per poter simulare il program counter.

class Program_counter():
    
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
    
    # Il metodo rende possibile simulare il program counter ( il dizionario diz_indirizzi_text viene modificato)
    
    def simula_program_counter(self, istruzione: str, indirizzo_text: int, carattere_trovato: bool, valore, valore_con_tonda_trovato: bool):
        if istruzione in self.insieme_addi: # Simulo program counter
            if carattere_trovato or type(valore) == bool:
                return indirizzo_text
            if self.range_meno_trenta <= valore <= self.range_piu_trenta:
                return indirizzo_text
            else:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
        if istruzione == self.istruzione_addu:
            if type(valore) == bool and not carattere_trovato:
                return indirizzo_text
            else:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
        if istruzione in self.insieme_beq_subi: # Simulo program counter
            if carattere_trovato:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
            if type(valore) == bool:
                return indirizzo_text
            if self.range_meno_trenta <= valore <= self.range_piu_trenta:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
            else:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = "" 
                return indirizzo_text
        if istruzione == self.istruzione_la: # Simulo program counter
            if carattere_trovato or type(valore) == bool:
                return indirizzo_text
            if self.range_meno_trenta <= valore <= self.range_sessanta:
                if valore_con_tonda_trovato:
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = ""  
                return indirizzo_text
            else:
                if valore_con_tonda_trovato:
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = ""
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = ""
                else:
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = "" 
                return indirizzo_text
        if istruzione in self.insieme_ori: # Simulo program counter
            if carattere_trovato or type(valore) == bool:
                return indirizzo_text
            if self.zero <= valore <= self.range_sessanta:
                return indirizzo_text
            else:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = "" 
                return indirizzo_text
        if istruzione in self.insieme_save_load: # Simulo program counter
            if carattere_trovato or type(valore) == bool:
                return indirizzo_text
            if self.range_meno_trenta <= valore <= self.range_piu_trenta: 
                return indirizzo_text
            else:
                if valore_con_tonda_trovato:
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = ""
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = ""
                else:
                    indirizzo_text += 4
                    self.diz_indirizzi_text[indirizzo_text] = "" 
                return indirizzo_text
        if istruzione == self.istruzione_li: # Simulo program counter
            if carattere_trovato or type(valore) == bool:
                return indirizzo_text
            if self.range_meno_trenta <= valore <= self.range_sessanta:
                return indirizzo_text
            else:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
        if istruzione in self.insieme_bge: # Simulo program counter
            if carattere_trovato or type(valore) == bool:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
            if self.range_meno_trenta <= valore <= self.range_piu_trenta:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                return indirizzo_text
            else:
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = ""
                indirizzo_text += 4
                self.diz_indirizzi_text[indirizzo_text] = "" 
                return indirizzo_text