# MIPS

Viene simulato il codice mips inserito nel file di testo testo.txt. Questo per ottenere dati relativi alla pipeline.
Il codice deve essere stato testato su Mars ( compilato ed eseguito). Deve risultare senza errori.

Alla fine del file simulatore.py é presente un oggetto Simulatore e sotto viene compilato un json file con tutti i dati.

Si può scegliere se eseguire di fare la simulazione con forwarding o meno, con le istruzioni branch a fase di decode o execute e se simulare il program counter.
(booleani true,false in simula_codice_mips del simulatore)

Il simulatore ha i suoi limiti. Questi sono scritti in vari commenti all'inizio del file simulatore.py.

I dati di tipo .byte, .half, .word, .ascii, .asciiz sono gestiti. Ma ci sono alcune complicazioni con ascii e asciiz durante l'analisi del testo.

Come scritto nel file simulatore.py non tutte le istruzioni mips sono simulabili.

Le pseudoistruzioni non vengono incluse o aggiunte nel testo. Quindi se si esegue un salto ad un indirizzo di una pseudoistruzione ( possibile tramite istruzione jalr ) ci sarà sicuramente un errore durante la simulazione del codice mips. 

Per aggiungere istruzioni:

In simulatore.py

1) Aggiungere l'istruzione nell'insieme insieme_istruzioni ( se l'istruzione é di tipo jump o branch aggiungerla anche all'insieme corrispondente)
Le istruzioni save e load dovrebbero essere tutte state simulate.
Per le jump manca solo la jr.
2) Le istruzioni di branch and link sono un caso particolare non gestito. Bisognerebbe molto probabilmente modificare il codice in trova_valori_per_pipeline. 

In program_counter.py
(Opzionale ma necessario se si esegue un istruzione di tipo jump o branch che permette un salto utilizzando l'indirizzo dell'istruzione nel testo ( sostanzialmente il program counter)).

1) Bisogna capire quante pseudoistruzioni vengono generate a seconda della casistica x per ogni istruzione. Le istruzioni infatti possono generare da 0 a più pseudoistruzioni. Quindi dovrei capire se quella determinata istruzione genera un certo numero di pseudoistruzioni in certe casistiche.
Esempio: l'istruzione add, se sommato un numero che non é nel range da 32767 a -32768 genera 2 pseudoistruzioni.

Posso poi mettere in insiemi comuni le istruzioni che hanno lo stesso numero di pseudoistruzioni per quelle determinate casistiche.

In istruzioni_mips.py:

  1) Aggiungere un metodo chiamandolo come l'istruzione mips da simulare.
  2) Il metodo deve sempre cominciare con Istruzioni.incrementa_program_counter(self) 
  3) A seconda del tipo di istruzione prendere come riferimento istruzioni già implementate a meno che sia un nuovo tipo di istruzione.
  4) Esempio su come iniziare: Se ho beq $t1, $t2, Cycl il metodo é di questo tipo: beq(registro_uno_o_intero_uno,registro_due_o_intero_due, stringa). Implemento i       vari controlli ( se ho un registro o un intero) e controllo se registro_uno_o_intero_uno == registro_due_o_intero_due. Siccome si tratta di un istruzione di salto     devo restituire un booleano (salto) a True o False oltre alla stringa. Per istruzioni non di salto il ragionamento è lo stesso solo che aggiorno l'intero del           registro (chiamato di solito registro_destinazione) e restituisco una stringa ( non serve farlo)
  5) Se un istruzione può essere scritta in piu modi si usa una tupla ( tupla_valori). Bisogna prendere i valori dalla tupla ma il ragionamento è lo stesso.
  6) Se l'istruzione permette salti nel testo senza uso di labels ma registri ( la jalr per esempio) bisognerà restituire un intero ( la stringa non é presente           nell'istruzione in questione e servirà l'implementazione del program counter)
 
