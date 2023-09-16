# MIPS

The program executes MIPS assembly code written in the text file (in my case "testo.txt", but it can be any text file). It generates 4 JSON files containing a lot of data related to the pipeline (stalls, clock cycles, hazards, ecc...) and 
it can generate one Excel file that can be used to see the data found. 

Instructions on how to run the program and how to add new MIPS instructions are in the instructions.txt file.

The simulator can run Mips programs that have data structures (.data segment) and Mips instructions (.text segment) or programs that only have Mips instructions. 
The simulator is intended to run programs that are correctly written (no memory errors, correct instruction inputs, ecc...). So unless you are an expert in MIPS programming and know what you are doing i suggest you to test your program in the MARS IDE (or any other IDE for MIPS).  

These are all the instructions supported by the simulator: or, and, ori, andi, xor, xori, subi, sub, add, addi, addiu, addu, slt, sle, j, jal, jalr, beq, beqz, bne, bnez, bge, bgez, blt, bltz, move, lui, srl , sll , li, la, lh, lhu, lw, lb, lbu, sw, sh, sb. (sle doesn't have the program counter implementation! So don't use the -pc commnad line argument if you are using sle).

These are all the data structures data types supported: .bytes, .half, .word, .ascii, .asciiz .

Here is an example on what the program can find:

The user runs the program in the command line shell: "python esegui_simulatore.py -f -cl 14 -exp -exh testo.txt"

The MIPS code inserted by the user in the testo.txt file:

<p align="center">
  <img src= "https://github.com/Maxitoth/MIPS/assets/105019914/caeb8154-20a1-4b13-8634-55c20d7abc23" width="300" heigth="250">
</p>

The Pipeline rappresentation showing all the instructions and stalls in every pipeline stage during the program execution (since the user ran the program with the -f command line argument, the forwarding technique has been applied):

<p align="center">
  <img src= "https://github.com/Maxitoth/MIPS/assets/105019914/551a484d-2b1b-4951-aa63-0eb5828d00a0" width="800" heigth="750">
</p>





