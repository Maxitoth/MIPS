# MIPS

Viene simulato il codice mips inserito nel file di testo testo.txt. Questo per ottenere dati relativi alla pipeline.
Il codice deve essere stato testato su Mars (compilato ed eseguito). Deve risultare senza errori. 

Per avviare il programma digitare su console di comandi "python esegui_simulatore.py testo.txt" 
(python o python3, testo.txt è il path del testo)

Sul file esegui_simulatore.py è presente la funzione main e i valori in input inoltre vengono compilati quattro json file con tutti i dati.
Il programma si deve avviare tramite shell e ci sono vari valori in input che si possono inserire in riga di comando anche se tutti hanno un valore di default.
L'unico input che deve essere inserito è il testo (va inserito il path del testo in cui è presente il codice MIPS).

Si può scegliere se eseguire di fare la simulazione con forwarding o meno, con le istruzioni branch a fase di decode o execute, se simulare il program counter 
e se visualizzare quali istruzioni sono nella pipeline a un certo ciclo di clock.
Inoltre si possono abilitare dei messaggi per ogni hazard trovato e creare un file excel con fino a quattro fogli per visualizzare i risultati ottenuti (serve installare xlsxwriter con 
pip install xlsxwriter).
(valori in input a riga di comando, usare python esegui_simulatore.py -h per vedere i vari input e come scriverli)
Vengono anche mostrati i cicli di clock totali e i cicli di clock presenti in ogni ciclo loop di codice trovato. (Funziona bene con un unico ciclo e dovrebbe funzionare anche con più loop in sequenza o loop dentro a loop, ma non posso garantire che sia sempre corretto per programmi grandi o con molti loop)

Il simulatore ha i suoi limiti. Questi sono scritti in vari commenti all'inizio del file simulatore.py.
Sono anche presenti altri commenti su istruzioni_mips.py su come devono essere scritte nuove istruzioni dopo il metodo incrementa_program_counter della classe Istruzioni.

I dati di tipo .byte, .half, .word, .ascii, .asciiz sono gestiti. L'unico carattere da non utilizzare è 'µ' ( usato nell'analisi dei dati .ascii e .asciiz) e la stringa vuota va usata da sola se si usano .ascii o .asciiz (note su simulatore.py nei commenti)

Le pseudoistruzioni non vengono incluse o aggiunte nel testo. Quindi se si esegue un salto ad un indirizzo di una pseudoistruzione (possibile tramite istruzione jalr ) ci sarà sicuramente un errore durante la simulazione del codice mips. 

Per aggiungere istruzioni:

In simulatore.py

1) Aggiungere l'istruzione nell'insieme insieme_istruzioni (se l'istruzione é di tipo jump o branch aggiungerla anche all'insieme corrispondente, lo stesso vale per store e load se volete aggiungere istruzioni particolare come per esempio lwl. In generale tutti i casi normali sono stati gestiti (lb, lbu, lh, lhu, lw, sb, sh, sw))
Per le jump manca solo la jr.
2) Le istruzioni di branch and link sono un caso particolare non gestito. Bisognerebbe molto probabilmente modificare il codice in trova_valori_per_pipeline. 

In program_counter.py
(Opzionale ma necessario se si esegue un istruzione di tipo jump o branch che permette un salto utilizzando l'indirizzo dell'istruzione nel testo (sostanzialmente il program counter) o per istruzioni load e save con nomi di testo (esempio: "la $a0, main" e "main: ..." è una riga del testo (non in .data)). Per avere un valore del program counter corretto è necessario che per le istruzioni del testo sia effettivamente simulato il numero di pseudo-istruzioni generate. Se il testo contiene istruzioni per cui il program counter non è simulato è bene non aggiungere l'opzione -pc ed è necessario non fare uso di input particolari descritti ("la $a0, main" o istruzioni "jal e jalr") in quanto i valori saranno errati e l'esecuzione darà risultati errati o si fermerà con errori.

1) Bisogna capire quante pseudo-istruzioni vengono generate a seconda della casistica dell'input inserito per ogni istruzione. Le istruzioni infatti possono generare da 0 a più pseudoistruzioni. Quindi dovrei capire se quella determinata istruzione genera un certo numero di pseudoistruzioni per certi input.
Esempio: l'istruzione add, se sommato un numero che non é nel range da 32767 a -32768 genera 2 pseudo-istruzioni.

Posso poi mettere in insiemi comuni le istruzioni che hanno lo stesso numero di pseudoistruzioni per quelle determinate casistiche. Aggiungere a indirizzo_text + 4 per ogni pseudo-istruzione.
Per casi nuovi aggiungere una variabile che contiene il nome dell'istruzione come stringa. Gestire il nuovo caso aggiungendo un nuova condizione (elif) con il verificarsi della nuova variabile (istruzione == nuova variabile). Adesso dipende tutto dagli input valutati: per esempio un istruzione dell'insieme addi non aggiunge nuove pseudo-istruzioni quando il terzo input è un registro (il valore è un bool) o un carattere (carattere_trovato == True), o quando il terzo input è un intero che si trova nel range 32767 a -32768 (se è esadecimale viene comunque convertito in decimale e deve rispettare questo range), altrimenti sono necessarie due pseudo-istruzioni

In istruzioni_mips.py:

  1) Aggiungere un metodo chiamandolo come l'istruzione mips da simulare.
  2) Il metodo deve sempre cominciare con Istruzioni.incrementa_program_counter(self) (anche se il program counter non è simulato) 
  3) A seconda del tipo di istruzione prendere come riferimento istruzioni già implementate a meno che sia un nuovo tipo di istruzione.
  4) Ogni metodo ha gli input dell'istruzione simulata (beq ha 3 input, beqz ha 2 input, ecc... tranne per alcuni casi tipo le istruzioni jump il ragionamento è sempre questo)
  5) Esempio su come iniziare: Se ho beq $t1, $t2, Cycl il metodo é di questo tipo: beq(self, registro_uno_o_intero_uno, registro_due_o_intero_due, stringa). Implemento i vari controlli (se ho un registro o un intero) e controllo se registro_uno_o_intero_uno == registro_due_o_intero_due. Siccome si tratta di un istruzione di salto devo restituire un booleano (salto) a True o False oltre alla stringa. Per istruzioni non di salto il ragionamento è lo stesso solo che aggiorno l'intero del registro (chiamato di solito registro_destinazione) e restituisco una stringa (non è necessario l'output)
  6) Se un istruzione può essere scritta in piu modi (diverso numero di input) si usa una tupla (tupla_valori). Bisogna prendere i valori dalla tupla ma il ragionamento è lo stesso.
  7) Se l'istruzione permette salti nel testo senza uso di labels ma registri (la jalr per esempio) bisognerà restituire un intero ( la stringa non è presente nell'istruzione in questione e servirà l'implementazione del program counter)
 
