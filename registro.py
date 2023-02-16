
# La classe Registro
# Ha vari campi utili a simulare la pipeline

class Registro:
    
    def __init__(self, nome, intero):
        self.nome = nome
        self.intero = intero
        self.istruzione_mips = ""
        self.fetch = True
        self.decode = False
        self.execute = False
        self.memory = False
        self.write_back = False
        self.stato_fase = 1
        self.stato_write_back = 5
        self.riga_registro = ""
        self.riga_precedente = ""
        self.istruzione_precedente = "" 
        
        
    def vai_a_writeback(self): # Non utilizzato
        self.fetch = False
        self.decode = False
        self.execute = False
        self.memory = False
        self.write_back = True
        self.stato_write_back = 5
        
    # Il metodo si occupa di cambiare lo stato del registro.   
        
    def cambia_fase(self):
        if self.fetch:
            self.fetch = False
            self.decode = True
            self.stato_fase = 2
        elif self.decode:
            self.decode = False
            self.execute = True
            self.stato_fase = 3
        elif self.execute:
            self.execute = False
            self.memory = True
            self.stato_fase = 4
        elif self.memory:
            self.memory = False
            self.write_back = True
            self.stato_fase = 5
        
         
    