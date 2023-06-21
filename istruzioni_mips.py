
import registro

# La funzione si occupa di trovare il valore esadecimale corretto per una architettura a nbits
# Nel mio caso 32 bit. 

def tohex(val, nbits):
    return hex((val + (1 << nbits)) % (1 << nbits))
   
# La funzione si occupa di trovare il valore corretto intero da esadecimale per un architettura a 32 bit.   
    
def toint(val):
    return -(val & 0x80000000) | (val & 0x7fffffff)


# La funzione si occupa di eseguire uno shift right logic di val posizioni. 

def srl_bit(esadecimale, val):
    stringa_bin_ris = ""
    stringa_bin_secondaria = ""
    zero = "0"
    stringa_shifter = ""
    esadecimale = esadecimale[2:] # rimuovo 0x
    esadecimale_ris = ""
    # Devo avere 8 esadecimali (aggiungo zeri)
    esadecimale_ris = esadecimale_ris.join(zero for _ in range(8-len(esadecimale))) + esadecimale
    # Numero di zeri da aggiungere per lo shift
    stringa_shifter = stringa_shifter.join(zero for _ in range(0, val))
    for elem in esadecimale_ris: # Converto ogni esadecimale in binario (4 bit per ogni esadecimale)
        stringa_bin_secondaria = bin(int(elem,16))[2:] # rimuovo 0b ([2:])
        # Servono 4 bit (aggiungo zeri)
        stringa_bin_secondaria = ''.join(zero for _ in range(4-len(stringa_bin_secondaria))) + stringa_bin_secondaria 
        stringa_bin_ris += stringa_bin_secondaria 
    stringa_bin_ris = stringa_shifter + stringa_bin_ris[0:len(stringa_bin_ris)-val] # Ottengo la stringa risultante dallo shift
    stringa_bin_ris = tohex(int(stringa_bin_ris,2),32) # Riconverto in esadecimale
    return stringa_bin_ris

# La funzione si occupa di eseguire uno shift left logic di val posizioni

def sll_bit(esadecimale, val):
    stringa_bin_ris = ""
    stringa_bin_secondaria = ""
    zero = "0"
    stringa_shifter = ""
    esadecimale = esadecimale[2:]
    esadecimale_ris = ""
    # Devo avere 8 esadecimali (aggiungo zeri)
    esadecimale_ris = esadecimale_ris.join(zero for _ in range(8-len(esadecimale))) + esadecimale
    # Numero di zeri da aggiungere per lo shift
    stringa_shifter = stringa_shifter.join(zero for _ in range(0, val))
    for elem in esadecimale_ris: # Converto ogni esadecimale in binario (4 bit per ogni esadecimale)
        stringa_bin_secondaria = bin(int(elem,16))[2:] # rimuovo 0b ([2:])
        # Servono 4 bit (aggiungo zeri)
        stringa_bin_secondaria = ''.join(zero for _ in range(4-len(stringa_bin_secondaria))) + stringa_bin_secondaria 
        stringa_bin_ris += stringa_bin_secondaria  
    stringa_bin_ris = stringa_bin_ris[-len(stringa_bin_ris)+val:] + stringa_shifter # Ottengo la stringa risultante dallo shift
    stringa_bin_ris = tohex(int(stringa_bin_ris,2),32) # Riconverto in esadecimale
    return stringa_bin_ris       

# La classe istruzioni
# La classe ha vari dizionari che vengono condivisi con il simulatore nel metodo simula_codice_mips
# Il registro program counter (viene salvato come registro, potrei semplicemente usarlo come intero, anche se preferisco cosi)
# Il registro $ra viene inizializzato qui.

