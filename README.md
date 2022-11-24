# MIPS

Viene simulato il codice mips inserito nel file di testo testoEsame.txt. Questo per ottenere dati relativi alla pipeline.
Il codice deve essere stato testato su Mars ( compilato ed eseguito). Deve risultare senza errori.

Alla fine del file simulatore.py é presente un oggetto Simulatore e sotto viene compilato un json file con tutti i dati.

Si può scegliere se eseguire di fare la simulazione con forwarding o meno, con le istruzioni branch a fase di decode o execute e se simulare il program counter.
(booleani true,false in simula_codice_mips del simulatore)

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

1) Bisogna capire quante pseudoistruzioni vengono generate a seconda della casistica x per ogni istruzione. Le istruzioni infatti possono generare da 0 a più pseudoistruzioni. Quindi dovrei capire se quella determinata istruzione genera un certo numero di pseudoistruzioni in certe casistiche.
Esempio: l'istruzione add, se sommato un numero che non é nel range da 32767 a -32768 genera 2 pseudoistruzioni.

Posso poi mettere in insiemi comuni le istruzioni che hanno lo stesso numero di pseudoistruzioni per quelle determinate casistiche.
