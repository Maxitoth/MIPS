# MIPS

Viene simulato il codice mips inserito nel file di testo testoEsame.txt. Questo per ottenere dati relativi alla pipeline.
Il codice deve essere stato testato su Mars ( compilato ed eseguito). Deve risultare senza errori.

Il simulatore ha i suoi limiti. Questi sono scritti in vari commenti all'inizio del file simulatore.py.

I dati di tipo .byte, .half, .word, .ascii, .asciiz sono gestiti. Ma ci sono alcune complicazioni con ascii e asciiz durante l'analisi del testo.

Come scritto nel file simulatore.py non tutte le istruzioni mips sono simulabili.

Le pseudoistruzioni non vengono incluse o aggiunte nel testo. Quindi se si esegue un salto ad un indirizzo di una pseudoistruzione ( possibile tramite istruzione jalr ) ci sarà sicuramente un errore. 

Per aggiungere istruzioni:

In simulatore.py

1) aggiungere l'istruzione nell'insieme insieme_istruzioni ( se l'istruzione é di tipo jump o branch aggiungerla anche all'insieme corrispondente)
Le istruzioni save e load dovrebbero essere tutte state simulate.
Per le jump manca solo la jr.
2) Le istruzioni di branch and link sono un caso particolare non gestito. Bisognerebbe molto probabilmente modificare il codice in trova_valori_per_pipeline. 

In program_counter.py
(Opzionale ma necessario se si esegue un istruzione di tipo jump o branch che permette un salto utilizzando l'indirizzo dell'istruzione nel testo ( sostanzialmente il program counter)).

1) 