class Istruzioni: 
    
    def __init__(self):
        self.ultimo_valore_possibile = 272629759
        # dizionario con 65536 valori per simulare la memoria iniziale (valori positivi)
        self.diz_dati = {key: 0 for key in range(268435456, 268500993)} 
        for key in range(1, 65537): # dizionario con 65536 valori per simulare la memoria iniziale (valori negativi)
            self.diz_dati[-key] = 0
        self.diz_indirizzi_text = {}
        self.diz_text = {}

        # Il program counter potrebbe essere pensato come un semplice intero che si incrementa
        # Salvarlo come registro non è necessario, tuttavia la classe registro salva un nome e un valore, per cui ho preferito questo approccio.
        self.pc = registro.Registro("pc", 4194300, "program counter") # il program counter non ha un valore numerico, devo inserire una stringa che non interferisca con il codice
        self.pc_finale = 0
        self.ra = registro.Registro("$ra", 0, "$31")
        self.bool_program_counter = True
    # Potrei aggiungere qua il registro at e poi aggiungerlo all'insieme registri in simula_codice_mips
    
    # Valori da non cambiare
    chiave = ""
    
    zero = "0"
    intero = 32
    
    stringa_meno_zero_x = "-0x"
    stringa_lb_f = "0xffffff"
    stringa_lh_f = "0xffff"
    stringa_zero_x = "0x" 
    
    # il metodo si occupa di incrementare il program counter per ogni pseudoistruzione trovata
    # solo se si vuole simulare il program counter
    
    def incrementa_program_counter(self):
        if self.bool_program_counter:
            while self.diz_indirizzi_text[self.pc.intero+4] == "": # Simulo program counter
                self.pc.intero += 4
                if self.pc.intero + 4 not in self.diz_indirizzi_text:
                    break
    
    
    # Ogni istruzione simula l'andamento del program counter grazie alla corretta rappresentazione
    # del dizionario diz_indirizzi_text ( quindi della parte .text di mars)
    
    # Viene ritornata una stringa per ogni metodo (non per le istruzioni che eseguono salti). Questo in realtà è ridondante al momento.
    
    # Quando si usa una tupla_valori è perchè l'istruzione mips associata puo avere diversi input.
    # Esempio: or $t1, $t1, 70
    #          or $t1, 70
    
    # I metodi che riguardano le istruzioni che eseguono salti devono sempre avere 2 output 
    # tipicamente una stringa e poi un booleano ( la jalr ha un intero)
    
    # Le altre istruzioni devono assolutamente avere un unico output
    
    # Il metodo si occupa di simulare le istruzioni mips or e ori
    
    def oor(self, tupla_valori):
        Istruzioni.incrementa_program_counter(self)        
        if isinstance(tupla_valori[0],int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if tupla_valori[2] == "": # Check su terza posizione (usato o meno)
            intero = tupla_valori[1]
            tupla_valori[0].intero = tupla_valori[0].intero | intero
        else:
            primo_registro_o_intero = tupla_valori[1]
            secondo_registro_o_intero = tupla_valori[2]
            if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero | secondo_registro_o_intero
            elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero.intero | secondo_registro_o_intero.intero
            elif isinstance(primo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero | secondo_registro_o_intero.intero
            elif isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero.intero | secondo_registro_o_intero  
        stringa_esadecimale = tohex(tupla_valori[0].intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        tupla_valori[0].intero = toint(int(stringa_esadecimale, 16))       
        return "registro modificato"
    
    # Il metodo si occupa di simulare le istruzioni mips xor e xori
    
    def xor(self, tupla_valori):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(tupla_valori[0],int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if tupla_valori[2] == "": # Check su terza posizione (usato o meno)
            intero = tupla_valori[1]
            tupla_valori[0].intero = tupla_valori[0].intero ^ intero
        else:
            primo_registro_o_intero = tupla_valori[1]
            secondo_registro_o_intero = tupla_valori[2]
            if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero ^ secondo_registro_o_intero
            elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero.intero ^ secondo_registro_o_intero.intero
            elif isinstance(primo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero ^ secondo_registro_o_intero.intero
            elif isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero.intero ^ secondo_registro_o_intero
        stringa_esadecimale = tohex(tupla_valori[0].intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        tupla_valori[0].intero = toint(int(stringa_esadecimale, 16))      
        return "registro modificato"
    
    # Il metodo si occupa di simulare le istruzioni mips and e andi
    
    def aand(self, tupla_valori):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(tupla_valori[0],int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if tupla_valori[2] == "": # Check su terza posizione (usato o meno)
            intero = tupla_valori[1]
            tupla_valori[0].intero = tupla_valori[0].intero & intero
        else:
            primo_registro_o_intero = tupla_valori[1]
            secondo_registro_o_intero = tupla_valori[2]
            if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero & secondo_registro_o_intero
            elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero.intero & secondo_registro_o_intero.intero
            elif isinstance(primo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero & secondo_registro_o_intero.intero
            elif isinstance(secondo_registro_o_intero,int):
                tupla_valori[0].intero = primo_registro_o_intero.intero & secondo_registro_o_intero      
        stringa_esadecimale = tohex(tupla_valori[0].intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        tupla_valori[0].intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato" 
    
    # Il metodo si occupa di simulare l'istruzione mips addu
    
    def addu(self, registro_destinazione, primo_registro_o_intero, secondo_registro_o_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!"  # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero + secondo_registro_o_intero
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero.intero + secondo_registro_o_intero.intero
        elif isinstance(primo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero + secondo_registro_o_intero.intero
        elif isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero.intero + secondo_registro_o_intero     
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato" 
    
    # Il metodo si occupa di simulare l'istruzione mips addi    
    
    def addi(self, registro_destinazione, registro_o_intero, secondo_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori 
        if isinstance(registro_o_intero,int):
            registro_destinazione.intero = registro_o_intero + secondo_intero
        else:
            registro_destinazione.intero = registro_o_intero.intero + secondo_intero
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips addiu
    
    def addiu(self, registro_destinazione, registro_o_intero, secondo_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori 
        if isinstance(registro_o_intero,int):
            registro_destinazione.intero = registro_o_intero + secondo_intero
        else:
            registro_destinazione.intero = registro_o_intero.intero + secondo_intero
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips add
    
    def add(self, registro_destinazione, primo_registro_o_intero, secondo_registro_o_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero + secondo_registro_o_intero
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero.intero + secondo_registro_o_intero.intero
        elif isinstance(primo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero + secondo_registro_o_intero.intero
        elif isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero.intero + secondo_registro_o_intero     
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips subi
    
    def subi(self, registro_destinazione, registro_o_intero, secondo_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(registro_o_intero,int):
            registro_destinazione.intero = registro_o_intero - secondo_intero
        else:
            registro_destinazione.intero = registro_o_intero.intero - secondo_intero
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips sub
    
    def sub(self, registro_destinazione, primo_registro_o_intero, secondo_registro_o_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero - secondo_registro_o_intero
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero.intero - secondo_registro_o_intero.intero
        elif isinstance(primo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero - secondo_registro_o_intero.intero
        elif isinstance(secondo_registro_o_intero,int):
            registro_destinazione.intero = primo_registro_o_intero.intero - secondo_registro_o_intero
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))      
        return "registro modificato"

    # Il metodo si occupa di simulare l'istruzione mips sle
    
    def sle(self, registro_destinazione, primo_registro_o_intero, secondo_registro_o_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero <= secondo_registro_o_intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero <= secondo_registro_o_intero.intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0
        elif isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero <= secondo_registro_o_intero.intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0
        elif isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero <= secondo_registro_o_intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0      
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips slt
    
    def slt(self, registro_destinazione, primo_registro_o_intero, secondo_registro_o_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero < secondo_registro_o_intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero < secondo_registro_o_intero.intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0
        elif isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero < secondo_registro_o_intero.intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0
        elif isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero < secondo_registro_o_intero:
                registro_destinazione.intero = 1
            else:
                registro_destinazione.intero = 0      
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips lui
    
    def lui(self, registro_destinazione, intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_esadecimale = sll_bit(tohex(intero,32),16) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
         
    # Il metodo si occupa di simulare l'istruzione mips sll       
    
    def sll(self, registro_destinazione, primo_registro_o_intero, secondo_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_esadecimale = ""
        if isinstance(primo_registro_o_intero,int):
            stringa_esadecimale = sll_bit(tohex(primo_registro_o_intero,32),secondo_intero) # controllo sul valore per dare una giusta 
            # rappresentazione a 32 bit
            registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        else:
            stringa_esadecimale = sll_bit(tohex(primo_registro_o_intero.intero,32),secondo_intero) # controllo sul valore per dare una giusta 
            # rappresentazione a 32 bit
            registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips srl
    
    def srl(self, registro_destinazione, primo_registro_o_intero, secondo_intero): 
        Istruzioni.incrementa_program_counter(self)
        # Potrebbe non funzionare. Usa la stessa strutture del sll. Va testato
        if isinstance(registro_destinazione,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_esadecimale = ""
        if isinstance(primo_registro_o_intero,int):
            stringa_esadecimale = srl_bit(tohex(primo_registro_o_intero,32),secondo_intero)
            # controllo sul valore per dare una giusta 
            # rappresentazione a 32 bit
            registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        else:
            stringa_esadecimale = srl_bit(tohex(primo_registro_o_intero.intero,32),secondo_intero) # controllo sul valore per dare una giusta 
            # rappresentazione a 32 bit
            registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips sw
    
    def sw(self, primo_registro, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(primo_registro,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_hex_primo_registro = tohex(primo_registro.intero,self.intero)
        stringa_hex_primo_registro = stringa_hex_primo_registro[2:] # rimuovo 0x
        aggiungi_zeri = 8 - len(stringa_hex_primo_registro)
        stringa_hex_primo_registro = self.zero*aggiungi_zeri + stringa_hex_primo_registro 
        self.diz_dati[chiave_in_diz] = int(stringa_hex_primo_registro[-2:],16)
        self.diz_dati[chiave_in_diz+1] = int(stringa_hex_primo_registro[-4:-2],16)
        self.diz_dati[chiave_in_diz+2] = int(stringa_hex_primo_registro[-6:-4],16)
        self.diz_dati[chiave_in_diz+3] = int(stringa_hex_primo_registro[-8:-6],16)
        return "memoria modificata"
    
    # Il metodo si occupa di simulare l'istruzione mips sh
    
    def sh(self, primo_registro, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(primo_registro,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_hex_primo_registro = tohex(primo_registro.intero,self.intero)
        stringa_hex_primo_registro = stringa_hex_primo_registro[2:] # rimuovo 0x
        aggiungi_zeri = 8 - len(stringa_hex_primo_registro)
        stringa_hex_primo_registro = self.zero*aggiungi_zeri + stringa_hex_primo_registro 
        self.diz_dati[chiave_in_diz] = int(stringa_hex_primo_registro[-2:],16)
        self.diz_dati[chiave_in_diz+1] = int(stringa_hex_primo_registro[-4:-2],16)
        return "memoria modificata"
    
    # Il metodo si occupa di simulare l'istruzione mips sb
    
    def sb(self, primo_registro, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(primo_registro,int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori 
        stringa_hex_primo_registro = tohex(primo_registro.intero,self.intero)
        stringa_hex_primo_registro = stringa_hex_primo_registro[2:] # rimuovo 0x
        stringa_hex_primo_registro = stringa_hex_primo_registro[-2:]
        self.diz_dati[chiave_in_diz] = int(stringa_hex_primo_registro,16)
        return "memoria modificata"
    
    # Il metodo si occupa di simulare l'istruzione mips blt
    
    def blt(self, primo_registro_o_intero, secondo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero < secondo_registro_o_intero:
                salto = True
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero < secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero < secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero < secondo_registro_o_intero:
                salto = True 
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips bltz
    
    def bltz(self, primo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero < 0:
                salto = True
        else:
            if primo_registro_o_intero.intero < 0:
                salto = True
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips bne
    
    def bne(self, primo_registro_o_intero, secondo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero != secondo_registro_o_intero:
                salto = True
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero != secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero != secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(secondo_registro_o_intero,int):  
            if primo_registro_o_intero.intero != secondo_registro_o_intero:
                salto = True 
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips bnez
    
    def bnez(self, primo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero != 0:
                salto = True
        else:
            if primo_registro_o_intero.intero != 0:
                salto = True
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips bge
    
    def bge(self, primo_registro_o_intero, secondo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero >= secondo_registro_o_intero:
                salto = True
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero >= secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero >= secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(secondo_registro_o_intero,int):  
            if primo_registro_o_intero.intero >= secondo_registro_o_intero:
                salto = True 
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips bgez
    
    def bgez(self, primo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero >= 0:
                salto = True
        else:
            if primo_registro_o_intero.intero >= 0:
                salto = True
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips beq
    
    def beq(self, primo_registro_o_intero, secondo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero,int) and isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero == secondo_registro_o_intero:
                salto = True
        elif not isinstance(primo_registro_o_intero,int) and not isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero == secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(primo_registro_o_intero,int):
            if primo_registro_o_intero == secondo_registro_o_intero.intero:
                salto = True
        elif isinstance(secondo_registro_o_intero,int):
            if primo_registro_o_intero.intero == secondo_registro_o_intero:
                salto = True 
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips beqz
    
    def beqz(self, primo_registro_o_intero, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = False
        if isinstance(primo_registro_o_intero, int):
            if primo_registro_o_intero == 0:
                salto = True
        else:
            if primo_registro_o_intero.intero == 0:
                salto = True
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips j
    
    def j(self, stringa):
        Istruzioni.incrementa_program_counter(self)
        salto = True 
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips jal
    
    def jal(self, stringa):
        pc_piu_quattro = True
        Istruzioni.incrementa_program_counter(self)
        salto = True
        if pc_piu_quattro:
            self.pc.intero += 4 
        self.ra.intero = self.pc.intero
        return stringa, salto
    
    # Il metodo si occupa di simulare l'istruzione mips jalr
    
    def jalr(self, tupla_valori):
        pc_piu_quattro = True
        Istruzioni.incrementa_program_counter(self)
        salto = True
        intero = ""
        if pc_piu_quattro:
            self.pc.intero += 4 
        if tupla_valori[1] == "":
            self.ra.intero = self.pc.intero
            intero = self.diz_indirizzi_text[tupla_valori[0].intero] # Non funziona per istruzioni non nelle righe del testo (generate da mars)
            # Bisogna usare una jalr verso un indirizzo di un nome nel text o una istruzione del testo originale.
            self.pc.intero = tupla_valori[0].intero - 4 # lo incrementiamo alla prossima istruzione quindi -4
        else:
            tupla_valori[0].intero = self.pc.intero
            intero = self.diz_indirizzi_text[tupla_valori[1].intero] # Non funziona per istruzioni non nelle righe del testo (generate da mars)
            # Bisogna usare una jalr verso un indirizzo di un nome nel text o una istruzione del testo originale.
            self.pc.intero = tupla_valori[1].intero - 4 # lo incrementiamo alla prossima istruzione quindi -4
        return intero, salto
    
    # Il metodo si occupa di simulare l'istruzione mips move
    
    def move(self, registro_destinazione, registro_o_intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        if isinstance(registro_o_intero, int):
            registro_destinazione.intero = registro_o_intero
        else:
            registro_destinazione.intero = registro_o_intero.intero
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato" 
    
    # Il metodo si occupa di simulare l'istruzione mips li
        
    def li(self, registro_destinazione, intero):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        # Per evitare possibili errori usiamo le stesse funzionalita di la
        registro_destinazione.intero = intero
        stringa_esadecimale = tohex(registro_destinazione.intero,self.intero) # controllo sul valore per dare una giusta 
        # rappresentazione a 32 bit
        registro_destinazione.intero = toint(int(stringa_esadecimale, 16))
        return "registro modificato" 
     
    # Il metodo si occupa di simulare l'istruzione mips lb 
        
    def lb(self, registro_destinazione, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_binario = hex(self.diz_dati[chiave_in_diz])[2:] # rimuovo 0x
        aggiungi_zeri = 2 - len(stringa_binario)
        stringa_binario = self.zero*aggiungi_zeri + stringa_binario
        stringa_bit = bin(int(stringa_binario[0],16))
        if len(stringa_bit) == 6: # per esempio caso 0b1000 (8 bit a byte e se ho 1 inserisco 0xff...)
            stringa_binario = self.stringa_lb_f+stringa_binario 
            registro_destinazione.intero = toint(int(stringa_binario,16)) # negativo
        else:
            registro_destinazione.intero = int(stringa_binario,16) # positivo
        return "registro modificato"  
    
    # Il metodo si occupa di simulare l'istruzione mips lbu
    
    def lbu(self, registro_destinazione, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        stringa_binario = hex(self.diz_dati[chiave_in_diz])[2:] # rimuovo 0x
        registro_destinazione.intero = int(stringa_binario,16) # positivo
        return "registro modificato"      
    
    # Il metodo si occupa di simulare l'istruzione mips lh
    
    def lh(self, registro_destinazione, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        # Salvo i valori presi dalla memoria ([2:] per rimuovere 0x)
        lista_byte = [hex(self.diz_dati[chiave_in_diz+1])[2:],hex(self.diz_dati[chiave_in_diz])[2:]]
        # Unisco ogni stringa esadecimale per ottenere la stringa risultante
        stringa_binario = ''.join(self.zero*(2-len(x))+x for x in lista_byte)
        stringa_bit = bin(int(stringa_binario[0],16))
        if len(stringa_bit) == 6: # per esempio caso 0b1000 (8 bit a byte e se ho 1 inserisco 0xff...)
            stringa_binario = self.stringa_lh_f+stringa_binario 
            registro_destinazione.intero = toint(int(stringa_binario,16)) # negativo
        else:
            registro_destinazione.intero = int(stringa_binario,16) # positivo
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips lhu
    
    def lhu(self, registro_destinazione, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        # Salvo i valori presi dalla memoria ([2:] per rimuovere 0x)
        lista_byte = [hex(self.diz_dati[chiave_in_diz+1])[2:],hex(self.diz_dati[chiave_in_diz])[2:]]
        # Unisco ogni stringa esadecimale per ottenere la stringa risultante
        stringa_binario = ''.join(self.zero*(2-len(x))+x for x in lista_byte)
        registro_destinazione.intero = int(stringa_binario,16) # positivo
        return "registro modificato"
    
    # Il metodo si occupa di simulare l'istruzione mips lw
    
    def lw(self, registro_destinazione, chiave_in_diz):
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        # Salvo i valori presi dalla memoria ([2:] per rimuovere 0x)
        lista_byte = [hex(self.diz_dati[chiave_in_diz+3])[2:],hex(self.diz_dati[chiave_in_diz+2])[2:], 
                      hex(self.diz_dati[chiave_in_diz+1])[2:], hex(self.diz_dati[chiave_in_diz])[2:]]
        # Unisco ogni stringa esadecimale per ottenere la stringa risultante
        stringa_binario = ''.join(self.zero*(2-len(x))+x for x in lista_byte)
        registro_destinazione.intero = toint(int(stringa_binario,16)) # positivo o negativo
        return "registro modificato" 
    
    # Il metodo si occupa di simulare l'istruzione mips la
    
    def la(self, registro_destinazione, indirizzo): 
        Istruzioni.incrementa_program_counter(self)
        if isinstance(registro_destinazione, int):
            return "!" # se per qualche motivo il registro usato fosse $zero o $0 non viene fatto niente
            # è un operazione valida ma non cambia nulla durante l'esecuzione.
            # Evito possibili errori
        registro_destinazione.intero = indirizzo
        return "registro modificato"
    
